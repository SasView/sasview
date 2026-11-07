"""Integration tests: the parameter slider inside a real FittingWidget.

The calculation dispatcher is mocked, so no calculation threads run; live
completions are delivered by calling the completion slot directly.
"""
import sys

import pytest
from PySide6 import QtCore, QtTest

from sas.qtgui.Perspectives.Fitting import FittingUtilities
from sas.qtgui.Perspectives.Fitting.FittingWidget import FittingWidget
from sas.qtgui.Perspectives.Fitting.ParameterSliderWidget import NO_SELECTION_REASON
from sas.qtgui.Perspectives.Fitting.UnitTesting.FittingWidgetTest import FittingWidgetMod, dummy_manager
from sas.qtgui.Plotting import PlotHelper

STEPS = 1000


@pytest.fixture
def widget(qapp, mocker):
    w = FittingWidgetMod(dummy_manager())
    mocker.patch.object(FittingUtilities, 'checkConstraints', return_value=None)
    w.calc = mocker.patch.object(w, 'calculateQGridForModelExt')
    # Most tests drag with the model curve on screen; TestPlotGate covers the check itself
    w.plotOpen = mocker.patch.object(w, '_modelPlotIsOpen', return_value=True)
    yield w
    w.close()


def selectModel(widget, category="Sphere", model="sphere", structure=None):
    widget.cbCategory.setCurrentIndex(widget.cbCategory.findText(category))
    widget.cbModel.setCurrentIndex(widget.cbModel.findText(model))
    if structure:
        widget.cbStructureFactor.setCurrentIndex(widget.cbStructureFactor.findText(structure))
    widget.calc.reset_mock()
    widget.undo_stack.clear()


def selectParams(widget, *names):
    selection = widget.lstParams.selectionModel()
    selection.clearSelection()
    flags = QtCore.QItemSelectionModel.Select | QtCore.QItemSelectionModel.Rows
    for name in names:
        selection.select(widget._model_model.index(widget._mainRowForParam(name), 0), flags)


def valueCell(widget, name):
    return widget._model_model.item(widget._mainRowForParam(name), widget.lstParams.itemDelegate().param_value)


def liveCalls(widget):
    return [c for c in widget.calc.call_args_list if c.kwargs.get('live_generation') is not None]


def finishLive(widget):
    widget._onLiveCalcFinished(None, widget._live_calc_gen)


def useRealDispatcher(widget, mocker):
    """Run the real calculateQGridForModelExt with only the calculation thread mocked."""
    widget.calc.side_effect = lambda **kwargs: FittingWidget.calculateQGridForModelExt(widget, **kwargs)
    thread = mocker.MagicMock()
    mocker.patch.object(widget, 'methodCalculateForData', return_value=thread)
    return thread


class TestBinding:

    def test_single_unconstrained_row_binds(self, widget):
        selectModel(widget)
        selectParams(widget, "radius")
        slider = widget.slider_widget
        assert slider.name() == "radius"
        assert slider.range() == (0.0, 100.0)
        assert slider.sldParameter.isEnabled()

    def test_scale_is_clipped_to_physical_limits(self, widget):
        selectModel(widget)
        selectParams(widget, "scale")
        assert widget.slider_widget.range() == (0.0, 2.0)

    def test_multiple_rows_unbind(self, widget):
        selectModel(widget)
        selectParams(widget, "radius", "sld")
        assert not widget.slider_widget.isBound()
        assert widget.slider_widget.sldParameter.toolTip() == NO_SELECTION_REASON

    def test_structure_factor_parameters(self, widget):
        selectModel(widget, structure="hardsphere")
        selectParams(widget, "volfraction")
        assert widget.slider_widget.name() == "volfraction"
        selectParams(widget, "radius_effective_mode")
        assert not widget.slider_widget.isBound()
        assert "fixed-choice" in widget.slider_widget.sldParameter.toolTip()

    def test_shell_count_ineligible_and_removed_shell_unbinds(self, widget):
        selectModel(widget, model="core_multi_shell")
        selectParams(widget, "n")
        assert "fixed-choice" in widget.slider_widget.sldParameter.toolTip()
        shells = widget.lstParams.indexWidget(widget._model_model.index(widget._n_shells_row, 1))
        shells.setCurrentIndex(2)
        selectParams(widget, "sld2")
        assert widget.slider_widget.name() == "sld2"
        shells.setCurrentIndex(1)
        assert not widget.slider_widget.isBound()

    @pytest.mark.parametrize("column", [0, 1, 2, 3, 4])
    def test_click_on_any_cell_binds(self, widget, column):
        # Clicking the value cell opens its editor, which must not look like a fixed-choice combo box
        widget.show()
        selectModel(widget)
        index = widget._model_model.index(widget._mainRowForParam("radius"), column)
        rect = widget.lstParams.visualRect(index)
        QtTest.QTest.mouseClick(widget.lstParams.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, rect.center())
        assert widget.slider_widget.name() == "radius"

    def test_model_change_unbinds_and_forgets_ranges(self, widget):
        selectModel(widget)
        selectParams(widget, "radius")
        widget.cbModel.setCurrentIndex(widget.cbModel.findText("vesicle"))
        assert not widget.slider_widget.isBound()
        assert widget._slider_ranges == {}


