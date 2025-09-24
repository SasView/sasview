#!/usr/bin/env python3

from PySide6.QtWidgets import QListWidget, QListWidgetItem

from sasdata.quantities.units import NamedUnit


class UnitListWidget(QListWidget):
    def reprUnit(self, unit: NamedUnit) -> str:
        return f"{unit.symbol} ({unit.name})"

    def populateList(self, units: list[NamedUnit]) -> None:
        self.clear()
        self.units = units
        for unit in units:
            item = QListWidgetItem(self.reprUnit(unit))
            self.addItem(item)

    @property
    def selectedUnit(self) -> NamedUnit | None:
        return self.units[self.currentRow()]

    def __init__(self):
        super().__init__()
        self.units: list[NamedUnit] = []
