from PySide2 import QtWidgets

import sas.sasview
import sas.system.version

from sas import config
from sas.system import legal

from sas.qtgui.MainWindow.UI.WelcomePanelUI import Ui_WelcomePanelUI

class WelcomePanel(QtWidgets.QDialog, Ui_WelcomePanelUI):
    def __init__(self, parent=None):
        super(WelcomePanel, self).__init__(parent)
        self.setupUi(self)

        self.setWindowTitle("Welcome")

        version = sas.system.version.__version__  # TODO: Make consistent with other version references

        ver = "\nSasView %s\n%s" % (version, legal.copyright)

        self.lblVersion.setText(ver)

        # no reason to have this widget resizable
        self.setFixedSize(self.minimumSizeHint())
