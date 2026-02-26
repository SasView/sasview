"""Tests for the Invariant perspective initialized state."""

import pytest
from PySide6 import QtWidgets

from sas.qtgui.Perspectives.Invariant.InvariantUtils import WIDGETS
from sas.qtgui.Utilities import GuiUtils


@pytest.mark.usefixtures("window_class")
class TestInvariantDefaults:
    def test_window_identity(self):
        """Test the InvariantWindow identity."""
        assert isinstance(self.window, QtWidgets.QDialog)
        assert self.window.name == "Invariant"
        assert self.window.windowTitle() == "Invariant Perspective"
        assert self.window.title == self.window.windowTitle()

    NUMERIC_CASES: list[tuple[str, float]] = [
        ("txtTotalQMin", 0.0),
        ("txtTotalQMax", 0.0),
        ("txtBackgd", 0.0),
        ("txtScale", 1.0),
        ("txtHighQPower_ex", 4.0),
        ("txtLowQPower_ex", 4.0),
    ]

    @pytest.mark.parametrize("field_name,expected", NUMERIC_CASES, ids=[c[0] for c in NUMERIC_CASES])
    def test_numeric_line_edit_defaults(self, field_name, expected):
        """Test that certain QLineEdits have expected numeric default values."""
        widget = self.window.findChild(QtWidgets.QLineEdit, field_name)
        assert widget is not None, f"UI widget not found: {field_name}"
        assert float(widget.text()) == pytest.approx(expected), f"Expected default text '{expected}' in {field_name}"

    NULL_CASES: list[str] = [
        "txtName",
        "txtPorodCst",
        "txtPorodCstErr",
        "txtContrast",
        "txtContrastErr",
        "txtVolFrac1",
        "txtVolFrac1Err",
        "txtVolFract",
        "txtVolFractErr",
        "txtContrastOut",
        "txtContrastOutErr",
        "txtSpecSurf",
        "txtSpecSurfErr",
        "txtInvariantTot",
        "txtInvariantTotErr",
        "txtFileName",
        "txtGuinierEnd_ex",
        "txtPorodStart_ex",
        "txtPorodEnd_ex",
    ]

    @pytest.mark.parametrize("field_name", NULL_CASES, ids=lambda name: name)
    def test_null_line_edit_defaults(self, field_name):
        """Test that certain QLineEdits are empty by default."""
        widget = self.window.findChild(QtWidgets.QLineEdit, field_name)
        assert widget is not None, f"UI widget not found: {field_name}"
        assert widget.text() == ""

    def test_tabs_exist(self):
        """Test that all expected tabs exist, and are labeled and ordered correctly."""
        tab = self.window.findChild(QtWidgets.QTabWidget, "tabWidget")
        assert tab is not None, "Tab widget not found"
        assert tab.count() == 2, "Expected 2 tabs in the Invariant window"
        assert tab.currentIndex() == 0, "Expected the first tab to be selected by default"
        expected_tabs = ["Invariant", "Extrapolation"]
        assert tab.tabText(0) == expected_tabs[0], f"First tab should be '{expected_tabs[0]}'"
        assert tab.tabText(1) == expected_tabs[1], f"Second tab should be '{expected_tabs[1]}'"

    TOOLTIP_CASES: list[tuple[str, str]] = [
        ("cmdStatus", "Get more details of computation such as fraction from extrapolation"),
        ("cmdCalculate", "Compute invariant"),
        ("txtInvariantTot", "Total invariant [Q*], including extrapolated regions."),
        ("txtHighQPower_ex", "Exponent to apply to the Power_law function."),
        ("txtLowQPower_ex", "Exponent to apply to the Power_law function."),
        ("chkHighQ_ex", "Check to extrapolate data at high-Q"),
        ("chkLowQ_ex", "Check to extrapolate data at low-Q"),
        ("txtGuinierEnd_ex", "Q value where low-Q extrapolation ends"),
        ("txtPorodStart_ex", "Q value where high-Q extrapolation starts"),
        ("txtPorodEnd_ex", "Q value where high-Q extrapolation ends"),
    ]

    @pytest.mark.parametrize("widget_name,expected_tooltip", TOOLTIP_CASES, ids=[c[0] for c in TOOLTIP_CASES])
    def test_tooltips_present(self, widget_name, expected_tooltip):
        """Test that tooltips are set correctly"""
        widget = self.window.findChild(QtWidgets.QWidget, widget_name)
        assert widget is not None, f"Widget {widget_name} not found"
        assert widget.toolTip() == expected_tooltip

    VALIDATOR_CASES: list[str] = [
        "txtBackgd",
        "txtScale",
        "txtPorodCst",
        "txtPorodCstErr",
        "txtContrast",
        "txtContrastErr",
        "txtVolFrac1",
        "txtVolFrac1Err",
        "txtGuinierEnd_ex",
        "txtPorodStart_ex",
        "txtPorodEnd_ex",
        "txtHighQPower_ex",
        "txtLowQPower_ex",
    ]

    @pytest.mark.parametrize("field_name", VALIDATOR_CASES, ids=lambda name: name)
    def test_validators(self, field_name):
        """Test that editable QLineEdits have double validators."""
        widget = self.window.findChild(QtWidgets.QLineEdit, field_name)
        assert widget is not None, f"UI widget not found: {field_name}"
        validator = widget.validator()
        assert validator is not None, f"Expected {field_name} to have a validator"
        assert isinstance(validator, GuiUtils.DoubleValidator), f"Expected {field_name} to have DoubleValidator"

    @pytest.mark.parametrize(
        "widget_name",
        [
            "txtName",
            "txtTotalQMin",
            "txtTotalQMax",
            "txtContrastOut",
            "txtContrastOutErr",
            "txtSpecSurf",
            "txtSpecSurfErr",
            "txtInvariantTot",
            "txtInvariantTotErr",
            "txtFileName",
        ],
        ids=lambda name: name,
    )
    def test_readonly_widgets(self, widget_name):
        """Test that widgets are read-only by default."""
        widget = self.window.findChild(QtWidgets.QLineEdit, widget_name)
        assert widget is not None, f"UI widget not found: {widget_name}"
        assert widget.isReadOnly()

    @pytest.mark.parametrize(
        "widget_name",
        [
            "txtBackgd",
            "txtScale",
            "txtPorodCst",
            "txtPorodCstErr",
            "txtContrast",
            "txtContrastErr",
            "txtVolFrac1",
            "txtVolFrac1Err",
            "txtGuinierEnd_ex",
            "txtPorodStart_ex",
            "txtPorodEnd_ex",
            "txtHighQPower_ex",
            "txtLowQPower_ex",
        ],
        ids=lambda name: name,
    )
    def test_editable_widgets(self, widget_name):
        """Test that widgets are editable by default."""
        widget = self.window.findChild(QtWidgets.QLineEdit, widget_name)
        assert widget is not None, f"UI widget not found: {widget_name}"
        assert widget.isReadOnly() is False

    @pytest.mark.parametrize("widget_name", ["cmdStatus", "cmdCalculate"], ids=lambda name: name)
    def test_disabled_widgets(self, widget_name):
        """Test that widgets are disabled by default."""
        widget = self.window.findChild(QtWidgets.QPushButton, widget_name)
        assert widget is not None, f"UI widget not found: {widget_name}"
        assert widget.isEnabled() is False

    @pytest.mark.parametrize(
        "rb_group, rb_list",
        [
            ("VolFracContrastGroup", ["rbVolFrac", "rbContrast"]),
            ("LowQGroup", ["rbLowQGuinier_ex", "rbLowQPower_ex"]),
            ("LowQPowerGroup", ["rbLowQFix_ex", "rbLowQFit_ex"]),
            ("HighQGroup", ["rbHighQFix_ex", "rbHighQFit_ex"]),
        ],
        ids=lambda name: name[0],
    )
    def test_rb_groups(self, rb_group, rb_list):
        """Test that radio buttons are grouped correctly."""
        group = getattr(self.window, rb_group)
        assert group is not None, f"Radio button group not found: {rb_group}"
        for rb in rb_list:
            button = getattr(self.window, rb)
            assert button is not None, f"Radio button not found: {rb}"
            assert isinstance(button, QtWidgets.QRadioButton), f"Expected {rb} to be a QRadioButton"
            assert button.group() == group, f"Expected {rb} to be in group {rb_group}"

    @pytest.mark.parametrize(
        "progress_bar", ["progressBarLowQ", "progressBarData", "progressBarHighQ"], ids=lambda name: name
    )
    def test_progress_bar_initial(self, progress_bar):
        """Test that the progress bar is at 0% initially."""
        bar = getattr(self.window, progress_bar)
        assert bar.value() == 0, "Progress bar should be at 0% initially"

    def test_default_calculation_state(self):
        """Test that contrast calculation is allowed by default."""
        assert self.window.rbContrast.isChecked() is True

    def test_default_extrapolation_state(self):
        """Test that extrapolation checkboxes are unchecked by default."""
        assert self.window.chkLowQ_ex.isChecked() is False
        assert self.window.chkHighQ_ex.isChecked() is False

    MODEL_LINE_EDITS = [
        (WIDGETS.W_BACKGROUND, "_background"),
        (WIDGETS.W_SCALE, "_scale"),
        (WIDGETS.W_POROD_CST, "_porod"),
        (WIDGETS.W_POROD_CST_ERR, "_porod_err"),
        (WIDGETS.W_CONTRAST, "_contrast"),
        (WIDGETS.W_CONTRAST_ERR, "_contrast_err"),
        (WIDGETS.W_VOLFRAC1, "_volfrac1"),
        (WIDGETS.W_VOLFRAC1_ERR, "_volfrac1_err"),
        (WIDGETS.W_HIGHQ_POWER_VALUE_EX, "_high_power_value"),
        (WIDGETS.W_LOWQ_POWER_VALUE_EX, "_low_power_value"),
    ]

    @pytest.mark.parametrize("model_item, variable_name", MODEL_LINE_EDITS, ids=[p[1] for p in MODEL_LINE_EDITS])
    def test_update_from_model_line_edits(self, model_item: int, variable_name: str):
        """Update the globals based on the data in the model line edits."""
        value = "2.0"
        self.window.model.item(model_item).setText(value)
        self.window.update_from_model()
        assert getattr(self.window, variable_name) == float(value)

    MODEL_RB_AND_CHKS = [
        (WIDGETS.W_ENABLE_LOWQ_EX, "_low_extrapolate"),
        (WIDGETS.W_ENABLE_HIGHQ_EX, "_high_extrapolate"),
        (WIDGETS.W_LOWQ_POWER_EX, "_low_power"),
    ]

    @pytest.mark.parametrize("model_item, variable_name", MODEL_RB_AND_CHKS, ids=[p[1] for p in MODEL_RB_AND_CHKS])
    def test_update_from_model_rb_and_chks(self, model_item: int, variable_name: str):
        """Update the globals based on the data in the model radio buttons and checkboxes."""
        self.window.model.item(model_item).setText("true")
        self.window.update_from_model()
        assert getattr(self.window, variable_name)

    GUI_LINE_EDITS = [
        ("txtBackgd", WIDGETS.W_BACKGROUND),
        ("txtScale", WIDGETS.W_SCALE),
        ("txtPorodCst", WIDGETS.W_POROD_CST),
        ("txtPorodCstErr", WIDGETS.W_POROD_CST_ERR),
        ("txtContrast", WIDGETS.W_CONTRAST),
        ("txtContrastErr", WIDGETS.W_CONTRAST_ERR),
        ("txtVolFrac1", WIDGETS.W_VOLFRAC1),
        ("txtVolFrac1Err", WIDGETS.W_VOLFRAC1_ERR),
        ("txtLowQPower_ex", WIDGETS.W_LOWQ_POWER_VALUE_EX),
        ("txtHighQPower_ex", WIDGETS.W_HIGHQ_POWER_VALUE_EX),
    ]

    @pytest.mark.parametrize("gui_widget, model_item", GUI_LINE_EDITS, ids=[p[0] for p in GUI_LINE_EDITS])
    def test_updateFromGui(self, gui_widget: str, model_item: int):
        """Update the globals based on the data in the GUI line edits."""
        line_edit = self.window.findChild(QtWidgets.QLineEdit, gui_widget)
        assert line_edit is not None, f"Line edit not found: {gui_widget}"

        line_edit.setText("5.0")
        line_edit.textEdited.emit("5.0")
        QtWidgets.QApplication.processEvents()

        assert self.window.model.item(model_item).text() == "5.0"

    def test_extrapolation_parameters(self):
        """Test that the extrapolation parameters return None for no data"""
        assert self.window.extrapolation_parameters is None

    def test_enableStatus(self, mocker):
        """Test that the enable status is set correctly."""
        mock_cmdStatus = mocker.patch.object(self.window, "cmdStatus")
        self.window.enableStatus()
        mock_cmdStatus.setEnabled.assert_called_once_with(True)

    @pytest.mark.parametrize("closable", [True, False], ids=["True", "False"])
    def test_setClosable(self, closable):
        """Test that the closable status is set correctly."""
        self.window.setClosable(closable)
        assert self.window._allow_close == closable

    def test_closeEvent(self, mocker):
        """Test that the close event is handled correctly."""
        self.window.setClosable(True)
        self.window.closeEvent(mocker.Mock())
        assert not self.window._allow_close

    def test_closeEvent_allows_close_with_parent(self, mocker):
        mock_parent = mocker.MagicMock()
        mock_set_closable = mocker.patch.object(self.window, "setClosable")
        mock_set_window_state = mocker.patch.object(self.window, "setWindowState")
        mocker.patch.object(self.window, "parentWidget", return_value=mock_parent)

        mock_event = mocker.MagicMock()

        self.window._allow_close = True
        self.window.closeEvent(mock_event)

        mock_set_closable.assert_called_once_with(value=False)
        mock_parent.close.assert_called_once()
        mock_event.accept.assert_called_once()
        mock_event.ignore.assert_not_called()
        mock_set_window_state.assert_not_called()

    def test_isSerializable(self):
        """Test that isSerializable returns the expected boolean."""
        assert self.window.isSerializable() is True

    def test_serialize_state_returns_expected_dict(self, mocker):
        """Test that the serializeState method returns the expected dictionary."""

        # Set fields to known values (strings for QLineEdit)
        self.window.txtVolFract.setText("0.123")
        self.window.txtVolFractErr.setText("0.001")
        self.window.txtContrastOut.setText("42.0")
        self.window.txtContrastOutErr.setText("0.5")
        self.window.txtSpecSurf.setText("3.14")
        self.window.txtSpecSurfErr.setText("0.01")
        self.window.txtInvariantTot.setText("10.0")
        self.window.txtInvariantTotErr.setText("0.2")
        self.window.txtBackgd.setText("0.0")
        self.window.txtContrast.setText("1.0")
        self.window.txtContrastErr.setText("0.05")
        self.window.txtScale.setText("2.0")
        self.window.txtPorodCst.setText("1.23")
        self.window.txtVolFrac1.setText("0.5")
        self.window.txtVolFrac1Err.setText("0.05")
        self.window.txtTotalQMin.setText("0.01")
        self.window.txtTotalQMax.setText("0.25")
        self.window.txtGuinierEnd_ex.setText("0.02")
        self.window.txtPorodStart_ex.setText("0.2")
        self.window.txtPorodEnd_ex.setText("1.0")
        self.window.txtLowQPower_ex.setText("4.0")
        self.window.txtHighQPower_ex.setText("3.0")

        # Set checkbox / radio states
        self.window.rbContrast.setChecked(True)
        self.window.rbVolFrac.setChecked(False)
        self.window.chkLowQ_ex.setChecked(True)
        self.window.chkHighQ_ex.setChecked(False)
        self.window.rbLowQGuinier_ex.setChecked(True)
        self.window.rbLowQPower_ex.setChecked(False)
        self.window.rbLowQFit_ex.setChecked(False)
        self.window.rbLowQFix_ex.setChecked(True)
        self.window.rbHighQFit_ex.setChecked(False)
        self.window.rbHighQFix_ex.setChecked(True)

        mock_update_from_model = mocker.patch.object(self.window, "update_from_model", autospec=True)

        state = self.window.serializeState()

        assert mock_update_from_model.called
        mock_update_from_model.assert_called_once()

        expected = {
            "vol_fraction": "0.123",
            "vol_fraction_err": "0.001",
            "contrast_out": "42.0",
            "contrast_out_err": "0.5",
            "specific_surface": "3.14",
            "specific_surface_err": "0.01",
            "invariant_total": "10.0",
            "invariant_total_err": "0.2",
            "background": "0.0",
            "contrast": "1.0",
            "contrast_err": "0.05",
            "scale": "2.0",
            "porod": "1.23",
            "volfrac1": "0.5",
            "volfrac1_err": "0.05",
            "enable_contrast": True,
            "enable_volfrac": False,
            "total_q_min": "0.01",
            "total_q_max": "0.25",
            "guinier_end_low_q_ex": "0.02",
            "porod_start_high_q_ex": "0.2",
            "porod_end_high_q_ex": "1.0",
            "power_low_q_ex": "4.0",
            "power_high_q_ex": "3.0",
            "enable_low_q_ex": True,
            "enable_high_q_ex": False,
            "low_q_guinier_ex": True,
            "low_q_power_ex": False,
            "low_q_fit_ex": False,
            "low_q_fix_ex": True,
            "high_q_fit_ex": False,
            "high_q_fix_ex": True,
        }

        assert state == expected


