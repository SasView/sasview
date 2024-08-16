#!/usr/bin/env python3

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class StrViewWidget(QWidget):
    def __init__(self, initial_str: str | None):
        super().__init__()
        self._current_str: str | None = initial_str

        self.value_label = QLabel()

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.value_label)

    def update_view(self):
        self.value_label.setText(f'Value: {self._current_str}')

    @property
    def current_str(self):
        return self._current_str

    @current_str.setter
    def current_str(self, value: str | None):
        self._current_str = value
        self.update_view()
