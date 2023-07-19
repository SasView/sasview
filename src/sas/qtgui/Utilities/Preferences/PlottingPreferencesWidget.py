from sas.system import config

from .PreferencesWidget import PreferencesWidget


class PlottingPreferencesWidget(PreferencesWidget):
    def __init__(self):
        super(PlottingPreferencesWidget, self).__init__("Plotting Options")
        self.config_params = ['FITTING_PLOT_FULL_WIDTH_LEGENDS',
                              'FITTING_PLOT_LEGEND_TRUNCATE',
                              'FITTING_PLOT_LEGEND_MAX_LINE_LENGTH',
                              'DISABLE_RESIDUALS']

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
        self.disableResiduals = self.addCheckBox(
            title="Disable Residuals Display",
            checked=config.DISABLE_RESIDUALS)
        self.disableResiduals.clicked.connect(
            lambda: self._stageChange('DISABLE_RESIDUALS', self.disableResiduals.isChecked()))

    def _toggleBlockAllSignaling(self, toggle):
        self.legendFullWidth.blockSignals(toggle)
        self.legendTruncate.blockSignals(toggle)
        self.legendLineLength.blockSignals(toggle)
        self.disableResiduals.blockSignals(toggle)

    def _restoreFromConfig(self):
        self.legendFullWidth.setChecked(bool(config.FITTING_PLOT_FULL_WIDTH_LEGENDS))
        self.legendTruncate.setChecked(bool(config.FITTING_PLOT_LEGEND_TRUNCATE))
        self.legendLineLength.setText(str(config.FITTING_PLOT_LEGEND_MAX_LINE_LENGTH))
        self.legendLineLength.setStyleSheet("background-color: white")
        self.disableResiduals.setChecked(config.DISABLE_RESIDUALS)
