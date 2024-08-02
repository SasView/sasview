#!/usr/bin/env python3

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QWidget
from PySide6.QtGui import QRegularExpressionValidator
from dataset_types import default_units

class ColumnUnit(QWidget):
    column_changed = Signal()

    def create_col_combo_box(self, options) -> QComboBox:
        new_combo_box = QComboBox()
        for option in options:
            new_combo_box.addItem(option)
        new_combo_box.setEditable(True)
        validator = QRegularExpressionValidator(r"[a-zA-Z0-9]+")
        new_combo_box.setValidator(validator)
        new_combo_box.currentTextChanged.connect(self.on_option_change)
        return new_combo_box

    def create_unit_combo_box(self, selected_option: str) -> QComboBox:
        new_combo_box = QComboBox()
        default_unit = default_units[selected_option]
        new_combo_box.addItem(default_unit)
        return new_combo_box

    def replace_options(self, new_options):
        self.col_widget.clear()
        self.col_widget.addItems(new_options)

    def set_current_column(self, new_column_value: str):
        self.col_widget.setCurrentText(new_column_value)
        new_unit = default_units[new_column_value]
        self.unit_widget.clear()
        self.unit_widget.addItem(new_unit)


    @Slot()
    def on_option_change(self):
        # Need to update units.
        #
        # If the new option is empty string, its probably because the current
        # options have been removed. Can safely ignore this.
        self.column_changed.emit()
        new_option = self.col_widget.currentText()
        if new_option == '':
            return
        try:
            new_unit = default_units[new_option]
            self.unit_widget.clear()
            self.unit_widget.addItem(new_unit)
        except KeyError:
            # Means the units for this column aren't known. This shouldn't be
            # the case in the real version so for now we'll just clear the unit
            # widget.
            self.unit_widget.clear()

    @property
    def current_column(self):
        return self.col_widget.currentText()


    def __init__(self, options) -> None:
        super().__init__()
        self.col_widget = self.create_col_combo_box(options)
        self.unit_widget = self.create_unit_combo_box(self.col_widget.currentText())
        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.col_widget)
        self.layout.addWidget(self.unit_widget)