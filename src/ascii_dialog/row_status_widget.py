#!/usr/bin/env python3

from PySide6.QtWidgets import QCheckBox


class RowStatusWidget(QCheckBox):
    def __init__(self):
        super().__init__()
        self.setTristate(True)
