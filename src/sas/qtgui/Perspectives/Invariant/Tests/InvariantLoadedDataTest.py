"""Tests for the Invariant perspective with loaded data."""\

# from src.sas.qtgui.Utilities.BackgroundColor import BG_DEFAULT, BG_ERROR

import pytest
from PySide6 import QtGui

from sas.qtgui.Plotting.PlotterData import Data1D

# REMOVE WHEN BG_FIX PR IS MERGED
# Default background color (transparent)
BG_DEFAULT = ""
# Error background color
BG_ERROR   = "background-color: rgb(244, 170, 164);"


@pytest.mark.usefixtures("window_with_small_data")
class TestInvariantWithData:
    """Test the Invariant perspective behavior when data is loaded."""

    def test_data_loading(self, small_data):
        """Test that data can be loaded into the perspective."""
        assert self.window._data is not None, "Data not loaded."
        assert self.window._data == small_data, "Data is not the same as loaded."

    def test_data_name_displayed(self, small_data: Data1D):
        """Test that the data name is displayed when data is loaded."""
        assert self.window.txtName.text() == small_data.name, "Data name not displayed."

    def test_q_range_displayed(self, small_data: Data1D):
        """Test that Q range is displayed when data is loaded."""
        assert float(self.window.txtTotalQMin.text()) == pytest.approx(min(small_data.x))
        assert float(self.window.txtTotalQMax.text()) == pytest.approx(max(small_data.x))

    def test_calculate_button_disabled_on_load(self):
        """Test that calculate button starts disabled even with data loaded."""
        assert not self.window.cmdCalculate.isEnabled()
        assert self.window.cmdCalculate.text() == "Calculate (Enter volume fraction or contrast)"

    def test_data_removal(self, small_data: Data1D, dummy_manager):
        """Test that data can be removed from the perspective."""
        assert self.window._data is not None

        # Pass the QStandardItem that is currently loaded
        self.window.removeData([self.window._model_item])

        assert self.window._data is None
        assert self.window.txtName.text() == ""

    def test_load_same_data_twice(self, small_data: Data1D, dummy_manager, mocker):
        """Test that loading the same data pops up a warning message."""
        assert self.window._data == small_data

        # Mock warning message box
        mock_warning = mocker.patch("PySide6.QtWidgets.QMessageBox.warning")

        # Load the same data again
        data_item = dummy_manager.createGuiData(small_data)
        self.window.setData([data_item])

        # Assert that the warning message is shown
        mock_warning.assert_called_once()
        args, _ = mock_warning.call_args
        assert args[1] == "Invariant Panel"
        assert args[2] == "This file is already loaded in Invariant panel."

        assert self.window._data == small_data

    def test_load_incorrect_data_not_list(self, dummy_manager, mocker):
        """Test that loading incorrect data (not a list) raises an error."""
        # Create a mock item that has .text() method to pass the preliminary check
        mock_item = mocker.Mock()
        mock_item.text.return_value = "new_data"

        # Attempt to load data of incorrect type (not a list)
        incorrect_data_type = (mock_item,)

        assert not isinstance(incorrect_data_type, list)

        with pytest.raises(AttributeError, match="Incorrect type passed to the Invariant Perspective."):
            self.window.setData(incorrect_data_type)

    def test_load_incorrect_data_not_qstandarditem(self, dummy_manager, mocker):
        """Test that loading incorrect data (not a QStandardItem) raises an error."""
        mock_non_standard_item = mocker.Mock()
        mock_non_standard_item.text.return_value = "new_data"
        # mocker.Mock() is NOT an instance of QStandardItem

        incorrect_list = [mock_non_standard_item]

        assert not isinstance(incorrect_list[0], QtGui.QStandardItem)

        with pytest.raises(AttributeError, match="Incorrect type passed to the Invariant Perspective."):
            self.window.setData(incorrect_list)

    def test_extrapolation_slider_loaded(self, small_data: Data1D):
        """Test that extrapolation slider values are loaded when data is loaded."""
        assert self.window.txtFileName.text() == small_data.name

        # Check that the extrapolation slider values are loaded
        assert not self.window.txtGuinierEnd_ex.text() == ""
        assert not self.window.txtPorodStart_ex.text() == ""
        assert not self.window.txtPorodEnd_ex.text() == ""


