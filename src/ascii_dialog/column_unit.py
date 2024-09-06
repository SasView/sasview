#!/usr/bin/env python3

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QComboBox, QCompleter, QHBoxLayout, QWidget
from PySide6.QtGui import QRegularExpressionValidator
from sasdata.dataset_types import unit_kinds
from sasdata.quantities.units import symbol_lookup

from unit_selector import UnitSelector

class ColumnUnit(QWidget):
    """Widget with 2 combo boxes: one allowing the user to pick a column, and
    another to specify the units for that column."""
    def __init__(self, options) -> None:
        super().__init__()
        self.col_widget = self.createColComboBox(options)
        self.unit_widget = self.createUnitComboBox(self.col_widget.currentText())
        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.col_widget)
        self.layout.addWidget(self.unit_widget)

    column_changed = Signal()

    def createColComboBox(self, options: list[str]) -> QComboBox:
        """Create the combo box for specifying the column based on the given
        options."""
        new_combo_box = QComboBox()
        for option in options:
            new_combo_box.addItem(option)
        new_combo_box.setEditable(True)
        validator = QRegularExpressionValidator(r"[a-zA-Z0-9]+")
        new_combo_box.setValidator(validator)
        new_combo_box.currentTextChanged.connect(self.onOptionChange)
        return new_combo_box

    def createUnitComboBox(self, selected_option: str) -> QComboBox:
        """Create the combo box for specifying the unit for selected_option"""
        new_combo_box = QComboBox()
        new_combo_box.setEditable(True)
        # word_list = ['alpha', 'omega', 'omicron', 'zeta']
        # completer = QCompleter(word_list, self)
        # new_combo_box.setCompleter(completer)
        self.updateUnits(new_combo_box, selected_option)
        new_combo_box.currentTextChanged.connect(self.onUnitChange)
        return new_combo_box

    def updateUnits(self, unit_box: QComboBox, selected_option: str):
        unit_box.clear()
        options = [unit.symbol for unit in unit_kinds[selected_option].units]
        # We don't have preferred units yet. In order to simulate this, just
        # take the first 5 options to display.
        for option in options[:5]:
            unit_box.addItem(option)
        unit_box.addItem('Select More')


    def replaceOptions(self, new_options) -> None:
        """Replace the old options for the column with new_options"""
        self.col_widget.clear()
        self.col_widget.addItems(new_options)

    def setCurrentColumn(self, new_column_value: str) -> None:
        """Change the current selected column to new_column_value"""
        self.col_widget.setCurrentText(new_column_value)
        self.updateUnits(self.unit_widget, new_column_value)


    @Slot()
    def onOptionChange(self):
        # If the new option is empty string, its probably because the current
        # options have been removed. Can safely ignore this.
        self.column_changed.emit()
        new_option = self.col_widget.currentText()
        if new_option == '':
            return
        try:
            self.updateUnits(self.unit_widget, new_option)
        except KeyError:
            # Means the units for this column aren't known. This shouldn't be
            # the case in the real version so for now we'll just clear the unit
            # widget.
            self.unit_widget.clear()

    @Slot()
    def onUnitChange(self):
        if self.unit_widget.currentText() == 'Select More':
            selector = UnitSelector(unit_kinds[self.col_widget.currentText()].name, False)
            selector.exec()
            self.unit_widget.setCurrentText(selector.selected_unit.symbol)

    @property
    def currentColumn(self):
        """The currently selected column."""
        return self.col_widget.currentText()

    @property
    def currentUnit(self):
        """The currently selected unit."""
        return symbol_lookup[self.unit_widget.currentText()]
