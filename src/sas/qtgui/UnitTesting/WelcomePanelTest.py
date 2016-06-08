import sys
import unittest

from PyQt4.QtGui import *
from PyQt4.QtTest import QTest
from PyQt4.QtCore import *

# Local
from WelcomePanel import WelcomePanel

app = QApplication(sys.argv)

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
        self.assertIsInstance(self.widget, QDialog)
        self.assertEqual(self.widget.windowTitle(), "Welcome")
        
    def testVersion(self):
        """
        """
        version = self.widget.lblVersion
        self.assertIsInstance(version, QLabel)
        ver_text = "\nSasView 4.0.0-alpha\nBuild: 1\n(c) 2009 - 2013, UTK, UMD, NIST, ORNL, ISIS, ESS and IL"
        #self.assertEqual(str(version.text()), ver_text)
        self.assertIn("SasView", str(version.text()))
        self.assertIn("Build:", str(version.text()))
       
if __name__ == "__main__":
    unittest.main()