@pytest.mark.usefixtures("window_with_real_data")
class TestInvariantCalculationPrerequisites:
    """Test the conditions required for calculation to be enabled."""

    def test_calculate_enabled_with_contrast(self, real_data: Data1D):
        """Test that calculate is enabled when data is loaded and contrast is set."""
        self.window.rbContrast.setChecked(True)

        contrast_value = "2e-06"
        self.window.txtContrast.setText(contrast_value)
        self.window.txtContrast.textEdited.emit(contrast_value)

        assert self.window.rbContrast.isChecked()
        assert self.window._contrast == float(contrast_value)
        assert self.window.txtContrast.styleSheet() == BG_DEFAULT
        assert self.window.cmdCalculate.isEnabled(), "Calculate button should be enabled when contrast is set."

    def test_calculate_disabled_without_contrast(self):
        """Test that calculate is disabled when contrast is empty."""
        self.window.rbContrast.setChecked(True)
        self.window.txtContrast.setText("")
        self.window.txtContrast.textEdited.emit("")

        assert not self.window.cmdCalculate.isEnabled()
        assert self.window.cmdCalculate.text() == "Calculate (Enter volume fraction or contrast)"
        assert self.window.txtContrast.styleSheet() == BG_DEFAULT

    def test_enter_invalid_contrast(self):
        """Test that calculate is disabled when contrast is invalid."""
        self.window.rbContrast.setChecked(True)

        self.window.txtContrast.setText("invalid")
        assert not self.window.cmdCalculate.isEnabled()

        self.window.txtContrast.setText("e")
        self.window.txtContrast.textEdited.emit("e")
        assert self.window.txtContrast.styleSheet() == BG_ERROR
        assert not self.window.cmdCalculate.isEnabled()\

        self.window.txtContrast.setText("1e-")
        self.window.txtContrast.textEdited.emit("1e-")
        assert self.window.txtContrast.styleSheet() == BG_ERROR
        assert not self.window.cmdCalculate.isEnabled()

    def test_calculate_enabled_with_volume_fraction(self):
        """Test that calculate is enabled when data is loaded and volume fraction is set."""
        self.window.rbVolFrac.setChecked(True)
        self.window.txtVolFrac1.setText("0.01")
        self.window.txtVolFrac1.textEdited.emit("0.01")

        assert self.window.rbVolFrac.isChecked()
        assert self.window.txtVolFrac1.text() == "0.01"
        assert self.window.txtVolFrac1.styleSheet() == BG_DEFAULT
        assert self.window.cmdCalculate.isEnabled(), "Calculate button should be enabled when volume fraction is set."

    def test_calculate_disabled_without_volume_fraction(self):
        """Test that calculate is disabled when volume fraction is empty."""
        self.window.rbVolFrac.setChecked(True)
        self.window.txtVolFrac1.setText("")
        self.window.txtVolFrac1.textEdited.emit("")

        assert not self.window.cmdCalculate.isEnabled()
        assert self.window.txtVolFrac1.styleSheet() == BG_DEFAULT

    def test_enter_invalid_volume_fraction(self, mocker):
        """Test that calculate is disabled when volume fraction is invalid."""

        mock_warning = mocker.patch("PySide6.QtWidgets.QMessageBox.warning")

        self.window.rbVolFrac.setChecked(True)
        self.window.txtVolFrac1.setText("2")
        self.window.txtVolFrac1.editingFinished.emit()


        # Assert that the warning message is shown
        mock_warning.assert_called_once()
        args, _ = mock_warning.call_args
        assert args[1] == "Invalid Volume Fraction"
        assert args[2] == "Volume fraction must be between 0 and 1."

        # Assert that the text field is styled red and calculate is disabled
        assert self.window.txtVolFrac1.styleSheet() == BG_ERROR
        assert not self.window.cmdCalculate.isEnabled()

