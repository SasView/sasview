import sys
import unittest

from PyQt5 import QtGui, QtWidgets

# set up import paths
import sas.qtgui.path_prepare

# Local
from sas.qtgui.MainWindow.WelcomePanel import WelcomePanel

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)

class WelcomePanelTest(unittest.TestCase):
    '''Test the WelcomePanel'''
    def setUp(self):
        '''Create the WelcomePanel'''

        self.widget = WelcomePanel(None)

    def tearDown(self):
        '''Destroy the GUI'''
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        '''Test the GUI in its default state'''
        assert isinstance(self.widget, QtWidgets.QDialog)
        assert self.widget.windowTitle() == "Welcome"
        
    def testVersion(self):
        '''Test the version string'''
        version = self.widget.lblVersion
        assert isinstance(version, QtWidgets.QLabel)

        assert "SasView" in version.text()
        assert "Build:" in version.text()
        for inst in "UTK, UMD, ESS, NIST, ORNL, ISIS, ILL, DLS, TUD, BAM, ANSTO".split(", "):
            assert inst in version.text()
       
if __name__ == "__main__":
    unittest.main()
