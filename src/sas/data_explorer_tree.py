from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget
from sasdata.data import SasData
from sas.data_manager import NewDataManager as DataManager
from sas.refactored import Perspective


class DataExplorerTree(QTreeWidget):
    def __init__(self, data_manager: DataManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data_manager = data_manager
        _ = self._data_manager.new_data.connect(self.buildTable)

    def buildTable(self):
        # TODO: Right now we are ignoring associations.
        self.clear()
        self.setColumnCount(1)
        self.header().setStretchLastSection(True)
        for datum in  self._data_manager.all_data:
            if isinstance(datum, SasData):
                name = datum.name
            else: # If perspective
                name = datum.title
            item = QTreeWidgetItem([name])
            self.addTopLevelItem(item)
