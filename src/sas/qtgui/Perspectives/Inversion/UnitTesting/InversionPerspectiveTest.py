import logging

import matplotlib as mpl
import numpy as np
import pytest
from PySide6 import QtGui, QtWidgets

mpl.use("Qt5Agg")

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Perspectives.Inversion.InversionPerspective import InversionWindow
from sas.qtgui.Perspectives.Inversion.InversionUtils import WIDGETS
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Utilities.GuiUtils import Communicate


class InversionTest:
    """ Test the Inversion Perspective GUI """

    @pytest.fixture(autouse=True)
    def widget(self, qapp, mocker):
        '''Create/Destroy the InversionWindow'''

        class dummy_manager:
            HELP_DIRECTORY_LOCATION = "html"
            communicate = Communicate()
            def communicator(self):
                return self.communicate

        w = InversionWindow(parent=dummy_manager())
        w._parent = QtWidgets.QMainWindow()
        mocker.patch.object(w, 'showBatchOutput')
        mocker.patch.object(w, 'startThread')
        mocker.patch.object(w, 'startThreadAll')
        w.show()

        self.fakeData1 = GuiUtils.HashableStandardItem("A")
        self.fakeData2 = GuiUtils.HashableStandardItem("B")
        reference_data1 = Data1D(x=[0.1, 0.2], y=[0.0, 0.0], dy=[0.0, 0.0])
        reference_data1.filename = "Test A"
        reference_data2 = Data1D(x=[0.1, 0.2], y=[0.0, 0.0], dy=[0.0, 0.0])
        reference_data2.filename = "Test B"
        GuiUtils.updateModelItem(self.fakeData1, reference_data1)
        GuiUtils.updateModelItem(self.fakeData2, reference_data2)

        yield w

        """ Destroy the InversionWindow """
        w.setClosable(False)
        w.close()

    def removeAllData(self, widget):
        """ Cleanup method to restore widget to its base state """
        while len(widget.dataList) > 0:
            remove_me = list(widget._dataList.keys())
            widget.removeData(remove_me)

    def baseGUIState(self, widget):
        """ Testing base state of Inversion """
        # base class information
        assert isinstance(widget, QtWidgets.QWidget)
        assert widget.windowTitle() == "P(r) Inversion Perspective"
        assert not widget.isClosable()
        assert not widget.isCalculating
        # mapper
        assert isinstance(widget.mapper, QtWidgets.QDataWidgetMapper)
        assert widget.mapper.mappedSection(widget.dataList) != -1
        # validators
        assert isinstance(widget.noOfTermsInput.validator(), QtGui.QIntValidator)
        assert isinstance(widget.regularizationConstantInput.validator(), QtGui.QDoubleValidator)
        assert isinstance(widget.maxDistanceInput.validator(), QtGui.QDoubleValidator)
        assert isinstance(widget.minQInput.validator(), QtGui.QDoubleValidator)
        assert isinstance(widget.maxQInput.validator(), QtGui.QDoubleValidator)
        assert isinstance(widget.slitHeightInput.validator(), QtGui.QDoubleValidator)
        assert isinstance(widget.slitWidthInput.validator(), QtGui.QDoubleValidator)
        # model
        assert widget.model.rowCount() == 22
        assert widget.model.columnCount() == 1
        assert widget.mapper.model() == widget.model
        # buttons
        assert not widget.calculateThisButton.isEnabled()
        assert not widget.removeButton.isEnabled()
        assert widget.stopButton.isEnabled()
        assert not widget.stopButton.isVisible()
        assert not widget.regConstantSuggestionButton.isEnabled()
        assert not widget.noOfTermsSuggestionButton.isEnabled()
        assert not widget.explorerButton.isEnabled()
        assert widget.helpButton.isEnabled()
        # extra windows and charts
        assert widget.dmaxWindow is None
        assert widget.prPlot is None
        assert widget.dataPlot is None
        # threads
        assert widget.calcThread is None
        assert widget.estimationThread is None
        assert widget.estimationThreadNT is None

    def baseBatchState(self, widget):
        """ Testing the base batch fitting state """
        assert not widget.allowBatch()
        assert not widget.isBatch
        assert not widget.calculateAllButton.isEnabled()
        assert len(widget.batchResults) == 0
        assert len(widget.batchComplete) == 0
        widget.closeBatchResults()

    def zeroDataSetState(self, widget):
        """ Testing the base data state of the GUI """
        # data variables
        assert widget._data is None
        assert len(widget._dataList) == 0
        assert widget.nTermsSuggested == 10
        # inputs
        assert len(widget.dataList) == 0
        assert widget.backgroundInput.text() == "0.0"
        assert widget.minQInput.text() == "0.0"
        assert widget.maxQInput.text() == "0.0"
        assert widget.regularizationConstantInput.text() == "0.0001"
        assert widget.noOfTermsInput.text() == "10"
        assert widget.maxDistanceInput.text() == "140.0"

    def oneDataSetState(self, widget):
        """ Testing the base data state of the GUI """
        # Test the globals after first sent
        assert len(widget._dataList) == 1
        assert widget.dataList.count() == 1
        # See that the buttons are now enabled properly
        widget.enableButtons()
        assert not widget.calculateAllButton.isEnabled()
        assert widget.calculateThisButton.isEnabled()
        assert widget.removeButton.isEnabled()
        assert widget.explorerButton.isEnabled()

    def twoDataSetState(self, widget):
        """ Testing the base data state of the GUI """
        # Test the globals after first sent
        assert len(widget._dataList) == 2
        assert widget.dataList.count() == 2
        # See that the buttons are now enabled properly
        widget.enableButtons()
        assert widget.calculateThisButton.isEnabled()
        assert widget.calculateAllButton.isEnabled()
        assert widget.removeButton.isEnabled()
        assert widget.explorerButton.isEnabled()

    def testDefaults(self, widget):
        """ Test the GUI in its default state """
        self.baseGUIState(widget)
        self.zeroDataSetState(widget)
        self.baseBatchState(widget)
        self.removeAllData(widget)

    def notestAllowBatch(self, widget):
        """ Batch P(r) Tests """
        self.baseBatchState()
        widget.setData([self.fakeData1])
        self.oneDataSetState()
        widget.setData([self.fakeData2])
        self.twoDataSetState()
        widget.calculateAllButton.click()
        assert widget.isCalculating
        assert widget.isBatch
        assert widget.stopButton.isVisible()
        assert widget.stopButton.isEnabled()
        assert widget.batchResultsWindow is not None
        assert widget.batchResultsWindow.cmdHelp.isEnabled()
        assert widget.batchResultsWindow.tblParams.columnCount() == 9
        assert widget.batchResultsWindow.tblParams.rowCount() == 2
        # Test stop button
        widget.stopButton.click()
        assert widget.batchResultsWindow.isVisible()
        assert not widget.stopButton.isVisible()
        assert widget.stopButton.isEnabled()
        assert not widget.isBatch
        assert not widget.isCalculating
        widget.batchResultsWindow.close()
        assert widget.batchResultsWindow is None
        # Last test
        self.removeAllData(widget)
        self.baseBatchState(widget)

    @pytest.mark.skip(reason="2022-09 already broken - causes Qt event loop exception")
    def testSetData(self, widget):
        """ Check if sending data works as expected """
        self.zeroDataSetState(widget)
        widget.setData([self.fakeData1])
        self.oneDataSetState(widget)
        widget.setData([self.fakeData1])
        self.oneDataSetState(widget)
        widget.setData([self.fakeData2])
        self.twoDataSetState(widget)
        self.removeAllData(widget)
        self.zeroDataSetState(widget)
        self.removeAllData(widget)

    @pytest.mark.skip(reason="2022-09 already broken - causes Qt event loop exception")
    def testRemoveData(self, widget):
        """ Test data removal from widget """
        widget.setData([self.fakeData1, self.fakeData2])
        self.twoDataSetState(widget)
        # Remove data 0
        widget.removeData()
        self.oneDataSetState(widget)
        self.removeAllData(widget)

    def testClose(self, widget):
        """ Test methods related to closing the window """
        assert not widget.isClosable()
        widget.close()
        assert widget.isMinimized()
        assert widget.dmaxWindow is None
        widget.setClosable(False)
        assert not widget.isClosable()
        widget.close()
        assert widget.isMinimized()
        widget.setClosable(True)
        assert widget.isClosable()
        widget.setClosable()
        assert widget.isClosable()
        self.removeAllData(widget)

    def testGetNFunc(self, widget, caplog):
        """ test nfunc getter """
        # Float
        widget.noOfTermsInput.setText("10")
        assert widget.getNFunc() == 10
        # Int
        widget.noOfTermsInput.setText("980")
        assert widget.getNFunc() == 980
        # Empty
        with caplog.at_level(logging.ERROR):
            widget.noOfTermsInput.setText("")
            n = widget.getNFunc()
        assert 'Incorrect number of terms specified:' in caplog.text
        assert widget.getNFunc() == 10
        # string
        with caplog.at_level(logging.ERROR):
            widget.noOfTermsInput.setText("Nordvest Pizza")
            n = widget.getNFunc()
        assert "Incorrect number of terms specified: Nordvest Pizza" in caplog.text
        assert widget.getNFunc() == 10
        self.removeAllData(widget)

    @pytest.mark.skip(reason="2022-09 already broken - causes Qt event loop exception")
    def testSetCurrentData(self, widget):
        """ test current data setter """
        widget.setData([self.fakeData1, self.fakeData2])

        # Check that the current data is reference2
        assert widget._data == self.fakeData2
        # Set the ref to none
        widget.setCurrentData(None)
        assert widget._data == self.fakeData2
        # Set the ref to wrong type
        with pytest.raises(AttributeError):
            widget.setCurrentData("Afandi Kebab")
        # Set the reference to ref1
        widget.setCurrentData(self.fakeData1)
        assert widget._data == self.fakeData1
        self.removeAllData(widget)

    def testModelChanged(self, widget):
        """ Test setting the input and the model and vice-versa """
        # Initial values
        assert widget._calculator.get_dmax() == 140.0
        assert widget._calculator.get_qmax() == -1.0
        assert widget._calculator.get_qmin() == -1.0
        assert widget._calculator.slit_height == 0.0
        assert widget._calculator.slit_width == 0.0
        assert widget._calculator.alpha == 0.0001
        # Set new values
        # Min Q must always be less than max Q - Set max Q first
        widget.maxQInput.setText("5.0")
        widget.check_q_high()
        widget.minQInput.setText("3.0")
        widget.check_q_low()
        widget.slitHeightInput.setText("7.0")
        widget.slitWidthInput.setText("9.0")
        widget.regularizationConstantInput.setText("11.0")
        widget.maxDistanceInput.setText("1.0")
        # Check new values
        assert widget._calculator.get_dmax() == 1.0
        assert widget._calculator.get_qmin() == 3.0
        assert widget._calculator.get_qmax() == 5.0
        assert widget._calculator.slit_height == 7.0
        assert widget._calculator.slit_width == 9.0
        assert widget._calculator.alpha == 11.0
        # Change model directly
        widget.model.setItem(WIDGETS.W_MAX_DIST, QtGui.QStandardItem("2.0"))
        widget.model.setItem(WIDGETS.W_SLIT_HEIGHT, QtGui.QStandardItem("8.0"))
        widget.model.setItem(WIDGETS.W_SLIT_WIDTH, QtGui.QStandardItem("10.0"))
        widget.model.setItem(WIDGETS.W_REGULARIZATION, QtGui.QStandardItem("12.0"))
        # Check values
        assert widget._calculator.get_dmax() == 2.0
        assert widget._calculator.slit_height == 8.0
        assert widget._calculator.slit_width == 10.0
        assert widget._calculator.alpha == 12.0
        self.removeAllData(widget)

    @pytest.mark.skip(reason="2022-09 already broken - generates numba crash")
    def testOpenExplorerWindow(self, widget):
        """ open Dx window """
        assert widget.dmaxWindow is None
        assert not widget.explorerButton.isEnabled()
        widget.openExplorerWindow()
        assert widget.dmaxWindow is not None
        assert widget.dmaxWindow.isVisible()
        assert widget.dmaxWindow.windowTitle() == "Dmax Explorer"

    @pytest.mark.skip(reason="2022-09 already broken - generates numba crash")
    def testSerialization(self, widget):
        """ Serialization routines """
        assert hasattr(widget, 'isSerializable')
        assert widget.isSerializable()
        widget.setData([self.fakeData1])
        self.oneDataSetState(widget)
        data_id = widget.currentTabDataId()[0]
        # Test three separate serialization routines
        state_all = widget.serializeAll()
        state_one = widget.serializeCurrentPage()
        page = widget.getPage()
        # Pull out params from state
        params = state_all[data_id]['pr_params']
        # Tests
        assert len(state_all) == len(state_one)
        assert len(state_all) == 1
        # getPage should include an extra param 'data_id' removed by serialize
        assert len(params) != len(page)
        assert len(params) == 26
        assert params.get('data_id', None) is None
        assert page.get('data_id', None) is not None
        assert params.get('alpha', None) is not None
        assert params.get('alpha', None) == page.get('alpha', None)
        assert np.isnan(params.get('rg'))
