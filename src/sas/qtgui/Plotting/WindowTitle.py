"""
Allows users to change the title of the current graph
from "Graph_n" to any ASCII text.
"""
from PyQt5 import QtWidgets, QtCore

from sas.qtgui.Plotting.UI.WindowTitleUI import Ui_WindowTitle

class WindowTitle(QtWidgets.QDialog, Ui_WindowTitle):
    """ Simple GUI for a single line text query """
    def __init__(self, parent=None, new_title=""):
        super(WindowTitle, self).__init__(parent)
        self.setupUi(self)
        # disable the context help icon
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)

        self.txtTitle.setText(new_title)

    def title(self):
        """ Return the new title """
        return self.txtTitle.text()

