from PyQt5 import QtCore
from PyQt5 import QtWidgets

from sas.qtgui.Utilities.UI.ModelEditor import Ui_ModelEditor
from sas.qtgui.Utilities import GuiUtils

class ModelEditor(QtWidgets.QDialog, Ui_ModelEditor):
    """
    Class describing the "advanced" model editor.
    This is a simple text browser allowing for editing python and
    supporting simple highlighting.
    """
    modelModified = QtCore.pyqtSignal()
    def __init__(self, parent=None, is_python=True):
        super(ModelEditor, self).__init__(parent)
        self.setupUi(self)

        self.is_python = is_python

        self.setupWidgets()

        self.addSignals()

    def setupWidgets(self):
        """
        Set up dialog widgets.
        Here - just the highlighter connected to the text edit.
        """
        # Weird import location - workaround for a bug in Sphinx choking on
        # importing QSyntaxHighlighter
        # DO NOT MOVE TO TOP
        from sas.qtgui.Utilities.PythonSyntax import PythonHighlighter
        self.highlight = PythonHighlighter(self.txtEditor.document(), is_python=self.is_python)

        self.txtEditor.setFont(GuiUtils.getMonospaceFont())

    def addSignals(self):
        """
        Respond to signals in the widget
        """
        self.txtEditor.textChanged.connect(self.onEdit)

    def onEdit(self):
        """
        Respond to changes in the text browser.
        """
        # We have edited the model - notify the parent.
        if self.txtEditor.toPlainText() != "":
            self.modelModified.emit()

    def getModel(self):
        """
        Return the current model, as displayed in the window
        """
        model = {'text':self.txtEditor.toPlainText()}
        model['filename'] = ""
        return model

