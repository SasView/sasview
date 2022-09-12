from PyQt5 import QtWidgets

import sas.sasview

from sas import config
from sas.system import legal

from sas.qtgui.MainWindow.UI.WelcomePanelUI import Ui_WelcomePanelUI

class WelcomePanel(QtWidgets.QDialog, Ui_WelcomePanelUI):
    def __init__(self, parent=None):
        super(WelcomePanel, self).__init__(parent)
        self.setupUi(self)

        self.setWindowTitle("Welcome")

        version = sas.sasview.__version__ # TODO: Make consistent with other version references
        build = sas.sasview.__build__ # TODO: Make consistent with other build references

        ver = "\nSasView %s\nBuild: %s\n%s" % (version, build, legal._copyright)

        self.lblVersion.setText(ver)

        # no reason to have this widget resizable
        self.setFixedSize(self.minimumSizeHint())
