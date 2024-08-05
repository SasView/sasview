#!/usr/bin/env python3

from PySide6.QtCore import Slot
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QCheckBox


class RowStatusWidget(QCheckBox):
    def update_label(self):
        current_status = self.checkState()
        match current_status:
            case Qt.CheckState.Unchecked:
                self.setText('Not included')
            case Qt.CheckState.PartiallyChecked:
                self.setText('Included as metadata')
            case Qt.CheckState.Checked:
                self.setText('Included as data')

    @Slot()
    def on_state_change(self):
        self.update_label()

    def __init__(self, initial_value: Qt.CheckState, row: int):
        super().__init__()
        self.row = row
        self.setTristate(True)
        self.setCheckState(initial_value)
        self.update_label()
        self.stateChanged.connect(self.on_state_change)
