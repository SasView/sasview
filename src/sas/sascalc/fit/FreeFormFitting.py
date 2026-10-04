"""
FreeFormFitting is the SasView-side adapter for free-form SAS inversion. All
of the numerics live in the external `ffsi` package, reached through its public
API `ffsi.api.invert()`; this module only translates between SasView's
model / data objects and that API. The model is taken from the GUI selection;
every model ffsi supports is handled (see FREE_FORM_PARAM_MAP). 1D data.

This is a sibling of BumpsFitting: a FitEngine subclass returning FResult
objects through the same FitThread pipeline, so the GUI drives it exactly
like a bumps fit. The optimizer is not bumps -- ffsi solves for the full
parameter distribution(s) (bin weights on a simplex, smoothness-regularized)
in a single constrained solve.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from sas.sascalc.fit.AbstractFitEngine import FitEngine, FResult

if TYPE_CHECKING:
    import numpy as np

logger = logging.getLogger(__name__)

try:
    from ffsi.api import invert

    FFSI_AVAILABLE = True
except ImportError as exc:
    FFSI_AVAILABLE = False
    _FFSI_IMPORT_ERROR = str(exc)
    logger.info("ffsi not available, free-form inversion disabled: %s", exc)

# TODO: Add an input box for this value
DEFAULT_SIGMA = 0.25

FREE_FORM_FIT_PARAMS = ["scale", "background"]

# Per model, the {SasView parameter name: ffsi parameter name} translation the
# API needs. ffsi keys its grids and distributions by its own short names
# ('r', 'l', 'rp', 're')
FREE_FORM_PARAM_MAP = {
    "sphere": {"radius": "r"},
    "cylinder": {"radius": "r", "length": "l"},
    "ellipsoid": {"radius_polar": "rp", "radius_equatorial": "re"},
}

# Models free-form inversion can handle (those ffsi supports).
SUPPORTED_MODELS = frozenset(FREE_FORM_PARAM_MAP)


def model_id(model):
    """The sasmodels id of a SasviewModel, falling back to its name."""
    return getattr(model, "id", model.name)


def is_supported(model):
    """True if free-form inversion can handle this model."""
    return model_id(model) in SUPPORTED_MODELS


@dataclass
class FreeFormDistribution:
    """One fitted parameter distribution, named in SasView terms."""

    param: str  # SasView parameter name, e.g. 'radius', 'length'
    grid: np.ndarray  # bin centers
    weights: np.ndarray  # distribution weights (sum to 1)
    # volume-weighted distribution; single-parameter models only, else None
    volume_weights: np.ndarray = None


@dataclass
class FreeFormResult:
    """
    Output of one inversion: a SasView-side view of an
    `ffsi.api.InversionResult`, carrying only what the GUI plots and the fit
    engine reports. Distributions are named with SasView parameter names.
    """

    scale: float  # SasView scale (volume fraction) = xi * <V> * 1e4
    xi: float  # raw ffsi scale: I_opt = xi * Gw + background
    background: float  # b_opt
    q: np.ndarray  # masked q the inversion ran on
    theory: np.ndarray  # I_opt = xi * Gw + background on q
    residuals: np.ndarray  # (theory - iq) / diq
    chi2: float  # sum(residuals**2) / residuals.size
    distributions: list  # list[FreeFormDistribution]

    def distribution(self, param):
        """The `FreeFormDistribution` for SasView parameter `param`."""
        for dist in self.distributions:
            if dist.param == param:
                return dist
        raise KeyError(
            "No distribution for parameter '%s', have: %s" % (param, ", ".join(d.param for d in self.distributions))
        )


def invert_shape(
    model_name, q, iq, diq, bins, sigma=DEFAULT_SIGMA, sld=None, sld_solvent=None, q_calc=None, resolution_weights=None
):
    """
    Free-form inversion of any supported model, delegated to `ffsi.api.invert`.

    :param model_name: SasView/ffsi model id (see `SUPPORTED_MODELS`)
    :param q: masked scattering vectors
    :param iq: measured intensity I(q)
    :param diq: intensity errors dI(q)
    :param bins: `dict` of `{SasView parameter name: (min, max, nbins)}`
    :param sigma: smoothness regularization weight
    :param sld: particle scattering length density
    :param sld_solvent: solvent scattering length density (drho = sld - sld_solvent)
    :param q_calc: extended q grid for resolution smearing (None = no smearing)
    :param resolution_weights: resolution weight matrix, shape (len(q_calc), len(q))

    The contrast (`sld`, `sld_solvent`) is passed straight through: the API
    builds the Green's tensor with `drho = sld - sld_solvent` baked in and
    returns `scale` as a SasView volume fraction directly. `q_calc` and
    `resolution_weights` are passed through as-is, like `q`/`iq`/`diq`; when both
    are given the API builds and smears the Green's tensor.
    """
    if not FFSI_AVAILABLE:
        raise RuntimeError("ffsi is not installed: %s" % _FFSI_IMPORT_ERROR)
    try:
        name_map = FREE_FORM_PARAM_MAP[model_name]  # SasView -> ffsi
    except KeyError:
        raise ValueError(
            "Free-form inversion does not support the '%s' model (supported: %s)."
            % (model_name, ", ".join(sorted(SUPPORTED_MODELS)))
        ) from None
    ffsi_to_sasview = {ffsi_name: sv for sv, ffsi_name in name_map.items()}

    # Translate the SasView-named bins into the ffsi names the API expects,
    # keeping only the geometric parameters the model inverts.
    grids = {name_map[sv]: spec for sv, spec in bins.items() if sv in name_map}
    missing = set(name_map.values()) - set(grids)
    if missing:
        raise ValueError(
            "No bin specification for parameter(s): %s." % ", ".join(sorted(ffsi_to_sasview[m] for m in missing))
        )

    # q is passed through as-is; invert() owns the backend/dtype conversion
    # (ffsi picks numpy vs cupy from the input arrays), keeping this adapter
    # free of a direct numpy dependency.
    result = invert(
        model_name,
        q,
        iq,
        diq,
        grids,
        sld=sld,
        sld_solvent=sld_solvent,
        sigma=sigma,
        q_calc=q_calc,
        resolution_weights=resolution_weights,
    )

    distributions = [
        FreeFormDistribution(
            param=ffsi_to_sasview[d.name], grid=d.grid, weights=d.weights, volume_weights=d.volume_weights
        )
        for d in result.distributions
    ]
    return FreeFormResult(
        scale=result.scale,
        xi=result.xi,
        background=result.background,
        q=q,
        theory=result.theory,
        residuals=result.residuals,
        chi2=result.chi2,
        distributions=distributions,
    )


class FreeFormFit(FitEngine):
    """
    Fit parameter distribution(s) to the data using free-form inversion (ffsi).

    Driven through the same interface as BumpsFit: set_model()/set_data()
    from the FitEngine base class, then fit() from a FitThread.
    """

    def __init__(self, bins=None, sigma=DEFAULT_SIGMA):
        """
        :param bins: dict {SasView parameter name: (min, max, nbins)}; must
            cover the model's geometric parameters (see FREE_FORM_PARAM_MAP)
        :param sigma: smoothness regularization weight
        """
        FitEngine.__init__(self)
        self.fitter_id = None
        self.bins = dict(bins) if bins else {}
        self.sigma = sigma

    def fit(self, msg_q=None, q=None, handler=None, curr_thread=None, ftol=1.49012e-8, reset_flag=False):
        # ftol/reset_flag are part of the FitThread calling convention but
        # have no meaning for the GALAHAD solve.
        if handler is not None:
            # handler.error() stringifies the last result, so seed one
            handler.set_result("Free-form inversion (GALAHAD SNLS)")

        all_results = []
        for fit_id, arrange in self.fit_arrange_dict.items():
            if not arrange.get_to_fit():
                continue
            if curr_thread is not None:
                curr_thread.isquit()  # raises KeyboardInterrupt on stop

            model = arrange.get_model().model  # the SasviewModel
            model_name = model_id(model)
            if not is_supported(model):
                raise ValueError(
                    "Free-form inversion does not support the '%s' model (supported: %s)."
                    % (model_name, ", ".join(sorted(SUPPORTED_MODELS)))
                )

            # The contrast lets the API return `scale` as a SasView volume
            # fraction. Without it (sld == sld_solvent) there is nothing to
            # report to the model pane.
            sld = model.getParam("sld")
            sld_solvent = model.getParam("sld_solvent")
            if sld == sld_solvent:
                raise ValueError("Free-form inversion needs a non-zero contrast (sld must differ from sld_solvent).")

            fitdata = arrange.get_data()  # FitData1D
            idx = fitdata.idx

            # Resolution smearing rides on the smearer (set from the Resolution
            # tab). Its sasmodels resolution exposes the extended q_calc grid and
            # the (nq_calc, nq) weight matrix; ffsi smears the Green's tensor with
            # them. The weight matrix is built over the full data q, so slice its
            # columns to the qmin/qmax + nonzero-dy fit window (`idx`).
            q_calc = resolution_weights = None
            smearer = getattr(fitdata, "smearer", None)
            resolution = getattr(smearer, "resolution", None)
            if resolution is not None and getattr(resolution, "weight_matrix", None) is not None:
                q_calc = resolution.q_calc
                resolution_weights = resolution.weight_matrix[:, idx]

            result = invert_shape(
                model_name,
                fitdata.x[idx],
                fitdata.y[idx],
                fitdata.dy[idx],
                self.bins,
                sigma=self.sigma,
                sld=sld,
                sld_solvent=sld_solvent,
                q_calc=q_calc,
                resolution_weights=resolution_weights,
            )

            fitting_result = FResult(model=model, data=fitdata, param_list=list(FREE_FORM_FIT_PARAMS))
            fitting_result.theory = result.theory
            # residuals and chi2 come straight from the API (ffsi's
            # (theory - iq)/diq convention, chi2 = sum(res**2)/Npts, matching
            # SasView's calculateChi2).
            fitting_result.residuals = result.residuals
            fitting_result.index = idx
            fitting_result.fitter_id = self.fitter_id
            fitting_result.success = True
            fitting_result.mesg = ""
            fitting_result.pvec = [result.scale, result.background]
            # GALAHAD returns no uncertainties
            fitting_result.stderr = [0.0, 0.0]
            fitting_result.fitness = result.chi2
            # no convergence trace; empty keeps the convergence tab from opening
            fitting_result.convergence = []
            fitting_result.freeform = result
            all_results.append(fitting_result)

        if not all_results:
            raise RuntimeError("Nothing to fit")

        if q is not None:
            q.put(all_results)
            return q
        return all_results
