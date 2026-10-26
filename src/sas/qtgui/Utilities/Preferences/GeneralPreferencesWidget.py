from PySide6.QtWidgets import QHBoxLayout, QLabel, QSpinBox

from sas.system import config

from .PreferencesWidget import PreferencesWidget


class GeneralPreferencesWidget(PreferencesWidget):
    def __init__(self):
        super().__init__("General Settings")
        self.config_params = ['UNDO_STACK_MAX_DEPTH']

    def _addAllWidgets(self):
        layout = QHBoxLayout()
        label = QLabel("Undo History Depth: ", self)
        layout.addWidget(label)

        self.undoDepthSpinner = QSpinBox(self)
        self.undoDepthSpinner.setMinimum(10)
        self.undoDepthSpinner.setMaximum(1000)
        self.undoDepthSpinner.setValue(config.UNDO_STACK_MAX_DEPTH)
        layout.addWidget(self.undoDepthSpinner)

        self.verticalLayout.addLayout(layout)

        self.undoDepthSpinner.valueChanged.connect(
            lambda val: self._stageChange('UNDO_STACK_MAX_DEPTH', val))

    def _toggleBlockAllSignaling(self, toggle):
        self.undoDepthSpinner.blockSignals(toggle)

    def _restoreFromConfig(self):
        self.undoDepthSpinner.setValue(config.UNDO_STACK_MAX_DEPTH)
