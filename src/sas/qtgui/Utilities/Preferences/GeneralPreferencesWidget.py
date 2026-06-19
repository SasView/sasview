from sas.system import config

from .PreferencesWidget import PreferencesWidget


class GeneralPreferencesWidget(PreferencesWidget):
    def __init__(self):
        super().__init__("General Settings")
        self.config_params = ['UNDO_STACK_MAX_DEPTH']

    def _addAllWidgets(self):
        self.undoDepthSpinner = self.addSpinBox(
            title="Undo History Depth", minimum=10, maximum=1000, default=config.UNDO_STACK_MAX_DEPTH)
        self.undoDepthSpinner.valueChanged.connect(
            lambda val: self._stageChange('UNDO_STACK_MAX_DEPTH', val))

    def _toggleBlockAllSignaling(self, toggle):
        self.undoDepthSpinner.blockSignals(toggle)

    def _restoreFromConfig(self):
        self.undoDepthSpinner.setValue(config.UNDO_STACK_MAX_DEPTH)
