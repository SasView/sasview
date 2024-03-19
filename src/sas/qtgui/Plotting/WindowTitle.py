"""
Allows users to change the title of the current graph
from "Graph_n" to any ASCII text.
"""
from PySide6 import QtWidgets, QtCore

from sas.qtgui.Plotting.UI.WindowTitleUI import Ui_WindowTitle

class WindowTitle(QtWidgets.QDialog, Ui_WindowTitle):
    """ Simple GUI for a single line text query """
    def __init__(self, parent=None, new_title=""):
        super(WindowTitle, self).__init__(parent)
        self.setupUi(self)

        self.txtTitle.setText(new_title)

    def title(self):
        """ Return the new title """
        return self.txtTitle.text()

