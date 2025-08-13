from PySide6.QtCore import Slot
from PySide6.QtWidgets import QApplication, QComboBox, QDialog, QLineEdit, QPushButton, QVBoxLayout

from sasdata.quantities.units import NamedUnit, UnitGroup, unit_group_names, unit_groups

from ascii_dialog.unit_list_widget import UnitListWidget

all_unit_groups = list(unit_groups.values())

class UnitSelector(QDialog):
    def currentUnitGroup(self) -> UnitGroup:
        index = self.unit_type_selector.currentIndex()
        return all_unit_groups[index]

    @property
    def selected_unit(self) -> NamedUnit | None:
        return self.unit_list_widget.selectedUnit

    @Slot()
    def onSearchChanged(self):
        search_input = self.search_box.text()
        current_group = self.currentUnitGroup()
        units = current_group.units
        if search_input != '':
            units = [unit for unit in units if search_input.lower() in unit.name]
        self.unit_list_widget.populateList(units)


    @Slot()
    def unitGroupChanged(self):
        new_group = self.currentUnitGroup()
        self.search_box.setText('')
        self.unit_list_widget.populateList(new_group.units)

    @Slot()
    def selectUnit(self):
        self.accept()

    @Slot()
    def selectionChanged(self):
        self.select_button.setDisabled(False)

    def __init__(self, default_group='length', allow_group_edit=True):
        super().__init__()

        self.unit_type_selector = QComboBox()
        self.unit_type_selector.addItems(unit_group_names)
        self.unit_type_selector.setCurrentText(default_group)
        if not allow_group_edit:
            self.unit_type_selector.setDisabled(True)
        self.unit_type_selector.currentTextChanged.connect(self.unitGroupChanged)

        self.search_box = QLineEdit()
        self.search_box.textChanged.connect(self.onSearchChanged)
        self.search_box.setPlaceholderText('Search for a unit...')

        self.unit_list_widget = UnitListWidget()
        # TODO: Are they all named units?
        self.unit_list_widget.populateList(self.currentUnitGroup().units)
        self.unit_list_widget.itemSelectionChanged.connect(self.selectionChanged)
        self.unit_list_widget.itemDoubleClicked.connect(self.selectUnit)

        self.select_button = QPushButton('Select Unit')
        self.select_button.pressed.connect(self.selectUnit)
        self.select_button.setDisabled(True)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.unit_type_selector)
        self.layout.addWidget(self.search_box)
        self.layout.addWidget(self.unit_list_widget)
        self.layout.addWidget(self.select_button)

if __name__ == "__main__":
    app = QApplication([])

    widget = UnitSelector()
    widget.exec()
    print(widget.selected_unit)

    exit()
