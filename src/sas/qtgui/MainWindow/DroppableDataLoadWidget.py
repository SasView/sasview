# global
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

# UI
from sas.qtgui.UI import main_resources_rc
from sas.qtgui.MainWindow.UI.DataExplorerUI import Ui_DataLoadWidget

class DroppableDataLoadWidget(QtWidgets.QTabWidget, Ui_DataLoadWidget):
    """
    Overwrite drag and drop methods in the base class
    so users can drop files directly onto the Data Explorer
    """
    def __init__(self, parent=None, guimanager=None):
        super(DroppableDataLoadWidget, self).__init__(parent)
        self.setupUi(self)

        # Enable file drag-drop on treeView
        self.setAcceptDrops(True)
        self.communicator = guimanager.communicator()
        flags = QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowSystemMenuHint
        self.setWindowFlags(flags)

    def dragIsOK(self, event):
        """
        Return True if the event contain URLs
        """
        # Analyze mime data
        return bool(event.mimeData().hasUrls() and self.currentIndex() == 0)

    def dragEnterEvent(self, event):
        """
        Called automatically on a drag into the treeview
        """
        if self.dragIsOK(event):
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """
        Called automatically when a drag is
        moved inside the treeview
        """
        if self.dragIsOK(event):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """
        Called automatically when a drop
        is added to the treeview.
        """
        if self.dragIsOK(event):
            filenames=[]
            for url in event.mimeData().urls():
                filenames.append(url.toLocalFile())
            self.communicator.fileReadSignal.emit(filenames)
            event.accept()
        else:
            event.ignore()

    def closeEvent(self, event):
        """
        Overwrite the close event - no close!
        """
        event.ignore()
