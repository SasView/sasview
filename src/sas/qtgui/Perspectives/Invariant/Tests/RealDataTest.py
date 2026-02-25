"""Tests for the Invariant perspective with real data loaded."""

import pytest
from PySide6.QtWidgets import QApplication

from sas.qtgui.Plotting.PlotterData import Data1D

# REMOVE WHEN BG_FIX PR IS MERGED
# Default background color (transparent)
BG_DEFAULT = ""
# Error background color
BG_ERROR = "background-color: rgb(244, 170, 164);"

# Tolerance for floating point comparisons
TOLERANCE = 1e-7


class UIHelpersMixin:
    """Helper functions for testing."""

    def update_and_emit_line_edits(self, line_edit, value: str):
        """Helper function to update and emit line edits."""
        line_edit.setText(value)
        line_edit.textEdited.emit(value)
        line_edit.editingFinished.emit()
        QApplication.processEvents()

    def setup_contrast(self):
        """Setup contrast for testing."""
        self.window.rbContrast.setChecked(True)
        self.update_and_emit_line_edits(self.window.txtContrast, "2e-06")

    def setup_volume_fraction(self):
        """Setup volume fraction for testing."""
        self.window.rbVolFrac.setChecked(True)
        self.update_and_emit_line_edits(self.window.txtVolFrac1, "0.1")


@pytest.mark.parametrize("window_class", ["real_data"], indirect=True)
@pytest.mark.usefixtures("window_class")
class TestInvariantSetup(UIHelpersMixin):
    """Test the Invariant perspective behavior when real data is loaded."""

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


