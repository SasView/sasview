from PyQt5 import QtWidgets

import sas.sasview

from sas import config

from sas.qtgui.MainWindow.UI.WelcomePanelUI import Ui_WelcomePanelUI

class WelcomePanel(QtWidgets.QDialog, Ui_WelcomePanelUI):
    def __init__(self, parent=None):
        super(WelcomePanel, self).__init__(parent)
        self.setupUi(self)

        self.setWindowTitle("Welcome")

        version = sas.sasview.__version__
        build = sas.sasview.__build__

        ver = "\nSasView %s\nBuild: %s\n%s" % (version, build, config._copyright)

        self.lblVersion.setText(ver)

        # no reason to have this widget resizable
        self.setFixedSize(self.minimumSizeHint())
