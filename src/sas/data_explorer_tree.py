from typing_extensions import cast
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QTreeWidget,
    QTreeWidgetItem,
    QWidget,
)
from sasdata.data import SasData
from sas.data_manager import NewDataManager as DataManager, TrackedData
from sas.refactored import Perspective
from src.sas.data_explorer_error_message import DataExplorerErrorMessage
from src.sas.data_explorer_menu import DataExplorerMenu, DataExplorerMenuAction
from sas.qtgui.MainWindow.DataViewer import DataViewer


# TODO: Is this the right place for this?
def tracked_data_name(data: TrackedData) -> str:
    if isinstance(data, SasData):
        return data.name
    else:
        return data.formatName


class DataExplorerTree(QTreeWidget):
    current_datum_removed = Signal()
    view_data_activated = Signal()

    def __init__(
        self, data_manager: DataManager, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._data_manager = data_manager
        _ = self._data_manager.new_data.connect(self.addToTable)
        _ = self._data_manager.data_removed.connect(self.removeFromTable)
        _ = self.view_data_activated.connect(self.showViewData)

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
        # TODO: Order of data is assumed which may not be true.
        root = self.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            # FIXME: Repetition
            item_datum = cast(TrackedData, item.data(0, Qt.ItemDataRole.UserRole))
            if item_datum == datum1:
                new_assoc_item = QTreeWidgetItem([tracked_data_name(datum2)])
                new_assoc_item.setData(0, Qt.ItemDataRole.UserRole, datum2)
                item.addChild(new_assoc_item)
                # By breaking here, we are assuming there are no more top level datum1 items in the tree.
                break

    def removeAssociation(self, datum1: TrackedData, datum2: TrackedData):
        # TODO: Again, order.
        self.removeFromTable(datum2, root_datum=datum1)

    def addToTable(self, datum: TrackedData):
        item = QTreeWidgetItem([tracked_data_name(datum)])
        item.setData(0, Qt.ItemDataRole.UserRole, datum)
        self.addTopLevelItem(item)

    def removeFromTable(
        self,
        datum: TrackedData,
        starting_root: QTreeWidgetItem | None = None,
        root_datum: TrackedData | None = None,
    ):
        """The root_datum param is needed when you want to delete something from the tree that has a certain root item.
        This is mostly useful for getting rid of associations."""
        root = self.invisibleRootItem() if starting_root is None else starting_root
        # TODO: This assumes that, if the root item is to be deleted, all of its children have already been deleted.
        # This may be the right assumption to make but I need to verify this.
        to_remove: list[QTreeWidgetItem] = []
        for i in range(root.childCount()):
            item = root.child(i)
            item_datum = cast(TrackedData, item.data(0, Qt.ItemDataRole.UserRole))
            if item_datum == datum and (
                root_datum is not None
                or root_datum == root.data(0, Qt.ItemDataRole.UserRole)
            ):
                # Need to defer this to later so we don't delete data while we're doing a for loop over it.
                to_remove.append(item)
            elif item.childCount() != 0:
                self.removeFromTable(datum, item)
        for item in to_remove:
            root.removeChild(item)

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
            case "remove":
                # TODO: Work for all data.
                self.current_datum_removed.emit()
            case "view_data":
                self.view_data_activated.emit()
            case "send_to":
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

    def showViewData(self):
        viewer = DataViewer(self.currentTrackedDatum)
        viewer.exec()

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
    def setCurrentTrackedDatum(
        self, datum: TrackedData, root: QTreeWidgetItem | None = None
    ):
        if root is None:
            root = self.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            item_datum = cast(TrackedData, item.data(0, Qt.ItemDataRole.UserRole))
            if item_datum == datum:
                self.setCurrentItem(item)
                return
            self.setCurrentTrackedDatum(datum, item)
