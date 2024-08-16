#!/usr/bin/env python3

from PySide6.QtWidgets import QWidget


class StrView(QWidget):
    def __init__(self, initial_str = str | None):
        super().__init__()
        self._current_str: str | None = initial_str

    @property
    def current_str(self):
        return self._current_str

    @current_str.setter
    def current_str(self, value: str | None):
        self._current_str = value
