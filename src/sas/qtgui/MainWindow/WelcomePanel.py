# global
import sys
import os

from PyQt5 import QtWidgets

import sas.sasview
import sas.qtgui.Utilities.LocalConfig as LocalConfig
from sas.qtgui.UI import images_rc
from sas.qtgui.UI import main_resources_rc

from sas.qtgui.MainWindow.UI.WelcomePanelUI import Ui_WelcomePanelUI

class WelcomePanel(QtWidgets.QDialog, Ui_WelcomePanelUI):
    def __init__(self, parent=None):
        super(WelcomePanel, self).__init__(parent)
        self.setupUi(self)

        self.setWindowTitle("Welcome")

        version = sas.sasview.__version__
        build = sas.sasview.__build__

        ver = "\nSasView %s\nBuild: %s\n%s" % (version, build, LocalConfig._copyright)

        self.lblVersion.setText(ver)

        # no reason to have this widget resizable
        self.setFixedSize(self.minimumSizeHint())
