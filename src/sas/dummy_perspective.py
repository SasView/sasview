from typing import override
from PySide6.QtWidgets import QDialog, QVBoxLayout, QWidget
from qtpy.QtWidgets import QLabel
from sas.refactored import Perspective
from sas.data_manager import NewDataManager as DataManager

class DummyPerspective(Perspective):
    def __init__(self, data_manager: DataManager, parent: QWidget | None = None) -> None:
        super().__init__(data_manager, parent)

        self.current_data_label = QLabel('Placeholder Title Label')

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.current_data_label)

    @property
    @override
    def title(self) -> str:
        return "Dummy"

    @property
    @override
    def title(self) -> str:
        return "Dummy Perspective"
