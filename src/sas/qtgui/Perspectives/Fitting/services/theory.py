"""
Theory calculations of a fit page (FW-MVC-DESIGN.md §3.3 and §3.4, Phase 7).

- ``build_smearer(smearing, data, kernel)``: the resolution of a request, built against the
  request's own engine instance (``smear_selection`` binds both). Never cached.
- ``resolution_of(data)``: the resolution a dataset carries ("Pinhole", "Slit", "Pinhole2d",
  "Hankel Transform" or None), which decides the smearing options it offers.
- ``TheoryService``: makes a ``TheoryRequest`` from the document, runs it with ``Calc1D``/``Calc2D``
  on the existing thread machinery and hands the completion back on the GUI thread; turns the
  return data into a ``DatasetResult`` (theory, residuals, chi², components, effective radius).

``runner`` is the one place that starts a computation: tests replace it with fake jobs that
complete when, and in the order, the test says.
"""
from __future__ import annotations

import copy

import numpy as np
from PySide6 import QtCore
from twisted.internet import threads

from sasmodels.resolution import Pinhole1D, Slit1D
from sasmodels.sesans import SesansTransform

from sas import config
from sas.qtgui.Perspectives.Fitting import FittingUtilities
from sas.qtgui.Perspectives.Fitting.FittingConstants import polydispersity_plot_name
from sas.qtgui.Perspectives.Fitting.model.results import DatasetResult
from sas.qtgui.Perspectives.Fitting.ModelThread import Calc1D, Calc2D
from sas.qtgui.Perspectives.Fitting.services import plots
from sas.qtgui.Perspectives.Fitting.services.requests import TheoryRequest
from sas.qtgui.Plotting.PlotterData import Data1D, Data2D, DataRole
from sas.sascalc.fit.qsmearing import PySmear, PySmear2D, smear_selection

# The smearing tab's accuracy captions, as the 2D smearer takes them
ACCURACY = {'Low': 'low', 'Medium': 'med', 'High': 'high', 'Extra high': 'xhigh'}


def _with_accuracy(smearer, data, accuracy: str):
    if smearer is not None and isinstance(data, Data2D):
        smearer.set_accuracy(accuracy=ACCURACY.get(accuracy, 'low'))
    return smearer


def build_smearer(smearing, data, kernel):
    """The smearer of *smearing* (the document's) for *data*, evaluated with *kernel*; None for none."""
    if data is None:
        return None
    mode = smearing.mode
    if mode in ("Use dQ Data", "Hankel Transform"):
        # The resolution the data carries (the Hankel transform is SESANS data's)
        return _with_accuracy(smear_selection(data, kernel), data, smearing.accuracy)
    if mode == "Custom Pinhole Smear":
        if not smearing.d_up:
            return None
        percent = smearing.d_up / 100.0
        data = copy.deepcopy(data)
        if isinstance(data, Data2D):
            data.dqx_data = data.dqy_data = percent * np.sqrt(data.qx_data ** 2 + data.qy_data ** 2)
        else:
            data.dx = percent * data.x
            data.dxl = data.dxw = None
        return _with_accuracy(smear_selection(data, kernel), data, smearing.accuracy)
    if mode == "Custom Slit Smear":
        if isinstance(data, Data2D):
            return smear_selection(data, kernel)
        width, length = smearing.d_down or 0.0, smearing.d_up or 0.0
        if length < width:
            # The only valid reading of swapped values (the smearing tab warns about it)
            width, length = length, width
        data = copy.deepcopy(data)
        data.dx = None
        data.dxl = length * np.ones(len(data.x))
        data.dxw = width * np.ones(len(data.x))
        return smear_selection(data, kernel)
    return None


def resolution_of(data) -> str | None:
    """The kind of resolution information *data* carries (SmearingWidget.smear_type)."""
    if data is None:
        return None
    smearer = smear_selection(data)
    if isinstance(data, Data2D):
        return "Pinhole2d" if isinstance(smearer, PySmear2D) else None
    if not isinstance(smearer, PySmear):
        return None
    if isinstance(smearer.resolution, SesansTransform):
        return "Hankel Transform"
    if isinstance(smearer.resolution, Pinhole1D):
        return "Pinhole"
    if isinstance(smearer.resolution, Slit1D):
        return "Slit"
    return None


