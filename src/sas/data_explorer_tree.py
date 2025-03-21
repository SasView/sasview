from cgitb import reset
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

    def initTable(self):
        self.clear()
        self.setColumnCount(1)
        self.header().setStretchLastSection(True)

    # These methods are designed to listen to updates coming from the data explorer. They will eventually replace the
    # 'buildTable' function.

    def addAssociation(self, datum1: TrackedData, datum2: TrackedData):
        pass

    def removeAssociation(self, datum1: TrackedData, datum2: TrackedData):
        pass

    def addToTable(self, datum: TrackedData):
        item = QTreeWidgetItem([tracked_data_name(datum)])
        item.setData(0, Qt.ItemDataRole.UserRole, datum)
        self.addTopLevelItem(item)

    def removeFromTable(self, datum: TrackedData, starting_root: QTreeWidgetItem | None):
        root = self.invisibleRootItem() if starting_root is None else starting_root
        # TODO: This assumes that, if the root item is to be deleted, all of its children have already been deleted.
        # This may be the right assumption to make but I need to verify this.
        for i in range(root.childCount()):
            item = root.child(i)
            item_datum = cast(TrackedData, item.data(0, Qt.ItemDataRole.UserRole))
            if item_datum == datum:
                root.removeChild(item)
            elif item.childCount() != 0:
                self.removeFromTable(datum, starting_root)

    def buildTable(self):
        self.clear()
        self.setColumnCount(1)
        self.header().setStretchLastSection(True)
        for datum in self._data_manager.all_data:
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
        send_to = all([isinstance(datum, SasData) for datum in self.currentTrackedData])
        menu = DataExplorerMenu(self, self._data_manager, send_to)
        action = menu.exec(QCursor.pos())
        # Result will be None if the user exited the menu without selecting anything.
        if action is None:
            return
        result: DataExplorerMenuAction = action.data()
        errors: list[ValueError] = []
        match result.action:
            case 'remove':
                # TODO: Work for all data.
                self.current_datum_removed.emit()
            case 'send_to':
                # TODO: This cast might not be necessary.
                to_perspective = cast(Perspective, result.action_data)
                # TODO: I'm a bit worried about potential repetition if there are more actions here. Will need to
                # watch this.
                for datum in self.currentTrackedData:
                    try:
                        self._data_manager.make_association(to_perspective, datum)
                    except ValueError as err:
                        errors.append(err)
        if len(errors):
            box = DataExplorerErrorMessage(self, errors)
            box.show()

    @property
    def currentTrackedDatum(self) -> TrackedData | None:
        if len(self.currentTrackedData) == 0:
            return None
        return self.currentTrackedData[0]

    @property
    def currentTrackedData(self) -> list[TrackedData]:
        # items = self.selectedItems()
        # for item in items:
        #     item.index
        return [item.data(0, Qt.ItemDataRole.UserRole) for item in self.selectedItems()]

    # Annoyingly, there is no way to get all the items in a tree. So we have to
    # do this recursively instead.
    def setCurrentTrackedDatum(self, datum: TrackedData, root: QTreeWidgetItem | None = None):
        if root is None:
            root = self.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            item_datum = cast(TrackedData, item.data(0, Qt.ItemDataRole.UserRole))
            if item_datum == datum:
                self.setCurrentItem(item)
                return
            self.setCurrentTrackedDatum(datum, item)
