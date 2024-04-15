from sas.system import config

from .PreferencesWidget import PreferencesWidget


class PlottingPreferencesWidget(PreferencesWidget):
    def __init__(self):
        super(PlottingPreferencesWidget, self).__init__("Plotting Options")
        self.config_params = ['FITTING_PLOT_FULL_WIDTH_LEGENDS',
                              'FITTING_PLOT_LEGEND_TRUNCATE',
                              'FITTING_PLOT_LEGEND_MAX_LINE_LENGTH',
                              'DISABLE_RESIDUAL_PLOT',
                              'DISABLE_POLYDISPERSITY_PLOT',
                              'USE_MATPLOTLIB_TOOLBAR']

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
        self.disableResidualPlot = self.addCheckBox(
            title="Disable Residuals Display",
            checked=config.DISABLE_RESIDUAL_PLOT)
        self.disableResidualPlot.clicked.connect(
            lambda: self._stageChange('DISABLE_RESIDUAL_PLOT', self.disableResidualPlot.isChecked()))
        self.disablePolydispersityPlot = self.addCheckBox(
            title="Disable Polydispersity Plot Display",
            checked=config.DISABLE_POLYDISPERSITY_PLOT)
        self.disablePolydispersityPlot.clicked.connect(
            lambda: self._stageChange('DISABLE_POLYDISPERSITY_PLOT', self.disablePolydispersityPlot.isChecked()))
        self.useMatplotlibToolbar = self.addCheckBox(
            title="Show toolbar on all new plots",
            checked=config.USE_MATPLOTLIB_TOOLBAR)
        self.useMatplotlibToolbar.clicked.connect(
            lambda: self._stageChange('USE_MATPLOTLIB_TOOLBAR', self.useMatplotlibToolbar.isChecked()))

    def _toggleBlockAllSignaling(self, toggle):
        self.legendFullWidth.blockSignals(toggle)
        self.legendTruncate.blockSignals(toggle)
        self.legendLineLength.blockSignals(toggle)
        self.disableResidualPlot.blockSignals(toggle)
        self.disablePolydispersityPlot.blockSignals(toggle)
        self.useMatplotlibToolbar.blockSignals(toggle)

    def _restoreFromConfig(self):
        self.legendFullWidth.setChecked(bool(config.FITTING_PLOT_FULL_WIDTH_LEGENDS))
        self.legendTruncate.setChecked(bool(config.FITTING_PLOT_LEGEND_TRUNCATE))
        self.legendLineLength.setText(str(config.FITTING_PLOT_LEGEND_MAX_LINE_LENGTH))
        self.legendLineLength.setStyleSheet("background-color: white")
        self.disableResidualPlot.setChecked(config.DISABLE_RESIDUAL_PLOT)
        self.disablePolydispersityPlot.setChecked(config.DISABLE_POLYDISPERSITY_PLOT)
        self.useMatplotlibToolbar.setChecked(config.USE_MATPLOTLIB_TOOLBAR)