@pytest.mark.parametrize("window_class", ["real_data"], indirect=True)
@pytest.mark.usefixtures("window_class")
class TestInvariantExtrapolation(UIHelpersMixin):
    """Test the extrapolation input validation and behavior."""

    @pytest.mark.parametrize(
        ("field_name", "range_pos"),
        [
            ("txtGuinierEnd_ex", "below"),
            ("txtGuinierEnd_ex", "above"),
            ("txtPorodStart_ex", "below"),
            ("txtPorodStart_ex", "above"),
            ("txtPorodEnd_ex", "below"),
            ("txtPorodEnd_ex", "above"),
        ],
        ids=[
            "low_q_end_below",
            "low_q_end_above",
            "high_q_start_below",
            "high_q_start_above",
            "high_q_end_below",
            "high_q_end_above",
        ],
    )
    def test_extrapolation_value_out_of_range(self, mocker, field_name, range_pos):
        """Unified test for out-of-range extrapolation fields."""
        mock_warning = mocker.patch("PySide6.QtWidgets.QMessageBox.warning")

        self.setup_contrast()

        self.window.chkLowQ_ex.setChecked(True)
        self.window.chkHighQ_ex.setChecked(True)

        min = self.window._data.x[0]
        max = self.window._data.x[-1]

        if field_name == "txtPorodEnd_ex":
            max = self.window.extrapolation_parameters.ex_q_max

        # compute value from window data
        if range_pos == "below":
            value = min - TOLERANCE
        else:
            value = max + TOLERANCE

        widget = getattr(self.window, field_name)

        # simulate user edit
        widget.setText(str(value))
        widget.textEdited.emit(str(value))

        # error colour displayed while editing
        assert widget.styleSheet() == BG_ERROR

        widget.editingFinished.emit()

        # value should be reset
        assert widget.styleSheet() == BG_DEFAULT

        mock_warning.assert_called_once()
        args, _ = mock_warning.call_args
        assert args[1] == "Invalid Extrapolation Values"

    @pytest.mark.parametrize(
        ("field_name", "range_pos"),
        [
            ("txtGuinierEnd_ex", "below"),
            ("txtGuinierEnd_ex", "above"),
            ("txtPorodStart_ex", "below"),
            ("txtPorodStart_ex", "above"),
            ("txtPorodEnd_ex", "below"),
            ("txtPorodEnd_ex", "above"),
        ],
        ids=[
            "low_q_end_below",
            "low_q_end_above",
            "high_q_start_below",
            "high_q_start_above",
            "high_q_end_below",
            "high_q_end_above",
        ],
    )
    def test_extrapolation_value_invalid(self, mocker, field_name, range_pos):
        """Test for invalid extrapolation fields that include being below/above the adjacent extrapolation point"""
        mock_warning = mocker.patch("PySide6.QtWidgets.QMessageBox.warning")

        self.setup_contrast()

        self.window.chkLowQ_ex.setChecked(True)
        self.window.chkHighQ_ex.setChecked(True)

        widget = getattr(self.window, "txtGuinierEnd_ex")
        value = self.window.extrapolation_parameters.point_2

        # simulate user edit
        widget.setText(str(value))
        widget.textEdited.emit(str(value))

        # error colour displayed while editing
        assert widget.styleSheet() == BG_ERROR

        widget.editingFinished.emit()

        # value should be reset
        assert widget.styleSheet() == BG_DEFAULT
        assert float(widget.text()) <= value

        mock_warning.assert_called_once()
        args, _ = mock_warning.call_args
        assert args[1] == "Invalid Extrapolation Values"

    def valid_extrapolation_order(self):
        """Helper to check if the extrapolation values are valid"""
        params = self.window.extrapolation_parameters
        min_data = params.data_q_min
        p1 = params.point_1
        p2 = params.point_2
        p3 = params.point_3
        max_data = params.data_q_max
        max_ex = params.ex_q_max

        return min_data < p1 < p2 < p3 <= max_ex and p2 < max_data

    @pytest.mark.parametrize(
        "case",
        [
            "valid",
            "invalid_p2_larger_than_p3",
            "invalid_p1_equal_p2",
            "invalid_p2_equal_p3",
            "invalid_p1_larger_than_p2",
            "invalid_p1_larger_than_p3",
        ],
        ids=["valid", "p2_larger_than_p3", "p1_eq_p2", "p2_eq_p3", "p1_larger_than_p2", "p1_larger_than_p3"],
    )
    def test_extrapolation_order(self, mocker, case):
        """Test that the p1<p2<p3 order is validated correctly."""
        mock_warning = mocker.patch("PySide6.QtWidgets.QMessageBox.warning")

        self.setup_contrast()
        self.window.chkLowQ_ex.setChecked(True)
        self.window.chkHighQ_ex.setChecked(True)

        params = self.window.extrapolation_parameters

        data_min = params.data_q_min
        data_max = params.data_q_max
        ex_max = params.ex_q_max

        base1 = data_min + (data_max - data_min) * 0.1
        base2 = data_min + (data_max - data_min) * 0.7
        base3 = ex_max

        if case == "valid":
            p1, p2, p3 = base1, base2, base3
            expected_valid = True
        elif case == "invalid_p2_larger_than_p3":
            p1, p2, p3 = base1, base3, base2  # p2 > p3
            expected_valid = False
        elif case == "invalid_p1_equal_p2":
            p1, p2, p3 = base1, base1, base3  # p1 == p2
            expected_valid = False
        elif case == "invalid_p2_equal_p3":
            p1, p2, p3 = base1, base2, base2
            expected_valid = False
        elif case == "invalid_p1_larger_than_p2":
            p1, p2, p3 = base2, base1, base3  # p1 > p2
            expected_valid = False
        elif case == "invalid_p1_larger_than_p3":
            p1, p2, p3 = base3, base2, base1  # p1 > p3
            expected_valid = False
        else:
            pytest.skip(f"unknown case {case}")

        w1 = self.window.txtGuinierEnd_ex
        w2 = self.window.txtPorodStart_ex
        w3 = self.window.txtPorodEnd_ex

        w1.setText(str(p1))
        w1.textEdited.emit(str(p1))
        w2.setText(str(p2))
        w2.textEdited.emit(str(p2))
        w3.setText(str(p3))
        w3.textEdited.emit(str(p3))

        if expected_valid:
            assert (
                self.window.txtGuinierEnd_ex.styleSheet() == BG_DEFAULT
                and self.window.txtPorodStart_ex.styleSheet() == BG_DEFAULT
                and self.window.txtPorodEnd_ex.styleSheet() == BG_DEFAULT
            )
        else:
            assert (
                self.window.txtGuinierEnd_ex.styleSheet() == BG_ERROR
                or self.window.txtPorodStart_ex.styleSheet() == BG_ERROR
                or self.window.txtPorodEnd_ex.styleSheet() == BG_ERROR
            )

        w1.editingFinished.emit()
        w2.editingFinished.emit()
        w3.editingFinished.emit()

        if expected_valid:
            mock_warning.assert_not_called()
        else:
            mock_warning.assert_called()

        assert (
            self.window.txtGuinierEnd_ex.styleSheet() == BG_DEFAULT
            and self.window.txtPorodStart_ex.styleSheet() == BG_DEFAULT
            and self.window.txtPorodEnd_ex.styleSheet() == BG_DEFAULT
        )
        assert self.valid_extrapolation_order()


