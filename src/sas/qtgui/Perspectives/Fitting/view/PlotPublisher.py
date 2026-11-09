"""
PlotPublisher (FW-MVC-DESIGN.md §3.4, Phase 7): theory results to the Data Explorer and the
plots. The only code of the fit page that touches Data Explorer items.

A result is routed by its dataset id to that dataset's item (a page without data creates
theory items instead). The publisher names the plots, adds them, removes the plots of the
item that the result no longer has (beta(Q), S_eff(Q), ...), and attaches the Q-range
slider hooks of the theory curve: the sliders call the page's controller intents
``set_q_min``/``set_q_max``.
"""
from __future__ import annotations

from PySide6 import QtWidgets

from sas.qtgui.Perspectives.Fitting.services.theory import weighted
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Utilities import GuiUtils


class PlotPublisher:

    def __init__(self, page) -> None:
        self._page = page

    def publish(self, result) -> None:
        page = self._page
        doc = page.document
        item = page.dataItem(result.provenance.dataset_id)
        theory = result.theory
        theory.symbol = "Line"
        loaded = doc.is_loaded()
        # The Data Explorer keeps the weighted curve
        self._add(item, weighted(theory, doc.is2D(), doc.options.theory_weighting) if loaded else theory)
        plots = [theory]
        if result.residuals is not None:
            self._add(item, result.residuals)
            plots.append(result.residuals)
        one_d = isinstance(theory, Data1D)
        if one_d:
            self._attach_sliders(theory)
            if loaded:
                # Delete the plots of the data that this result does not have (e.g. beta(Q), S_eff(Q))
                GuiUtils.deleteRedundantPlots(item, plots)
            else:
                page.communicator.deleteIntermediateTheoryPlotsSignal.emit(str(page.tab_id))
        for plot in result.polydispersity:
            self._add(item, plot)
            plots.append(plot)
        for plot in result.components:
            plot.symbol = "Line"
            self._add(item, plot)
            plots.append(plot)
        page.model_data = theory
        for plot in plots:
            page.communicator.plotUpdateSignal.emit([plot])
            if one_d:
                QtWidgets.QApplication.processEvents()

    def _attach_sliders(self, theory) -> None:
        page = self._page
        theory.show_q_range_sliders = True
        # Suppress the GUI update until the move is finished to limit model calculations
        theory.slider_update_on_move = False
        theory.slider_tab_name = page.modelName()
        theory.slider_perspective_name = 'Fitting'
        theory.slider_high_q_input = ['options_widget', 'txtMaxRange']
        theory.slider_high_q_setter = ['controller', 'set_q_max']
        theory.slider_low_q_input = ['options_widget', 'txtMinRange']
        theory.slider_low_q_setter = ['controller', 'set_q_min']

    def _add(self, item, plot) -> None:
        """A plot to the dataset's Data Explorer item, or a theory item for a page without data."""
        page = self._page
        if plot.name is None:
            plot.name = page.nameForFittedData(str(page.data.name))
            plot.title = plot.filename = plot.name
        if item is not None:
            if getattr(plot, 'symbol', None) is None:
                plot.symbol = 'Line'
            GuiUtils.updateModelItemWithPlot(item, plot, plot.name)
            return
        plot.title = plot.filename = plot.name
        plot.symbol = "Line"
        # TODO: Temporary Hack to fix NaNs in generated theory data
        #  This is usually from GSC models that are calculated outside the Q range they were created for
        from sasdata.dataloader.filereader import FileReader
        plot = FileReader()._remove_nans_in_data(plot)
        page.communicator.updateTheoryFromPerspectiveSignal.emit(GuiUtils.createModelItemWithPlot(plot, name=plot.name))
        # Switch to the theory tab for user's glee
        page.communicator.changeDataExplorerTabSignal.emit(1)
