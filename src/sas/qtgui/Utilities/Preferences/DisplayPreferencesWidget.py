from sas.system import config, style

from sas.qtgui.Utilities import GuiUtils

from .PreferencesWidget import PreferencesWidget


class DisplayPreferencesWidget(PreferencesWidget):
    def __init__(self):
        super(DisplayPreferencesWidget, self).__init__("Display Settings")
        self.config_params = ['QT_SCALE_FACTOR',
                              'QT_AUTO_SCREEN_SCALE_FACTOR',
                              'DISABLE_RESIDUAL_PLOT',
                              'DISABLE_POLYDISPERSITY_PLOT',
                              'THEME',
                              'FONT_SIZE']
        self.restart_params = {'QT_SCALE_FACTOR': 'QT Screen Scale Factor',
                               'QT_AUTO_SCREEN_SCALE_FACTOR': "Enable Automatic Scaling"}

    def _addAllWidgets(self):
        self.addHorizontalLine()
        self.theme = self.addComboBox(title="Theme", params=style.get_theme_names(), default=style.theme)
        self.theme.currentIndexChanged.connect(self._previewTheme)
        self.font_size = self.addComboBox(title="Font Size", params=['10.0', '12.0', '14.0'],
                                          default=str(style.font_size))
        self.font_size.currentIndexChanged.connect(self._previewFont)
        self.addHorizontalLine()
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

    def _toggleBlockAllSignaling(self, toggle):
        self.qtScaleFactor.blockSignals(toggle)
        self.autoScaling.blockSignals(toggle)

    def _restoreFromConfig(self):
        self.theme.setCurrentText(config.THEME)
        self._previewTheme()
        self.qtScaleFactor.setText(str(config.QT_SCALE_FACTOR))
        GuiUtils.updateProperty(self.qtScaleFactor, 'warning', 'false')
        self.autoScaling.setChecked(bool(config.QT_AUTO_SCREEN_SCALE_FACTOR))

    def _previewTheme(self):
        # Store existing theme
        self._stageChange('THEME', self.theme.currentText())
        self._set_theme()

    def _previewFont(self):
        self._stageChange('FONT_SIZE', float(self.font_size.currentText()))
        self._set_theme()

    def _set_theme(self):
        theme = config.THEME
        font = config.FONT_SIZE
        # The CSS and font_size getters uses the config values, not the set theme
        config.THEME = self.theme.currentText()
        config.FONT_SIZE = float(self.font_size.currentText())
        self.parent.parent.setStyleSheet(style.css)
        # Set the config theme items back for easy reset
        config.THEME = theme
        config.FONT_SIZE = font
