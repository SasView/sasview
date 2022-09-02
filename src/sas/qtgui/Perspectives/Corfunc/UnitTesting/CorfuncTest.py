import os
import sys

import unittest
from unittest.mock import MagicMock

from PyQt5 import QtGui, QtWidgets
from PyQt5 import QtCore
from PyQt5.QtTest import QTest

from sas.qtgui.Perspectives.Corfunc.CorfuncPerspective import CorfuncWindow
from sas.qtgui.Plotting.PlotterData import Data1D
from sasdata.dataloader.loader import Loader
from sas.qtgui.MainWindow.DataManager import DataManager
import sas.qtgui.Utilities.GuiUtils as GuiUtils


if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)


class CorfuncTest(unittest.TestCase):
    '''Test the Corfunc Interface'''
    def setUp(self):

        '''Create the CorfuncWindow'''
        class MainWindow(object):
            def __init__(self):
                self.model = QtGui.QStandardItemModel()

        class dummy_manager(object):
            def __init__(self):
                self.filesWidget = MainWindow()

            def communicator(self):
                return GuiUtils.Communicate()

            def communicate(self):
                return GuiUtils.Communicate()

        self.widget = CorfuncWindow(dummy_manager())
        reference_data1 = Data1D(x=[0.1, 0.2, 0.3, 0.4, 0.5], y=[1000, 1000, 100, 10, 1], dy=[0.0, 0.0, 0.0, 0.0, 0.0])
        reference_data1.filename = "Test A"
        GuiUtils.dataFromItem = MagicMock(return_value=reference_data1)
        self.fakeData = QtGui.QStandardItem("test")

    def tearDown(self):
        '''Destroy the CorfuncWindow'''
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        '''Test the GUI in its default state'''
        self.assertIsInstance(self.widget, QtWidgets.QWidget)
        self.assertEqual(self.widget.windowTitle(), "Corfunc Perspective")
        self.assertEqual(self.widget.model.columnCount(), 1)
        self.assertEqual(self.widget.model.rowCount(), 16)
        self.assertEqual(self.widget.txtLowerQMin.text(), '0.0')
        self.assertFalse(self.widget.txtLowerQMin.isEnabled())
        self.assertEqual(self.widget.txtFilename.text(), '')
        self.assertEqual(self.widget.txtLowerQMax.text(), '0.01')
        self.assertEqual(self.widget.txtUpperQMin.text(), '0.20')
        self.assertEqual(self.widget.txtUpperQMax.text(), '0.22')
        self.assertEqual(self.widget.txtBackground.text(), '0')
        self.assertEqual(self.widget.txtGuinierA.text(), '0.0')
        self.assertEqual(self.widget.txtGuinierB.text(), '0.0')
        self.assertEqual(self.widget.txtPorodK.text(), '0.0')
        self.assertEqual(self.widget.txtPorodSigma.text(), '0.0')
        self.assertEqual(self.widget.txtAvgCoreThick.text(), '0')
        self.assertEqual(self.widget.txtAvgIntThick.text(), '0')
        self.assertEqual(self.widget.txtAvgHardBlock.text(), '0')
        self.assertEqual(self.widget.txtPolydisp.text(), '0')
        self.assertEqual(self.widget.txtLongPeriod.text(), '0')
        self.assertEqual(self.widget.txtLocalCrystal.text(), '0')

    def testOnCalculate(self):
        """ Test onCompute function """
        self.widget.calculate_background = MagicMock()
        self.widget.cmdCalculateBg.setEnabled(True)
        QTest.mouseClick(self.widget.cmdCalculateBg, QtCore.Qt.LeftButton)
        self.assertTrue(self.widget.calculate_background.called_once())

    def testProcess(self):
        """Test the full analysis path"""

        filename = os.path.join("UnitTesting", "ISIS_98929.txt")
        try:
            os.stat(filename)
        except OSError:
            self.assertTrue(False, "ISIS_98929.txt does not exist")
        f = Loader().load(filename)
        QtWidgets.QFileDialog.getOpenFileName = MagicMock(return_value=(filename, ''))

        #self.assertEqual(self.widget.txtFilename.text(), filename)

        self.assertEqual(float(self.widget.txtBackground.text()), 0.0)

        self.widget.txtLowerQMin.setText("0.01")
        self.widget.txtLowerQMax.setText("0.20")
        self.widget.txtUpperQMax.setText("0.22")

        QTest.mouseClick(self.widget.cmdCalculateBg, QtCore.Qt.LeftButton)


        #TODO: All the asserts when Calculate is clicked and file properly loaded
        #self.assertTrue(float(self.widget.txtBackground.text()) > 0.2)

        #self.widget.extrapolateBtn.click()
        #self.assertTrue(float(self.widget.txtGuinierA.text()) > 1)
        #self.assertTrue(float(self.widget.txtGuinierB.text()) < -10000)
        #self.assertTrue(float(self.widget.txtPorodK.text()) > 10)
        #self.assertTrue(float(self.widget.txtPorodSigma.text()) > 10)

        #################################################
        # The testing framework does not seem to handle
        # multi-threaded Qt.  Signals emitted from threads
        # are not detected when run in the unittest, even
        # though they ARE handled in the actual application.
        #################################################
        # sleep(1)
        # self.widget.transformBtn.click()
        # while float(self.widget.longPeriod.text()) == 0.0:
        #     print("Waiting")
        #     sleep(1)
        # self.assertTrue(float(self.widget.longPeriod.text()) > 10)
        # self.assertTrue(float(self.widget.polydisp.text()) > 0)
        # self.assertTrue(float(self.widget.localCrystal.text()) > 0)
        # self.assertTrue(float(self.widget.longPeriod.text()) >
        #                 float(self.widget.avgHardBlock.text()) > 0)
        # self.assertTrue(float(self.widget.longPeriod.text()) >
        #                 float(self.widget.avgIntThick.text()) > 0)
        # self.assertTrue(float(self.widget.longPeriod.text()) >
        #                 float(self.widget.avgCoreThick.text()) > 0)

    def testSerialization(self):
        """ Serialization routines """
        self.widget.setData([self.fakeData])
        self.assertTrue(hasattr(self.widget, 'isSerializable'))
        self.assertTrue(self.widget.isSerializable())
        self.checkFakeDataState()
        data = GuiUtils.dataFromItem(self.widget._model_item)
        data_id = str(data.id)
        # Test three separate serialization routines
        state_all = self.widget.serializeAll()
        state_one = self.widget.serializeCurrentPage()
        page = self.widget.getPage()
        # Pull out params from state
        params_dict = state_all.get(data_id)
        params = params_dict.get('corfunc_params')
        # Tests
        self.assertEqual(len(state_all), len(state_one))
        self.assertEqual(len(state_all), 1)
        # getPage should include an extra param 'data_id' removed by serialize
        self.assertNotEqual(len(params), len(page))
        self.assertEqual(len(params), 15)
        self.assertEqual(len(page), 16)

    def testRemoveData(self):
        self.widget.setData([self.fakeData])
        self.checkFakeDataState()
        # Removing something not already in the perspective should do nothing
        self.widget.removeData([])
        self.checkFakeDataState()
        # Removing the data from the perspective should set it to base state
        self.widget.removeData([self.fakeData])
        # Be sure the defaults hold true after data removal
        self.testDefaults()

    def testLoadParams(self):
        self.widget.setData([self.fakeData])
        self.checkFakeDataState()
        pageState = self.widget.getPage()
        self.widget.updateFromParameters(pageState)
        self.checkFakeDataState()
        self.widget.removeData([self.fakeData])
        self.testDefaults()

    def checkFakeDataState(self):
        self.assertEqual(self.widget.txtFilename.text(), 'data')
        self.assertEqual(self.widget.txtLowerQMin.text(), '0.0')
        self.assertFalse(self.widget.txtLowerQMin.isEnabled())
        self.assertEqual(self.widget.txtLowerQMax.text(), '0.01')
        self.assertEqual(self.widget.txtUpperQMin.text(), '0.20')
        self.assertEqual(self.widget.txtUpperQMax.text(), '0.22')
        self.assertEqual(self.widget.txtBackground.text(), '0')
        self.assertEqual(self.widget.txtGuinierA.text(), '')
        self.assertEqual(self.widget.txtGuinierB.text(), '')
        self.assertEqual(self.widget.txtPorodK.text(), '')
        self.assertEqual(self.widget.txtPorodSigma.text(), '')
        self.assertEqual(self.widget.txtAvgCoreThick.text(), '')
        self.assertEqual(self.widget.txtAvgIntThick.text(), '')
        self.assertEqual(self.widget.txtAvgHardBlock.text(), '')
        self.assertEqual(self.widget.txtPolydisp.text(), '')
        self.assertEqual(self.widget.txtLongPeriod.text(), '')
        self.assertEqual(self.widget.txtLocalCrystal.text(), '')


if __name__ == "__main__":
    unittest.main()
