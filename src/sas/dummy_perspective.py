from typing import override
from PySide6.QtWidgets import QDialog, QListWidget, QVBoxLayout, QWidget
from qtpy.QtWidgets import QLabel
from sas.refactored import Perspective
from sas.data_manager import NewDataManager as DataManager

class DummyPerspective(Perspective):
    def __init__(self, data_manager: DataManager, parent: QWidget | None = None) -> None:
        super().__init__(data_manager, parent)

        self.data_list_label = QLabel('Current Loaded Data')
        self.data_list = QListWidget()

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.data_list_label)
        self.layout.addWidget(self.data_list)

    @property
    @override
    def title(self) -> str:
        return "Dummy Perspective"

    @override
    def newAssocation(self):
        self.data_list.clear()
        for datum in self.associatedData:
            self.data_list.addItem(datum.name)
