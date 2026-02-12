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

    NULL_CASES: list[str] = ["txtName", "txtPorodCst", "txtPorodCstErr", "txtContrast", "txtContrastErr",
        "txtVolFrac1", "txtVolFrac1Err", "txtVolFract", "txtVolFractErr",
        "txtContrastOut", "txtContrastOutErr", "txtSpecSurf", "txtSpecSurfErr",
        "txtInvariantTot", "txtInvariantTotErr", "txtFileName",
        "txtGuinierEnd_ex", "txtPorodStart_ex", "txtPorodEnd_ex"]

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
        "txtBackgd", "txtScale", "txtPorodCst", "txtPorodCstErr", "txtContrast", "txtContrastErr",
        "txtVolFrac1", "txtVolFrac1Err", "txtGuinierEnd_ex", "txtPorodStart_ex", "txtPorodEnd_ex",
        "txtHighQPower_ex", "txtLowQPower_ex"
    ]

    @pytest.mark.parametrize("field_name", VALIDATOR_CASES, ids=lambda name: name)
    def test_validators(self, field_name):
        """Test that editable QLineEdits have double validators."""
        widget = self.window.findChild(QtWidgets.QLineEdit, field_name)
        assert widget is not None, f"UI widget not found: {field_name}"
        validator = widget.validator()
        assert validator is not None, f"Expected {field_name} to have a validator"
        assert isinstance(validator, GuiUtils.DoubleValidator), f"Expected {field_name} to have DoubleValidator"

    @pytest.mark.parametrize("widget_name", [
        "txtName", "txtTotalQMin", "txtTotalQMax", "txtContrastOut", "txtContrastOutErr", "txtSpecSurf",
        "txtSpecSurfErr", "txtInvariantTot", "txtInvariantTotErr", "txtFileName"
    ], ids=lambda name: name)
    def test_readonly_widgets(self, widget_name):
        """Test that widgets are read-only by default."""
        widget = self.window.findChild(QtWidgets.QLineEdit, widget_name)
        assert widget is not None, f"UI widget not found: {widget_name}"
        assert widget.isReadOnly()

    @pytest.mark.parametrize("widget_name", [
        "txtBackgd", "txtScale", "txtPorodCst", "txtPorodCstErr", "txtContrast", "txtContrastErr",
        "txtVolFrac1", "txtVolFrac1Err", "txtGuinierEnd_ex", "txtPorodStart_ex", "txtPorodEnd_ex",
        "txtHighQPower_ex", "txtLowQPower_ex"
    ], ids=lambda name: name)
    def test_editable_widgets(self, widget_name):
        """Test that widgets are editable by default."""
        widget = self.window.findChild(QtWidgets.QLineEdit, widget_name)
        assert widget is not None, f"UI widget not found: {widget_name}"
        assert widget.isReadOnly() is False

    @pytest.mark.parametrize("widget_name", [
        "cmdStatus", "cmdCalculate"
    ], ids=lambda name: name)
    def test_disabled_widgets(self, widget_name):
        """Test that widgets are disabled by default."""
        widget = self.window.findChild(QtWidgets.QPushButton, widget_name)
        assert widget is not None, f"UI widget not found: {widget_name}"
        assert widget.isEnabled() is False

    @pytest.mark.parametrize("rb_group, rb_list", [
        ("VolFracContrastGroup", ["rbVolFrac", "rbContrast"]),
        ("LowQGroup", ["rbLowQGuinier_ex", "rbLowQPower_ex"]),
        ("LowQPowerGroup", ["rbLowQFix_ex", "rbLowQFit_ex"]),
        ("HighQGroup", ["rbHighQFix_ex", "rbHighQFit_ex"]),
    ], ids=lambda name: name[0])
    def test_rb_groups(self, rb_group, rb_list):
        """Test that radio buttons are grouped correctly."""
        group = getattr(self.window, rb_group)
        assert group is not None, f"Radio button group not found: {rb_group}"
        for rb in rb_list:
            button = getattr(self.window, rb)
            assert button is not None, f"Radio button not found: {rb}"
            assert isinstance(button, QtWidgets.QRadioButton), f"Expected {rb} to be a QRadioButton"
            assert button.group() == group, f"Expected {rb} to be in group {rb_group}"

    @pytest.mark.parametrize("progress_bar", [
        "progressBarLowQ", "progressBarData", "progressBarHighQ"
    ], ids=lambda name: name)
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
    @pytest.mark.parametrize("model_item, variable_name", MODEL_LINE_EDITS, ids = [p[1] for p in MODEL_LINE_EDITS])
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
    @pytest.mark.parametrize("model_item, variable_name", MODEL_RB_AND_CHKS, ids = [p[1] for p in MODEL_RB_AND_CHKS])
    def test_update_from_model_rb_and_chks(self, model_item: int, variable_name: str):
        """Update the globals based on the data in the model radio buttons and checkboxes."""
        self.window.model.item(model_item).setText("true")
        self.window.update_from_model()
        assert getattr(self.window, variable_name) == True

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
    @pytest.mark.parametrize("gui_widget, model_item", GUI_LINE_EDITS, ids = [p[0] for p in GUI_LINE_EDITS])
    def test_updateFromGui(self, gui_widget: str, model_item: int):
        """Update the globals based on the data in the GUI line edits."""
        line_edit = self.window.findChild(QtWidgets.QLineEdit, gui_widget)
        assert line_edit is not None, f"Line edit not found: {gui_widget}"

        line_edit.textEdited.emit("5.0")
        QtWidgets.QApplication.processEvents()

        assert self.window.model.item(model_item).text() == "5.0"


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
