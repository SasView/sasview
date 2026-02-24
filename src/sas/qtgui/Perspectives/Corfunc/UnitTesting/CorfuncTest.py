import os
from pathlib import Path

import pytest
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtTest import QTest

from sasdata.dataloader.loader import Loader

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Perspectives.Corfunc.CorfuncPerspective import CorfuncWindow
from sas.qtgui.Plotting.PlotterData import Data1D


class CorfuncTest:
    '''Test the Corfunc Interface'''

    @pytest.fixture(autouse=True)
    def widget(self, qapp, mocker):
        '''Create/Destroy the CorfuncWindow'''
        class MainWindow:
            def __init__(self):
                self.model = QtGui.QStandardItemModel()

        class dummy_manager(QtWidgets.QWidget):
            def __init__(self):
                self.filesWidget = MainWindow()

            def communicator(self):
                return GuiUtils.Communicate()

            def communicate(self):
                return GuiUtils.Communicate()

        w = CorfuncWindow(dummy_manager())
        reference_data1 = Data1D(x=[0.1, 0.2, 0.3, 0.4, 0.5], y=[1000, 1000, 100, 10, 1], dy=[0.0, 0.0, 0.0, 0.0, 0.0])
        reference_data1.filename = "Test A"
        mocker.patch.object(GuiUtils, 'dataFromItem', return_value=reference_data1)
        self.fakeData = QtGui.QStandardItem("test")

        yield w

        w.close()

    def checkDefaults(self, widget):
        '''Test the GUI in its default state'''
        assert isinstance(widget, QtWidgets.QWidget)
        assert widget.windowTitle() == "Corfunc Perspective"
        assert widget.model.columnCount() == 1
        assert widget.model.rowCount() == 18
        assert widget.txtFilename.text() == ''
        assert widget.txtLowerQMax.text() == '0.01'
        assert widget.txtUpperQMin.text() == '0.20'
        assert widget.txtUpperQMax.text() == '0.22'
        assert widget.txtBackground.text() == '0'
        assert widget.txtGuinierA.text() == '0.0'
        assert widget.txtGuinierB.text() == '0.0'
        assert widget.txtPorodK.text() == '0.0'
        assert widget.txtPorodSigma.text() == '0.0'
        assert widget.txtAvgCoreThick.text() == '0'
        assert widget.txtAvgIntThick.text() == '0'
        assert widget.txtAvgHardBlock.text() == '0'
        assert widget.txtPolyRyan.text() == '0'
        assert widget.txtLongPeriod.text() == '0'
        assert widget.txtLocalCrystal.text() == '0'

    # This is throwing an error. Skip for now
    @pytest.mark.skip()
    def testOnCalculate(self, widget, mocker):
        """ Test onCompute function """
        mocker.patch.object(widget._calculator, '_calculate_background')
        widget.cmdExtract.setEnabled(True)
        QTest.mouseClick(widget.cmdExtract, QtCore.Qt.LeftButton)
        widget._calculator._calculate_background.assert_called_once()

    def testProcess(self, widget, mocker):
        """Test the full analysis path"""

        filename = str(Path("./src/sas/qtgui/UnitTesting/ISIS_98929.TXT").absolute())
        try:
            os.stat(filename)
        except OSError:
            assert False, "ISIS_98929.TXT does not exist"
        f = Loader().load(filename)
        mocker.patch.object(QtWidgets.QFileDialog, 'getOpenFileName', return_value=(filename, ''))

        #assert widget.txtFilename.text() == filename

        assert widget.txtBackground.text() == ''

        widget.txtLowerQMax.setText("0.20")
        widget.txtUpperQMax.setText("0.22")

        QTest.mouseClick(widget.cmdExtract, QtCore.Qt.LeftButton)


        #TODO: All the asserts when Calculate is clicked and file properly loaded
        #assert float(widget.txtBackground.text()) > 0.2

        #widget.extrapolateBtn.click()
        #assert float(widget.txtGuinierA.text()) > 1
        #assert float(widget.txtGuinierB.text()) < -10000
        #assert float(widget.txtPorodK.text()) > 10
        #assert float(widget.txtPorodSigma.text()) > 10

        #################################################
        # The testing framework does not seem to handle
        # multi-threaded Qt.  Signals emitted from threads
        # are not detected when run in the unittest, even
        # though they ARE handled in the actual application.
        #################################################
        # sleep(1)
        # widget.transformBtn.click()
        # while float(widget.longPeriod.text()) == 0.0:
        #     print("Waiting")
        #     sleep(1)
        # assert float(widget.longPeriod.text()) > 10
        # assert float(widget.polydisp.text()) > 0
        # assert float(widget.localCrystal.text()) > 0
        # assert float(widget.longPeriod.text()) > float(widget.avgHardBlock.text()) > 0
        # assert float(widget.longPeriod.text()) > float(widget.avgIntThick.text()) > 0
        # assert float(widget.longPeriod.text()) > float(widget.avgCoreThick.text()) > 0

    def testSerialization(self, widget):
        """ Serialization routines """
        widget.setData([self.fakeData])
        assert hasattr(widget, 'isSerializable')
        assert widget.isSerializable()
        self.checkFakeDataState(widget)
        data = GuiUtils.dataFromItem(widget._model_item)
        data_id = str(data.id)
        # Test three separate serialization routines
        state_all = widget.serializeAll()
        state_one = widget.serializeCurrentPage()
        page = widget.getPage()
        # Pull out params from state
        params_dict = state_all.get(data_id)
        params = params_dict.get('corfunc_params')
        # Tests
        assert len(state_all) == len(state_one)
        assert len(state_all) == 1
        # getPage should include an extra param 'data_id' removed by serialize
        assert len(params) != len(page)
        assert len(params) == 17
        assert len(page) == 18

    def testRemoveData(self, widget):
        widget.setData([self.fakeData])
        self.checkFakeDataState(widget)
        # Removing something not already in the perspective should do nothing
        widget.removeData([])
        self.checkFakeDataState(widget)
        # Removing the data from the perspective should set it to base state
        widget.removeData([self.fakeData])
        # Be sure the defaults hold true after data removal
        self.checkDefaults(widget)

    def testLoadParams(self, widget):
        widget.setData([self.fakeData])
        self.checkFakeDataState(widget)
        pageState = widget.getPage()
        widget.updateFromParameters(pageState)
        self.checkFakeDataState(widget)
        widget.removeData([self.fakeData])
        self.checkDefaults(widget)

    def checkFakeDataState(self, widget):
        assert widget.txtFilename.text() == 'data'
        assert widget.txtLowerQMax.text() == '0.137973'
        assert widget.txtUpperQMin.text() == '0.3085169'
        assert widget.txtUpperQMax.text() == '0.3623898'
        assert widget.txtBackground.text() == ''
        assert widget.txtGuinierA.text() == ''
        assert widget.txtGuinierB.text() == ''
        assert widget.txtPorodK.text() == ''
        assert widget.txtPorodSigma.text() == ''
        assert widget.txtAvgCoreThick.text() == ''
        assert widget.txtAvgIntThick.text() == ''
        assert widget.txtAvgHardBlock.text() == ''
        assert widget.txtPolyRyan.text() == ''
        assert widget.txtLongPeriod.text() == ''
        assert widget.txtLocalCrystal.text() == ''