@pytest.mark.parametrize("window_class", ["real_data"], indirect=True)
@pytest.mark.usefixtures("window_class")
class TestInvariantMethods(UIHelpersMixin):
    def test_low_q_extrapolation_getter(self, real_data):
        """Test that the low q extrapolation getter works correctly."""

        self.setup_contrast()
        self.window.chkLowQ_ex.setChecked(True)

        num_points = 10
        value = self.window._data.x[num_points - 1]

        self.window._low_points = 10
        upper_limit = self.window.get_low_q_extrapolation_upper_limit()

        assert upper_limit == value

    def test_low_q_extrapolation_setter(self, real_data):
        """Test that the low q extrapolation setter works correctly."""

        self.setup_contrast()
        self.window.chkLowQ_ex.setChecked(True)

        index = 15
        value = self.window._data.x[index - 1]

        self.window.set_low_q_extrapolation_upper_limit(value)

        assert self.window._low_points == index

    def test_high_q_extrapolation_getter(self, real_data):
        """Test that the high q extrapolation getter works correctly."""

        self.setup_contrast()
        self.window.chkHighQ_ex.setChecked(True)

        num_points = 10
        value = self.window._data.x[-num_points - 1]

        self.window._high_points = 10
        lower_limit = self.window.get_high_q_extrapolation_lower_limit()

        assert lower_limit == value

    def test_high_q_extrapolation_setter(self, real_data):
        """Test that the high q extrapolation setter works correctly."""

        self.setup_contrast()
        self.window.chkHighQ_ex.setChecked(True)

        index = 15
        value = self.window._data.x[-index + 1]

        self.window.set_high_q_extrapolation_lower_limit(value)

        assert self.window._high_points == index

    def test_updateGuiFromFile_1D(self, real_data):
        """Passing a real Data1D should set _data without raising."""
        self.window.updateGuiFromFile(real_data)
        assert self.window._data is real_data

    def test_updateGuiFromFile_not1D(self):
        """Passing a plain object (not a Data1D) raises the 2D-data error."""
        with pytest.raises(ValueError, match="Invariant cannot be computed with 2D data."):
            self.window.updateGuiFromFile(object())

    def test_serialize_page(self, mocker):
        """Test that the serializePage method returns the expected dictionary."""
        base = {"vol_fraction": "0.1"}
        mocker.patch.object(self.window, "serializeState", return_value=dict(base))

        out = self.window.serializePage()

        expected = dict(base)
        expected["data_name"] = str(self.window._data.name)
        expected["data_id"] = str(self.window._data.id)
        assert out == expected

    def test_serialize_current_page(self, mocker):
        """Test that the serializeCurrentPage method returns the expected dictionary."""
        tab_data = {
            "data_id": "abc-123",
            "vol_fraction": "0.1",
        }
        mocker.patch.object(self.window, "serializePage", return_value=dict(tab_data))

        out = self.window.serializeCurrentPage()

        assert "abc-123" in out
        assert out["abc-123"] == {"invar_params": {"vol_fraction": "0.1"}}

    def test_serialize_all(self, mocker):
        """Test that the serializeAll method returns the expected dictionary."""
        sentinel = {"SOMEKEY": {"invar_params": {"x": "y"}}}

        out = self.window.serializeAll()

        mock_serialize_current_page = mocker.patch.object(self.window, "serializeCurrentPage", return_value=sentinel)
        out = self.window.serializeAll()
        mock_serialize_current_page.assert_called_once()
        assert out is sentinel
