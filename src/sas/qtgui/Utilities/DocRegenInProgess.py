from PySide6 import QtWidgets, QtCore

from sas.qtgui.Utilities.UI.DocRegenInProgress import Ui_DocRegenProgress
from sas.sascalc.doc_regen.makedocumentation import USER_DOC_LOG, DOC_LOG


class DocRegenProgress(QtWidgets.QWidget, Ui_DocRegenProgress):
    def __init__(self, parent=None):
        super(DocRegenProgress, self).__init__()
        self.setupUi(self)
        self.parent = parent

        self.setWindowTitle("Documentation Regenerating")
        self.label.setText("Regeneration In Progress")
        self.textBrowser.setText("Placeholder Text.")
        self.addSignals()

    def addSignals(self):
        if self.parent:
            self.parent.communicate.documentationRegenInProgressSignal.connect(self.show)
            self.parent.communicate.documentationRegeneratedSignal.connect(self.hide)
        self.file_watcher = QtCore.QFileSystemWatcher()
        self.file_watcher.addPath(str(DOC_LOG.absolute()))
        self.file_watcher.fileChanged.connect(self.updateLog)

    def updateLog(self):
        self.textBrowser.setText("")
        with open(DOC_LOG, 'r') as f:
            self.textBrowser.append(f.read())

    def close(self):
        # Override close and hide the window instead
        self.hide()
