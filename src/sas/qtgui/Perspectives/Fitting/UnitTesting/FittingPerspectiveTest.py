import sys
import unittest
import webbrowser

from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import QtTest
from PyQt5 import QtCore
from unittest.mock import MagicMock

# set up import paths
import sas.qtgui.path_prepare

# Local
import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Perspectives.Fitting.FittingPerspective import FittingWindow

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)


class FittingPerspectiveTest(unittest.TestCase):
    '''Test the Fitting Perspective'''
    def setUp(self):
        class dummy_manager(object):
            def communicator(self):
                return GuiUtils.Communicate()
            communicate = GuiUtils.Communicate()

        '''Create the perspective'''
        self.widget = FittingWindow(dummy_manager())

    def tearDown(self):
        '''Destroy the perspective'''
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        '''Test the GUI in its default state'''
        self.assertIsInstance(self.widget, QtWidgets.QWidget)
        self.assertIn("Fit panel", self.widget.windowTitle())
        self.assertEqual(self.widget.optimizer, "Levenberg-Marquardt")
        self.assertEqual(len(self.widget.tabs), 1)
        self.assertEqual(self.widget.maxIndex, 1)
        self.assertEqual(self.widget.getTabName(), "FitPage1")

    def testAddTab(self):
        '''Add a tab and test it'''

        # Add an empty tab
        self.widget.addFit(None)
        self.assertEqual(len(self.widget.tabs), 2)
        self.assertEqual(self.widget.getTabName(), "FitPage2")
        self.assertEqual(self.widget.maxIndex, 2)
        # Add an empty batch tab
        self.widget.addFit(None, is_batch=True)
        self.assertEqual(len(self.widget.tabs), 3)
        self.assertEqual(self.widget.getTabName(2), "BatchPage3")
        self.assertEqual(self.widget.maxIndex, 3)

    def testAddCSTab(self):
        ''' Add a constraint/simult tab'''
        self.widget.addConstraintTab()
        self.assertEqual(len(self.widget.tabs), 2)
        self.assertEqual(self.widget.getCSTabName(), "Const. & Simul. Fit")

    def testResetTab(self):
        ''' Remove data from last tab'''
        self.assertEqual(len(self.widget.tabs), 1)
        self.assertEqual(self.widget.getTabName(), "FitPage1")
        self.assertEqual(self.widget.maxIndex, 1)

        # Attempt to remove the last tab
        self.widget.resetTab(0)

        # see that the tab didn't disappear, just changed the name/id
        self.assertEqual(len(self.widget.tabs), 1)
        self.assertEqual(self.widget.getTabName(), "FitPage2")
        self.assertEqual(self.widget.maxIndex, 2)

        # Now, add data
        data = Data1D(x=[1,2], y=[1,2])
        GuiUtils.dataFromItem = MagicMock(return_value=data)
        item = QtGui.QStandardItem("test")
        self.widget.setData([item])
        # Assert data is on widget
        self.assertEqual(len(self.widget.tabs[0].all_data), 1)
        # Reset the tab
        self.widget.resetTab(0)
        # See that the tab contains data no more
        self.assertEqual(len(self.widget.tabs[0].all_data), 0)

    def testCloseTab(self):
        '''Delete a tab and test'''
        # Add an empty tab
        self.widget.addFit(None)

        # Remove the original tab
        self.widget.tabCloses(1)
        self.assertEqual(len(self.widget.tabs), 1)
        self.assertEqual(self.widget.maxIndex, 2)
        self.assertEqual(self.widget.getTabName(), "FitPage2")

        # Attemtp to remove the last tab
        self.widget.tabCloses(1)
        # The tab should still be there
        self.assertEqual(len(self.widget.tabs), 1)
        self.assertEqual(self.widget.maxIndex, 3)
        self.assertEqual(self.widget.getTabName(), "FitPage3")

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

    def testSetBatchData(self):
        ''' Assure that setting batch data is correct'''

        # Mock the datafromitem() call from FittingWidget
        data1 = Data1D(x=[1,2], y=[1,2])
        data2 = Data1D(x=[1,2], y=[1,2])
        data_batch = [data1, data2]
        GuiUtils.dataFromItem = MagicMock(return_value=data1)

        item = QtGui.QStandardItem("test")
        self.widget.setData([item, item], is_batch=True)

        # First tab should not accept data
        self.assertEqual(len(self.widget.tabs), 2)

        # Add another set of data
        self.widget.setData([item, item], is_batch=True)

        # Now we should have two batch tabs
        self.assertEqual(len(self.widget.tabs), 3)

        # Check the names of the new tabs
        self.assertEqual(self.widget.tabText(1), "BatchPage1")
        self.assertEqual(self.widget.tabText(2), "BatchPage2")

if __name__ == "__main__":
    unittest.main()
