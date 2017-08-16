import sys
import unittest
import webbrowser

from PyQt4 import QtGui
from PyQt4 import QtTest
from PyQt4 import QtCore
from mock import MagicMock

# set up import paths
import sas.qtgui.path_prepare

# Local
import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Perspectives.Fitting.FittingPerspective import FittingWindow

app = QtGui.QApplication(sys.argv)

class FittingPerspectiveTest(unittest.TestCase):
    '''Test the Fitting Perspective'''
    def setUp(self):
        class dummy_manager(object):
            def communicator(self):
                return GuiUtils.Communicate()
            def communicate(self):
                return GuiUtils.Communicate()

        '''Create the perspective'''
        self.widget = FittingWindow(dummy_manager())

    def tearDown(self):
        '''Destroy the perspective'''
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        '''Test the GUI in its default state'''
        self.assertIsInstance(self.widget, QtGui.QWidget)
        self.assertIn("Fit panel", self.widget.windowTitle())
        self.assertEqual(self.widget.optimizer, "Levenberg-Marquardt")
        self.assertEqual(len(self.widget.tabs), 1)
        self.assertEqual(self.widget.maxIndex, 1)
        self.assertEqual(self.widget.tabName(), "FitPage1")

    def testAddTab(self):
        '''Add a tab and test it'''

        # Add an empty tab
        self.widget.addFit(None)
        self.assertEqual(len(self.widget.tabs), 2)
        self.assertEqual(self.widget.tabName(), "FitPage2")
        self.assertEqual(self.widget.maxIndex, 2)

    def testCloseTab(self):
        '''Delete a tab and test'''
        # Add an empty tab
        self.widget.addFit(None)

        # Remove the original tab
        self.widget.tabCloses(1)
        self.assertEqual(len(self.widget.tabs), 1)
        self.assertEqual(self.widget.maxIndex, 2)
        self.assertEqual(self.widget.tabName(), "FitPage2")

        # Attemtp to remove the last tab
        self.widget.tabCloses(1)
        # The tab should still be there
        self.assertEqual(len(self.widget.tabs), 1)
        self.assertEqual(self.widget.maxIndex, 3)
        self.assertEqual(self.widget.tabName(), "FitPage3")

    def testAllowBatch(self):
        '''Assure the perspective allows multiple datasets'''
        self.assertTrue(self.widget.allowBatch())

    def testSetData(self):
        ''' Assure that setting data is correct'''
        with self.assertRaises(AssertionError):
            self.widget.setData(None)

        with self.assertRaises(AttributeError):
            self.widget.setData("BOOP")

        # Mock the datafromitem() call from FittingWidget
        data = Data1D(x=[1,2], y=[1,2])
        GuiUtils.dataFromItem = MagicMock(return_value=data)

        item = QtGui.QStandardItem("test")
        self.widget.setData([item])

        # First tab should accept data
        self.assertEqual(len(self.widget.tabs), 1)

        # Add another set of data
        self.widget.setData([item])

        # Now we should have two tabs
        self.assertEqual(len(self.widget.tabs), 2)

        # Add two more items in a list
        self.widget.setData([item, item])

        # Check for 4 tabs
        self.assertEqual(len(self.widget.tabs), 4)


if __name__ == "__main__":
    unittest.main()
