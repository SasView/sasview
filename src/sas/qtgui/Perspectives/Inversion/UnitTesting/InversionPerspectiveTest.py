import unittest
import pytest

from unittest.mock import MagicMock

from sas.qtgui.Utilities.GuiUtils import *
from sas.qtgui.Perspectives.Inversion.InversionPerspective import InversionWindow
from sas.qtgui.Perspectives.Inversion.InversionUtils import WIDGETS
from sas.qtgui.Plotting.PlotterData import Data1D

import sas.qtgui.Utilities.GuiUtils as GuiUtils

if not QtWidgets.QApplication.instance():
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

        self.widget = InversionWindow(parent=dummy_manager())
        self.widget._parent = QtWidgets.QMainWindow()
        self.widget.showBatchOutput = MagicMock()
        self.widget.startThread = MagicMock()
        self.widget.startThreadAll = MagicMock()
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
        while len(self.widget.dataList) > 0:
            remove_me = list(self.widget._dataList.keys())
            self.widget.removeData(remove_me)

    def baseGUIState(self):
        """ Testing base state of Inversion """
        # base class information
        assert isinstance(self.widget, QtWidgets.QWidget)
        assert self.widget.windowTitle() == "P(r) Inversion Perspective"
        assert not self.widget.isClosable()
        assert not self.widget.isCalculating
        # mapper
        assert isinstance(self.widget.mapper, QtWidgets.QDataWidgetMapper)
        assert self.widget.mapper.mappedSection(self.widget.dataList) != -1
        # validators
        assert isinstance(self.widget.noOfTermsInput.validator(), QtGui.QIntValidator)
        assert isinstance(self.widget.regularizationConstantInput.validator(), QtGui.QDoubleValidator)
        assert isinstance(self.widget.maxDistanceInput.validator(), QtGui.QDoubleValidator)
        assert isinstance(self.widget.minQInput.validator(), QtGui.QDoubleValidator)
        assert isinstance(self.widget.maxQInput.validator(), QtGui.QDoubleValidator)
        assert isinstance(self.widget.slitHeightInput.validator(), QtGui.QDoubleValidator)
        assert isinstance(self.widget.slitWidthInput.validator(), QtGui.QDoubleValidator)
        # model
        assert self.widget.model.rowCount() == 22
        assert self.widget.model.columnCount() == 1
        assert self.widget.mapper.model() == self.widget.model
        # buttons
        assert not self.widget.calculateThisButton.isEnabled()
        assert not self.widget.removeButton.isEnabled()
        assert self.widget.stopButton.isEnabled()
        assert not self.widget.stopButton.isVisible()
        assert not self.widget.regConstantSuggestionButton.isEnabled()
        assert not self.widget.noOfTermsSuggestionButton.isEnabled()
        assert not self.widget.explorerButton.isEnabled()
        assert self.widget.helpButton.isEnabled()
        # extra windows and charts
        assert self.widget.dmaxWindow is None
        assert self.widget.prPlot is None
        assert self.widget.dataPlot is None
        # threads
        assert self.widget.calcThread is None
        assert self.widget.estimationThread is None
        assert self.widget.estimationThreadNT is None

    def baseBatchState(self):
        """ Testing the base batch fitting state """
        assert not self.widget.allowBatch()
        assert not self.widget.isBatch
        assert not self.widget.calculateAllButton.isEnabled()
        assert len(self.widget.batchResults) == 0
        assert len(self.widget.batchComplete) == 0
        self.widget.closeBatchResults()

    def zeroDataSetState(self):
        """ Testing the base data state of the GUI """
        # data variables
        assert self.widget._data is None
        assert len(self.widget._dataList) == 0
        assert self.widget.nTermsSuggested == 10
        # inputs
        assert len(self.widget.dataList) == 0
        assert self.widget.backgroundInput.text() == "0.0"
        assert self.widget.minQInput.text() == ""
        assert self.widget.maxQInput.text() == ""
        assert self.widget.regularizationConstantInput.text() == "0.0001"
        assert self.widget.noOfTermsInput.text() == "10"
        assert self.widget.maxDistanceInput.text() == "140.0"

    def oneDataSetState(self):
        """ Testing the base data state of the GUI """
        # Test the globals after first sent
        assert len(self.widget._dataList) == 1
        assert self.widget.dataList.count() == 1
        # See that the buttons are now enabled properly
        self.widget.enableButtons()
        assert not self.widget.calculateAllButton.isEnabled()
        assert self.widget.calculateThisButton.isEnabled()
        assert self.widget.removeButton.isEnabled()
        assert self.widget.explorerButton.isEnabled()

    def twoDataSetState(self):
        """ Testing the base data state of the GUI """
        # Test the globals after first sent
        assert len(self.widget._dataList) == 2
        assert self.widget.dataList.count() == 2
        # See that the buttons are now enabled properly
        self.widget.enableButtons()
        assert self.widget.calculateThisButton.isEnabled()
        assert self.widget.calculateAllButton.isEnabled()
        assert self.widget.removeButton.isEnabled()
        assert self.widget.explorerButton.isEnabled()

    def testDefaults(self):
        """ Test the GUI in its default state """
        self.baseGUIState()
        self.zeroDataSetState()
        self.baseBatchState()
        self.removeAllData()

    def notestAllowBatch(self):
        """ Batch P(r) Tests """
        self.baseBatchState()
        self.widget.setData([self.fakeData1])
        self.oneDataSetState()
        self.widget.setData([self.fakeData2])
        self.twoDataSetState()
        self.widget.calculateAllButton.click()
        assert self.widget.isCalculating
        assert self.widget.isBatch
        assert self.widget.stopButton.isVisible()
        assert self.widget.stopButton.isEnabled()
        assert self.widget.batchResultsWindow is not None
        assert self.widget.batchResultsWindow.cmdHelp.isEnabled()
        assert self.widget.batchResultsWindow.tblParams.columnCount() == 9
        assert self.widget.batchResultsWindow.tblParams.rowCount() == 2
        # Test stop button
        self.widget.stopButton.click()
        assert self.widget.batchResultsWindow.isVisible()
        assert not self.widget.stopButton.isVisible()
        assert self.widget.stopButton.isEnabled()
        assert not self.widget.isBatch
        assert not self.widget.isCalculating
        self.widget.batchResultsWindow.close()
        assert self.widget.batchResultsWindow is None
        # Last test
        self.removeAllData()
        self.baseBatchState()

    @pytest.mark.skip(reason="2022-09 already broken - causes Qt event loop exception")
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

    @pytest.mark.skip(reason="2022-09 already broken - causes Qt event loop exception")
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
        assert not self.widget.isClosable()
        self.widget.close()
        assert self.widget.isMinimized()
        assert self.widget.dmaxWindow is None
        self.widget.setClosable(False)
        assert not self.widget.isClosable()
        self.widget.close()
        assert self.widget.isMinimized()
        self.widget.setClosable(True)
        assert self.widget.isClosable()
        self.widget.setClosable()
        assert self.widget.isClosable()
        self.removeAllData()

    def testGetNFunc(self):
        """ test nfunc getter """
        # Float
        self.widget.noOfTermsInput.setText("10")
        assert self.widget.getNFunc() == 10
        # Int
        self.widget.noOfTermsInput.setText("980")
        assert self.widget.getNFunc() == 980
        # Empty
        with self.assertLogs(level='ERROR') as cm:
            self.widget.noOfTermsInput.setText("")
            n = self.widget.getNFunc()
            assert cm.output == ['ERROR:sas.qtgui.Perspectives.Inversion.InversionPerspective:Incorrect number of terms specified: ']
        assert self.widget.getNFunc() == 10
        # string
        with self.assertLogs(level='ERROR') as cm:
            self.widget.noOfTermsInput.setText("Nordvest Pizza")
            n = self.widget.getNFunc()
            assert cm.output == ['ERROR:sas.qtgui.Perspectives.Inversion.InversionPerspective:Incorrect number of terms specified: Nordvest Pizza']
        assert self.widget.getNFunc() == 10
        self.removeAllData()

    @pytest.mark.skip(reason="2022-09 already broken - causes Qt event loop exception")
    def testSetCurrentData(self):
        """ test current data setter """
        self.widget.setData([self.fakeData1, self.fakeData2])

        # Check that the current data is reference2
        assert self.widget._data == self.fakeData2
        # Set the ref to none
        self.widget.setCurrentData(None)
        assert self.widget._data == self.fakeData2
        # Set the ref to wrong type
        with pytest.raises(AttributeError):
            self.widget.setCurrentData("Afandi Kebab")
        # Set the reference to ref1
        self.widget.setCurrentData(self.fakeData1)
        assert self.widget._data == self.fakeData1
        self.removeAllData()

    def testModelChanged(self):
        """ Test setting the input and the model and vice-versa """
        # Initial values
        assert self.widget._calculator.get_dmax() == 140.0
        assert self.widget._calculator.get_qmax() == -1.0
        assert self.widget._calculator.get_qmin() == -1.0
        assert self.widget._calculator.slit_height == 0.0
        assert self.widget._calculator.slit_width == 0.0
        assert self.widget._calculator.alpha == 0.0001
        # Set new values
        # Min Q must always be less than max Q - Set max Q first
        self.widget.maxQInput.setText("5.0")
        self.widget.check_q_high()
        self.widget.minQInput.setText("3.0")
        self.widget.check_q_low()
        self.widget.slitHeightInput.setText("7.0")
        self.widget.slitWidthInput.setText("9.0")
        self.widget.regularizationConstantInput.setText("11.0")
        self.widget.maxDistanceInput.setText("1.0")
        # Check new values
        assert self.widget._calculator.get_dmax() == 1.0
        assert self.widget._calculator.get_qmin() == 3.0
        assert self.widget._calculator.get_qmax() == 5.0
        assert self.widget._calculator.slit_height == 7.0
        assert self.widget._calculator.slit_width == 9.0
        assert self.widget._calculator.alpha == 11.0
        # Change model directly
        self.widget.model.setItem(WIDGETS.W_MAX_DIST, QtGui.QStandardItem("2.0"))
        self.widget.model.setItem(WIDGETS.W_SLIT_HEIGHT, QtGui.QStandardItem("8.0"))
        self.widget.model.setItem(WIDGETS.W_SLIT_WIDTH, QtGui.QStandardItem("10.0"))
        self.widget.model.setItem(WIDGETS.W_REGULARIZATION, QtGui.QStandardItem("12.0"))
        # Check values
        assert self.widget._calculator.get_dmax() == 2.0
        assert self.widget._calculator.slit_height == 8.0
        assert self.widget._calculator.slit_width == 10.0
        assert self.widget._calculator.alpha == 12.0
        self.removeAllData()

    @pytest.mark.xfail(reason="2022-09 already broken - opens tk not qt mpl backend")
    def testOpenExplorerWindow(self):
        """ open Dx window """
        assert self.widget.dmaxWindow is None
        assert not self.widget.explorerButton.isEnabled()
        self.widget.openExplorerWindow()
        assert self.widget.dmaxWindow is not None
        assert self.widget.dmaxWindow.isVisible()
        assert self.widget.dmaxWindow.windowTitle() == "Dmax Explorer"

    def testSerialization(self):
        """ Serialization routines """
        assert hasattr(self.widget, 'isSerializable')
        assert self.widget.isSerializable()
        self.widget.setData([self.fakeData1])
        self.oneDataSetState()
        data_id = self.widget.currentTabDataId()[0]
        # Test three separate serialization routines
        state_all = self.widget.serializeAll()
        state_one = self.widget.serializeCurrentPage()
        page = self.widget.getPage()
        # Pull out params from state
        params = state_all[data_id]['pr_params']
        # Tests
        assert len(state_all) == len(state_one)
        assert len(state_all) == 1
        # getPage should include an extra param 'data_id' removed by serialize
        assert len(params) != len(page)
        assert len(params) == 26
        assert params.get('data_id', None) == None
        assert page.get('data_id', None) != None
        assert params.get('alpha', None) != None
        assert params.get('alpha', None) == page.get('alpha', None)
        assert np.isnan(params.get('rg'))


if __name__ == "__main__":
    unittest.main()
