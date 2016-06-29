# global
from PyQt4 import QtCore

# UI
from UI.TabbedFileLoadUI import DataLoadWidget
# from UI.Test2DataExplorerUI import DataLoadWidget

class DroppableDataLoadWidget(DataLoadWidget):
    """
    Overwrite drag and drop methods in the base class
    so users can drop files directly onto the Data Explorer
    """
    def __init__(self, parent=None, guimanager=None):
        super(DroppableDataLoadWidget, self).__init__(parent)

        # Enable file drag-drop on treeView
        self.setAcceptDrops(True)
        self.communicator = guimanager.communicator()

    def dragIsOK(self, event):
        """
        Return True if the event contain URLs
        """
        # Analyze mime data
        if event.mimeData().hasUrls():
            return True
        else:
            return False

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
                filenames.append(str(url.toLocalFile()))
            self.communicator.fileReadSignal.emit(filenames)
            event.accept()
        else:
            event.ignore()

