import logging
from typing import TYPE_CHECKING, cast

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QAbstractItemView, QDialog, QTreeWidget, QTreeWidgetItem, QTreeWidgetItemIterator, QWidget

from sasdata.data import SasData
from sasdata.trend import NamedTrend, Trend

from sas.data_explorer_drop_hint import AddDataRow
from sas.data_explorer_error_message import DataExplorerErrorMessage
from sas.data_explorer_menu import DataExplorerMenu, DataExplorerMenuAction
from sas.data_manager import NewDataManager as DataManager
from sas.data_manager import TrackedData, isinstance_fix
from sas.qtgui.MainWindow.DataViewer import DataViewer
from sas.qtgui.MainWindow.TrendCreation import TrendCreation
from sas.refactored import Perspective, TrackedPlot
from sas.refactored_plotting.ModifierCreator import ModifierCreator
from sas.refactored_plotting.PlotModifiers import PlotModifier

if TYPE_CHECKING:
    from sas.refactored_data_explorer import NewDataExplorer


# TODO: Is this the right place for this?
def tracked_data_name(data: TrackedData) -> str:
    if isinstance(data, SasData):
        return data.name
    elif isinstance(data, NamedTrend):
        return data.name
    elif isinstance(data, Trend):
        # Trends created in the data explorer should be named trends. If they're
        # not, that indicates something has gone wrong. We won't fail here, but
        # instead log a warning.
        logging.warning("Trend doesn't have a name. This shouldn't be happening.")
        return 'Unnamed Trend'
    elif isinstance(data, PlotModifier):
        return data.explorer_item_name
    else:
        return data.formatName


class DataExplorerTree(QTreeWidget):
    current_datum_removed = Signal()
    view_data_activated = Signal()
    load_requested = Signal()

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
        self._addLoadRow()

    @property
    def _data_explorer(self) -> "NewDataExplorer":
        return cast( "NewDataExplorer", self.parent())

    def initTable(self):
        self.clear()
        self.setColumnCount(1)
        self.header().setStretchLastSection(True)
        self._addLoadRow()

    def _addLoadRow(self):
        """Add a last row that offers to load more data, so there's always a way
        to load files from the list itself. New data is inserted above it."""
        self._load_row = QTreeWidgetItem()
        # Not selectable, and skipped by keyboard navigation.
        self._load_row.setFlags(Qt.ItemFlag.NoItemFlags)
        self.addTopLevelItem(self._load_row)
        self.load_hint = AddDataRow()
        self.load_hint.load_requested.connect(self.load_requested)
        # Zero width so the row never forces a horizontal scrollbar.
        self._load_row.setSizeHint(0, QSize(0, self.load_hint.sizeHint().height()))
        self.setItemWidget(self._load_row, 0, self.load_hint)

    def setDropActive(self, active: bool):
        """Highlight the load row while files are being dragged over the explorer."""
        self.load_hint.setActive(active)

    def _dataItems(self, root: QTreeWidgetItem) -> list[QTreeWidgetItem]:
        """The data items directly under root."""
        return [root.child(i) for i in range(root.childCount()) if root.child(i) is not self._load_row]

    def dataItemCount(self) -> int:
        """Number of top level data items (the load row isn't counted)."""
        return len(self._dataItems(self.invisibleRootItem()))

    # These methods are designed to listen to updates coming from the data explorer. They will eventually replace the
    # 'buildTable' function.

    def addAssociation(self, datum1: TrackedData, datum2: TrackedData):
        # TODO: Order of data is assumed which may not be true.
        for item in self._dataItems(self.invisibleRootItem()):
            # FIXME: Repetition
            item_datum = cast(TrackedData, item.data(0, Qt.ItemDataRole.UserRole))
            if item_datum == datum1:
                new_assoc_item = QTreeWidgetItem([tracked_data_name(datum2)])
                new_assoc_item.setData(0, Qt.ItemDataRole.UserRole, datum2)
                item.addChild(new_assoc_item)
                # By breaking here, we are assuming there are no more top level datum1 items in the tree.
                break
        # The new association may have changed some names, so update those.
        self.updateNames()

    def removeAssociation(self, datum1: TrackedData, datum2: TrackedData):
        # TODO: Again, order.
        self.removeFromTable(datum2, root_datum=datum1)

    def addToTable(self, datum: TrackedData):
        item = QTreeWidgetItem([tracked_data_name(datum)])
        item.setData(0, Qt.ItemDataRole.UserRole, datum)
        self.insertTopLevelItem(self.indexOfTopLevelItem(self._load_row), item)

    def updateNames(self):
        iter = QTreeWidgetItemIterator(self)
        while item := iter.value():
            data = item.data(0, Qt.ItemDataRole.UserRole)
            item.setText(0, tracked_data_name(data))
            iter += 1

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
        for item in self._dataItems(root):
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
        send_to = all([isinstance(datum, SasData) or isinstance(datum, Trend) for datum in self.currentTrackedData])
        view_data = len(self.currentTrackedData) == 1 and isinstance(self.currentTrackedData[0], SasData)
        make_trend = len(self.currentTrackedData) > 1 and all([isinstance_fix(datum, SasData) for datum in self.currentTrackedData])
        plot = len(self.currentTrackedData) == 1 and isinstance_fix(self.currentTrackedDatum, SasData)
        create_modifier = len(self.currentTrackedData) == 1 and isinstance(self.currentTrackedDatum, TrackedPlot)
        menu = DataExplorerMenu(self, self._data_manager, send_to, view_data, make_trend, plot, create_modifier)
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
            case "make_trend":
                trend_data = cast(list[SasData], self.currentTrackedData)
                trend_creation_dialog = TrendCreation(trend_data, self._data_manager.default_new_trend_name)
                creation_result = trend_creation_dialog.exec()
                if creation_result == QDialog.DialogCode.Accepted:
                    self._data_manager.register_trend(trend_creation_dialog.proposed_trend)
            case "plot":
                self._data_explorer.onPlot()
            case "create_modifier":
                dialog = ModifierCreator()
                modifier_result = dialog.exec()
                if modifier_result == QDialog.DialogCode.Accepted:
                    modifier = dialog.proposed_modifier
                    self._data_manager.add_data(modifier)
                    plot = cast(TrackedPlot, self.currentTrackedDatum)
                    self._data_manager.make_association(plot, modifier)
                    plot.update_plot()
        if len(errors):
            box = DataExplorerErrorMessage(self, errors)
            box.show()

    def showViewData(self):
        associated = self._data_manager.get_association_or_none(self.currentTrackedDatum)
        if isinstance(associated, Trend):
            trend = associated
        else:
            trend = None
        viewer = DataViewer(self.currentTrackedDatum, trend)
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
        return [
            item.data(0, Qt.ItemDataRole.UserRole)
            for item in self.selectedItems()
            if item is not self._load_row
        ]

    # Annoyingly, there is no way to get all the items in a tree. So we have to
    # do this recursively instead.
    def setCurrentTrackedDatum(
        self, datum: TrackedData, root: QTreeWidgetItem | None = None
    ):
        if root is None:
            root = self.invisibleRootItem()
        for item in self._dataItems(root):
            item_datum = cast(TrackedData, item.data(0, Qt.ItemDataRole.UserRole))
            if item_datum == datum:
                self.setCurrentItem(item)
                return
            self.setCurrentTrackedDatum(datum, item)