class TestDragging:

    def test_tick_writes_table_and_kernel(self, widget):
        selectModel(widget)
        selectParams(widget, "radius")
        widget.slider_widget.sldParameter.setValue(600)
        assert valueCell(widget, "radius").text() == "60"
        assert widget.logic.kernel_module.getParam("radius") == 60.0
        assert len(liveCalls(widget)) == 1

    def test_throttle_keeps_one_calculation_in_flight(self, widget):
        selectModel(widget)
        selectParams(widget, "radius")
        for position in (600, 650, 700):
            widget.slider_widget.sldParameter.setValue(position)
        # First tick starts a calculation at once; later ticks only mark it pending
        assert len(liveCalls(widget)) == 1
        finishLive(widget)
        assert len(liveCalls(widget)) == 2
        assert widget.logic.kernel_module.getParam("radius") == 70.0
        finishLive(widget)
        assert len(liveCalls(widget)) == 2
        assert not widget._live_calc_running

    def test_live_calculation_keeps_page_interactive(self, widget, mocker):
        selectModel(widget)
        selectParams(widget, "radius")
        thread = useRealDispatcher(widget, mocker)
        widget.slider_widget.sldParameter.setValue(600)
        assert thread.call_count == 1
        assert widget.lstParams.isEnabled()
        assert widget.cmdFit.text() == "Fit"
        # A non-live calculation still disables the page
        widget.calculateQGridForModel()
        assert not widget.lstParams.isEnabled()

    def test_live_completion_is_plotted_as_live(self, widget, mocker):
        selectModel(widget)
        selectParams(widget, "radius")
        thread = useRealDispatcher(widget, mocker)
        complete = mocker.patch.object(widget, 'complete1D')
        widget.slider_widget.sldParameter.setValue(600)
        thread.call_args.kwargs['completefn']({"result": 1})
        complete.assert_called_once_with({"result": 1}, live=True)
        assert not widget._live_calc_running

    def test_complete_live_does_not_touch_enablement(self, widget, mocker):
        enable = mocker.patch.object(widget, 'enableInteractiveElements')
        widget.complete1D(None, live=True)
        widget.complete2D(None, live=True)
        enable.assert_not_called()
        widget.complete1D(None)
        enable.assert_called_once()

    def test_kernel_exception_clears_in_flight_state(self, widget, mocker):
        selectModel(widget)
        selectParams(widget, "radius")
        thread = useRealDispatcher(widget, mocker)
        widget.slider_widget.sldParameter.setValue(600)
        assert widget._live_calc_running
        try:
            raise RuntimeError("kernel failure")
        except RuntimeError:
            thread.call_args.kwargs['exception_handler'](*sys.exc_info())
        assert not widget._live_calc_running

    def test_drag_is_one_undo_entry(self, widget):
        selectModel(widget)
        selectParams(widget, "radius")
        for position in (600, 700, 800):
            widget.slider_widget.sldParameter.setValue(position)
        assert len(widget.undo_stack._undo_stack) == 1
        widget.undo_stack.undo()
        assert widget.logic.kernel_module.getParam("radius") == 50.0
        assert widget.slider_widget.sldParameter.value() == STEPS // 2

    def test_drag_back_to_start_leaves_no_undo_entry(self, widget):
        selectModel(widget)
        selectParams(widget, "radius")
        widget.slider_widget.sldParameter.setValue(600)
        widget.slider_widget.sldParameter.setValue(500)
        assert not widget.undo_stack.can_undo()

    def test_rounding_at_range_end_does_not_reset_range(self, widget):
        selectModel(widget)
        widget.logic.kernel_module.setParam("radius", 9.9999)
        selectParams(widget, "radius")
        before = widget.slider_widget.range()
        widget.slider_widget.sldParameter.setValue(STEPS)
        assert valueCell(widget, "radius").text() == "20"
        assert widget.slider_widget.range() == before

    def test_range_edit_clamp_is_undoable(self, widget):
        selectModel(widget)
        selectParams(widget, "radius")
        box = widget.slider_widget.txtSliderMax
        box.setText("40")
        box.setModified(True)
        box.editingFinished.emit()
        assert widget.logic.kernel_module.getParam("radius") == 40.0
        assert widget.undo_stack._undo_stack[-1]._new_val == 40.0
        assert widget._slider_ranges["radius"] == (0.0, 40.0)


