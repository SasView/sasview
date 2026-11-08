"""Unit tests for the float-domain ParameterSliderWidget (no FittingWidget involved)."""
import math

import pytest
from PySide6 import QtCore, QtGui, QtWidgets

from sas.qtgui.Perspectives.Fitting.ParameterSliderWidget import NO_SELECTION_REASON, ParameterSliderWidget
from sas.qtgui.UnitTesting.TestUtils import QtSignalSpy
from sas.qtgui.Utilities.BackgroundColor import BG_ERROR

INF = math.inf


@pytest.fixture
def slider(qapp):
    w = ParameterSliderWidget()
    w.bind("radius", 50.0, 0.0, 100.0, 0.0, INF, "Ang")
    yield w
    w.close()


def _commitRange(slider, box, text):
    box.setText(text)
    box.setModified(True)
    box.editingFinished.emit()


class TestDefaultRange:

    @pytest.mark.parametrize("value, limits, expected", [
        (50.0, (-INF, INF), (0.0, 100.0)),
        (-5.0, (-INF, INF), (-10.0, 0.0)),
        (0.0, (-INF, INF), (-1.0, 1.0)),
        (0.0, (0.0, INF), (0.0, 1.0)),
        (1.0, (0.0, INF), (0.0, 2.0)),
        (0.5, (0.0, 0.74), (0.0, 0.74)),
    ])
    def test_default_range(self, value, limits, expected):
        assert ParameterSliderWidget.defaultRange(value, *limits) == pytest.approx(expected)

    def test_collapsed_range_is_widened_and_clipped_again(self):
        # value at the upper limit: [v-|v|, v+|v|] clipped is fine, but a value
        # sitting outside the limits collapses and is widened by +/-1
        assert ParameterSliderWidget.defaultRange(-0.5, 0.0, INF) == pytest.approx((0.0, 0.5))

    def test_no_valid_range(self):
        assert ParameterSliderWidget.defaultRange(-5.0, 0.0, INF) is None


class TestValidateRange:

    def test_reversed_range_is_swapped(self):
        assert ParameterSliderWidget.validateRange(10.0, 1.0, -INF, INF) == (1.0, 10.0)

    @pytest.mark.parametrize("vmin, vmax, limits", [
        (1.0, 1.0, (-INF, INF)),          # equal
        (-INF, 1.0, (-INF, INF)),         # not finite
        (-1.0, 1.0, (0.0, INF)),          # outside the hard limits
        (1000.0, 1000.05, (-INF, INF)),   # narrower than the table precision
        (6.36, 6.37, (-INF, INF)),        # step 1e-5, table shows 1e-4
        (99.0, 100.5, (-INF, INF)),       # step 1.5e-3, table shows 1e-2 above 100
    ])
    def test_invalid_ranges_return_a_message(self, vmin, vmax, limits):
        assert isinstance(ParameterSliderWidget.validateRange(vmin, vmax, *limits), str)

    @pytest.mark.parametrize("vmin, vmax", [
        (6.26, 6.46),       # sld +/- 0.1: step 2e-4, table shows 1e-4
        (95.0, 105.0),      # step equal to the 1e-2 resolution above 100
        (49.5, 50.5),       # +/- 1 %: step equal to the 1e-3 resolution
        (-0.5, 0.5),
        (1e-9, 3e-9),
    ])
    def test_narrow_ranges_within_table_precision_are_valid(self, vmin, vmax):
        assert ParameterSliderWidget.validateRange(vmin, vmax, -INF, INF) == (vmin, vmax)

    @pytest.mark.parametrize("value, resolution", [
        (6.36, 1e-4), (9.9999, 1e-4), (10.0, 1e-3), (-250.0, 1e-2), (1e-3, 1e-7),
    ])
    def test_table_resolution(self, value, resolution):
        assert ParameterSliderWidget.tableResolution(value) == pytest.approx(resolution)


