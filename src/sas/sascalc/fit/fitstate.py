"""
Interface to page state for saved fits.

The 4.x sasview gui builds the model, smearer, etc. directly inside the wx
GUI code.  This code separates the in-memory representation from the GUI.
Initially it is used for a headless bumps fitting backend that operates
directly on the saved XML; eventually it should provide methods to replace
direct access to the PageState object so that the code for setting up and
running fits in wx, qt, and headless versions of SasView shares a common
in-memory representation.
"""
from __future__ import print_function, division

import os
import copy
from collections import namedtuple

import numpy as np

from bumps.names import FitProblem

from sasmodels.core import load_model_info
from sasmodels.data import plot_theory
from sasmodels.sasview_model import _make_standard_model, MultiplicationModel, load_custom_model
from sasmodels.weights import MODELS as POLYDISPERSITY_MODELS

from .pagestate import Reader, PageState, SimFitPageState, CUSTOM_MODEL
from .BumpsFitting import SasFitness, ParameterExpressions
from .AbstractFitEngine import FitData1D, FitData2D, Model
from .models import PLUGIN_NAME_BASE, find_plugins_dir
from .qsmearing import smear_selection

# Monkey patch SasFitness class with plotter
def sasfitness_plot(self, view='log'):
    data, theory, resid = self.data.sas_data, self.theory(), self.residuals()
    plot_theory(data, theory, resid, view)
SasFitness.plot = sasfitness_plot

# Use a named tuple for the sasview parameters
PARAMETER_FIELDS = [
    "fitted", "name", "value", "plusminus", "uncertainty",
    "lower", "upper", "units",
    ]
SasviewParameter = namedtuple("Parameter", PARAMETER_FIELDS)

class FitState(object):
    def __init__(self, fitfile):
        self.fitfile = fitfile
        self.simfit = None
        self.fits = []

        reader = Reader(self._add_entry)
        datasets = reader.read(fitfile)
        #print("datasets", datasets[0])
        self._set_constraints()
        #print("loaded", datasets)

    def _add_entry(self, state=None, datainfo=None, format=None):
        """
        Handed to the reader to receive and accumulate the loaded state objects.
        """
        # Note: datainfo is in state.data; format=.svs means reset fit panels
        if isinstance(state, PageState):
            # TODO: shouldn't the update be part of the load?
            state._convert_to_sasmodels()
            self.fits.append(state)
        elif isinstance(state, SimFitPageState):
            self.simfit = state
        else:
            # ignore empty fit info
            pass

    def __str__(self):
        # type: () -> str
        return '<SasFit %s>'%self.fitfile

    def show(self):
        # type: () -> None
        """
        Summarize the fit pages in the state object.
        """
        # Note: _dump_attrs isn't a closure, but putting it here anyway
        # because it is specific to show and doesn't need to be efficient.
        def _dump_attrs(obj, label=""):
            #print(obj)
            print("="*20, label)
            for attr, value in sorted(obj.__dict__.items()):
                if isinstance(value, (list, tuple)):
                    print(attr)
                    for item in value:
                        print("   ", item)
                else:
                    print(attr, value)
        for k, fit in enumerate(self.fits):
            _dump_attrs(fit, label="Fit page "+str(k+1))
        if self.simfit:
            _dump_attrs(self.simfit, label="Constraints")

    def make_fitproblem(self):
        # type: () -> FitProblem
        """
        Build collection of bumps fitness calculators and return the FitProblem.
        """
        # TODO: batch info not stored with project/analysis file (ticket #907)
        models = [make_fitness(state) for state in self.fits]
        if not models:
            raise RuntimeError("Nothing to fit")
        fit_problem = FitProblem(models)
        fit_problem.setp_hook = ParameterExpressions(models)
        return fit_problem

    def _set_constraints(self):
        # type: () -> None
        """
        Adds fit_page and constraints list to each model.

        Raises ValueError if cannot resolve constraints unambiguously.
        """
        # early return if no sim fit
        if self.simfit is None:
            for fit in self.fits:
                fit.fit_page = 'M1'
                fit.constraints = {}
            return

        # Note: simfitpage.py:load_from_save_state relabels the model and
        # constraint on load, replacing the model name in the constraint
        # expression with the new name for every constraint expression. We
        # don't bother to do that here since we don't need to relabel the
        # model ids.
        constraints = {}
        for item in self.simfit.constraints_list:
            # model_cbox in the constraints list should match fit_page_source
            # in the model list.
            pairs = constraints.setdefault(item['model_cbox'], [])
            pairs.append((item['param_cbox'], item['constraint']))

        # No way to uniquely map the page id (M1, M2, etc.) to the different
        # items in fits; neither fit_number nor fit_page_source is in the
        # pagestate for the fit, and neither model_name nor data name are
        # unique.  The usual case of one model per data file will get us most
        # of the way there but there will be ambiguity when the data file
        # is not unique, e.g., when different parts of the data set are
        # fit with different models.  If the same model and same data are
        # used (e.g., with different background, scale or resolution in
        # different segments) then the model-fit association will be assigned
        # arbitrarily based on whichever happens to come first.
        used = []
        for model in self.simfit.model_list:
            matched = 0
            for fit in self.fits:
                #print(model['name'], fit.data_id, model_name(fit), model['model_name'])
                if (fit.data_id == model['name']
                        and model_name(fit) == model['model_name']
                        and fit not in used):
                    fit.fit_page = model['fit_page_source']
                    fit.constraints = constraints.setdefault(fit.fit_page, [])
                    used.append(fit)
                    matched += 1
            if matched > 1:
                raise ValueError("more than one model matches %s"
                                 % model['fit_page_source'])
            elif matched == 0:
                raise ValueError("could not find model %s in file"
                                 % model['fit_page_source'])


