from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QAbstractItemView
from PySide6.QtCore import QRect, Signal, QMimeData, QByteArray
from PySide6.QtGui import QDrag
from PlotTreeItems import TabItem, SubTabItem, PlotItem, PlottableItem
from PlotModifiers import PlotModifier
import ctypes
from typing import Tuple

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
        if event.mimeData().data('ID'):
            data_id = event.mimeData().data('ID').data()
            data_type = event.mimeData().data('Type').data()

            targetItem = self.itemAt(event.position().toPoint())
            if isinstance(targetItem.data(0, 1), PlotItem):
                new_plottable = PlottableItem(targetItem, [str(data_id.decode('utf-8'))],
                                              int(data_id), int(data_type))
                # get the fitpage index and the subtab index of the targetItem, so that they can be activated upon redrawing
                redraw_fitpage_index = targetItem.data(0, 1).get_figpage_index(),
                redraw_subtab_index = targetItem.data(0, 1).get_subtab_index()
            elif isinstance(targetItem.data(0, 1), PlottableItem):
                # as soon as plottable slots are there, they can be filled in here
                pass
            self.dropSignal.emit(redraw_fitpage_index, redraw_subtab_index)
            event.acceptProposedAction()

        elif event.mimeData().data('Modifier'):
            data_address = int(event.mimeData().data('Modifier').data())
            data = ctypes.cast(data_address, ctypes.py_object).value
            clone = data.clone()
            targetItem = self.itemAt(event.position().toPoint())
            if isinstance(targetItem.data(0, 1), PlottableItem):
                targetItem.addChild(clone)
                redraw_fitpage_index = targetItem.parent().data(0, 1).get_fitpage_index()
                redraw_subtab_index = targetItem.parent().data(0, 1).get_subtab_index()
                print(str(targetItem.data(0, 1).get_type()))
            elif isinstance(targetItem.data(0, 1), PlotItem):
                targetItem.addChild(clone)
                redraw_fitpage_index = targetItem.data(0, 1).get_fitpage_index()
                redraw_subtab_index = targetItem.data(0, 1).get_subtab_index()
                print(str(targetItem.data(0, 1).get_type()))

            self.dropSignal.emit(redraw_fitpage_index, redraw_subtab_index)
            event.acceptProposedAction()
        else:
            event.ignore()






