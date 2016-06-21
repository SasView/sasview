import sys
import unittest

from PyQt4 import QtGui
from PyQt4 import QtTest
from PyQt4 import QtCore
from mock import MagicMock

# Local
from MainWindow import MainSasViewWindow
from MainWindow import SplashScreen

app = QtGui.QApplication(sys.argv)

class MainWindowTest(unittest.TestCase):
    """Test the Main Window GUI"""
    def setUp(self):
        """Create the GUI"""

        self.widget = MainSasViewWindow(None)

    def tearDown(self):
        """Destroy the GUI"""
        self.widget = None

    def testDefaults(self):
        """Test the GUI in its default state"""
        self.assertIsInstance(self.widget, QtGui.QMainWindow)
        self.assertIsInstance(self.widget.centralWidget(), QtGui.QWorkspace)
        
    def testSplashScreen(self):
        """ Test the splash screen """
        splash = SplashScreen()
        self.assertIsInstance(splash, QtGui.QSplashScreen)

    def testExit(self):
        """
        Test that the custom exit method is called on shutdown
        """
        # Must mask sys.exit, otherwise the whole testing process stops.
        sys.exit = MagicMock()
        QtGui.QMessageBox.question = MagicMock(return_value=QtGui.QMessageBox.Yes)

        # Open, then close the main window
        tmp_main = MainSasViewWindow(None)
        tmp_main.close()

        # See that the MessageBox method got called
        self.assertTrue(QtGui.QMessageBox.question.called)
       
if __name__ == "__main__":
    unittest.main()