class TestBinding:

    def test_bind_populates_controls(self, slider):
        assert slider.isBound()
        assert slider.name() == "radius"
        assert slider.lblSliderName.text() == "radius"
        assert slider.txtSliderMin.text() == "0"
        assert slider.txtSliderMax.text() == "100"
        assert slider.sldParameter.value() == ParameterSliderWidget.STEPS // 2
        assert slider.lblSliderValue.text().startswith("50 ")
        assert slider.sldParameter.isEnabled()

    def test_unbind_disables_and_explains(self, slider):
        slider.unbind("radius is constrained")
        assert not slider.isBound()
        assert not slider.sldParameter.isEnabled()
        assert not slider.txtSliderMin.isEnabled()
        for control in (slider.lblSliderName, slider.txtSliderMin, slider.sldParameter,
                        slider.txtSliderMax, slider.lblSliderValue):
            assert control.toolTip() == "radius is constrained"
        slider.unbind()
        assert slider.sldParameter.toolTip() == NO_SELECTION_REASON

    def test_tick_emits_mapped_value(self, slider):
        spy = QtSignalSpy(slider, slider.valueChanged)
        slider.sldParameter.setValue(750)
        assert spy.count() == 1
        assert spy.called()[0]['args'] == ("radius", pytest.approx(75.0))
        assert slider.value() == pytest.approx(75.0)

    def test_programmatic_updates_do_not_emit(self, slider):
        spy = QtSignalSpy(slider, slider.valueChanged)
        slider.setValue(20.0)
        slider.setRange(0.0, 40.0)
        assert spy.count() == 0
        assert slider.sldParameter.value() == ParameterSliderWidget.STEPS // 2


class TestRangeEditing:

    def test_valid_edit_emits_range(self, slider):
        spy = QtSignalSpy(slider, slider.rangeChanged)
        _commitRange(slider, slider.txtSliderMax, "200")
        assert spy.count() == 1
        assert slider.range() == (0.0, 200.0)
        assert slider.sldParameter.value() == ParameterSliderWidget.STEPS // 4

    def test_unmodified_box_does_nothing_on_focus_loss(self, slider):
        spy = QtSignalSpy(slider, slider.rangeChanged)
        slider.txtSliderMax.editingFinished.emit()
        assert spy.count() == 0

    @pytest.mark.parametrize("text", ["-", "", "abc", "-5"])
    def test_invalid_edit_restores_text(self, slider, text):
        spy = QtSignalSpy(slider, slider.rangeRejected)
        _commitRange(slider, slider.txtSliderMin, text)
        assert spy.count() == 1
        assert slider.txtSliderMin.text() == "0"
        assert slider.txtSliderMin.styleSheet() == BG_ERROR
        assert slider.range() == (0.0, 100.0)

    def test_reversed_edit_is_swapped(self, slider):
        # Moving the range wholly upward by editing min first
        _commitRange(slider, slider.txtSliderMin, "300")
        assert slider.range() == (100.0, 300.0)

    def test_range_excluding_value_clamps_it(self, slider):
        spy = QtSignalSpy(slider, slider.valueChanged)
        _commitRange(slider, slider.txtSliderMax, "40")
        assert slider.value() == 40.0
        assert spy.count() == 1
        assert spy.called()[0]['args'] == ("radius", 40.0)


class TestWheel:

    def _wheel(self, slider):
        pos = QtCore.QPointF(slider.sldParameter.rect().center())
        event = QtGui.QWheelEvent(pos, slider.sldParameter.mapToGlobal(pos), QtCore.QPoint(0, 0),
                                  QtCore.QPoint(0, 120), QtCore.Qt.NoButton, QtCore.Qt.NoModifier,
                                  QtCore.Qt.NoScrollPhase, False)
        QtWidgets.QApplication.sendEvent(slider.sldParameter, event)

    def test_wheel_ignored_without_focus(self, slider):
        before = slider.sldParameter.value()
        self._wheel(slider)
        assert slider.sldParameter.value() == before

    def test_wheel_works_with_focus(self, slider, mocker):
        mocker.patch.object(slider.sldParameter, 'hasFocus', return_value=True)
        before = slider.sldParameter.value()
        self._wheel(slider)
        assert slider.sldParameter.value() != before
