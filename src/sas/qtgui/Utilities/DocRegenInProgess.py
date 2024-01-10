from PySide6 import QtWidgets, QtCore

from sas.qtgui.Utilities.UI.DocRegenInProgress import Ui_DocRegenProgress
from sas.sascalc.doc_regen.makedocumentation import DOC_LOG


class DocRegenProgress(QtWidgets.QWidget, Ui_DocRegenProgress):
    def __init__(self, parent=None):
        super(DocRegenProgress, self).__init__()
        self.setupUi(self)
        self.parent = parent

        self.setWindowTitle("Documentation Regenerating")
        self.label.setText("...Regeneration Progress...")
        self.textBrowser.setText("Placeholder Text.")
        self.textBrowser.setWindowFilePath(str(DOC_LOG.absolute()))

        self.addSignals()

    def addSignals(self):
        if self.parent:
            self.parent.communicate.documentationRegenInProgressSignal.connect(self.show)
            self.parent.communicate.documentationRegeneratedSignal.connect(self.close)
        if not DOC_LOG.exists():
            with open(DOC_LOG, 'w') as fp:
                pass
        self.file_watcher = QtCore.QFileSystemWatcher()
        self.file_watcher.addPath(str(DOC_LOG.absolute()))
        self.file_watcher.fileChanged.connect(self.updateLog)

    def updateLog(self):
        with open(DOC_LOG) as f:
            for line in f.read():
                self.textBrowser.append(line)
