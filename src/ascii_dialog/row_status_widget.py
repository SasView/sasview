#!/usr/bin/env python3

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QCheckBox


class RowStatusWidget(QCheckBox):
    """Widget to toggle whether the row is to be included as part of the data."""
    def __init__(self, initial_value: bool, row: int):
        super().__init__()
        self.row = row
        self.setChecked(initial_value)
        self.updateLabel()
        self.stateChanged.connect(self.onStateChange)

    status_changed = Signal(int)
    def updateLabel(self):
        """Update the label of the check box depending on whether it is checked,
        or not."""
        if self.isChecked():
            self.setText('Included')
        else:
            self.setText('Not Included')


    @Slot()
    def onStateChange(self):
        self.updateLabel()
        self.status_changed.emit(self.row)
