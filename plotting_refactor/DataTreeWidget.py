from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QAbstractItemView
from PySide6.QtCore import QMimeData, QRect, QByteArray, QDataStream, QIODevice
from PySide6.QtGui import QDrag
from DataTreeItems import DataItem

class DataTreeWidget(QTreeWidget):
    def __init__(self, DataViewer, datacollector):
        super().__init__(parent=DataViewer)
        self.datacollector = datacollector
        self.setGeometry(QRect(10, 10, 391, 312))
        self.setDragEnabled(True)
        self.setColumnCount(1)
        self.setHeaderLabels(["Data Name"])

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item:
            if isinstance(item.data(0, 1), DataItem):
                drag = QDrag(self)
                mimeData = QMimeData()
                mimeData.setData('ID', QByteArray(str(item.data(0, 1).get_data_id())))
                mimeData.setData('Type', QByteArray(str(item.data(0, 1).get_type_num())))

                drag.setMimeData(mimeData)
                drag.exec(supportedActions)
