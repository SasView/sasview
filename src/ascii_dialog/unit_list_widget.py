#!/usr/bin/env python3

from PySide6.QtWidgets import QListWidget, QListWidgetItem
from sasdata.quantities.units import NamedUnit


class UnitListWidget(QListWidget):
    def repr_unit(self, unit: NamedUnit) -> str:
        return f"{unit.symbol} ({unit.name})"

    def populate_list(self, units: list[NamedUnit]) -> None:
        self.clear()
        for unit in units:
            item = QListWidgetItem(self.repr_unit(unit))
            self.addItem(item)

    def __init__(self):
        super().__init__()
