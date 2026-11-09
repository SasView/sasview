"""
Fitting of a fit page (FW-MVC-DESIGN.md §3.4, Phase 7); it absorbs ``FittingController``.

``FitService.prepare`` sets up the fit problems from the document: one engine instance with
the document's effective state, one smearer built against it from the active dataset, shared
by every dataset of a batch (§9.2 B-2), the datasets in their order (the chain order when chain
fitting), each weighted as the options say. ``outcome`` reads a fit result back.
"""
from __future__ import annotations

import logging

import numpy as np

from sas.qtgui.Perspectives.Fitting.model import rules
from sas.qtgui.Perspectives.Fitting.services.theory import build_smearer, weighted
from sas.sascalc.fit.BumpsFitting import BumpsFit as Fit

logger = logging.getLogger(__name__)


class FitService:

    def __init__(self, kernel_builder) -> None:
        self._builder = kernel_builder

    def prepare(self, doc, constraints, fitter: Fit | None = None, fit_id: int = 0,
                weight_increase: int = 1, page_id: int = 0) -> tuple[list[Fit], int]:
        """The Fit objects for the page (one per dataset; *fitter* is the simultaneous fit's
        shared one) and the next fit id. ValueError if there is nothing to fit."""
        keys = [doc.parameters.legacy_key(k) for k in rules.keys_to_fit(doc)]
        if not keys:
            raise ValueError('Fitting requires at least one parameter to optimize.')
        model = self._builder.build(doc)
        smearer = build_smearer(doc.smearing, doc.data(), model)
        is2d, flag = doc.is2D(), doc.options.theory_weighting
        order = doc.chain_order if doc.flags.chain_fit else doc.dataset_order
        fitters = []
        for dataset_id in order:
            fitter_single = Fit() if fitter is None else fitter
            data = weighted(doc.datasets[dataset_id].data, is2d, flag)
            try:
                fitter_single.set_model(model, fit_id, keys, data=data, constraints=constraints)
            except ValueError as ex:
                raise ValueError("Setting model parameters failed with: %s" % ex)
            fitter_single.set_data(data=data, id=fit_id, smearer=smearer,
                                   qmin=doc.options.qmin, qmax=doc.options.qmax)
            fitter_single.select_problem_for_fit(id=fit_id, value=1)
            fitter_single.set_weight_increase(fit_id, weight_increase)
            if fitter is None:
                fitter_single.fitter_id = [page_id]
            fit_id += 1
            fitters.append(fitter_single)
        return fitters, fit_id

    @staticmethod
    def outcome(result) -> dict[str, tuple[float, float]] | None:
        """{parameter: (value, error)} of a fit result, or None if the fit did not converge (logged)."""
        pvec = [float(p) for p in result.pvec]
        if (result.fitness is None or not np.isfinite(result.fitness)
                or np.any(pvec is None) or not np.all(np.isfinite(pvec))):
            logger.error("Fitting did not converge!" + result.mesg)
            return None
        if result.mesg:
            logger.warning(result.mesg)
        return dict(zip(result.param_list, zip(pvec, result.stderr)))
