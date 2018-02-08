# global
import sys
import os
import types
import webbrowser

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Utilities.PythonSyntax import PythonHighlighter

from sas.qtgui.Utilities.UI.ModelEditor import Ui_ModelEditor

class ModelEditor(QtWidgets.QDialog, Ui_ModelEditor):
    """
    Class describing the "advanced" model editor.
    This is a simple text browser allowing for editing python and
    supporting simple highlighting.
    """
    modelModified = QtCore.pyqtSignal()
    def __init__(self, parent=None):
        super(ModelEditor, self).__init__(parent)
        self.setupUi(self)

        self.setupWidgets()

        self.addSignals()

    def setupWidgets(self):
        """
        Set up dialog widgets.
        Here - just the highlighter connected to the text edit.
        """
        self.highlight = PythonHighlighter(self.txtEditor.document())

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
        pass

    def getModel(self):
        """
        Return the current model, as displayed in the window
        """
        model = {'text':self.txtEditor.toPlainText()}
        model['filename'] = ""
        return model

