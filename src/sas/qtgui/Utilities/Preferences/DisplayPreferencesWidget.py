from sas.system import config, style

from .PreferencesWidget import PreferencesWidget


class DisplayPreferencesWidget(PreferencesWidget):
    def __init__(self):
        super(DisplayPreferencesWidget, self).__init__("Display Settings")
        self.config_params = ['QT_SCALE_FACTOR',
                              'QT_AUTO_SCREEN_SCALE_FACTOR',
                              'DISABLE_RESIDUAL_PLOT',
                              'DISABLE_POLYDISPERSITY_PLOT',
                              'THEME']
        self.restart_params = {'QT_SCALE_FACTOR': 'QT Screen Scale Factor',
                               'QT_AUTO_SCREEN_SCALE_FACTOR': "Enable Automatic Scaling",
                               'THEME': "Display theme"}

    def _addAllWidgets(self):
        self.theme = self.addComboBox(title="Theme", params=style.get_theme_names(), default='Default')
        self.theme.currentIndexChanged.connect(
            lambda: self._stageChange('THEME', self.theme.currentText()))
        self.qtScaleFactor = self.addFloatInput(
            title="QT Screen Scale Factor",
            default_number=config.QT_SCALE_FACTOR)
        self.qtScaleFactor.textChanged.connect(
            lambda: self._validate_input_and_stage(self.qtScaleFactor, 'QT_SCALE_FACTOR'))
        self.autoScaling = self.addCheckBox(
            title="Enable Automatic Scaling",
            checked=config.QT_AUTO_SCREEN_SCALE_FACTOR)
        self.autoScaling.clicked.connect(
            lambda: self._stageChange('QT_AUTO_SCREEN_SCALE_FACTOR', self.autoScaling.isChecked()))
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

    def _toggleBlockAllSignaling(self, toggle):
        self.qtScaleFactor.blockSignals(toggle)
        self.autoScaling.blockSignals(toggle)
        self.disableResidualPlot.blockSignals(toggle)
        self.disablePolydispersityPlot.blockSignals(toggle)

    def _restoreFromConfig(self):
        self.theme.setCurrentText(config.THEME)
        self.qtScaleFactor.setText(str(config.QT_SCALE_FACTOR))
        self.qtScaleFactor.setStyleSheet("background-color: white")
        self.autoScaling.setChecked(bool(config.QT_AUTO_SCREEN_SCALE_FACTOR))
        self.disableResidualPlot.setChecked(config.DISABLE_RESIDUAL_PLOT)
        self.disablePolydispersityPlot.setChecked(config.DISABLE_POLYDISPERSITY_PLOT)