def model_name(state):
    # type: (FitState) -> str
    """
    Build the model name out of form factor and structure factor (if present).

    This will be the name that is stored as the model name in the simultaneous
    fit model_list structure corresponding to the form factor and structure
    factor given on the individual fit pages.  The model name is used to help
    disambiguate different SASentry sections with the same dataset.
    """
    # TODO: need better handling of "[plug-in]" prefix for reloaded models
    # The constraint box appears to use the base name while the fit pages
    # prefix the name with "[plug-in] ".
    p_model, s_model = state.formfactorcombobox, state.structurecombobox
    if p_model.startswith(PLUGIN_NAME_BASE):
        p_model = p_model[len(PLUGIN_NAME_BASE):]
    if s_model.startswith(PLUGIN_NAME_BASE):
        s_model = s_model[len(PLUGIN_NAME_BASE):]
    if s_model is not None and s_model != "" and s_model.lower() != "none":
        return '*'.join((p_model, s_model))
    else:
        return p_model

def get_data_weight(state):
    # type: (FitState) -> np.ndarray
    """
    Get error bars on data.  These could be the values computed by reduction
    and stored in the file, the square root of the intensity (if instensity
    is approximately counts), the intensity itself (would be better as a
    percentage of the intensity, such as 2% or 5% depending on relative
    counting time), or one for equal weight uncertainty depending on the
    value of state.dI_*.
    """
    # Cribbed from perspectives/fitting/utils.py:get_weight and
    # perspectives/fitting/fitpage.py: get_weight_flag
    weight = None
    if state.enable2D:
        dy_data = state.data.err_data
        data = state.data.data
    else:
        dy_data = state.data.dy
        data = state.data.y
    if state.dI_noweight:
        weight = np.ones_like(data)
    elif state.dI_didata:
        weight = dy_data
    elif state.dI_sqridata:
        weight = np.sqrt(np.abs(data))
    elif state.dI_idata:
        weight = np.abs(data)
    return weight

