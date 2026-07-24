#!/usr/bin/env python3

import random

from PySide6.QtGui import Qt
from PySide6.QtWidgets import QApplication, QScrollArea, QVBoxLayout, QWidget

from sasdata.dataset_types import unit_kinds
from sasdata.quantities.units import NamedUnit

from ascii_dialog.unit_preference_line import UnitPreferenceLine


class UnitPreferences(QWidget):
    def __init__(self):
        super().__init__()

        # TODO: Presumably this will be loaded from some config from somewhere.
        # For now just fill it with some placeholder values.
        column_names = unit_kinds.keys()
        self.columns: dict[str, NamedUnit] = {}
        for name in column_names:
            self.columns[name] = random.choice(unit_kinds[name].units)

        self.layout = QVBoxLayout(self)
        preference_lines = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_layout = QVBoxLayout(preference_lines)
        for column_name, unit in self.columns.items():
            line = UnitPreferenceLine(column_name, unit, unit_kinds[column_name])
            scroll_layout.addWidget(line)

        scroll_area.setWidget(preference_lines)
        self.layout.addWidget(scroll_area)


if __name__ == "__main__":
    app = QApplication([])

    widget = UnitPreferences()
    widget.show()

    exit(app.exec())
