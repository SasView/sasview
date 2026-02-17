"""Tests for the Invariant perspective with real data loaded."""

import pytest
from PySide6.QtWidgets import QApplication

from sas.qtgui.Plotting.PlotterData import Data1D

# REMOVE WHEN BG_FIX PR IS MERGED
# Default background color (transparent)
BG_DEFAULT = ""
# Error background color
BG_ERROR   = "background-color: rgb(244, 170, 164);"

# Tolerance for floating point comparisons
TOLERANCE = 1e-7


@pytest.mark.parametrize("window_class", ["real_data"], indirect=True)
@pytest.mark.usefixtures("window_class")
class TestInvariantWithRealData:
    """Test the Invariant perspective behavior when real data is loaded."""
    def wait_for(self, condition, timeout=0.5, poll=0.01):
        import time
        end = time.time() + timeout
        while time.time() < end:
            if condition():
                return True
            QApplication.processEvents()
            time.sleep(poll)
        return False

    def setup_contrast(self):
        """Setup contrast for testing."""
        self.window.rbContrast.setChecked(True)
        self.update_and_emit_line_edits(self.window.txtContrast, "2e-06")

    def setup_volume_fraction(self):
        """Setup volume fraction for testing."""
        self.window.rbVolFrac.setChecked(True)
        self.update_and_emit_line_edits(self.window.txtVolFrac1, "0.1")

    def update_and_emit_line_edits(self, line_edit, value: str):
        """Helper function to update and emit line edits."""
        line_edit.setText(value)
        line_edit.textEdited.emit(value)
        line_edit.editingFinished.emit()
        QApplication.processEvents()

    def test_data_loading(self, real_data: Data1D):
        """Tests that real data was loaded into the perspective."""
        assert self.window._data is not None, "Data not loaded."
        assert self.window._data == real_data, "Data is not the same as loaded."
        assert self.window.txtName.text() == real_data.name, "Data name not displayed."

    def test_q_range_displayed(self, real_data: Data1D):
        """Tests that correct Q range is displayed when real data is loaded."""
        assert float(self.window.txtTotalQMin.text()) == pytest.approx(min(real_data.x))
        assert float(self.window.txtTotalQMax.text()) == pytest.approx(max(real_data.x))

    def test_calculate_button_disabled_on_load(self):
        """Test that calculate button starts disabled even with data loaded."""
        assert not self.window.cmdCalculate.isEnabled()
        assert self.window.cmdCalculate.text() == "Calculate (Enter volume fraction or contrast)"

    def test_calculate_button_enabled_with_contrast(self):
        """Test that calculate button is enabled when contrast is set."""
        self.setup_contrast()

        assert self.window.cmdCalculate.isEnabled()
        assert self.window.cmdCalculate.text() == "Calculate"

    def test_calculate_button_enabled_with_volume_fraction(self):
        """Test that calculate button is enabled when volume fraction is set."""
        self.setup_volume_fraction()

        assert self.window.cmdCalculate.isEnabled()
        assert self.window.cmdCalculate.text() == "Calculate"

    def test_low_extrapolation_enable(self):
        """Test that low extrapolation is set correctly."""
        self.setup_contrast()

        self.window.chkLowQ_ex.setChecked(True)

        assert not self.window.txtGuinierEnd_ex.text() == ""
        assert self.window.txtGuinierEnd_ex.styleSheet() == BG_DEFAULT

    def test_low_extrapolation_value(self):
        """Test that low extrapolation is set correctly."""
        self.setup_contrast()
        self.window.chkLowQ_ex.setChecked(True)

        # Set the low extrapolation value to be outside the data range
        self.update_and_emit_line_edits(self.window.txtGuinierEnd_ex, str(self.window._data.x[0] - 0.1))

        # Check that the value is reset to within the data range
        assert self.window.txtGuinierEnd_ex.styleSheet() == BG_ERROR

    def test_low_extrapolation_value_reset(self):
        """Test that low extrapolation is set correctly."""
        mocker.patch("PySide6.QtWidgets.QMessageBox.warning")

        self.setup_contrast()
        self.window.chkLowQ_ex.setChecked(True)

        # Set the low extrapolation value to be outside the data range
        data_min = self.window._data.x[0]
        out_of_range_value = data_min - TOLERANCE
        self.window.txtGuinierEnd_ex.setText(str(out_of_range_value))
        self.window.txtGuinierEnd_ex.returnPressed.emit()

        expected_corrected = data_min + ADJUST_EPS

        # ok = self.wait_for(lambda: pytest.approx(expected_corrected, rel=TOLERANCE) == float(self.window.txtGuinierEnd_ex.text()), timeout=0.5)
        # assert ok, f"field not reset, current='{self.window.txtGuinierEnd_ex.text()}' expected ~{expected_corrected}"

        # Assert that the warning message is shown
        mock_warning.assert_called_once()
        args, _ = mock_warning.call_args
        assert args[1] == "Invalid Extrapolation Values"
        assert "Values have been adjusted to the nearest valid values." in args[2]
