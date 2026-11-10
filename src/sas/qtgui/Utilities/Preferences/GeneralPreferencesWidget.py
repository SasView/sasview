from sas.system import config

from .PreferencesWidget import PreferencesWidget


class GeneralPreferencesWidget(PreferencesWidget):
    def __init__(self):
        super().__init__("General Settings")
        # The window placement settings apply to windows opened after the change;
        # no restart is needed
        self.config_params = ['UNDO_STACK_MAX_DEPTH',
                              'OPEN_PLOTS_DETACHED',
                              'OPEN_PERSPECTIVE_DETACHED']

    def _addAllWidgets(self):
        self.undoDepthSpinner = self.addSpinBox(
            title="Undo History Depth", minimum=10, maximum=1000, default=config.UNDO_STACK_MAX_DEPTH)
        self.undoDepthSpinner.valueChanged.connect(
            lambda val: self._stageChange('UNDO_STACK_MAX_DEPTH', val))

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
        self.undoDepthSpinner.blockSignals(toggle)
        self.plotsDetached.blockSignals(toggle)
        self.perspectiveDetached.blockSignals(toggle)

    def _restoreFromConfig(self):
        self.undoDepthSpinner.setValue(config.UNDO_STACK_MAX_DEPTH)
        self.plotsDetached.setChecked(bool(config.OPEN_PLOTS_DETACHED))
        self.perspectiveDetached.setChecked(bool(config.OPEN_PERSPECTIVE_DETACHED))
