from DataTreeItems import DataItem
from PySide6.QtCore import QByteArray, QMimeData, QRect, Qt
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import QTreeWidget


class DataTreeWidget(QTreeWidget):
    """
    Tree widget that is appearing in the DataViewer. It represents data stored in the DataCollector by objects from
    DataTreeItems. Instantiating of these DataTreeItems happens in the DataViewer.
    """
    def __init__(self, dataviewer, datacollector):
        super().__init__(parent=dataviewer)
        self.datacollector = datacollector
        self.setGeometry(QRect(10, 10, 391, 312))
        self.setDragEnabled(True)
        self.setColumnCount(1)
        self.setHeaderLabels(["Data Name"])

    def startDrag(self, supportedActions: Qt.DropAction):
        """
        Overwriting the startDrag from the normal QTreeWidget. When dragging the QTreeWidgetItem to another plot,
        mimetypes ID and Type are used to store the dataset.data_id and the type_num. Type_num represents if the
        item is a data, fit or residuals item.
        """
        item = self.currentItem()
        if item:
            if isinstance(item.data(0, 1), DataItem):
                drag = QDrag(self)
                mimeData = QMimeData()
                mimeData.setData('ID', QByteArray(str(item.data(0, 1).data_id)))
                mimeData.setData('Type', QByteArray(str(item.data(0, 1).type_num)))

                drag.setMimeData(mimeData)
                drag.exec(supportedActions)
