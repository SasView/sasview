#!/usr/bin/env python3

from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QWidget


class RowStatusWidget(QWidget):
    """Widget to toggle whether the row is to be included as part of the data."""
    def __init__(self, initial_value: bool, row: int):
        super().__init__()
        self.row = row
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(initial_value)
        self.updateLabel()
        self.checkbox.stateChanged.connect(self.onStateChange)
        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.checkbox, alignment=Qt.AlignmentFlag.AlignCenter)

    status_changed = Signal(int)
    def updateLabel(self):
        """Update the label of the check box depending on whether it is checked,
        or not."""
        pass


    @Slot()
    def onStateChange(self):
        self.updateLabel()
        self.status_changed.emit(self.row)

    def isChecked(self) -> bool:
        return self.checkbox.isChecked()

    def setChecked(self, new_value: bool):
        self.checkbox.setChecked(new_value)
