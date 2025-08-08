from PySide6 import QtCore, QtWidgets

from sas.qtgui.Utilities.UI.DocRegenInProgress import Ui_DocRegenProgress
from sas.system.user import DOC_LOG


class DocRegenProgress(QtWidgets.QWidget, Ui_DocRegenProgress):
    def __init__(self, parent=None):
        """The DocRegenProgress class is a window to display the progress of the documentation regeneration process.

        :param parent: Any Qt object with a communicator that can trigger events.
        """
        super(DocRegenProgress, self).__init__()
        self.setupUi(self)
        self.parent = parent
        if parent and hasattr(parent, 'communicate'):
            self.communicate = parent.communicate
        else:
            from sas.qtgui.Utilities.GuiUtils import communicate
            self.communicate = communicate

        self.textBrowser.setText("Generating Plugin Documentation...")
        self.file_watcher = QtCore.QFileSystemWatcher()

        self.addSignals()

    def addSignals(self):
        """Adds triggers and signals to the window to ensure proper behavior."""
        self.communicate.documentationRegenInProgressSignal.connect(self.show)
        self.communicate.documentationRegeneratedSignal.connect(self.close)
        self.communicate.documentationUpdateLogSignal.connect(self.updateLog)
        # Trigger the file watcher when the documentation log changes on disk.
        self.file_watcher.addPath(str(DOC_LOG.absolute()))
        self.file_watcher.fileChanged.connect(self.updateLog)

    def updateLog(self):
        """This method is triggered whenever the file associated with the file_watcher object is changed."""
        self.textBrowser.setText("")
        with open(DOC_LOG) as f:
            self.textBrowser.append(f.read())

    def close(self):
        """Override the close behavior to ensure the window always exists in memory."""
        self.hide()
