#!/usr/bin/env python3


from PySide6.QtCore import Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu

class SelectionMenu(QMenu):
    select_all_event = Signal()
    deselect_all_event = Signal()

    def __init__(self):
        super().__init__()

        select_all = QAction("Select All")
        select_all.triggered.connect(self.select_all_event)

        deselect_all = QAction("Deselect All")
        deselect_all.triggered.connect(self.deselect_all_event)

        self.addAction(select_all)
        self.addAction(deselect_all)