class TestSynchronisation:

    def test_table_edit_outside_range_resets_range(self, widget):
        selectModel(widget)
        selectParams(widget, "radius")
        valueCell(widget, "radius").setText("500")
        assert widget.slider_widget.range() == (0.0, 1000.0)
        assert widget.slider_widget.sldParameter.value() == STEPS // 2

    def test_refresh_after_signal_free_update(self, widget):
        # Fit results are written with dataChanged disconnected
        selectModel(widget)
        selectParams(widget, "radius")
        widget.logic.kernel_module.setParam("radius", 75.0)
        widget._refreshSlider()
        assert widget.slider_widget.value() == 75.0


class TestFitting:

    def test_fit_start_discards_live_completion(self, widget):
        selectModel(widget)
        selectParams(widget, "radius")
        widget.slider_widget.sldParameter.setValue(600)
        stale = widget._live_calc_gen
        widget.fit_started = True
        widget.disableInteractiveElements()
        widget._onLiveCalcFinished({}, stale)
        assert widget.fit_started
        assert not widget.lstParams.isEnabled()
        assert widget.cmdFit.text() == "Stop fit"
        assert not widget.slider_widget.isEnabled()

    def test_failed_dispatch_does_not_latch(self, widget):
        selectModel(widget)
        selectParams(widget, "radius")
        widget.calc.side_effect = RuntimeError("boom")
        widget.slider_widget.sldParameter.setValue(600)
        assert not widget._live_calc_running


class TestPlotGate:

    @pytest.fixture(autouse=True)
    def realGate(self, widget, mocker):
        mocker.stop(widget.plotOpen)

    class FakePlot:
        def __init__(self, name, use_dict=True):
            self.plot_dict = {name: None} if use_dict else {}
            self.data = [] if use_dict else [type("Data", (), {"name": name})()]

    def test_no_calculation_before_anything_was_computed(self, widget):
        selectModel(widget)
        selectParams(widget, "radius")
        assert widget.model_data is None
        widget.slider_widget.sldParameter.setValue(600)
        assert widget.logic.kernel_module.getParam("radius") == 60.0
        assert liveCalls(widget) == []

    def test_no_calculation_when_model_plot_is_closed(self, widget, mocker):
        selectModel(widget)
        selectParams(widget, "radius")
        widget.model_data = type("Data", (), {"name": "M1 [sphere]"})()
        mocker.patch.object(PlotHelper, 'currentPlotIds', return_value=["Graph1"])
        mocker.patch.object(PlotHelper, 'plotById', return_value=self.FakePlot("other curve"))
        widget.slider_widget.sldParameter.setValue(600)
        assert liveCalls(widget) == []

    @pytest.mark.parametrize("use_dict", [True, False])  # 1D and 2D plotters
    def test_calculation_when_model_plot_is_open(self, widget, mocker, use_dict):
        selectModel(widget)
        selectParams(widget, "radius")
        widget.model_data = type("Data", (), {"name": "M1 [sphere]"})()
        mocker.patch.object(PlotHelper, 'currentPlotIds', return_value=["Graph1"])
        mocker.patch.object(PlotHelper, 'plotById', return_value=self.FakePlot("M1 [sphere]", use_dict))
        widget.slider_widget.sldParameter.setValue(600)
        assert len(liveCalls(widget)) == 1