def weighted(data, is2d: bool, flag: int):
    """A copy of *data* whose errors are the weights of *flag* (FittingWidget.addWeightingToData)."""
    new_data = copy.deepcopy(data)
    weight = FittingUtilities.getWeight(data=data, is2d=is2d, flag=flag)
    if is2d:
        new_data.err_data = weight
    else:
        new_data.dy = weight
    return new_data


class TheoryService(QtCore.QObject):
    """One page's theory calculations."""

    _finished = QtCore.Signal(object, object, object)   # done, request, return data

    def __init__(self, exception_handler=None, failure_handler=None) -> None:
        super().__init__()
        self._exception_handler = exception_handler
        self._failure_handler = failure_handler
        # The receiver lives on the GUI thread: completions from a worker are queued to it
        self._finished.connect(self._deliver)
        self.runner = self.compute

    # -- requests ---------------------------------------------------------

    @staticmethod
    def prepare(doc, provenance, kernel) -> TheoryRequest:
        """The request for the dataset of *provenance*, with its own smearer and weights."""
        data = doc.datasets[provenance.dataset_id].data
        weight = FittingUtilities.getWeight(data=data, is2d=doc.is2D(), flag=doc.options.theory_weighting)
        return TheoryRequest(provenance, kernel, data, build_smearer(doc.smearing, data, kernel), weight,
                             doc.options.qmin, doc.options.qmax)

    def run(self, request: TheoryRequest, done, use_threads: bool = True) -> None:
        """Start *request*; ``done(request, return_data)`` is called on the GUI thread
        (return data None if the calculation failed)."""
        self.runner(request, lambda result: self._finished.emit(done, request, result), use_threads)

    @QtCore.Slot(object, object, object)
    def _deliver(self, done, request, result) -> None:
        done(request, result)

    def compute(self, request: TheoryRequest, complete, use_threads: bool = True) -> None:
        """The default runner: Calc1D/Calc2D on a thread (Twisted or the queue), or here."""
        calc = (Calc1D if isinstance(request.data, Data1D) else Calc2D)(
            data=request.data, model=request.kernel, page_id=0, qmin=request.qmin, qmax=request.qmax,
            smearer=request.smearer, state=None, weight=request.weight, fid=None, toggle_mode_on=False,
            completefn=complete, update_chisqr=True, exception_handler=self._exception_handler, source=None)
        if not use_threads:
            result = calc.compute()
            if config.USING_TWISTED:
                complete(result)    # otherwise compute() has called it
        elif config.USING_TWISTED:
            thread = threads.deferToThread(calc.compute)
            thread.addCallback(complete)
            if self._failure_handler is not None:
                thread.addErrback(self._failure_handler)
        else:
            calc.queue()
            calc.ready(2.5)

    # -- outcomes ---------------------------------------------------------

    @staticmethod
    def outcome(doc, request: TheoryRequest, return_data: dict) -> DatasetResult:
        """The plots and numbers of a completed calculation (complete1D/complete2D, calculateResiduals)."""
        is2d, flag = doc.is2D(), doc.options.theory_weighting
        one_d = 'image' not in return_data
        theory = plots.theory_1d(return_data, doc.identity.tab_id) if one_d else plots.theory_2d(return_data)
        result = DatasetResult(request.provenance, theory)
        data = request.data
        if doc.is_loaded():
            weights = FittingUtilities.getWeight(data, is2d, flag=flag)
            result.chi2 = FittingUtilities.calculateChi2(weighted(theory, is2d, flag), data, weights)
            residuals = FittingUtilities.plotResiduals(data, theory, weights)
            if residuals is not None:
                residuals.id = "Residual " + residuals.id
                # SESANS residuals are on a lin-lin scale
                residuals.plot_role = (DataRole.ROLE_RESIDUAL_SESANS if one_d and data.isSesans
                                       else DataRole.ROLE_RESIDUAL)
                result.residuals = residuals
        for plot in FittingUtilities.plotPolydispersities(return_data.get('model')):
            data_id = theory.id.split()
            plot.id = f"{data_id[0]} [{plot.name} polydispersity] {' '.join(data_id[1:])}"
            data_name = theory.name.split()
            plot.name = polydispersity_plot_name.format(data_name[0], plot.name, " ".join(data_name[1:]))
            result.polydispersity.append(plot)
        if one_d:
            result.components = plots.product_plots(return_data, doc.identity.tab_id)
            result.radius_effective = plots.scalar_results(return_data).get("radius_effective")
        return result
