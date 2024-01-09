from PySide6 import QtWidgets

from .UI.DocRegenInProgressDialog import Ui_Dialog


class DocRegenProgress(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        super(DocRegenProgress, self).__init__()
        self.parent = parent
        self.setupUi(self)

        self.setWindowTitle("Documentation Regenerating")
        self.label.setText("Regeneration Progress:")

        self.addSignals()

    def addSignals(self):
        self.parent.communicate.documentationRegenInProgressSignal.connect(self.show)
        self.parent.communicate.documentationRegeneratedSignal.connect(self.close)