@pytest.mark.usefixtures("window_class")
class TestInvariantUIBehaviour:
    def test_contrast_volfrac_group(self):
        """Test that the contrast and volume fraction group works correctly."""
        self.window.rbContrast.setChecked(True)
        assert self.window.rbContrast.isChecked()
        assert not self.window.rbVolFrac.isChecked()

        self.window.rbVolFrac.setChecked(True)
        assert not self.window.rbContrast.isChecked()
        assert self.window.rbVolFrac.isChecked()

    def test_contrast_active(self):
        """Test that the contrast fields are enabled when contrast is selected."""
        self.window.rbContrast.setChecked(True)
        # contrast and contrast error should be enabled
        assert self.window.txtContrast.isEnabled()
        assert self.window.txtContrastErr.isEnabled()
        # volume fraction and volume fraction error should be disabled
        assert not self.window.txtVolFrac1.isEnabled()
        assert not self.window.txtVolFrac1Err.isEnabled()
        # volume fraction and volume fraction error output should be enabled
        assert self.window.txtVolFract.isEnabled()
        assert self.window.txtVolFractErr.isEnabled()
        # contrast and contrast error output should be disabled
        assert not self.window.txtContrastOut.isEnabled()
        assert not self.window.txtContrastOutErr.isEnabled()

    def test_volfrac_active(self):
        """Test that the volume fraction fields are enabled when volume fraction is selected."""
        self.window.rbVolFrac.setChecked(True)
        # contrast and contrast error should be disabled
        assert not self.window.txtContrast.isEnabled()
        assert not self.window.txtContrastErr.isEnabled()
        # volume fraction and volume fraction error should be enabled
        assert self.window.txtVolFrac1.isEnabled()
        assert self.window.txtVolFrac1Err.isEnabled()
        # volume fraction and volume fraction error output should be disabled
        assert not self.window.txtVolFract.isEnabled()
        assert not self.window.txtVolFractErr.isEnabled()
        # contrast and contrast error output should be enabled
        assert self.window.txtContrastOut.isEnabled()
        assert self.window.txtContrastOutErr.isEnabled()

    def test_lowq_extrapolation(self):
        """Test that the lowq extrapolation fields are enabled when lowq extrapolation is selected."""
        self.window.chkLowQ_ex.setChecked(True)
        assert self.window.chkLowQ_ex.isChecked()

        # guinier and power law should be enabled
        assert self.window.rbLowQGuinier_ex.isEnabled()
        assert self.window.rbLowQPower_ex.isEnabled()

        # Guinier selected by default
        assert self.window.rbLowQGuinier_ex.isChecked()
        assert not self.window.rbLowQPower_ex.isChecked()
        assert not self.window.rbLowQFit_ex.isChecked()
        assert not self.window.rbLowQFix_ex.isChecked()
        assert not self.window.txtLowQPower_ex.isEnabled()

    def test_lowq_power_law(self):
        """Test that the power law fields are enabled when power law is selected."""
        self.window.chkLowQ_ex.setChecked(True)
        self.window.rbLowQPower_ex.setChecked(True)
        assert self.window.rbLowQPower_ex.isChecked()

        # Checking power law should uncheck guinier
        assert not self.window.rbLowQGuinier_ex.isChecked()

        # Fit and Fix should be enabled
        assert self.window.rbLowQFit_ex.isEnabled()
        assert self.window.rbLowQFix_ex.isEnabled()

        # Fit checked by default
        assert self.window.rbLowQFit_ex.isChecked()
        assert not self.window.rbLowQFix_ex.isChecked()
        assert not self.window.txtLowQPower_ex.isEnabled()

    def test_lowq_power_law_fix(self):
        """Test that the power law fields are enabled when power law is selected."""
        self.window.chkLowQ_ex.setChecked(True)
        self.window.rbLowQPower_ex.setChecked(True)
        self.window.rbLowQFix_ex.setChecked(True)
        assert self.window.rbLowQFix_ex.isChecked()
        assert not self.window.rbLowQFit_ex.isChecked()

        # fix selected: power text should be enabled
        assert self.window.txtLowQPower_ex.isEnabled()

    def test_lowq_power_law_fit(self):
        """Test that the power law fields are enabled when power law is selected."""
        self.window.chkLowQ_ex.setChecked(True)
        self.window.rbLowQPower_ex.setChecked(True)
        self.window.rbLowQFix_ex.setChecked(True)  # First check fix
        self.window.rbLowQFit_ex.setChecked(True)  # Then check fit
        assert self.window.rbLowQFit_ex.isChecked()
        assert not self.window.rbLowQFix_ex.isChecked()

        # fit selected: power text should be disabled
        assert not self.window.txtLowQPower_ex.isEnabled()

    def test_lowq_guinier(self):
        """Test that the guinier fields are enabled when guinier is selected."""
        self.window.chkLowQ_ex.setChecked(True)
        self.window.rbLowQPower_ex.setChecked(True)  # First check power
        self.window.rbLowQGuinier_ex.setChecked(True)  # Then check guinier
        assert self.window.rbLowQGuinier_ex.isChecked()
        assert not self.window.rbLowQPower_ex.isChecked()

        # guinier selected: power law options should be disabled
        assert not self.window.rbLowQFit_ex.isEnabled()
        assert not self.window.rbLowQFix_ex.isEnabled()
        assert not self.window.txtLowQPower_ex.isEnabled()

    def test_highq_extrapolation(self):
        """Test that the highq extrapolation fields are enabled when highq extrapolation is selected."""
        self.window.chkHighQ_ex.setChecked(True)
        assert self.window.chkHighQ_ex.isChecked()

        # fit should be enabled by default
        assert self.window.rbHighQFit_ex.isChecked()
        assert not self.window.rbHighQFix_ex.isChecked()
        assert not self.window.txtHighQPower_ex.isEnabled()

        # fix selected: power text should be enabled
        self.window.rbHighQFix_ex.setChecked(True)
        assert self.window.rbHighQFix_ex.isChecked()
        assert not self.window.rbHighQFit_ex.isChecked()
        assert self.window.txtHighQPower_ex.isEnabled()

        # switch back to fit
        self.window.rbHighQFit_ex.setChecked(True)
        assert self.window.rbHighQFit_ex.isChecked()
        assert not self.window.rbHighQFix_ex.isChecked()
        assert not self.window.txtHighQPower_ex.isEnabled()
