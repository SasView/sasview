from PySide6.QtWidgets import QTreeWidget, QWidget
from sas.data_manager import NewDataManager as DataManager


class DataExplorerTree(QTreeWidget):
    def __init__(self, data_manager: DataManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data_manager = data_manager
