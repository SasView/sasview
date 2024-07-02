from PySide6 import QtWidgets, QtCore, QtGui

from sas.qtgui.Utilities.UI.ReparameterizationEditorUI import Ui_ReparameterizationEditor

class ReparameterizationEditor(QtWidgets.QDialog, Ui_ReparameterizationEditor):
    """
    """

    def __init__(self, parent=None):
        super(ReparameterizationEditor, self).__init__(parent._parent)

        self.parent = parent

        self.setupUi(self)
