import sys
import unittest

from PyQt4 import QtGui

# set up import paths
import path_prepare

# Local
from sas.qtgui.MainWindow.WelcomePanel import WelcomePanel

if not QtGui.QApplication.instance():
    app = QtGui.QApplication(sys.argv)

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
        self.assertIsInstance(self.widget, QtGui.QDialog)
        self.assertEqual(self.widget.windowTitle(), "Welcome")
        
    def testVersion(self):
        '''Test the version string'''
        version = self.widget.lblVersion
        self.assertIsInstance(version, QtGui.QLabel)

        self.assertIn("SasView", version.text())
        self.assertIn("Build:", version.text())
        self.assertIn("UTK, UMD, NIST, ORNL, ISIS, ESS, ILL and ANSTO", version.text())
       
if __name__ == "__main__":
    unittest.main()
