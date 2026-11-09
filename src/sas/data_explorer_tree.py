import logging
from typing import TYPE_CHECKING, cast

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QAbstractItemView, QDialog, QTreeWidget, QTreeWidgetItem, QTreeWidgetItemIterator, QWidget

from sasdata.data import SasData
from sasdata.trend import NamedTrend, Trend

from sas.data_explorer_error_message import DataExplorerErrorMessage
from sas.data_explorer_menu import DataExplorerMenu, DataExplorerMenuAction
from sas.data_manager import NewDataManager as DataManager
from sas.data_manager import TrackedData
from sas.qtgui.MainWindow.DataViewer import DataViewer
from sas.qtgui.MainWindow.TrendCreation import TrendCreation
from sas.refactored import Perspective
from sas.refactored_plotting.ModifierCreator import ModifierCreator
from sas.refactored_plotting.PlotModifiers import PlotModifier
from sas.tracked_objects import TrackedPlot

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

    def __init__(
        self, data_manager: DataManager, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._data_manager = data_manager
        self._data_manager.data_added.connect(self.addToTable)
        self._data_manager.data_removed.connect(self.removeFromTable)
        self._data_manager.reference_added.connect(self.addReference)
        self._data_manager.reference_removed.connect(self.removeReference)
        _ = self.view_data_activated.connect(self.showViewData)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        _ = self.customContextMenuRequested.connect(self.showContextMenu)
        self.headerItem().setHidden(True)

    @property
    def _data_explorer(self) -> "NewDataExplorer":
        return cast( "NewDataExplorer", self.parent())

    def initTable(self):
        self.clear()
        self.setColumnCount(1)
        self.header().setStretchLastSection(True)

    # These methods listen to the data manager's hooks, keeping the tree in sync with it. Each top-level item is a
    # top-level item of the data manager, with the objects it references as its children.

    def _makeItem(self, datum: TrackedData) -> QTreeWidgetItem:
        """An item for datum, with items for everything it references below it."""
        item = QTreeWidgetItem([tracked_data_name(datum)])
        item.setData(0, Qt.ItemDataRole.UserRole, datum)
        for target in self._data_manager.references_of(datum):
            item.addChild(self._makeItem(target))
        return item

    def _itemsOf(self, datum: TrackedData) -> list[QTreeWidgetItem]:
        """All the items showing datum, wherever they are in the tree."""
        items: list[QTreeWidgetItem] = []
        iterator = QTreeWidgetItemIterator(self)
        while (item := iterator.value()) is not None:
            if item.data(0, Qt.ItemDataRole.UserRole) is datum:
                items.append(item)
            iterator += 1
        return items

    def addToTable(self, datum: TrackedData):
        self.addTopLevelItem(self._makeItem(datum))

    def removeFromTable(self, datum: TrackedData):
        root = self.invisibleRootItem()
        for item in self._itemsOf(datum):
            if item.parent() is None:
                root.removeChild(item)

    def addReference(self, holder: TrackedData, target: TrackedData):
        for item in self._itemsOf(holder):
            item.addChild(self._makeItem(target))
        # The new reference may have changed some names, so update those.
        self.updateNames()

    def removeReference(self, holder: TrackedData, target: TrackedData):
        for item in self._itemsOf(holder):
            for i in range(item.childCount()):
                if item.child(i).data(0, Qt.ItemDataRole.UserRole) is target:
                    item.removeChild(item.child(i))
                    break
        self.updateNames()

    def updateNames(self):
        iterator = QTreeWidgetItemIterator(self)
        while (item := iterator.value()) is not None:
            data = item.data(0, Qt.ItemDataRole.UserRole)
            item.setText(0, tracked_data_name(data))
            iterator += 1

    def showContextMenu(self):
        send_to = all([isinstance(datum, SasData) or isinstance(datum, Trend) for datum in self.currentTrackedData])
        view_data = len(self.currentTrackedData) == 1 and isinstance(self.currentTrackedData[0], SasData)
        make_trend = len(self.currentTrackedData) > 1 and all([isinstance(datum, SasData) for datum in self.currentTrackedData])
        plot = len(self.currentTrackedData) == 1 and isinstance(self.currentTrackedDatum, SasData)
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
                        to_perspective.acceptData(datum)
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
                    plot.modifiers.append(self._data_manager.reference(plot, modifier))
                    self._data_manager.notify_changed(plot)
        if len(errors):
            box = DataExplorerErrorMessage(self, errors)
            box.show()

    def showViewData(self):
        trends = self._data_manager.dependents_of(self.currentTrackedDatum, Trend)
        trend = trends[0] if trends else None
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
