#!/usr/bin/env python3

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

    def __init__(self):
        super().__init__()
        self.setTristate(True)
