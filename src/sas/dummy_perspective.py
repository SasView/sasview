from typing import override
from PySide6.QtWidgets import QDialog, QListView, QVBoxLayout, QWidget
from qtpy.QtWidgets import QLabel
from sas.refactored import Perspective
from sas.data_manager import NewDataManager as DataManager

class DummyPerspective(Perspective):
    def __init__(self, data_manager: DataManager, parent: QWidget | None = None) -> None:
        super().__init__(data_manager, parent)

        self.data_list_label = QLabel('Current Loaded Data')
        self.data_list = QListView()

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.data_list_label)
        self.layout.addWidget(self.data_list)

    @property
    @override
    def title(self) -> str:
        return "Dummy Perspective"