_MODEL_CACHE = {}  # type: Dict[str, "SasviewModel"]
def load_model(name):
    # type: (str) -> Optional["SasviewModel"]
    """
    Given a model name load the Sasview shim model from sasmodels.

    If name starts with "[Plug-in]" then load it as a custom model from the
    plugins directory.  This code does not go through the Sasview model manager
    interface since that loads all available models rather than just those
    needed.
    """
    # Remember the models that are loaded so they are only loaded once.  While
    # not strictly necessary (the models will use identical but different model
    # info structure) it saves a little time and memory for the usual case
    # where models are reused for simultaneous and batch fitting.
    if name in _MODEL_CACHE:
        return _MODEL_CACHE[name]
    if name.startswith(PLUGIN_NAME_BASE):
        name = name[len(PLUGIN_NAME_BASE):]
        plugins_dir = find_plugins_dir()
        path = os.path.abspath(os.path.join(plugins_dir, name + ".py"))
        #print("loading custom", path)
        model = load_custom_model(path)
        _MODEL_CACHE[name] = model
    elif name != "" and name.lower() != "none":
        #print("loading standard", name)
        model = _make_standard_model(name)
        _MODEL_CACHE[name] = model
    else:
        model = None
    return model

def parse_optional_float(value):
    # type: str -> Optional[float]
    """
    Convert optional floating point from string to value, returning None
    if string is None, empty or contains the word "None" (case insensitive).
    """
    if value is not None and value != "" and value.lower() != "none":
        return float(value)
    else:
        return None

def make_fitness(state):
    # type: (FitState) -> SasFitness
    """
    Return a Bumps fitness object for the given fit state.

    Raises ValueError if could not parse the fit state.
    """
    # Load the model
    category_name = state.categorycombobox
    form_factor_name = state.formfactorcombobox
    structure_factor_name = state.structurecombobox
    multiplicity = state.multi_factor
    if category_name == CUSTOM_MODEL:
        assert form_factor_name.startswith(PLUGIN_NAME_BASE)
    form_factor_model = load_model(form_factor_name)
    structure_factor_model = load_model(structure_factor_name)
    model = form_factor_model(multiplicity)
    if structure_factor_model is not None:
        model = MultiplicationModel(model, structure_factor_model())

    # Set the dispersity distributions for all model parameters.
    # Default to gaussian
    dists = {par_name + ".type": "gaussian" for par_name in model.dispersion}
    dists.update(state.disp_obj_dict)
    for par_name, dist_name in state.disp_obj_dict.items():
        dispersion = POLYDISPERSITY_MODELS[dist_name]()
        if dist_name == "array":
            dispersion.set_weights(state.values[par_name], state.weights[par_name])
        base_par = par_name.replace('.width', '')
        model.set_dispersion(base_par, dispersion)

    # Put parameter values and ranges into the model
    fitted = []
    for par_tuple in state.parameters + state.fixed_param + state.fittable_param:
        par = SasviewParameter(*par_tuple)
        if par.name not in state.weights:
            # Don't try to set parameter values for array distributions
            # TODO: keep weights filename in the array distribution object
            model.setParam(par.name, parse_optional_float(par.value))
        if par.fitted:
            fitted.append(par.name)
        if par.name in model.details:
            lower = parse_optional_float(par.lower[1])
            upper = parse_optional_float(par.upper[1])
            model.details[par.name] = [par.units, lower, upper]
    #print("pars", model.params)
    #print("limits", model.details)
    #print("fitted", fitted)

    # Set the resolution
    data = copy.deepcopy(state.data)
    if state.disable_smearer:
        smearer = None
    elif state.enable_smearer:
        smearer = smear_selection(data, model)
    elif state.pinhole_smearer:
        # see sasgui/perspectives/fitting/basepage.py: reset_page_helper
        dx_percent = state.dx_percent
        if state.dx_old:
            dx_percent = 100*(state.dx_percent / data.x[0])
        # see sasgui/perspectives/fitting/fitpage.py: _set_pinhole_smear
        percent = dx_percent / 100.
        if state.enable2D:
            # smear_type is Pinhole2D.
            q = np.sqrt(data.qx_data**2 + data.qy_data**2)
            data.dqx_data = data.dqy_data = percent*q
        else:
            data.dx = percent * data.x
            data.dxl = data.dxw = None  # be sure it is not slit-smeared
        smearer = smear_selection(data, model)
    elif state.slit_smearer:
        # see sasgui/perspectives/fitting/fitpage.py: _set_pinhole_smear
        data_len = len(data.x)
        data.dx = None
        data.dxl = (state.dxl if state.dxl is not None else 0.) * np.ones(data_len)
        data.dxw = (state.dxw if state.dxw is not None else 0.) * np.ones(data_len)
        smearer = smear_selection(data, model)
    else:
        raise ValueError("expected resolution specification for fit")

    # Set the data weighting (dI, sqrt(I), I, or uniform)
    weight = get_data_weight(state)

    # Note: wx GUI makes a copy of the data and assigns weight to
    # data.err_data/data.dy instead of using the err_data/dy keywords
    # when creating the Fit object.

    # Make fit data object and set the data weights
    # TODO: check 2D masked data
    if state.enable2D:
        fitdata = FitData2D(sas_data2d=data, data=data.data,
                            err_data=weight)
    else:
        data.mask = (np.isnan(data.y) if data.y is not None
                        else np.zeros_like(data.x, dtype='bool'))
        fitdata = FitData1D(x=data.x, y=data.y,
                            dx=data.dx, dy=weight, smearer=smearer)
        fitdata.set_fit_range(qmin=state.qmin, qmax=state.qmax)
    fitdata.sas_data = data

    # Don't need initial values since they have been stuffed into the model
    # If provided, then they should be one-to-one with the parameter names
    # listed in fitted.
    initial_values = None

    fitmodel = Model(model, fitdata)
    fitmodel.name = state.fit_page
    fitness = SasFitness(
        model=fitmodel,
        data=fitdata,
        constraints=state.constraints,
        fitted=fitted,
        initial_values=initial_values,
        )

    return fitness

