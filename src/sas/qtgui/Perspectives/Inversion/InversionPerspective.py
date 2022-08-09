import logging
import numpy as np


from PySide6 import QtGui, QtCore, QtWidgets

# sas-global

import sas.qtgui.Utilities.GuiUtils as GuiUtils

# pr inversion GUI elements
from .InversionWidget import InversionWidget

# pr inversion calculation elements

from sas.sascalc.pr.invertor import Invertor
from sas.qtgui.Plotting.PlotterData import Data1D, DataRole
# Batch calculation display
from sas.qtgui.Utilities.GridPanel import BatchInversionOutputPanel
from sas.qtgui.Perspectives.perspective import Perspective


def str_to_float(string: str):
    """Converts text input values to float.
    Failure to parse string returns zero"""
    try:
        return float(string)
    except ValueError:
        return 0.0


NUMBER_OF_TERMS = 10
REGULARIZATION = 0.0001
BACKGROUND_INPUT = 0.0
MAX_DIST = 140.0
DICT_KEYS = ["Calculator", "PrPlot", "DataPlot"]

logger = logging.getLogger(__name__)



class InversionWindow(QtWidgets.QDialog, Ui_PrInversion, Perspective):


    name = "Inversion"


    ext = "pr"
    tabsModifiedSignal = QtCore.Signal()
    @property
    def title(self) -> str:
        """ Window title"""
        return "P(r) Inversion Perspective"

    estimateSignal = QtCore.Signal(tuple)
    estimateNTSignal = QtCore.Signal(tuple)
    estimateDynamicNTSignal = QtCore.Signal(tuple)
    estimateDynamicSignal = QtCore.Signal(tuple)
    calculateSignal = QtCore.Signal(tuple)




    def __init__(self, parent=None):

        super(InversionWindow, self).__init__()


        self.setWindowTitle("P(r) Inversion Perspective")

        self._manager = parent
        # Needed for Batch fitting
        self.parent = parent
        self._parent = parent
        self.communicate = parent.communicator()
        self.tabCloseRequested.connect(self.tabCloses)

        # self.logic = InversionLogic()

        # List of active Pr Tabs
        self.tabs = []
        self.setTabsClosable(True)

        # The window should not close
        self._allowClose = False

        # Visible data items
        # current QStandardItem showing on the panel
        self._data = None
        # Reference to Dmax window for self._data
        self.dmaxWindow = None
        # p(r) calculator for self._data
        self._calculator = None

        # plots of self._data
        self.prPlot = None
        self.dataPlot = None
        # suggested nTerms
        self.nTermsSuggested = NUMBER_OF_TERMS

        self.maxIndex = 1
        self.tab_id = 1

        # Calculation threads used by all data items
        self.calcThread = None
        self.estimationThread = None
        self.estimationThreadNT = None
        self.isCalculating = False

        # Mapping for all data items
        # Dictionary mapping data to all parameters
        self._dataList = {}

        self.dataDeleted = False

        self.model = QtGui.QStandardItemModel(self)
        self.mapper = QtWidgets.QDataWidgetMapper(self)

        # Batch fitting parameters
        self.isBatch = False
        self.batchResultsWindow = None
        self.batchResults = {}

        # Max index for adding new, non-clashing tab names
        self.maxIndex = 1

        # The tabs need to be closeable
        self.setTabsClosable(True)

        # The tabs need to be movable
        self.setMovable(True)

        # Initialize the first tab
        self.addData(None)

    ######################################################################
    # Batch Mode and Tab Functions

    def calculate(self):
        # Default to background estimate
        self._calculator.est_bck = True

    def resetTab(self, index):
        """
        Adds a new tab and removes the last tab
        as a way of resetting the fit tabs
        """
        # If data on tab empty - do nothing
        if index in self.tabs and not self.tabs[index].data:
            return
        # Remove the previous last tab
        self.tabCloses(index)

    def tabCloses(self, index):
        """
        Update local bookkeeping on tab close
        """
        # don't remove the last tab
        if len(self.tabs) <= 1:
            return
        self.closeTabByIndex(index)

    def closeTabByIndex(self, index):
        """
        Close/delete a tab with the given index.
        No checks on validity of the index.
        """
        try:
            self.removeTab(index)
            del self.tabs[index]
            self.tabsModifiedSignal.emit()
        except IndexError:
            # The tab might have already been deleted previously
            pass

    ######################################################################
    # Base Perspective Class Definitions

    def communicator(self):
        return self.communicate

    def allowBatch(self):
        """
        Tell the caller we accept batch mode
        """
        return True

    def allowSwap(self):
        """
        Tell the caller we don't accept swapping data
        """
        return False

    def setClosable(self, value=True):
        """
        Allow outsiders close this widget
        """
        assert isinstance(value, bool)
        self._allowClose = value

    def isClosable(self):
        """
        Allow outsiders close this widget
        """
        return self._allowClose

    def isSerializable(self):
        """
        Tell the caller that this perspective writes its state
        """
        return True

    def closeDMax(self):
        if self.dmaxWindow is not None:
            self.dmaxWindow.close()

    def closeBatchResults(self):
        if self.batchResultsWindow is not None:
            self.batchResultsWindow.close()

    ######################################################################

    def setData(self, data_item=None, is_batch=False):
        """
        Assign new data set(s) to the P(r) perspective
        Obtain a QStandardItem object and parse it to get Data1D/2D
        Pass it over to the calculator
        """
        assert data_item is not None

        if not isinstance(data_item, list):
            msg = "Incorrect type passed to the P(r) Perspective"
            raise AttributeError(msg)

        if not isinstance(data_item[0], QtGui.QStandardItem):
            msg = "Incorrect type passed to the P(r) Perspective"
            raise AttributeError(msg)

        #
        for data in data_item:

            logic_data = GuiUtils.dataFromItem(data)

            if isinstance(logic_data, Data2D) and not is_batch:
                tab = self.addData(data=data)
                tab.is2D = True
                tab.tab2D.setEnabled(True)
                qmin, qmax = tab.logic.computeDataRange()
                tab._calculator.set_qmin(qmin)
                tab._calculator.set_qmax(qmax)
                tab.show2DPlot()

            if is_batch and not isinstance(logic_data, Data2D):
                # initiate a single Tab for batch
                self.addData(data=data_item, is_batch=is_batch)
                return

            if isinstance(logic_data, Data1D):
                tab = self.addData(data=data)
                qmin, qmax = tab.logic.computeDataRange()
                tab._calculator.set_qmin(qmin)
                tab._calculator.set_qmax(qmax)
                if np.size(logic_data.dy) == 0 or np.all(logic_data.dy) == 0:
                    tab.logic.add_errors()

            if isinstance(logic_data, Data2D) and is_batch:
                msg = "2D data cannot be batch processed in P(r) Perspective yet"
                raise AttributeError(msg)

                ###############

        # Checking for 1D again to mitigate the case when 2D data is last on the data list
        # if isinstance(self.logic.data, Data1D):
        #     self.setCurrentData(data)




    def removeData(self, data_list=None):
        """Remove the existing data reference from the P(r) Persepective"""
        self.dataDeleted = True
        self.batchResults = {}
        if not data_list:
            data_list = [self._data]
        self.closeDMax()
        for data in data_list:
            self._dataList.pop(data, None)
        if self.dataPlot:
            # Reset dataplot sliders
            self.dataPlot.slider_low_q_input = []
            self.dataPlot.slider_high_q_input = []
            self.dataPlot.slider_low_q_setter = []
            self.dataPlot.slider_high_q_setter = []
        self._data = None
        length = self.dataList.count()
        for index in reversed(range(length)):
            if self.dataList.itemData(index) in data_list:
                self.dataList.removeItem(index)
        # Last file removed
        self.dataDeleted = False
        # if self._dataList.count() == 0:
        if len(self._dataList) == 0:
            self.prPlot = None
            self.dataPlot = None
            self.logic.data = None
            self._calculator = Invertor()
            self.closeBatchResults()
            self.nTermsSuggested = NUMBER_OF_TERMS
            self.noOfTermsSuggestionButton.setText("{:n}".format(
                self.nTermsSuggested))
            self.regConstantSuggestionButton.setText("{:-3.2g}".format(
                REGULARIZATION))
            # self.updateGuiValues()
            self.setupModel()
        else:
            self.dataList.setCurrentIndex(0)
            self.updateGuiValues()

    def serializeAll(self):
        """
        Serialize the inversion state so data can be saved
        Inversion is not batch-ready so this will only effect a single page
        :return: {data-id: {self.name: {inversion-state}}}
        """
        return self.serializeCurrentPage()

    def serializeCurrentPage(self):
        # Serialize and return a dictionary of {data_id: inversion-state}
        # Return original dictionary if no data
        state = {}
        if self.logic.data_is_loaded:
            tab_data = self.getPage()
            data_id = tab_data.pop('data_id', '')
            state[data_id] = {'pr_params': tab_data}
        return state

    def getPage(self):
        """
        serializes full state of this fit page
        """
        # Get all parameters from page
        param_dict = self.getState()
        param_dict['data_name'] = str(self.logic.data.name)
        param_dict['data_id'] = str(self.logic.data.id)
        return param_dict

    def currentTabDataId(self):
        """
        Returns the data ID of the current tab
        """
        tab_id = []
        if self.logic.data_is_loaded:
            tab_id.append(str(self.logic.data.id))
        return tab_id


    def addData(self, data=None, is_batch=False, tab_index=None):
        """
        Add a new tab for passed data
        """

        if tab_index is None:
            tab_index = self.maxIndex
        else:
            self.maxIndex = tab_index

        # Create tab
        tab = InversionWidget(parent=self.parent, data=data, tab_id=tab_index)
        tab.set_tab_name("New Tab")

        if data is not None and not is_batch:
            tab.logic.data = GuiUtils.dataFromItem(data)
            tab.set_tab_name(tab.logic.data.name)
            tab.populateDataComboBox(tab.logic.data.name, data)

        # Setting UP batch Mode
        icon = QtGui.QIcon()
        if is_batch:
            tab.isBatch = True
            tab.set_tab_name("Pr Batch")
            icon.addPixmap(QtGui.QPixmap("src/sas/qtgui/images/icons/layers.svg"))
            tab.calculateAllButton.setVisible(True)
            tab.calculateThisButton.setVisible(False)
            tab.setPlotable(False)
            tab._allowPlots = False

            for i in data:
                tab.logic.data = GuiUtils.dataFromItem(i)
                tab.populateDataComboBox(name=tab.logic.data.name, data_ref=i)
        else:
            tab.calculateAllButton.setVisible(False)
            tab.showResultsButton.setVisible(False)
        self.addTab(tab, icon, tab.tab_name)
        tab.enableButtons()
        self.tabs.append(tab)

        # Show the new tab
        self.setCurrentWidget(tab)
        return tab
