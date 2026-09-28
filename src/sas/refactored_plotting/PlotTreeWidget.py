import ctypes

from PlotModifiers import PlotModifier
from PlotTreeItems import PlotItem, PlottableItem
from PySide6.QtCore import QByteArray, QMimeData, QRect, Signal
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import QTreeWidget


class PlotTreeWidget(QTreeWidget):
    dropSignal = Signal(int, int)
    def __init__(self, DataViewer):
        super().__init__(parent=DataViewer)
        self.setGeometry(QRect(10, 332, 391, 312))
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setColumnCount(1)
        self.setHeaderLabels(["Plot Names"])

    def startDrag(self, supportedActions):
        """
        Function for starting the drag of modifiers across the PlotTreeWidget.
        """
        item = self.currentItem()

        if item:
            if isinstance(item, PlotModifier):
                drag = QDrag(self)
                mimeData = QMimeData()
                mimeData.setData('Modifier', QByteArray(str(id(item))))

                drag.setMimeData(mimeData)
                drag.exec(supportedActions)

    def dragEnterEvent(self, event):
        event.acceptProposedAction()


    def dragMoveEvent(self, event):
        """
        Function for checking if a drop should be accepted or not. DataItems from the DataTreeWidget are allowed and
        the drop is accepted, if they are dropped onto a plot item.
        Drops of modifiers are allowed if the modifier is dragged onto a PlotItem or a PlottableItem
        TODO: This needs some change, since 1d modifiers should only be droppable onto Plottables and 2d only on Plots.
        """
        targetItem = self.itemAt(event.position().toPoint())
        if targetItem is not None:
            if event.mimeData().hasFormat('ID'):
                if isinstance(targetItem, PlotItem):
                    event.acceptProposedAction()
                else:
                    event.ignore()
            elif event.mimeData().hasFormat('Modifier'):
                if isinstance(targetItem, PlotItem):
                    event.acceptProposedAction()
                elif isinstance(targetItem, PlottableItem):
                    event.acceptProposedAction()
                else:
                    event.ignore()
            else:
                event.ignore()
        else:
            event.ignore()

    def dropEvent(self, event):
        """
        Processing of the drop of either a modifier from this widget or a data item from the DataTreeWidget.
        """

        # Check, if the drag item contains "ID", then we can be sure that this comes from the DataTreeWidget
        # (this might not be best practice, but with the serialization of the pointer as it is now, is seemed to me
        # like it was the easiest method to achieve this)
        if event.mimeData().data('ID'):

            # Re-collect the data from these streams in the drop
            data_id = event.mimeData().data('ID').data()
            data_type = event.mimeData().data('Type').data()

            # get the targetItem from the drop position
            targetItem = self.itemAt(event.position().toPoint())

            # if the target is a PlotItem, we deserialize the address of the pointer and create a new item from the
            # object that is behind the pointer.
            if isinstance(targetItem.data(0, 1), PlotItem):
                new_plottable = PlottableItem(targetItem, [str(data_id.decode('utf-8'))],
                                              int(data_id), int(data_type))

                # get the fitpage index and the subtab index of the targetItem, so that they can be activated upon redrawing
                redraw_fitpage_index = targetItem.data(0, 1).fitpage_index
                redraw_subtab_index = targetItem.data(0, 1).subtab_index

            elif isinstance(targetItem.data(0, 1), PlottableItem):
                # as soon as plottable slots are there, they can be filled in here
                pass

            # the drop signal can be emitted now so that the tab where something was dragged onto can be redrawn.
            self.dropSignal.emit(redraw_fitpage_index, redraw_subtab_index)
            event.acceptProposedAction()

        # Here, the serialization also plays a role, because the modifier is cloned in the process and used to create
        # a new child that the modifier will be for the target item.
        elif event.mimeData().data('Modifier'):
            data_address = int(event.mimeData().data('Modifier').data())
            data = ctypes.cast(data_address, ctypes.py_object).value
            clone = data.clone()
            targetItem = self.itemAt(event.position().toPoint())

            if isinstance(targetItem.data(0, 1), PlottableItem):
                targetItem.addChild(clone)
                redraw_fitpage_index = targetItem.parent().data(0, 1).fitpage_index
                redraw_subtab_index = targetItem.parent().data(0, 1).subtab_index

            elif isinstance(targetItem.data(0, 1), PlotItem):
                targetItem.addChild(clone)
                redraw_fitpage_index = targetItem.data(0, 1).fitpage_index
                redraw_subtab_index = targetItem.data(0, 1).subtab_index

            self.dropSignal.emit(redraw_fitpage_index, redraw_subtab_index)
            event.acceptProposedAction()

        else:
            event.ignore()






