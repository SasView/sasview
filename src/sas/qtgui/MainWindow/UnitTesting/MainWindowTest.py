import sys
import unittest
import logging

from PyQt5 import QtGui, QtWidgets
from PyQt5 import QtTest
from PyQt5 import QtCore
from unittest.mock import MagicMock

# set up import paths
import path_prepare

# Local
from sas.qtgui.MainWindow.MainWindow import MainSasViewWindow
from sas.qtgui.MainWindow.MainWindow import SplashScreen
from sas.qtgui.MainWindow.GuiManager import GuiManager
from sas.qtgui.Perspectives.Fitting import FittingPerspective

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)

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
        self.assertIsInstance(self.widget, QtWidgets.QMainWindow)
        self.assertIsInstance(self.widget.centralWidget(), QtWidgets.QMdiArea)
        
    def testSplashScreen(self):
        """ Test the splash screen """
        splash = SplashScreen()
        self.assertIsInstance(splash, QtWidgets.QSplashScreen)

    def testWidgets(self):
        """ Test enablement/disablement of widgets """
        # Open the main window
        tmp_main = MainSasViewWindow(None)
        tmp_main.showMaximized()
        # See that only one subwindow is up
        self.assertEqual(len(tmp_main.workspace.subWindowList()), 1)
        # and that the subwindow is the fitting perspective
        self.assertIsInstance(tmp_main.workspace.subWindowList()[0].widget(),
                              FittingPerspective.FittingWindow)
        # Show the message widget
        tmp_main.guiManager.showWelcomeMessage()
        # Assure it is visible and a part of the MdiArea
        self.assertTrue(tmp_main.guiManager.welcomePanel.isVisible())
        self.assertEqual(len(tmp_main.workspace.subWindowList()), 2)

        tmp_main.close()

    def testExit(self):
        """
        Test that the custom exit method is called on shutdown
        """
        # Must mask sys.exit, otherwise the whole testing process stops.
        sys.exit = MagicMock()
        QtWidgets.QMessageBox.question = MagicMock(return_value=QtWidgets.QMessageBox.Yes)

        # Open, then close the main window
        tmp_main = MainSasViewWindow(None)
        tmp_main.close()

        # See that the MessageBox method got called
        self.assertTrue(QtWidgets.QMessageBox.question.called)
       
if __name__ == "__main__":
    unittest.main()
