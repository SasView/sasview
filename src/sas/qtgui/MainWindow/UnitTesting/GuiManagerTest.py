import sys
import subprocess
import unittest
import webbrowser
import logging

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtTest import QTest
from PyQt5 import QtCore
from unittest.mock import MagicMock

# set up import paths
import path_prepare

# Local
from sas.qtgui.MainWindow.DataExplorer import DataExplorerWindow
from sas.qtgui.MainWindow.AboutBox import AboutBox
from sas.qtgui.MainWindow.WelcomePanel import WelcomePanel
from sas.qtgui.Utilities.IPythonWidget import IPythonWidget

from sas.qtgui.MainWindow.GuiManager import Acknowledgements, GuiManager
from sas.qtgui.MainWindow.MainWindow import MainSasViewWindow
from sas.qtgui.UnitTesting.TestUtils import QtSignalSpy

if not QApplication.instance():
    app = QApplication(sys.argv)

class GuiManagerTest(unittest.TestCase):
    '''Test the Main Window functionality'''
    def setUp(self):
        '''Create the tested object'''
        class MainWindow(MainSasViewWindow):
            # Main window of the application
            def __init__(self, reactor, parent=None):
                screen_resolution = QtCore.QRect(0,0,640,480)
                super(MainWindow, self).__init__(screen_resolution, parent)
        
                # define workspace for dialogs.
                self.workspace = QMdiArea(self)
                self.setCentralWidget(self.workspace)

        self.manager = GuiManager(MainWindow(None))

    def tearDown(self):
        '''Destroy the GUI'''
        self.manager = None

    def testDefaults(self):
        """
        Test the object in its default state
        """
        self.assertIsInstance(self.manager.filesWidget, DataExplorerWindow)
        self.assertIsInstance(self.manager.dockedFilesWidget, QDockWidget)
        self.assertIsInstance(self.manager.dockedFilesWidget.widget(), DataExplorerWindow)
        self.assertEqual(self.manager._workspace.dockWidgetArea(self.manager.dockedFilesWidget), QtCore.Qt.LeftDockWidgetArea)

        self.assertIsInstance(self.manager.logDockWidget, QDockWidget)
        self.assertIsInstance(self.manager.logDockWidget.widget(), QTextBrowser)
        self.assertEqual(self.manager._workspace.dockWidgetArea(self.manager.logDockWidget), QtCore.Qt.BottomDockWidgetArea)

        self.assertIsInstance(self.manager.ackWidget, Acknowledgements)
        self.assertIsInstance(self.manager.aboutWidget, AboutBox)
        #self.assertIsInstance(self.manager.welcomePanel, WelcomePanel)

    def skip_testLogging(self):
        """
        Test logging of stdout, stderr and log messages
        """
        # See if the log window is empty
        self.assertEqual(self.manager.logDockWidget.widget().toPlainText(), "")

        # Now, send some message to stdout.
        # We are in the MainWindow scope, so simple 'print' will work
        message = "from stdout"
        print(message)
        self.assertIn(message, self.manager.logDockWidget.widget().toPlainText())

        # Send some message to stderr
        message = "from stderr"
        sys.stderr.write(message)
        self.assertIn(message, self.manager.logDockWidget.widget().toPlainText())

        # And finally, send a log message
        import logging
        message = "from logging"
        message_logged = "ERROR: " + message
        logging.error(message)
        self.assertIn(message_logged, self.manager.logDockWidget.widget().toPlainText())

    def testConsole(self):
        """
        Test the docked QtConsole
        """
        # Invoke the console action
        self.manager.actionPython_Shell_Editor()

        # Test the widegt properties
        self.assertIsInstance(self.manager.ipDockWidget, QDockWidget)
        self.assertIsInstance(self.manager.ipDockWidget.widget(), IPythonWidget)
        self.assertEqual(self.manager._workspace.dockWidgetArea(self.manager.ipDockWidget), QtCore.Qt.RightDockWidgetArea)

    def testUpdatePerspective(self):
        """
        """
        pass

    def testUpdateStatusBar(self):
        """
        """
        pass

    def testSetData(self):
        """
        """
        pass

    def testQuitApplication(self):
        """
        Test that the custom exit method is called on shutdown
        """
        self.manager._workspace.show()

        # Must mask sys.exit, otherwise the whole testing process stops.
        sys.exit = MagicMock()

        # Say No to the close dialog
        QMessageBox.question = MagicMock(return_value=QMessageBox.No)

        # Open, then close the manager
        self.manager.quitApplication()

        # See that the MessageBox method got called
        #self.assertTrue(QMessageBox.question.called)

        # Say Yes to the close dialog
        QMessageBox.question = MagicMock(return_value=QMessageBox.Yes)

        # Open, then close the manager
        self.manager.quitApplication()

        # See that the MessageBox method got called
        #self.assertTrue(QMessageBox.question.called)

    def testCheckUpdate(self):
        """
        Tests the SasView website version polling
        """
        self.manager.processVersion = MagicMock()
        version = {'version'     : '4.2.2',
                   'update_url'  : 'http://www.sasview.org/sasview.latestversion', 
                   'download_url': 'https://github.com/SasView/sasview/releases/tag/v4.2.2'}
        self.manager.checkUpdate()

        self.manager.processVersion.assert_called_with(version)

        pass

    def testProcessVersion(self):
        """
        Tests the version checker logic
        """
        # 1. version = 0.0.0
        version_info = {'version' : '0.0.0'}
        spy_status_update = QtSignalSpy(self.manager, self.manager.communicate.statusBarUpdateSignal)

        self.manager.processVersion(version_info)

        self.assertEqual(spy_status_update.count(), 1)
        message = 'Could not connect to the application server. Please try again later.'
        self.assertIn(message, str(spy_status_update.signal(index=0)))

        # 2. version < LocalConfig.__version__
        version_info = {'version' : '0.0.1'}
        spy_status_update = QtSignalSpy(self.manager, self.manager.communicate.statusBarUpdateSignal)

        self.manager.processVersion(version_info)

        self.assertEqual(spy_status_update.count(), 1)
        message = 'You have the latest version of SasView'
        self.assertIn(message, str(spy_status_update.signal(index=0)))

        # 3. version > LocalConfig.__version__
        version_info = {'version' : '999.0.0'}
        spy_status_update = QtSignalSpy(self.manager, self.manager.communicate.statusBarUpdateSignal)
        webbrowser.open = MagicMock()

        self.manager.processVersion(version_info)

        self.assertEqual(spy_status_update.count(), 1)
        message = 'Version 999.0.0 is available!'
        self.assertIn(message, str(spy_status_update.signal(index=0)))

        webbrowser.open.assert_called_with("https://github.com/SasView/sasview/releases")

        # 4. couldn't load version
        version_info = {}
        logging.error = MagicMock()
        spy_status_update = QtSignalSpy(self.manager, self.manager.communicate.statusBarUpdateSignal)

        self.manager.processVersion(version_info)

        # Retrieve and compare arguments of the mocked call
        message = "guiframe: could not get latest application version number"
        args, _ = logging.error.call_args
        self.assertIn(message, args[0])

        # Check the signal message
        message = 'Could not connect to the application server.'
        self.assertIn(message, str(spy_status_update.signal(index=0)))

    def testActions(self):
        """
        """
        pass

    #### FILE ####
    def testActionLoadData(self):
        """
        Menu File/Load Data File(s)
        """
        # Mock the system file open method
        QFileDialog.getOpenFileNames = MagicMock(return_value=('',''))

        # invoke the action
        self.manager.actionLoadData()

        # Test the getOpenFileName() dialog called once
        self.assertTrue(QFileDialog.getOpenFileNames.called)

    def testActionLoadDataFolder(self):
        """
        Menu File/Load Data Folder
        """
        # Mock the system file open method
        QFileDialog.getExistingDirectory = MagicMock(return_value=('',''))

        # invoke the action
        self.manager.actionLoad_Data_Folder()

        # Test the getOpenFileName() dialog called once
        self.assertTrue(QFileDialog.getExistingDirectory.called)

    #### VIEW ####
    def testActionHideToolbar(self):
        """
        Menu View/Hide Toolbar
        """
        # Need to display the main window to initialize the toolbar.
        self.manager._workspace.show()

        # Check the initial state
        self.assertFalse(self.manager._workspace.toolBar.isVisible())
        self.assertEqual('Show Toolbar', self.manager._workspace.actionHide_Toolbar.text())

        # Invoke action
        self.manager.actionHide_Toolbar()

        # Assure changes propagated correctly
        self.assertTrue(self.manager._workspace.toolBar.isVisible())
        self.assertEqual('Hide Toolbar', self.manager._workspace.actionHide_Toolbar.text())

        # Revert
        self.manager.actionHide_Toolbar()

        # Assure the original values are back
        self.assertFalse(self.manager._workspace.toolBar.isVisible())
        self.assertEqual('Show Toolbar', self.manager._workspace.actionHide_Toolbar.text())


    #### HELP ####
    # test when PyQt5 works with html
    def testActionDocumentation(self):
        """
        Menu Help/Documentation
        """
        webbrowser.open = MagicMock()

        # Invoke the action
        self.manager.actionDocumentation()

        # see that webbrowser open was attempted
        webbrowser.open.assert_called_once()


    def skip_testActionTutorial(self):
        """
        Menu Help/Tutorial
        """
        # Mock subprocess.Popen
        subprocess.Popen = MagicMock()

        tested_location = self.manager._tutorialLocation

        # Assure the filename is correct
        self.assertIn("Tutorial.pdf", tested_location)

        # Invoke the action
        self.manager.actionTutorial()

        # Check if popen() got called
        self.assertTrue(subprocess.Popen.called)

        #Check the popen() call arguments
        subprocess.Popen.assert_called_with([tested_location], shell=True)

    def testActionAcknowledge(self):
        """
        Menu Help/Acknowledge
        """
        self.manager.actionAcknowledge()

        # Check if the window is actually opened.
        self.assertTrue(self.manager.ackWidget.isVisible())
        self.assertIn("developers@sasview.org", self.manager.ackWidget.label_3.text())

    def testActionCheck_for_update(self):
        """
        Menu Help/Check for update
        """
        # Just make sure checkUpdate is called.
        self.manager.checkUpdate = MagicMock()

        self.manager.actionCheck_for_update()

        self.assertTrue(self.manager.checkUpdate.called)
             
       
if __name__ == "__main__":
    unittest.main()

