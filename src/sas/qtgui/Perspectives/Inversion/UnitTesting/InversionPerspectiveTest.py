import sys
import unittest
import logging
from unittest.mock import MagicMock

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtTest import QTest
from PyQt5 import QtCore

import sas.qtgui.path_prepare
from sas.qtgui.Perspectives.Inversion.InversionPerspective import InversionWindow
from sas.sascalc.dataloader.loader import Loader
from sas.qtgui.Plotting.PlotterData import Data1D

from sas.qtgui.MainWindow.DataManager import DataManager
import sas.qtgui.Utilities.LocalConfig
import sas.qtgui.Utilities.GuiUtils as GuiUtils

#if not QtWidgets.QApplication.instance():
app = QtWidgets.QApplication(sys.argv)

class InversionTest(unittest.TestCase):
    '''Test the Inversion Interface'''
    def setUp(self):
        '''Create the InversionWindow'''
        self.widget = InversionWindow(None)

    def tearDown(self):
        '''Destroy the InversionWindow'''
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        '''Test the GUI in its default state'''
        self.assertIsInstance(self.widget, QtWidgets.QWidget)
        self.assertEqual(self.widget.windowTitle(), "P(r) Inversion Perspective")
        self.assertEqual(self.widget.model.columnCount(), 1)
        self.assertEqual(self.widget.model.rowCount(), 22)
        self.assertFalse(self.widget.calculateAllButton.isEnabled())
        self.assertFalse(self.widget.calculateThisButton.isEnabled())
        self.assertIsInstance(self.widget.mapper, QtWidgets.QDataWidgetMapper)
        # make sure the model is assigned and at least the data is mapped
        self.assertEqual(self.widget.mapper.model(), self.widget.model)
        self.assertNotEqual(self.widget.mapper.mappedSection(self.widget.dataList), -1)

        # validators
        self.assertIsInstance(self.widget.noOfTermsInput.validator(), QtGui.QIntValidator)
        self.assertIsInstance(self.widget.regularizationConstantInput.validator(), QtGui.QDoubleValidator)
        self.assertIsInstance(self.widget.maxDistanceInput.validator(), QtGui.QDoubleValidator)
        self.assertIsInstance(self.widget.minQInput.validator(), QtGui.QDoubleValidator)
        self.assertIsInstance(self.widget.maxQInput.validator(), QtGui.QDoubleValidator)
        self.assertIsInstance(self.widget.slitHeightInput.validator(), QtGui.QDoubleValidator)
        self.assertIsInstance(self.widget.slitWidthInput.validator(), QtGui.QDoubleValidator)

        # model
        self.assertEqual(self.widget.model.rowCount(), 22)

    def testSetData(self):
        ''' Check if sending data works as expected'''
        # Create dummy data
        item1 = GuiUtils.HashableStandardItem("A")
        item2 = GuiUtils.HashableStandardItem("B")
        reference_data = Data1D(x=[0.1, 0.2], y=[0.0, 0.0], dy=[0.0, 0.0])
        GuiUtils.updateModelItem(item1, [reference_data])
        GuiUtils.updateModelItem(item2, [reference_data])
        self.widget.performEstimate = MagicMock()
        self.widget.setData([item1, item2])

        # Test the globals
        self.assertEqual(len(self.widget._data_list), 2)
        self.assertEqual(len(self.widget.data_plot_list), 2)
        self.assertEqual(len(self.widget.pr_plot_list), 2)
        self.assertEqual(self.widget.dataList.count(), 2)

        # See that the buttons are now enabled
        self.assertTrue(self.widget.calculateAllButton.isEnabled())
        self.assertTrue(self.widget.calculateThisButton.isEnabled())
        self.assertTrue(self.widget.removeButton.isEnabled())
        self.assertTrue(self.widget.explorerButton.isEnabled())

    def notestRemoveData(self):
        ''' Test data removal from widget '''
        # Create dummy data
        item1 = GuiUtils.HashableStandardItem("A")
        item2 = GuiUtils.HashableStandardItem("B")
        reference_data1 = Data1D(x=[0.1, 0.2], y=[0.0, 0.0], dy=[0.0, 0.0])
        reference_data2 = Data1D(x=[0.1, 0.2], y=[0.0, 0.0], dy=[0.0, 0.0])
        GuiUtils.updateModelItem(item1, [reference_data1])
        GuiUtils.updateModelItem(item2, [reference_data2])
        self.widget.performEstimate = MagicMock()
        self.widget.setData([item1, item2])

        # Remove data 0
        self.widget.removeData()

        # Test the globals
        self.assertEqual(len(self.widget._data_list), 1)
        self.assertEqual(len(self.widget.data_plot_list), 1)
        self.assertEqual(len(self.widget.pr_plot_list), 1)
        self.assertEqual(self.widget.dataList.count(), 1)


    def testAllowBatch(self):
        ''' Batch is allowed for this perspective'''
        self.assertTrue(self.widget.allowBatch())

    def notestModelChanged(self):
        ''' test the model update '''
        # unfinished functionality
        pass

    def notestHelp(self):
        ''' test help widget show '''
        # unfinished functionality
        pass

    def testOpenExplorerWindow(self):
        ''' open Dx window '''
        self.widget.openExplorerWindow()
        self.assertTrue(self.widget.dmaxWindow.isVisible())

    def testGetNFunc(self):
        ''' test nfunc getter '''
        # Float
        self.widget.noOfTermsInput.setText("10.0")
        self.assertEqual(self.widget.getNFunc(), 10)
        # Int
        self.widget.noOfTermsInput.setText("980")
        self.assertEqual(self.widget.getNFunc(), 980)
        # Empty
        with self.assertLogs(level='ERROR') as cm:
            self.widget.noOfTermsInput.setText("")
            n = self.widget.getNFunc()
            self.assertEqual(cm.output, ['ERROR:root:Incorrect number of terms specified: '])
        self.assertEqual(self.widget.getNFunc(), 10)
        # string
        with self.assertLogs(level='ERROR') as cm:
            self.widget.noOfTermsInput.setText("Nordvest Pizza")
            n = self.widget.getNFunc()
            self.assertEqual(cm.output, ['ERROR:root:Incorrect number of terms specified: Nordvest Pizza'])
        self.assertEqual(self.widget.getNFunc(), 10)

    def testSetCurrentData(self):
        ''' test current data setter '''
        # Create dummy data
        item1 = GuiUtils.HashableStandardItem("A")
        item2 = GuiUtils.HashableStandardItem("B")
        reference_data1 = Data1D(x=[0.1, 0.2], y=[0.0, 0.0], dy=[0.0, 0.0])
        reference_data2 = Data1D(x=[0.1, 0.2], y=[0.0, 0.0], dy=[0.0, 0.0])
        GuiUtils.updateModelItem(item1, [reference_data1])
        GuiUtils.updateModelItem(item2, [reference_data2])
        self.widget.performEstimate = MagicMock()
        self.widget.setData([item1, item2])

        # Check that the current data is reference2
        self.assertEqual(self.widget._data, item2)

        # Set the ref to none
        self.widget.setCurrentData(None)
        self.assertEqual(self.widget._data, item2)

        # Set the ref to wrong type
        with self.assertRaises(AttributeError):
            self.widget.setCurrentData("Afandi Kebab")

        # Set the reference to ref2
        self.widget.setCurrentData(item1)
        self.assertEqual(self.widget._data, item1)

if __name__ == "__main__":
    unittest.main()
