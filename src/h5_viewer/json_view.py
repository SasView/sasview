#!/usr/bin/env python3

from PySide6.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget
from json import dumps
from pprint import pformat

class JsonViewWidget(QWidget):
    def __init__(self, initial_json_dict: dict[str, object]):
        super().__init__()
        self._json_dict: dict[str, object ] = initial_json_dict

        self.label = QLabel('JSON Data')
        self.text_box = QTextEdit()
        self.text_box.setReadOnly(True)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.text_box)

    @property
    def current_json_dict(self):
        return self._json_dict

    @current_json_dict.setter
    def current_json_dict(self, value: dict[str, object]):
        self._json_dict = value

    @property
    def formatted_json(self) -> str:
        return pformat(dumps(self._json_dict))
