from PySide6.QtWidgets import QApplication, QComboBox, QVBoxLayout, QWidget
from sasdata.quantities.units import length, area, volume, inverse_length, inverse_area, inverse_volume, time, rate, speed, density, force, pressure, energy, power, charge, potential, resistance

# TODO: Ask Lucas if this list can be in his code (or if it already is and I
# can't find it). I am lazy so only doing a subsection for now.

all_unit_groups = [
    length, area, volume, inverse_length, inverse_area, inverse_volume, time, rate, speed, density, force, pressure, energy, power, charge, potential, resistance
]

class UnitSelector(QWidget):
    def __init__(self):
        super().__init__()

        self.unit_type_selector = QComboBox()
        unit_group_names = [group.name for group in all_unit_groups]
        self.unit_type_selector.addItems(unit_group_names)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.unit_type_selector)

if __name__ == "__main__":
    app = QApplication([])

    widget = UnitSelector()
    widget.show()

    exit(app.exec())
