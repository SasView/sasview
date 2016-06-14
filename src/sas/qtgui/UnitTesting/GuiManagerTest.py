import sys
import unittest

from PyQt4.QtGui import *
from PyQt4.QtTest import QTest
from PyQt4.QtCore import *
from mock import MagicMock

# Local
from GuiManager import GuiManager
from UI.MainWindowUI import MainWindow

app = QApplication(sys.argv)

class GuiManagerTest(unittest.TestCase):
    '''Test the Main Window functionality'''
    def setUp(self):
        '''Create the tested object'''
        class MainSasViewWindow(MainWindow):
            # Main window of the application
            def __init__(self, reactor, parent=None):
                super(MainSasViewWindow, self).__init__(parent)
        
                # define workspace for dialogs.
                self.workspace = QWorkspace(self)
                self.setCentralWidget(self.workspace)

        self.manager = GuiManager(MainSasViewWindow(None), None)

    def tearDown(self):
        '''Destroy the GUI'''
        self.manager = None

    def testDefaults(self):
        '''Test the object in its default state'''
        pass
        
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

    def testSetData(self):
        """
        """
        pass

    def testActions(self):
        """
        """
        pass

    def testActionLoadData(self):
        """
        Menu File/Load Data File(s)
        """
        # Mock the system file open method
        QFileDialog.getOpenFileName = MagicMock(return_value=None)

        # invoke the action

        # Test the getOpenFileName() dialog called once
        #self.assertTrue(QtGui.QFileDialog.getOpenFileName.called)
        #QtGui.QFileDialog.getOpenFileName.assert_called_once()
        

    # test each action separately
       
if __name__ == "__main__":
    unittest.main()

