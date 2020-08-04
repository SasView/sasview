import sys
import unittest

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtTest import QTest
from PyQt5 import QtCore
from unittest.mock import MagicMock

# set up import paths
import path_prepare

# Local
from sas.qtgui.MainWindow.MainWindow import MainSasViewWindow
from sas.qtgui.MainWindow.MainWindow import SplashScreen
from sas.qtgui.Perspectives.Fitting import FittingPerspective

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)

class MainWindowTest(unittest.TestCase):
    """Test the Main Window GUI"""
    def setUp(self):
        """Create the GUI"""
        screen_resolution = QtCore.QRect(0, 0, 640, 480)
        self.widget = MainSasViewWindow(screen_resolution, None)

    def tearDown(self):
        """Destroy the GUI"""
        self.widget = None

    def testDefaults(self):
        """Test the GUI in its default state"""
        self.assertIsInstance(self.widget, QtWidgets.QMainWindow)
        self.assertIsInstance(self.widget.centralWidget(), QtWidgets.QMdiArea)
        self.assertTrue(self.widget.workspace.horizontalScrollBarPolicy() ==
                        QtCore.Qt.ScrollBarAsNeeded)
        self.assertTrue(self.widget.workspace.verticalScrollBarPolicy() ==
                        QtCore.Qt.ScrollBarAsNeeded)

    def testSplashScreen(self):
        """ Test the splash screen """
        splash = SplashScreen()
        self.assertIsInstance(splash, QtWidgets.QSplashScreen)

    def testWidgets(self):
        """ Test enablement/disablement of widgets """
        # Open the main window
        screen_resolution = QtCore.QRect(0, 0, 640, 480)
        tmp_main = MainSasViewWindow(screen_resolution, None)
        tmp_main.showMaximized()
        # See that only one subwindow is up
        self.assertEqual(len(tmp_main.workspace.subWindowList()), 3)
        # and that the subwindow is the fitting perspective
        self.assertIsInstance(tmp_main.workspace.subWindowList()[0].widget(),
                              FittingPerspective.FittingWindow)
        # Show the message widget
        tmp_main.guiManager.showWelcomeMessage()
        # Assure it is visible and a part of the MdiArea
        self.assertEqual(len(tmp_main.workspace.subWindowList()), 3)

        tmp_main.close()

    def testPerspectiveChanges(self):
        """
        Test all information is retained on perspective change
        """
        def check_after_load(name):
            self.assertEqual(name, gui.perspective().name)
            self.assertEqual(1, len(gui.perspective().currentTabDataId()))
            self.assertTrue(
                (gui.perspective().currentTabDataId()[0]) in dataIDList)

        # Base definitions
        FIT = 'Fitting'
        PR = 'Inversion'
        gui = self.widget.guiManager
        filesWidget = gui.filesWidget
        currentPers = filesWidget.cbFitting
        sendDataButton = filesWidget.cmdSendTo
        # Verify defaults
        self.assertTrue(hasattr(gui, 'loadedPerspectives'))
        self.assertEqual(4, len(gui.loadedPerspectives))
        # Load data
        file = ["cyl_400_20.txt"]
        filesWidget.readData(file)
        data, _ = filesWidget.getAllData()
        dataIDList = list(data.keys())
        # Send data to fitting perspective
        QTest.mouseClick(sendDataButton, QtCore.Qt.LeftButton)
        # Verify one data set is loaded in the current Fitting Tab
        check_after_load(FIT)
        # Change to Inversion Perspective, Send data, and verify
        currentPers.setCurrentIndex(currentPers.findText(PR))
        QTest.mouseClick(sendDataButton, QtCore.Qt.LeftButton)
        check_after_load(PR)
        # Change back to Fitting Perspective and verify
        currentPers.setCurrentIndex(currentPers.findText(FIT))
        check_after_load(FIT)
        # Go back to Inversion perspective and verify data still exists
        currentPers.setCurrentIndex(currentPers.findText(PR))
        check_after_load(PR)

    def testExit(self):
        """
        Test that the custom exit method is called on shutdown
        """
        # Must mask sys.exit, otherwise the whole testing process stops.
        sys.exit = MagicMock()
        QtWidgets.QMessageBox.question = MagicMock(return_value=QtWidgets.QMessageBox.Yes)

        # Open, then close the main window
        screen_resolution = QtCore.QRect(0, 0, 640, 480)
        tmp_main = MainSasViewWindow(screen_resolution, None)
        tmp_main.close()

        # See that the MessageBox method got called
        self.assertTrue(QtWidgets.QMessageBox.question.called)


if __name__ == "__main__":
    unittest.main()
