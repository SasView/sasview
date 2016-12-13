from PyQt4 import QtGui

import sas.sasview

from sas.qtgui.UI.WindowTitleUI import Ui_WindowTitle

class WindowTitle(QtGui.QDialog, Ui_WindowTitle):
    """ Simple GUI for a single line text query """
    def __init__(self, parent=None, new_title=""):
        super(WindowTitle, self).__init__(parent)
        self.setupUi(self)
        self.txtTitle.setText(new_title)

    def title(self):
        return self.txtTitle.text()

