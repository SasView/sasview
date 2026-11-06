from typing import cast, override

from PySide6.QtWidgets import QListWidget, QVBoxLayout, QWidget
from qtpy.QtWidgets import QLabel

from sasdata.data import SasData

from sas.data_manager import NewDataManager as DataManager
from sas.data_manager import TrackedData
from sas.refactored import DataFormat, DataHandler, Perspective


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

    @property
    @override
    def accepted_data(self) -> list[tuple[DataFormat, DataHandler]]:
        return [(SasData, self.onSasData)]

    @property
    @override
    def supports_multiple_data(self) -> bool:
        return True

    def onSasData(self, datum: TrackedData):
        self.data_list.addItem(cast(SasData, datum).name)
