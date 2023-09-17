from sas.system import config

from sas.qtgui.Utilities import GuiUtils

from .PreferencesWidget import PreferencesWidget


class PlottingPreferencesWidget(PreferencesWidget):
    def __init__(self):
        super(PlottingPreferencesWidget, self).__init__("Plotting Options")
        self.config_params = ['FITTING_PLOT_FULL_WIDTH_LEGENDS',
                              'FITTING_PLOT_LEGEND_TRUNCATE',
                              'FITTING_PLOT_LEGEND_MAX_LINE_LENGTH']

    def _addAllWidgets(self):
        self.legendFullWidth = self.addCheckBox(
            title="Use full-width plot legends (most compatible)?",
            checked=config.FITTING_PLOT_FULL_WIDTH_LEGENDS)
        self.legendFullWidth.clicked.connect(
            lambda: self._stageChange('FITTING_PLOT_FULL_WIDTH_LEGENDS', self.legendFullWidth.isChecked()))
        self.legendTruncate = self.addCheckBox(
            title="Use truncated legend entries?",
            checked=config.FITTING_PLOT_LEGEND_TRUNCATE)
        self.legendTruncate.clicked.connect(
            lambda: self._stageChange('FITTING_PLOT_LEGEND_TRUNCATE', self.legendTruncate.isChecked()))
        self.legendLineLength = self.addIntegerInput(
            title="Legend entry line length",
            default_number=config.FITTING_PLOT_LEGEND_MAX_LINE_LENGTH)
        self.legendLineLength.textChanged.connect(
            lambda: self._validate_input_and_stage(self.legendLineLength, 'FITTING_PLOT_LEGEND_MAX_LINE_LENGTH'))

    def _toggleBlockAllSignaling(self, toggle):
        self.legendFullWidth.blockSignals(toggle)
        self.legendTruncate.blockSignals(toggle)
        self.legendLineLength.blockSignals(toggle)

    def _restoreFromConfig(self):
        self.legendFullWidth.setChecked(bool(config.FITTING_PLOT_FULL_WIDTH_LEGENDS))
        self.legendTruncate.setChecked(bool(config.FITTING_PLOT_LEGEND_TRUNCATE))
        self.legendLineLength.setText(str(config.FITTING_PLOT_LEGEND_MAX_LINE_LENGTH))
        GuiUtils.updateProperty(self.legendLineLength, 'warning', 'false')
