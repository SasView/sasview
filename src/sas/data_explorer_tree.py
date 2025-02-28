from cgitb import reset
import logging
from typing_extensions import cast
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget
from sasdata.data import SasData
from sas.data_manager import NewDataManager as DataManager, TrackedData
from sas.refactored import Perspective
from src.sas.data_explorer_menu import DataExplorerMenu, DataExplorerMenuAction

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
                name = datum.formatName
            self.table_values.append(datum)
            item = QTreeWidgetItem([name])
            self.addTopLevelItem(item)

    def showContextMenu(self):
        send_to = isinstance(self.currentTrackedDatum, SasData)
        menu = DataExplorerMenu(self, self._data_manager, send_to)
        action = menu.exec(QCursor.pos())
        # Result will be None if the user exited the menu without selecting anything.
        if action is None:
            return
        result: DataExplorerMenuAction = action.data()
        match result.action:
            case 'remove':
                self.current_datum_removed.emit()
            case 'send_to':
                # TODO: This cast might not be necessary.
                to_perspective = cast(Perspective, result.action_data)
                self._data_manager.make_association(self.currentTrackedDatum, to_perspective)

    @property
    def currentTrackedDatum(self) -> TrackedData:
        index = self.currentIndex().row()
        return self.table_values[index]

    def setCurrentTrackedDatum(self, datum: TrackedData):
        datum_index = self.table_values.index(datum)
        datum_item = self.topLevelItem(datum_index)
        self.setCurrentItem(datum_item)
