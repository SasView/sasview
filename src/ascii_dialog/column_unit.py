#!/usr/bin/env python3

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QComboBox, QCompleter, QHBoxLayout, QSizePolicy, QWidget
from PySide6.QtGui import QRegularExpressionValidator
from sasdata.dataset_types import unit_kinds
from sasdata.quantities.units import symbol_lookup, NamedUnit

from unit_selector import UnitSelector
from default_units import default_units

def configure_size_policy(combo_box: QComboBox) -> None:
    policy = combo_box.sizePolicy()
    policy.setHorizontalPolicy(QSizePolicy.Policy.Ignored)
    combo_box.setSizePolicy(policy)

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
        self.current_option: str

    column_changed = Signal()

    def createColComboBox(self, options: list[str]) -> QComboBox:
        """Create the combo box for specifying the column based on the given
        options."""
        new_combo_box = QComboBox()
        configure_size_policy(new_combo_box)
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
        configure_size_policy(new_combo_box)
        new_combo_box.setEditable(True)
        self.updateUnits(new_combo_box, selected_option)
        new_combo_box.currentTextChanged.connect(self.onUnitChange)
        return new_combo_box

    def updateUnits(self, unit_box: QComboBox, selected_option: str):
        unit_box.clear()
        self.current_option = selected_option
        # Use the list of preferred units but fallback to the first 5 if there aren't any for this particular column.
        unit_options = default_units.get(self.current_option, unit_kinds[selected_option].units)
        option_symbols = [unit.symbol for unit in unit_options]
        for option in option_symbols[:5]:
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
            # We need the selection unit in the list of options, or else QT has some dodgy behaviour.
            self.unit_widget.insertItem(-1, selector.selected_unit.symbol)
            self.unit_widget.setCurrentText(selector.selected_unit.symbol)
        self.column_changed.emit()

    @property
    def currentColumn(self):
        """The currently selected column."""
        return self.col_widget.currentText()

    @property
    def currentUnit(self) -> NamedUnit:
        """The currently selected unit."""
        current_unit_symbol = self.unit_widget.currentText()
        for unit in unit_kinds[self.current_option].units:
            if current_unit_symbol == unit.symbol:
                return unit
        # This error shouldn't really happen so if it does, it indicates there is a bug in the code.
        raise ValueError("Current unit doesn't seem to exist")

    @currentUnit.setter
    def currentUnit(self, new_value: NamedUnit):
        self.unit_widget.setCurrentText(new_value.symbol)
