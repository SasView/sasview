import sys

import pytest
from PySide6 import QtCore, QtWidgets
from PySide6.QtTest import QTest

# Local
from sas.qtgui.MainWindow.MainWindow import MainSasViewWindow, SplashScreen
from sas.qtgui.Perspectives.Fitting import FittingPerspective
from sas.qtgui.Utilities.HidableDialog import HidableDialog
from sas.system import config


class MainWindowTest:
    """Test the Main Window GUI"""

    def __init__(self):
        config.override_with_defaults() # Disable saving of test file
        config.LAST_WHATS_NEW_HIDDEN_VERSION = "999.999.999" # Give a very large version number

    @pytest.fixture(autouse=True)
    def widget(self, qapp):
        '''Create/Destroy the GUI'''
        screen_resolution = QtCore.QRect(0, 0, 640, 480)
        w = MainSasViewWindow(screen_resolution, None)

        yield w

    def testDefaults(self, widget):
        """Test the GUI in its default state"""
        assert isinstance(widget, QtWidgets.QMainWindow)
        assert isinstance(widget.centralWidget(), QtWidgets.QMdiArea)
        assert widget.workspace.horizontalScrollBarPolicy() == \
                        QtCore.Qt.ScrollBarAsNeeded
        assert widget.workspace.verticalScrollBarPolicy() == \
                        QtCore.Qt.ScrollBarAsNeeded

    def testSplashScreen(self, qapp):
        """ Test the splash screen """
        splash = SplashScreen()
        assert isinstance(splash, QtWidgets.QSplashScreen)

    def testWidgets(self, qapp):
        """ Test enablement/disablement of widgets """
        # Open the main window
        screen_resolution = QtCore.QRect(0, 0, 640, 480)
        tmp_main = MainSasViewWindow(screen_resolution, None)
        tmp_main.showMaximized()
        # See that only one subwindow is up
        assert len(tmp_main.workspace.subWindowList()) == 3
        # and that the subwindow is the fitting perspective
        assert isinstance(tmp_main.workspace.subWindowList()[0].widget(), FittingPerspective.FittingWindow)
        # Show the message widget
        tmp_main.guiManager.showWelcomeMessage()
        # Assure it is visible and a part of the MdiArea
        assert len(tmp_main.workspace.subWindowList()) == 3

    @pytest.mark.xfail(reason="2022-09 already broken - input file issue")
    def testPerspectiveChanges(self, widget):
        """
        Test all information is retained on perspective change
        """
        def check_after_load(name):
            assert name == gui.perspective().name
            assert len(gui.perspective().currentTabDataId()) == 1
            assert (gui.perspective().currentTabDataId()[0]) in dataIDList

        # Base definitions
        FIT = 'Fitting'
        PR = 'Inversion'
        gui = widget.guiManager
        filesWidget = gui.filesWidget
        currentPers = filesWidget.cbFitting
        sendDataButton = filesWidget.cmdSendTo
        # Verify defaults
        assert hasattr(gui, 'loadedPerspectives')
        assert len(gui.loadedPerspectives) == 4
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

    def testExit(self, qapp, mocker):
        """
        Test that the custom exit method is called on shutdown
        """
        # Must mask sys.exit, otherwise the whole testing process stops.
        mocker.patch.object(sys, 'exit')
        # mocker.patch.object(QtWidgets.QMessageBox, 'question', return_value=QtWidgets.QMessageBox.Yes)
        mocker.patch.object(HidableDialog, 'exec', return_value=1)

        # Open, then close the main window
        screen_resolution = QtCore.QRect(0, 0, 640, 480)
        tmp_main = MainSasViewWindow(screen_resolution, None)
        tmp_main.close()

        # See that the MessageBox method got called
        assert HidableDialog.exec.called_once()
