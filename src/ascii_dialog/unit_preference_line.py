#!/usr/bin/env python3

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget
from sasdata.quantities.units import NamedUnit, UnitGroup

from ascii_dialog.unit_selector import UnitSelector

class UnitPreferenceLine(QWidget):
    def __init__(self, column_name: str, initial_unit: NamedUnit, group: UnitGroup):
        super().__init__()

        self.group = group
        self.current_unit = initial_unit

        self.column_label = QLabel(column_name)
        self.unit_button = QPushButton(initial_unit.symbol)
        self.unit_button.clicked.connect(self.onUnitPress)

        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.column_label)
        self.layout.addWidget(self.unit_button)

    @Slot()
    def onUnitPress(self):
        picker = UnitSelector(self.group.name, False)
        picker.exec()
        self.current_unit = picker.selected_unit
        self.unit_button.setText(self.current_unit.symbol)
