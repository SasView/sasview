#!/usr/bin/env python3

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QComboBox, QCompleter, QHBoxLayout, QWidget
from PySide6.QtGui import QRegularExpressionValidator
from sasdata.dataset_types import unit_kinds

class ColumnUnit(QWidget):
    """Widget with 2 combo boxes: one allowing the user to pick a column, and
    another to specify the units for that column."""
    def __init__(self, options) -> None:
        super().__init__()
        self.col_widget = self.create_col_combo_box(options)
        self.unit_widget = self.create_unit_combo_box(self.col_widget.currentText())
        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.col_widget)
        self.layout.addWidget(self.unit_widget)

    column_changed = Signal()

    def create_col_combo_box(self, options: list[str]) -> QComboBox:
        """Create the combo box for specifying the column based on the given
        options."""
        new_combo_box = QComboBox()
        for option in options:
            new_combo_box.addItem(option)
        new_combo_box.setEditable(True)
        validator = QRegularExpressionValidator(r"[a-zA-Z0-9]+")
        new_combo_box.setValidator(validator)
        new_combo_box.currentTextChanged.connect(self.on_option_change)
        return new_combo_box

    def create_unit_combo_box(self, selected_option: str) -> QComboBox:
        """Create the combo box for specifying the unit for selected_option"""
        new_combo_box = QComboBox()
        new_combo_box.setEditable(True)
        # word_list = ['alpha', 'omega', 'omicron', 'zeta']
        # completer = QCompleter(word_list, self)
        # new_combo_box.setCompleter(completer)
        self.update_units(new_combo_box, selected_option)
        return new_combo_box

    def update_units(self, unit_box: QComboBox, selected_option: str):
        unit_box.clear()
        options = [unit.symbol for unit in unit_kinds[selected_option].units]
        for option in options:
            unit_box.addItem(option)


    def replace_options(self, new_options) -> None:
        """Replace the old options for the column with new_options"""
        self.col_widget.clear()
        self.col_widget.addItems(new_options)

    def set_current_column(self, new_column_value: str) -> None:
        """Change the current selected column to new_column_value"""
        self.col_widget.setCurrentText(new_column_value)
        self.update_units(self.unit_widget, new_column_value)


    @Slot()
    def on_option_change(self):
        # If the new option is empty string, its probably because the current
        # options have been removed. Can safely ignore this.
        self.column_changed.emit()
        new_option = self.col_widget.currentText()
        if new_option == '':
            return
        try:
            self.update_units(self.unit_widget, new_option)
        except KeyError:
            # Means the units for this column aren't known. This shouldn't be
            # the case in the real version so for now we'll just clear the unit
            # widget.
            self.unit_widget.clear()

    @property
    def current_column(self):
        """The currently selected column."""
        return self.col_widget.currentText()
