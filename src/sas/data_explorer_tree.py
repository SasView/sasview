from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget
from sasdata.data import SasData
from sas.data_manager import NewDataManager as DataManager, TrackedData
from sas.refactored import Perspective
from src.sas.data_explorer_menu import DataExplorerMenu

class DataExplorerTree(QTreeWidget):
    current_datum_removed = Signal()

    def __init__(self, data_manager: DataManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data_manager = data_manager
        _ = self._data_manager.new_data.connect(self.buildTable)
        _ = self._data_manager.data_removed.connect(self.buildTable)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        _ = self.customContextMenuRequested.connect(self.showContextMenu)

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

    def showContextMenu(self):
        menu = DataExplorerMenu(self)
        result = menu.exec(QCursor.pos())
        if result is None:
            return
        match result.text():
            case "Remove":
                self.current_datum_removed.emit()
            case _:
                pass

    @property
    def currentTrackedDatum(self) -> TrackedData:
        index = self.currentIndex().row()
        return self.table_values[index]

    def setCurrentTrackedDatum(self, datum: TrackedData):
        datum_index = self.table_values.index(datum)
        datum_item = self.topLevelItem(datum_index)
        self.setCurrentItem(datum_item)
