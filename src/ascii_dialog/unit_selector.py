from PySide6.QtWidgets import QApplication, QComboBox, QListWidget, QVBoxLayout, QWidget
from sasdata.quantities.units import UnitGroup, length, area, volume, inverse_length, inverse_area, inverse_volume, time, rate, speed, density, force, pressure, energy, power, charge, potential, resistance

from unit_list_widget import UnitListWidget

# TODO: Ask Lucas if this list can be in his code (or if it already is and I
# can't find it). I am lazy so only doing a subsection for now.

all_unit_groups = [
    length, area, volume, inverse_length, inverse_area, inverse_volume, time, rate, speed, density, force, pressure, energy, power, charge, potential, resistance
]

class UnitSelector(QWidget):
    def current_unit_group(self) -> UnitGroup:
        index = self.unit_type_selector.currentIndex()
        return all_unit_groups[index]

    def __init__(self):
        super().__init__()

        self.unit_type_selector = QComboBox()
        unit_group_names = [group.name for group in all_unit_groups]
        self.unit_type_selector.addItems(unit_group_names)

        self.unit_list_widget = UnitListWidget()
        # TODO: Are they all named units?
        self.unit_list_widget.populate_list(self.current_unit_group().units)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.unit_type_selector)
        self.layout.addWidget(self.unit_list_widget)

if __name__ == "__main__":
    app = QApplication([])

    widget = UnitSelector()
    widget.show()

    exit(app.exec())
