#!/usr/bin/env python3

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QCheckBox


class RowStatusWidget(QCheckBox):
    """Widget to toggle whether the row is to be included as part of the data."""
    def __init__(self, initial_value: bool, row: int):
        super().__init__()
        self.row = row
        self.setChecked(initial_value)
        self.update_label()
        self.stateChanged.connect(self.on_state_change)

    status_changed = Signal(int)
    def update_label(self):
        """Update the label of the check box depending on whether it is checked,
        or not."""
        if self.isChecked():
            self.setText('Included')
        else:
            self.setText('Not Included')


    @Slot()
    def on_state_change(self):
        self.update_label()
        self.status_changed.emit(self.row)
