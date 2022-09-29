import os
import sys

import pytest

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

    @pytest.mark.xfail(reason="2022-09 already broken")
    def testDefaults(self):
        '''Test the GUI in its default state'''
        assert isinstance(self.widget, QtWidgets.QWidget)
        assert self.widget.windowTitle() == "Corfunc Perspective"
        assert self.widget.model.columnCount() == 1
        assert self.widget.model.rowCount() == 16
        assert self.widget.txtLowerQMin.text() == '0.0'
        assert not self.widget.txtLowerQMin.isEnabled()
        assert self.widget.txtFilename.text() == ''
        assert self.widget.txtLowerQMax.text() == '0.01'
        assert self.widget.txtUpperQMin.text() == '0.20'
        assert self.widget.txtUpperQMax.text() == '0.22'
        assert self.widget.txtBackground.text() == '0'
        assert self.widget.txtGuinierA.text() == '0.0'
        assert self.widget.txtGuinierB.text() == '0.0'
        assert self.widget.txtPorodK.text() == '0.0'
        assert self.widget.txtPorodSigma.text() == '0.0'
        assert self.widget.txtAvgCoreThick.text() == '0'
        assert self.widget.txtAvgIntThick.text() == '0'
        assert self.widget.txtAvgHardBlock.text() == '0'
        assert self.widget.txtPolydisp.text() == '0'
        assert self.widget.txtLongPeriod.text() == '0'
        assert self.widget.txtLocalCrystal.text() == '0'

    @pytest.mark.xfail(reason="2022-09 already broken")
    def testOnCalculate(self):
        """ Test onCompute function """
        self.widget.calculate_background = MagicMock()
        self.widget.cmdCalculateBg.setEnabled(True)
        QTest.mouseClick(self.widget.cmdCalculateBg, QtCore.Qt.LeftButton)
        assert self.widget.calculate_background.called_once()

    @pytest.mark.xfail(reason="2022-09 already broken - input file issue")
    def testProcess(self):
        """Test the full analysis path"""

        filename = os.path.join("UnitTesting", "ISIS_98929.txt")
        try:
            os.stat(filename)
        except OSError:
            assert False, "ISIS_98929.txt does not exist"
        f = Loader().load(filename)
        QtWidgets.QFileDialog.getOpenFileName = MagicMock(return_value=(filename, ''))

        #self.assertEqual(self.widget.txtFilename.text(), filename)

        assert float(self.widget.txtBackground.text()) == 0.0

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

    @pytest.mark.xfail(reason="2022-09 already broken")
    def testSerialization(self):
        """ Serialization routines """
        self.widget.setData([self.fakeData])
        assert hasattr(self.widget, 'isSerializable')
        assert self.widget.isSerializable()
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
        assert len(state_all) == len(state_one)
        assert len(state_all) == 1
        # getPage should include an extra param 'data_id' removed by serialize
        assert len(params) != len(page)
        assert len(params) == 15
        assert len(page) == 16

    @pytest.mark.xfail(reason="2022-09 already broken")
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

    @pytest.mark.xfail(reason="2022-09 already broken")
    def testLoadParams(self):
        self.widget.setData([self.fakeData])
        self.checkFakeDataState()
        pageState = self.widget.getPage()
        self.widget.updateFromParameters(pageState)
        self.checkFakeDataState()
        self.widget.removeData([self.fakeData])
        self.testDefaults()

    def checkFakeDataState(self):
        assert self.widget.txtFilename.text() == 'data'
        assert self.widget.txtLowerQMin.text() == '0.0'
        assert not self.widget.txtLowerQMin.isEnabled()
        assert self.widget.txtLowerQMax.text() == '0.01'
        assert self.widget.txtUpperQMin.text() == '0.20'
        assert self.widget.txtUpperQMax.text() == '0.22'
        assert self.widget.txtBackground.text() == '0'
        assert self.widget.txtGuinierA.text() == ''
        assert self.widget.txtGuinierB.text() == ''
        assert self.widget.txtPorodK.text() == ''
        assert self.widget.txtPorodSigma.text() == ''
        assert self.widget.txtAvgCoreThick.text() == ''
        assert self.widget.txtAvgIntThick.text() == ''
        assert self.widget.txtAvgHardBlock.text() == ''
        assert self.widget.txtPolydisp.text() == ''
        assert self.widget.txtLongPeriod.text() == ''
        assert self.widget.txtLocalCrystal.text() == ''


if __name__ == "__main__":
    unittest.main()
