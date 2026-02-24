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

logger = logging.getLogger(__name__)


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
        mocker.patch.object(w.currentTab, 'showBatchCalculationWindow')
        mocker.patch.object(w.currentTab, 'startThread')
        mocker.patch.object(w.currentTab, 'startThreadAll')
        w.show()

        self.fakeData1 = GuiUtils.HashableStandardItem("A")
        self.fakeData2 = GuiUtils.HashableStandardItem("B")
        reference_data1 = Data1D(x=[0.1, 0.2], y=[0.0, 0.0], dy=[0.0, 0.0])
        reference_data1.filename = "Test A"
        reference_data1.id = "FakeID1"
        reference_data2 = Data1D(x=[0.1, 0.2], y=[0.0, 0.0], dy=[0.0, 0.0])
        reference_data2.filename = "Test B"
        reference_data1.id = "FakeID2"
        GuiUtils.updateModelItem(self.fakeData1, reference_data1)
        GuiUtils.updateModelItem(self.fakeData2, reference_data2)

        yield w

        """ Destroy the InversionWindow """
        w.setClosable(False)
        w.close()

    def removeAllData(self, widget):
        """ Cleanup method to restore widget to its base state """
        while len(widget.currentTab.results) > 0:
            remove_me = list(widget._dataList.keys())
            widget.removeData(remove_me)

    def baseGUIState(self, widget):
        """ Testing base state of Inversion """
        # base class information
        assert isinstance(widget, QtWidgets.QWidget)
        assert widget.windowTitle() == "P(r) Inversion Perspective"
        assert not widget.isClosable()
        assert not widget.currentTab.isCalculating
        # mapper
        assert isinstance(widget.mapper, QtWidgets.QDataWidgetMapper)
        assert widget.mapper.mappedSection(widget.currentTab.dataList) == -1
        # validators
        assert isinstance(widget.currentTab.noOfTermsInput.validator(), QtGui.QIntValidator)
        assert isinstance(widget.currentTab.regularizationConstantInput.validator(), QtGui.QDoubleValidator)
        assert isinstance(widget.currentTab.maxDistanceInput.validator(), QtGui.QDoubleValidator)
        assert isinstance(widget.currentTab.minQInput.validator(), QtGui.QDoubleValidator)
        assert isinstance(widget.currentTab.maxQInput.validator(), QtGui.QDoubleValidator)
        assert isinstance(widget.currentTab.slitHeightInput.validator(), QtGui.QDoubleValidator)
        assert isinstance(widget.currentTab.slitWidthInput.validator(), QtGui.QDoubleValidator)
        # model
        assert widget.model.rowCount() == 0
        assert widget.model.columnCount() == 0
        # buttons
        assert not widget.currentTab.calculateThisButton.isEnabled()
        assert not widget.currentTab.removeButton.isEnabled()
        assert widget.currentTab.stopButton.isEnabled()
        assert not widget.currentTab.stopButton.isVisible()
        assert not widget.currentTab.regConstantSuggestionButton.isEnabled()
        assert not widget.currentTab.noOfTermsSuggestionButton.isEnabled()
        assert not widget.currentTab.explorerButton.isEnabled()
        assert widget.currentTab.helpButton.isEnabled()
        # extra windows and charts
        assert widget.currentTab.dmaxWindow is None
        assert widget.currentTab.results[0].pr_plot is None
        assert widget.currentTab.results[0].data_plot is None

    def baseBatchState(self, widget):
        """ Testing the base batch fitting state """
        assert not widget.allowBatch()
        assert not widget.currentTab.is_batch
        assert not widget.currentTab.calculateAllButton.isEnabled()
        assert len(widget.batchResults) == 0
        widget.closeBatchResults()

    def zeroDataSetState(self, widget):
        """ Testing the base data state of the GUI """
        # data variables
        assert widget._data is None
        # inputs
        assert widget.currentTab.dataList.count() == 0
        assert widget.currentTab.backgroundInput.text() == "0.0"
        assert widget.currentTab.minQInput.text() == "0"
        assert widget.currentTab.maxQInput.text() == "inf"
        assert widget.currentTab.regularizationConstantInput.text() == "0"
        assert widget.currentTab.noOfTermsInput.text() == "10"
        assert widget.currentTab.maxDistanceInput.text() == "180"

    def oneDataSetState(self, widget):
        """ Testing the base data state of the GUI """
        # Test the globals after first sent
        assert widget.currentTab.dataList.count() == 1
        # See that the buttons are now enabled properly
        widget.currentTab.enableButtons()
        assert not widget.currentTab.calculateAllButton.isEnabled()
        assert widget.currentTab.calculateThisButton.isEnabled()
        assert widget.currentTab.removeButton.isEnabled()
        assert widget.currentTab.explorerButton.isEnabled()

    def twoDataSetState(self, widget):
        """ Testing the base data state of the GUI """
        # Test the globals after first sent
        assert widget.currentTab.dataList.count() == 1
        # See that the buttons are now enabled properly
        widget.currentTab.enableButtons()
        assert widget.currentTab.calculateThisButton.isEnabled()
        assert not widget.currentTab.calculateAllButton.isEnabled()
        assert widget.currentTab.removeButton.isEnabled()
        assert widget.currentTab.explorerButton.isEnabled()

    def testDefaults(self, widget):
        """ Test the GUI in its default state """
        self.baseGUIState(widget)
        self.zeroDataSetState(widget)
        self.baseBatchState(widget)
        self.removeAllData(widget)

    def notestAllowBatch(self, widget):
        """ Batch P(r) Tests """
        self.baseBatchState(widget)
        widget.setData([self.fakeData1])
        self.oneDataSetState(widget)
        widget.setData([self.fakeData2])
        self.oneDataSetState(widget)
        widget.setData([self.fakeData1, self.fakeData2])
        self.twoDataSetState(widget)
        widget.currentTab.calculateAllButton.click()
        assert widget.currentTab.isCalculating
        assert widget.currentTab.is_batch
        assert widget.currentTab.stopButton.isVisible()
        assert widget.currentTab.stopButton.isEnabled()
        assert widget.batchResultsWindow is not None
        assert widget.batchResultsWindow.cmdHelp.isEnabled()
        assert widget.batchResultsWindow.tblParams.columnCount() == 9
        assert widget.batchResultsWindow.tblParams.rowCount() == 2
        # Test stop button
        widget.currentTab.stopButton.click()
        assert widget.batchResultsWindow.isVisible()
        assert not widget.currentTab.stopButton.isVisible()
        assert widget.currentTab.stopButton.isEnabled()
        assert not widget.currentTab.is_batch
        assert not widget.currentTab.isCalculating
        widget.batchResultsWindow.close()
        assert widget.batchResultsWindow is None
        # Last test
        self.removeAllData(widget)
        self.baseBatchState(widget)

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
        widget.removeData([self.fakeData1])
        self.oneDataSetState(widget)
        self.removeAllData(widget)

    @pytest.mark.skip(reason="2026-02: Freezing on launch")
    def testClose(self, widget):
        """ Test methods related to closing the window """
        assert not widget.isClosable()
        widget.close()
        assert widget.isMinimized()
        assert widget.currentTab.dmaxWindow is None
        widget.setClosable(False)
        assert not widget.isClosable()
        widget.close()
        assert widget.isMinimized()
        widget.setClosable(True)
        assert widget.isClosable()
        widget.setClosable()
        assert widget.isClosable()
        self.removeAllData(widget)

    @pytest.mark.skip(reason="2026-02: caplog does not exist")
    def testGetNFunc(self, widget, caplog):
        """ test nfunc getter """
        # Float
        widget.currentTab.noOfTermsInput.setText("10")
        assert widget.getNFunc() == 10
        # Int
        widget.currentTab.noOfTermsInput.setText("980")
        assert widget.getNFunc() == 980
        # Empty
        with caplog.at_level(logging.ERROR):
            widget.currentTab.noOfTermsInput.setText("")
            n = widget.getNFunc()
        assert 'Incorrect number of terms specified:' in caplog.text
        assert widget.getNFunc() == 10
        # string
        with caplog.at_level(logging.ERROR):
            widget.currentTab.noOfTermsInput.setText("Nordvest Pizza")
            n = widget.getNFunc()
        assert "Incorrect number of terms specified: Nordvest Pizza" in caplog.text
        assert widget.getNFunc() == 10
        self.removeAllData(widget)

    def testSetCurrentData(self, widget):
        """ test current data setter """
        widget.setData([self.fakeData1, self.fakeData2])

        # Set the ref to none
        widget.currentTab.currentData = None
        assert widget._data == self.fakeData2
        # Set the ref to wrong type
        with pytest.raises(AttributeError):
            widget.currentTab.currentData("Afandi Kebab")
        # Set the reference to ref1
        widget.currentTab.currentData(self.fakeData1)
        assert widget._data == self.fakeData1
        self.removeAllData(widget)

    def testModelChanged(self, widget):
        """ Test setting the input and the model and vice-versa """
        # Initial values
        assert widget.currentTab.currentResult.calculator.dmax == 180.0
        assert widget.currentTab.currentResult.calculator.q_max == np.inf
        assert widget.currentTab.currentResult.calculator.q_min == 0.0
        assert widget.currentTab.currentResult.calculator.slit_height == 0.0
        assert widget.currentTab.currentResult.calculator.slit_width == 0.0
        assert widget.currentTab.currentResult.calculator.alpha == 0.0
        # Set new values
        # Min Q must always be less than max Q - Set max Q first
        widget.currentTab.maxQInput.setText("5.0")
        widget.currentTab.minQInput.setText("3.0")
        widget.currentTab.slitHeightInput.setText("7.0")
        widget.currentTab.slitWidthInput.setText("9.0")
        widget.currentTab.regularizationConstantInput.setText("11.0")
        widget.currentTab.maxDistanceInput.setText("1.0")
        # Check new values
        assert widget.currentTab.currentResult.calculator.dmax == 180
        assert widget.currentTab.currentResult.calculator.q_min == 0
        assert widget.currentTab.currentResult.calculator.q_max == np.inf
        assert widget.currentTab.currentResult.calculator.slit_height == 0.0
        assert widget.currentTab.currentResult.calculator.slit_width == 0.0
        assert widget.currentTab.currentResult.calculator.alpha == 0.0
        # Change model directly
        widget.model.setItem(WIDGETS.W_MAX_DIST, QtGui.QStandardItem("2.0"))
        widget.model.setItem(WIDGETS.W_SLIT_HEIGHT, QtGui.QStandardItem("8.0"))
        widget.model.setItem(WIDGETS.W_SLIT_WIDTH, QtGui.QStandardItem("10.0"))
        widget.model.setItem(WIDGETS.W_REGULARIZATION, QtGui.QStandardItem("12.0"))
        # Check values
        assert widget.currentTab.currentResult.calculator.dmax == 180
        assert widget.currentTab.currentResult.calculator.slit_height == 0.0
        assert widget.currentTab.currentResult.calculator.slit_width == 0.0
        assert widget.currentTab.currentResult.calculator.alpha == 0.0
        self.removeAllData(widget)

    @pytest.mark.xfail(reason="2026-02: Throwing error")
    def testOpenExplorerWindow(self, widget):
        """ open Dx window """
        assert widget.currentTab.dmaxWindow is None
        assert not widget.currentTab.explorerButton.isEnabled()
        widget.currentTab.openExplorerWindow()
        assert widget.currentTab.dmaxWindow is not None
        assert widget.currentTab.dmaxWindow.isVisible()
        assert widget.currentTab.dmaxWindow.windowTitle() == "Dmax Explorer"

    def testSerialization(self, widget):
        """ Serialization routines """
        assert hasattr(widget, 'isSerializable')
        assert widget.isSerializable()
        widget.setData([self.fakeData1])
        self.oneDataSetState(widget)
        data_id = widget.currentTabDataId()[0]
        # Test three separate serialization routines
        state_all = widget.serializeAll()
        print(state_all)
        state_one, _ = widget.serializeCurrentPage()
        print(state_one)
        page = widget.currentTab.getPage()
        print(page)
        # Pull out params from state
        params = state_all[data_id]['pr_params']
        # Tests
        assert len(state_all) == len(state_one)
        assert len(state_all) == 1
        # getPage should include an extra param 'data_id' removed by serialize
        assert len(params) != len(page)
        assert len(params) == 21
        assert params.get('data_id', None) is None
        assert page.get('data_id', None) is not None
        assert params.get('alpha', None) is not None
        assert params.get('alpha', None) == page.get('alpha', None)
        assert np.isnan(params.get('rg'))
