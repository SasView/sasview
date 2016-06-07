# global
import sys
import os
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import QtWebKit

import sas.sasview

from UI.WelcomePanelUI import WelcomePanelUI

class WelcomePanel(WelcomePanelUI):
    def __init__(self, parent=None):
        super(WelcomePanel, self).__init__(parent)
        self.setWindowTitle("Welcome")

        version = sas.sasview.__version__
        build = sas.sasview.__build__

        self.lblVersion = "\nSasView %s\nBuild: %s" % (version, build)
        self.lblVersion += "\n(c) 2009 - 2013, UTK, UMD, NIST, ORNL, ISIS, ESS and IL"
