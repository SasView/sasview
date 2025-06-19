#!/usr/bin/env python3


from PySide6.QtCore import Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QWidget

class SelectionMenu(QMenu):
    select_all_event = Signal()
    deselect_all_event = Signal()

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        select_all = QAction("Select All", parent)
        select_all.triggered.connect(self.select_all_event)

        deselect_all = QAction("Deselect All", parent)
        deselect_all.triggered.connect(self.deselect_all_event)

        self.addAction(select_all)
        self.addAction(deselect_all)
