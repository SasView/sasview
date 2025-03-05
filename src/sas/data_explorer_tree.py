from cgitb import reset
import logging
from typing_extensions import cast
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QAbstractItemView, QMessageBox, QTreeWidget, QTreeWidgetItem, QWidget
from sasdata.data import SasData
from sas.data_manager import NewDataManager as DataManager, TrackedData
from sas.refactored import Perspective
from src.sas.data_explorer_error_message import DataExplorerErrorMessage
from src.sas.data_explorer_menu import DataExplorerMenu, DataExplorerMenuAction

# TODO: Is this the right place for this?
def tracked_data_name(data: TrackedData) -> str:
    if isinstance(data, SasData):
        return data.name
    else:
        return data.formatName

class DataExplorerTree(QTreeWidget):
    current_datum_removed = Signal()

    def __init__(self, data_manager: DataManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data_manager = data_manager
        _ = self._data_manager.new_data.connect(self.buildTable)
        _ = self._data_manager.data_removed.connect(self.buildTable)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        _ = self.customContextMenuRequested.connect(self.showContextMenu)
        self.headerItem().setHidden(True)

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
            self.table_values.append(datum)
            item = QTreeWidgetItem([tracked_data_name(datum)])
            item.setData(0, Qt.ItemDataRole.UserRole, datum)
            # TODO: Dodgy placeholder test for Perspective.
            if hasattr(datum, 'title'):
                for assoc_datum in datum.associatedData:
                    assoc_item = QTreeWidgetItem([tracked_data_name(assoc_datum)])
                    assoc_item.setData(0, Qt.ItemDataRole.UserRole, assoc_datum)
                    item.addChild(assoc_item)
            self.addTopLevelItem(item)

    def showContextMenu(self):
        send_to = isinstance(self.currentTrackedDatum, SasData)
        menu = DataExplorerMenu(self, self._data_manager, send_to)
        action = menu.exec(QCursor.pos())
        # Result will be None if the user exited the menu without selecting anything.
        if action is None:
            return
        result: DataExplorerMenuAction = action.data()
        try:
            match result.action:
                case 'remove':
                    self.current_datum_removed.emit()
                case 'send_to':
                    # TODO: This cast might not be necessary.
                    to_perspective = cast(Perspective, result.action_data)
                    self._data_manager.make_association(to_perspective, self.currentTrackedDatum)
        except ValueError as err:
            box = DataExplorerErrorMessage(self, err)
            box.show()

    @property
    def currentTrackedDatum(self) -> TrackedData:
        index = self.currentIndex().row()
        return self.table_values[index]

    @property
    def currentTrackedData(self) -> list[TrackedData]:
        # items = self.selectedItems()
        # for item in items:
        #     item.index
        return [item.data(0, Qt.ItemDataRole.UserRole) for item in self.selectedItems()]

    def setCurrentTrackedDatum(self, datum: TrackedData):
        datum_index = self.table_values.index(datum)
        datum_item = self.topLevelItem(datum_index)
        self.setCurrentItem(datum_item)
