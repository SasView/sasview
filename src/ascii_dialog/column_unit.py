#!/usr/bin/env python3

from PySide6.QtWidgets import QComboBox, QWidget
from PySide6.QtGui import QRegularExpressionValidator
from dataset_types import default_units


class ColumnUnit(QWidget):
    def create_col_combo_box(self, options) -> QComboBox:
        new_combo_box = QComboBox()
        for option in options:
            new_combo_box.addItem(option)
        new_combo_box.setEditable(True)
        validator = QRegularExpressionValidator(r"[a-zA-Z0-9]+")
        new_combo_box.setValidator(validator)
        return new_combo_box

    def create_unit_combo_box(self, selected_option: str) -> QComboBox:
        new_combo_box = QComboBox()
        default_unit = default_units[selected_option]
        new_combo_box.addItem(default_unit)
        return new_combo_box

    def replace_options(self, new_options):
        self.col_widget.clear()
        self.col_widget.addItems(new_options)
        new_unit = default_units[self.col_widget.currentText()]
        self.unit_widget.clear()
        self.unit_widget.addItem(new_unit)

    def set_current_column(self, new_column_value: str):
        self.col_widget.setCurrentText(new_column_value)
        new_unit = default_units[new_column_value]
        self.unit_widget.clear()
        self.unit_widget.addItem(new_unit)

    @property
    def current_column(self):
        self.col_widget.currentText()


    def __init__(self, options) -> None:
        super().__init__()
        self.col_widget = self.create_col_combo_box(options)
        self.unit_widget = self.create_unit_combo_box(self.col_widget.currentText())
