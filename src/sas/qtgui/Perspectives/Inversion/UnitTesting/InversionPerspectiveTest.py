import time
import unittest
from unittest.mock import MagicMock

from PyQt5 import QtGui, QtWidgets

from sas.qtgui.Utilities.GuiUtils import *
from sas.qtgui.Perspectives.Inversion.InversionPerspective import InversionWindow
from sas.qtgui.Perspectives.Inversion.InversionUtils import WIDGETS
from sas.qtgui.Plotting.PlotterData import Data1D

import sas.qtgui.Utilities.GuiUtils as GuiUtils

#if not QtWidgets.QApplication.instance():
app = QtWidgets.QApplication(sys.argv)


class dummy_manager(object):
    HELP_DIRECTORY_LOCATION = "html"
    communicate = Communicate()

    def communicator(self):
        return self.communicate


class InversionTest(unittest.TestCase):
    """ Test the Inversion Perspective GUI """

    def setUp(self):
        """ Create the InversionWindow """
        self.widget = InversionWindow(dummy_manager())
        self.widget.show()
        self.fakeData1 = GuiUtils.HashableStandardItem("A")
        self.fakeData2 = GuiUtils.HashableStandardItem("B")
        reference_data1 = Data1D(x=[0.1, 0.2], y=[0.0, 0.0], dy=[0.0, 0.0])
        reference_data1.filename = "Test A"
        reference_data2 = Data1D(x=[0.1, 0.2], y=[0.0, 0.0], dy=[0.0, 0.0])
        reference_data2.filename = "Test B"
        GuiUtils.updateModelItem(self.fakeData1, reference_data1)
        GuiUtils.updateModelItem(self.fakeData2, reference_data2)

    def tearDown(self):
        """ Destroy the InversionWindow """
        self.widget.setClosable(False)
        self.widget.close()
        self.widget = None

    def removeAllData(self):
        """ Cleanup method to restore widget to its base state """
        if len(self.widget.dataList) > 0:
            remove_me = list(self.widget._dataList.keys())
            self.widget.removeData(remove_me)

    def baseGUIState(self):
        """ Testing base state of Inversion """
        # base class information
        self.assertIsInstance(self.widget, QtWidgets.QWidget)
        self.assertEqual(self.widget.windowTitle(), "P(r) Inversion Perspective")
        self.assertFalse(self.widget.isClosable())
        self.assertFalse(self.widget.isCalculating)
        # mapper
        self.assertIsInstance(self.widget.mapper, QtWidgets.QDataWidgetMapper)
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
        self.assertEqual(self.widget.model.columnCount(), 1)
        self.assertEqual(self.widget.mapper.model(), self.widget.model)
        # buttons
        self.assertFalse(self.widget.calculateThisButton.isEnabled())
        self.assertFalse(self.widget.removeButton.isEnabled())
        self.assertTrue(self.widget.stopButton.isEnabled())
        self.assertFalse(self.widget.stopButton.isVisible())
        self.assertFalse(self.widget.regConstantSuggestionButton.isEnabled())
        self.assertFalse(self.widget.noOfTermsSuggestionButton.isEnabled())
        self.assertFalse(self.widget.explorerButton.isEnabled())
        self.assertTrue(self.widget.helpButton.isEnabled())
        # extra windows and charts
        self.assertIsNone(self.widget.dmaxWindow)
        self.assertIsNone(self.widget.prPlot)
        self.assertIsNone(self.widget.dataPlot)
        # threads
        self.assertIsNone(self.widget.calcThread)
        self.assertIsNone(self.widget.estimationThread)
        self.assertIsNone(self.widget.estimationThreadNT)

    def baseBatchState(self):
        """ Testing the base batch fitting state """
        self.assertTrue(self.widget.allowBatch())
        self.assertFalse(self.widget.isBatch)
        self.assertIsNone(self.widget.batchResultsWindow)
        self.assertFalse(self.widget.calculateAllButton.isEnabled())
        self.assertEqual(len(self.widget.batchResults), 0)
        self.assertEqual(len(self.widget.batchComplete), 0)
        self.widget.closeBatchResults()
        self.assertIsNone(self.widget.batchResultsWindow)

    def zeroDataSetState(self):
        """ Testing the base data state of the GUI """
        # data variables
        self.assertIsNone(self.widget._data)
        self.assertEqual(len(self.widget._dataList), 0)
        self.assertEqual(self.widget.nTermsSuggested, 10)
        # inputs
        self.assertEqual(len(self.widget.dataList), 0)
        self.assertEqual(self.widget.backgroundInput.text(), "0.0")
        self.assertEqual(self.widget.minQInput.text(), "")
        self.assertEqual(self.widget.maxQInput.text(), "")
        self.assertEqual(self.widget.regularizationConstantInput.text(), "0.0001")
        self.assertEqual(self.widget.noOfTermsInput.text(), "10")
        self.assertEqual(self.widget.maxDistanceInput.text(), "140.0")

    def oneDataSetState(self):
        """ Testing the base data state of the GUI """
        # Test the globals after first sent
        self.assertEqual(len(self.widget._dataList), 1)
        self.assertEqual(self.widget.dataList.count(), 1)
        # See that the buttons are now enabled properly
        self.widget.enableButtons()
        self.assertFalse(self.widget.calculateAllButton.isEnabled())
        self.assertTrue(self.widget.calculateThisButton.isEnabled())
        self.assertTrue(self.widget.removeButton.isEnabled())
        self.assertTrue(self.widget.explorerButton.isEnabled())

    def twoDataSetState(self):
        """ Testing the base data state of the GUI """
        # Test the globals after first sent
        self.assertEqual(len(self.widget._dataList), 2)
        self.assertEqual(self.widget.dataList.count(), 2)
        # See that the buttons are now enabled properly
        self.widget.enableButtons()
        self.assertTrue(self.widget.calculateThisButton.isEnabled())
        self.assertTrue(self.widget.calculateAllButton.isEnabled())
        self.assertTrue(self.widget.removeButton.isEnabled())
        self.assertTrue(self.widget.explorerButton.isEnabled())

    def testDefaults(self):
        """ Test the GUI in its default state """
        self.baseGUIState()
        self.zeroDataSetState()
        self.baseBatchState()
        self.removeAllData()

    def testAllowBatch(self):
        """ Batch P(r) Tests """
        self.baseBatchState()
        self.widget.setData([self.fakeData1])
        self.oneDataSetState()
        self.widget.setData([self.fakeData2])
        self.twoDataSetState()
        self.widget.calculateAllButton.click()
        self.assertTrue(self.widget.isCalculating)
        self.assertTrue(self.widget.isBatch)
        self.assertTrue(self.widget.stopButton.isVisible())
        self.assertTrue(self.widget.stopButton.isEnabled())
        self.assertIsNotNone(self.widget.batchResultsWindow)
        self.assertTrue(self.widget.batchResultsWindow.cmdHelp.isEnabled())
        self.assertEqual(self.widget.batchResultsWindow.tblParams.columnCount(), 9)
        self.assertEqual(self.widget.batchResultsWindow.tblParams.rowCount(), 2)
        # Test stop button
        self.widget.stopButton.click()
        self.assertTrue(self.widget.batchResultsWindow.isVisible())
        self.assertFalse(self.widget.stopButton.isVisible())
        self.assertTrue(self.widget.stopButton.isEnabled())
        self.assertFalse(self.widget.isBatch)
        self.assertFalse(self.widget.isCalculating)
        self.widget.batchResultsWindow.close()
        self.assertIsNone(self.widget.batchResultsWindow)
        # Last test
        self.removeAllData()
        self.baseBatchState()

    def testSetData(self):
        """ Check if sending data works as expected """
        self.zeroDataSetState()
        self.widget.setData([self.fakeData1])
        self.oneDataSetState()
        self.widget.setData([self.fakeData1])
        self.oneDataSetState()
        self.widget.setData([self.fakeData2])
        self.twoDataSetState()
        self.removeAllData()
        self.zeroDataSetState()
        self.removeAllData()

    def testRemoveData(self):
        """ Test data removal from widget """
        self.widget.setData([self.fakeData1, self.fakeData2])
        self.twoDataSetState()
        # Remove data 0
        self.widget.removeData()
        self.oneDataSetState()
        self.removeAllData()

    def testClose(self):
        """ Test methods related to closing the window """
        self.assertFalse(self.widget.isClosable())
        self.widget.close()
        self.assertTrue(self.widget.isMinimized())
        self.assertIsNone(self.widget.dmaxWindow)
        self.assertIsNone(self.widget.batchResultsWindow)
        self.widget.setClosable(False)
        self.assertFalse(self.widget.isClosable())
        self.widget.close()
        self.assertTrue(self.widget.isMinimized())
        self.widget.setClosable(True)
        self.assertTrue(self.widget.isClosable())
        self.widget.setClosable()
        self.assertTrue(self.widget.isClosable())
        self.removeAllData()

    def testGetNFunc(self):
        """ test nfunc getter """
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
            self.assertEqual(cm.output, ['ERROR:sas.qtgui.Perspectives.Inversion.InversionPerspective:Incorrect number of terms specified: '])
        self.assertEqual(self.widget.getNFunc(), 10)
        # string
        with self.assertLogs(level='ERROR') as cm:
            self.widget.noOfTermsInput.setText("Nordvest Pizza")
            n = self.widget.getNFunc()
            self.assertEqual(cm.output, ['ERROR:sas.qtgui.Perspectives.Inversion.InversionPerspective:Incorrect number of terms specified: Nordvest Pizza'])
        self.assertEqual(self.widget.getNFunc(), 10)
        self.removeAllData()

    def testSetCurrentData(self):
        """ test current data setter """
        self.widget.setData([self.fakeData1, self.fakeData2])

        # Check that the current data is reference2
        self.assertEqual(self.widget._data, self.fakeData2)
        # Set the ref to none
        self.widget.setCurrentData(None)
        self.assertEqual(self.widget._data, self.fakeData2)
        # Set the ref to wrong type
        with self.assertRaises(AttributeError):
            self.widget.setCurrentData("Afandi Kebab")
        # Set the reference to ref1
        self.widget.setCurrentData(self.fakeData1)
        self.assertEqual(self.widget._data, self.fakeData1)
        self.removeAllData()

    def testModelChanged(self):
        """ Test setting the input and the model and vice-versa """
        # Initial values
        self.assertEqual(self.widget._calculator.get_dmax(), 140.0)
        self.assertEqual(self.widget._calculator.get_qmax(), -1.0)
        self.assertEqual(self.widget._calculator.get_qmin(), -1.0)
        self.assertEqual(self.widget._calculator.slit_height, 0.0)
        self.assertEqual(self.widget._calculator.slit_width, 0.0)
        self.assertEqual(self.widget._calculator.alpha, 0.0001)
        # Set new values
        self.widget.maxDistanceInput.setText("1.0")
        self.widget.maxQInput.setText("3.0")
        self.widget.minQInput.setText("5.0")
        self.widget.slitHeightInput.setText("7.0")
        self.widget.slitWidthInput.setText("9.0")
        self.widget.regularizationConstantInput.setText("11.0")
        # Check new values
        self.assertEqual(self.widget._calculator.get_dmax(), 1.0)
        self.assertEqual(self.widget._calculator.get_qmax(), 3.0)
        self.assertEqual(self.widget._calculator.get_qmin(), 5.0)
        self.assertEqual(self.widget._calculator.slit_height, 7.0)
        self.assertEqual(self.widget._calculator.slit_width, 9.0)
        self.assertEqual(self.widget._calculator.alpha, 11.0)
        # Change model directly
        self.widget.model.setItem(WIDGETS.W_MAX_DIST, QtGui.QStandardItem("2.0"))
        self.widget.model.setItem(WIDGETS.W_QMIN, QtGui.QStandardItem("4.0"))
        self.widget.model.setItem(WIDGETS.W_QMAX, QtGui.QStandardItem("6.0"))
        self.widget.model.setItem(WIDGETS.W_SLIT_HEIGHT, QtGui.QStandardItem("8.0"))
        self.widget.model.setItem(WIDGETS.W_SLIT_WIDTH, QtGui.QStandardItem("10.0"))
        self.widget.model.setItem(WIDGETS.W_REGULARIZATION, QtGui.QStandardItem("12.0"))
        # Check values
        self.assertEqual(self.widget._calculator.get_dmax(), 2.0)
        self.assertEqual(self.widget._calculator.get_qmin(), 4.0)
        self.assertEqual(self.widget._calculator.get_qmax(), 6.0)
        self.assertEqual(self.widget._calculator.slit_height, 8.0)
        self.assertEqual(self.widget._calculator.slit_width, 10.0)
        self.assertEqual(self.widget._calculator.alpha, 12.0)
        self.removeAllData()

    def testOpenExplorerWindow(self):
        """ open Dx window """
        self.assertIsNone(self.widget.dmaxWindow)
        self.assertFalse(self.widget.explorerButton.isEnabled())
        self.widget.openExplorerWindow()
        self.assertIsNotNone(self.widget.dmaxWindow)
        self.assertTrue(self.widget.dmaxWindow.isVisible())
        self.assertTrue(self.widget.dmaxWindow.windowTitle() == "Dₐₓ Explorer")


if __name__ == "__main__":
    unittest.main()
