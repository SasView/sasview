from sas.system import config

from .PreferencesWidget import PreferencesWidget


class GeneralPreferencesWidget(PreferencesWidget):
    def __init__(self):
        super().__init__("General Settings")
        # Both settings apply to windows opened after the change; no restart is needed
        self.config_params = ['OPEN_PLOTS_DETACHED',
                              'OPEN_PERSPECTIVE_DETACHED']

    def _addAllWidgets(self):
        self.addHeaderText("Window placement")
        self.plotsDetached = self.addCheckBox(
            title="Open new plots in separate windows",
            checked=config.OPEN_PLOTS_DETACHED)
        self.plotsDetached.clicked.connect(
            lambda: self._stageChange('OPEN_PLOTS_DETACHED', self.plotsDetached.isChecked()))
        self.perspectiveDetached = self.addCheckBox(
            title="Open analysis perspectives in separate windows",
            checked=config.OPEN_PERSPECTIVE_DETACHED)
        self.perspectiveDetached.clicked.connect(
            lambda: self._stageChange('OPEN_PERSPECTIVE_DETACHED', self.perspectiveDetached.isChecked()))

    def _toggleBlockAllSignaling(self, toggle):
        self.plotsDetached.blockSignals(toggle)
        self.perspectiveDetached.blockSignals(toggle)

    def _restoreFromConfig(self):
        self.plotsDetached.setChecked(bool(config.OPEN_PLOTS_DETACHED))
        self.perspectiveDetached.setChecked(bool(config.OPEN_PERSPECTIVE_DETACHED))
