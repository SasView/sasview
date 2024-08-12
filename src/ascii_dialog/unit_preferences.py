#!/usr/bin/env python3

from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget
from sasdata.quantities.units import NamedUnit
from sasdata.dataset_types import unit_kinds
from unit_preference_line import UnitPreferenceLine
import random

class UnitPreferences(QWidget):
    def __init__(self):
        super().__init__()

        # TODO: Presumably this will be loaded from some config from somewhere.
        # For now just fill it with some placeholder values.
        column_names = unit_kinds.keys()
        self.columns: dict[str, NamedUnit] = {}
        for name in column_names:
            self.columns[name] = random.choice(unit_kinds[name].units)

        self.layout = QVBoxLayout()
        for column_name, unit in self.columns.items():
            line = UnitPreferenceLine(column_name, unit, unit_kinds[column_name])
            self.layout.addWidget(line)



if __name__ == "__main__":
    app = QApplication([])

    widget = UnitPreferences()
    widget.show()

    exit(app.exec())
