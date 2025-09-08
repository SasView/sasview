import logging
import subprocess
import sys
import webbrowser

import pytest
from PySide6 import QtCore
from PySide6.QtWidgets import QDockWidget, QFileDialog, QMdiArea, QMessageBox, QTextBrowser

# Local
from sas.qtgui.MainWindow.DataExplorer import DataExplorerWindow
from sas.qtgui.MainWindow.GuiManager import Acknowledgements, GuiManager
from sas.qtgui.MainWindow.MainWindow import MainSasViewWindow
from sas.qtgui.UnitTesting.TestUtils import QtSignalSpy
from sas.qtgui.Utilities.HidableDialog import HidableDialog
from sas.qtgui.Utilities.IPythonWidget import IPythonWidget
from sas.system import config


class GuiManagerTest:
    '''Test the Main Window functionality'''

    def __init__(self):
        config.override_with_defaults() # Disable saving of test file
        config.LAST_WHATS_NEW_HIDDEN_VERSION = "999.999.999" # Give a very large version number

    @pytest.fixture(autouse=True)
    def manager(self, qapp):
        '''Create/Destroy the GUI Manager'''
        class MainWindow(MainSasViewWindow):
            # Main window of the application

            def __init__(self,  parent=None):
                super(MainWindow, self).__init__( parent)

                # define workspace for dialogs.
                self.workspace = QMdiArea(self)
                self.setCentralWidget(self.workspace)

        m = GuiManager(MainWindow(None))

        yield m

    def testDefaults(self, manager):
        """
        Test the object in its default state
        """
        assert isinstance(manager.filesWidget, DataExplorerWindow)
        assert isinstance(manager.dockedFilesWidget, QDockWidget)
        assert isinstance(manager.dockedFilesWidget.widget(), DataExplorerWindow)
        assert manager._workspace.dockWidgetArea(manager.dockedFilesWidget) == QtCore.Qt.LeftDockWidgetArea

        assert isinstance(manager.logDockWidget, QDockWidget)
        assert isinstance(manager.logDockWidget.widget(), QTextBrowser)
        assert manager._workspace.dockWidgetArea(manager.logDockWidget) == QtCore.Qt.BottomDockWidgetArea

        assert isinstance(manager.ackWidget, Acknowledgements)

    def skip_testLogging(self, manager):
        """
        Test logging of stdout, stderr and log messages
        """
        # See if the log window is empty
        assert manager.logDockWidget.widget().toPlainText() == ""

        # Now, send some message to stdout.
        # We are in the MainWindow scope, so simple 'print' will work
        message = "from stdout"
        print(message)
        assert message in manager.logDockWidget.widget().toPlainText()

        # Send some message to stderr
        message = "from stderr"
        sys.stderr.write(message)
        assert message in manager.logDockWidget.widget().toPlainText()

        # And finally, send a log message
        import logging
        message = "from logging"
        message_logged = "ERROR: " + message
        logging.error(message)
        assert message_logged in manager.logDockWidget.widget().toPlainText()

    @pytest.mark.skip("2022-09 already broken - generates runtime error")
    # IPythonWidget.py:38: RuntimeWarning: coroutine 'InteractiveShell.run_code' was never awaited
    def testConsole(self, manager):
        """
        Test the docked QtConsole
        """
        # Invoke the console action
        manager.actionPython_Shell_Editor()

        # Test the widegt properties
        assert isinstance(manager.ipDockWidget, QDockWidget)
        assert isinstance(manager.ipDockWidget.widget(), IPythonWidget)
        assert manager._workspace.dockWidgetArea(manager.ipDockWidget) == QtCore.Qt.RightDockWidgetArea

    def testUpdatePerspective(self, manager):
        """
        """
        pass

    def testUpdateStatusBar(self, manager):
        """
        """
        pass

    def testSetData(self, manager):
        """
        """
        pass

    def testQuitApplication(self, manager, mocker):
        """
        Test that the custom exit method is called on shutdown
        """
        manager._workspace.show()

        # Must mask sys.exit, otherwise the whole testing process stops.
        mocker.patch.object(sys, 'exit')

        # Say No to the close dialog
        mocker.patch.object(QMessageBox, 'question', return_value=QMessageBox.No)
        mocker.patch.object(HidableDialog, 'exec', return_value=0)

        # Open, then close the manager
        manager.quitApplication()

        # See that the HidableDialog.exec method got called
        assert HidableDialog.exec.called

        # Say Yes to the close dialog
        mocker.patch.object(QMessageBox, 'question', return_value=QMessageBox.Yes)
        mocker.patch.object(HidableDialog, 'exec', return_value=1)

        # Open, then close the manager
        manager.quitApplication()

        # See that the HidableDialog.exec method got called
        assert HidableDialog.exec.called

    @pytest.mark.xfail(reason="2022-09 already broken")
    def testCheckUpdate(self, manager, mocker):
        """
        Tests the SasView website version polling
        """
        mocker.patch.object(manager, 'processVersion')
        version = {'version'     : '5.0.2',
                   'update_url'  : 'http://www.sasview.org/sasview.latestversion',
                   'download_url': 'https://github.com/SasView/sasview/releases/tag/v5.0.2'}
        manager.checkUpdate()

        manager.processVersion.assert_called_with(version)

        pass

    def testProcessVersion(self, manager, mocker):
        """
        Tests the version checker logic
        """
        # 1. version = 0.0.0
        version_info = {'version' : '0.0.0'}
        spy_status_update = QtSignalSpy(manager, manager.communicate.statusBarUpdateSignal)

        manager.processVersion(version_info)

        assert spy_status_update.count() == 1
        message = 'Could not connect to the application server. Please try again later.'
        assert message in str(spy_status_update.signal(index=0))

        # 2. version < config.__version__
        version_info = {'version' : '0.0.1'}
        spy_status_update = QtSignalSpy(manager, manager.communicate.statusBarUpdateSignal)

        manager.processVersion(version_info)

        assert spy_status_update.count() == 1
        message = 'You have the latest version'
        assert message in str(spy_status_update.signal(index=0))

        # 3. version > LocalConfig.__version__
        version_info = {'version' : '999.0.0'}
        spy_status_update = QtSignalSpy(manager, manager.communicate.statusBarUpdateSignal)
        mocker.patch.object(webbrowser, 'open')

        manager.processVersion(version_info)

        assert spy_status_update.count() == 1
        message = 'Version 999.0.0 is available!'
        assert message in str(spy_status_update.signal(index=0))

        webbrowser.open.assert_called_with("https://github.com/SasView/sasview/releases/latest")

        # 4. couldn't load version
        version_info = {}
        mocker.patch.object(logging, 'error')
        spy_status_update = QtSignalSpy(manager, manager.communicate.statusBarUpdateSignal)

        manager.processVersion(version_info)

        # Retrieve and compare arguments of the mocked call
        message = "guiframe: could not get latest application version number"
        args, _ = logging.error.call_args
        assert message in args[0]

        # Check the signal message
        message = 'Could not connect to the application server.'
        assert message in str(spy_status_update.signal(index=0))

    def testActions(self, manager):
        """
        """
        pass

    #### FILE ####
    def testActionLoadData(self, manager, mocker):
        """
        Menu File/Load Data File(s)
        """
        # Mock the system file open method
        mocker.patch.object(QFileDialog, 'getOpenFileNames', return_value=('',''))

        # invoke the action
        manager.actionLoadData()

        # Test the getOpenFileName() dialog called once
        assert QFileDialog.getOpenFileNames.called

    def testActionLoadDataFolder(self, manager, mocker):
        """
        Menu File/Load Data Folder
        """
        # Mock the system file open method
        mocker.patch.object(QFileDialog, 'getExistingDirectory', return_value=('',''))

        # invoke the action
        manager.actionLoad_Data_Folder()

        # Test the getOpenFileName() dialog called once
        assert QFileDialog.getExistingDirectory.called

    #### VIEW ####
    @pytest.mark.xfail(reason="2022-10 - broken by config refactoring")
    # default show/hide for toolbar (accidentally?) changed during
    # refactoring of config code in a32de61ba038da9a1435c15875d6ce764262cea9
    def testActionHideToolbar(self, manager):
        """
        Menu View/Hide Toolbar
        """
        # Need to display the main window to initialize the toolbar.
        manager._workspace.show()

        # Check the initial state
        assert not manager._workspace.toolBar.isVisible()
        assert manager._workspace.actionHide_Toolbar.text() == 'Show Toolbar'

        # Invoke action
        manager.actionHide_Toolbar()

        # Assure changes propagated correctly
        assert manager._workspace.toolBar.isVisible()
        assert manager._workspace.actionHide_Toolbar.text() == 'Hide Toolbar'

        # Revert
        manager.actionHide_Toolbar()

        # Assure the original values are back
        assert not manager._workspace.toolBar.isVisible()
        assert manager._workspace.actionHide_Toolbar.text() == 'Show Toolbar'


    #### HELP ####
    # test when PyQt5 works with html
    def testActionDocumentation(self, manager, mocker):
        """
        Menu Help/Documentation
        """
        mocker.patch.object(webbrowser, 'open')

        # Invoke the action
        manager.actionDocumentation()

        # see that webbrowser open was attempted
        webbrowser.open.assert_called_once()


    def skip_testActionTutorial(self, manager, mocker):
        """
        Menu Help/Tutorial
        """
        # Mock subprocess.Popen
        mocker.patch.object(subprocess, 'Popen')

        tested_location = manager._tutorialLocation

        # Assure the filename is correct
        assert "Tutorial.pdf" in tested_location

        # Invoke the action
        manager.actionTutorial()

        # Check if popen() got called
        assert subprocess.Popen.called

        #Check the popen() call arguments
        subprocess.Popen.assert_called_with([tested_location], shell=True)

    def testActionAcknowledge(self, manager):
        """
        Menu Help/Acknowledge
        """
        manager.actionAcknowledge()

        # Check if the window is actually opened.
        assert manager.ackWidget.isVisible()
        assert "developers@sasview.org" in manager.ackWidget.label_3.text()

    def testActionCheck_for_update(self, manager, mocker):
        """
        Menu Help/Check for update
        """
        # Just make sure checkUpdate is called.
        mocker.patch.object(manager, 'checkUpdate')

        manager.actionCheck_for_update()

        assert manager.checkUpdate.called
