from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget
from sasdata.data import SasData
from sas.data_manager import NewDataManager as DataManager, TrackedData
from sas.refactored import Perspective


class DataExplorerTree(QTreeWidget):
    def __init__(self, data_manager: DataManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data_manager = data_manager
        _ = self._data_manager.new_data.connect(self.buildTable)
        _ = self._data_manager.data_removed.connect(self.buildTable)

        # The idea of this list is so we can keep track of the index of each. Which is useful if we want to delete it
        # from the data manager, or create associations.
        self.table_values: list[TrackedData]  = []

    def buildTable(self):
        # TODO: Right now we are ignoring associations.
        self.clear()
        self.table_values = []
        self.setColumnCount(1)
        self.header().setStretchLastSection(True)
        for datum in self._data_manager.all_data:
            if isinstance(datum, SasData):
                name = datum.name
            else: # If perspective
                name = f"{datum.title} #{datum.perspective_number}"
            self.table_values.append(datum)
            item = QTreeWidgetItem([name])
            self.addTopLevelItem(item)

    @property
    def currentTrackedDatum(self) -> TrackedData:
        index = self.currentIndex().row()
        return self.table_values[index]

    def setCurrentTrackedDatum(self, datum: TrackedData):
        datum_index = self.table_values.index(datum)
        datum_item = self.topLevelItem(datum_index)
        self.setCurrentItem(datum_item)