class BumpsPlugin:
    """
    Object holding methods for interacting with SasView using the direct
    bumps interface.
    """
    #@staticmethod
    #def data_view():
    #    pass

    #@staticmethod
    #def model_view():
    #    pass

    @staticmethod
    def load_model(filename):
        # type: (str) -> FitProblem
        state = FitState(filename)
        #state.show()
        #print("====\nfit", state)
        problem = state.make_fitproblem()
        #print(problem.show())

        # CRUFT: older bumps doesn't handle missing fit parameters
        from distutils.version import StrictVersion
        from bumps import __version__ as bumps_version
        if StrictVersion(bumps_version) < StrictVersion("0.7.12"):
            if not len(problem.getp()):
                raise ValueError("No fitted parameters in %r." % filename)

        return problem

    #@staticmethod
    #def new_model():
    #    pass


def setup_sasview():
    # type: () -> None
    from sas.sasview.sasview import setup_logging, setup_mpl, setup_sasmodels
    #setup_logging()
    #setup_mpl()
    setup_sasmodels()

def setup_bumps():
    # type: () -> None
    """
    Install the refl1d plugin into bumps, but don't run main.
    """
    import os
    import bumps.cli
    bumps.cli.set_mplconfig(appdatadir=os.path.join('.sasview', 'bumpsfit'))
    bumps.cli.install_plugin(BumpsPlugin)

def bumps_cli():
    # type: () -> None
    """
    Install the SasView plugin into bumps and run the command line interface.
    """
    setup_sasview()
    setup_bumps()
    import bumps.cli
    bumps.cli.main()

if __name__ == "__main__":
    # Allow run with:
    #    python -m sas.sascalc.fit.fitstate
    bumps_cli()
