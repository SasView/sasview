import logging
import numpy as np

from PyQt5 import QtGui, QtCore, QtWidgets

# sas-global
import sas.qtgui.Utilities.GuiUtils as GuiUtils

# pr inversion GUI elements
from .InversionWidget import InversionWidget

# pr inversion calculation elements
from sas.qtgui.Plotting.PlotterData import Data1D, Data2D

logger = logging.getLogger(__name__)


class InversionWindow(QtWidgets.QTabWidget):
    """
    The main window for the P(r) Inversion perspective.
    This is the main window where the tabs for each of the widgets are shown

    """

    name = "Inversion"
    ext = "pr"  # Extension used for saving analyses
    tabsModifiedSignal = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(InversionWindow, self).__init__()

        self.setWindowTitle("P(r) Inversion Perspective")
        self._manager = parent
        # Needed for Batch fitting
        self.parent = parent
        self._parent = parent
        self.communicate = parent.communicator()
        self.tabCloseRequested.connect(self.tabCloses)

        # List of active Pr Tabs
        self.tabs = []
        self.setTabsClosable(True)


        self.supports_reports = True
        self.supports_fitting_menu= False



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

    def serializeAll(self):
        """
        Serialize the inversion state so data can be saved
        Inversion is not batch-ready so this will only effect a single page
        :return: {data-id: {self.name: {inversion-state}}}
        """
        return self.serializeCurrentPage()

    def serializeCurrentPage(self, Index=None):
        """
        Serialize and return a dictionary of {data_id: inversion-state}
        Return original dictionary if no data
        """
        if Index is None:
            Index = self.currentIndex()
        tab = self.tabs[Index]
        state = {}
        if tab.logic.data_is_loaded:
            tab_data = tab.getPage()
            data_id = tab_data.pop('data_id', '')
            state[data_id] = {'pr_params': tab_data}
        return state

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

        for data in data_item:
            logic_data = GuiUtils.dataFromItem(data)

            # Tab for 2D data
            if isinstance(logic_data, Data2D) and not is_batch:
                data.isSliced = False
                tab = self.addData(data=data, is2D=True)
                tab.tab2D.setEnabled(True)
                tab.show2DPlot()

            # Tab for 1D batch
            if is_batch and not isinstance(logic_data, Data2D):
                # initiate a single Tab for batch
                self.addData(data=data_item, is_batch=is_batch)
                return

            # Tab for 1D
            if isinstance(logic_data, Data1D):
                tab = self.addData(data=data)
                tab.setQ()

                if np.size(logic_data.dy) == 0 or np.all(logic_data.dy) == 0:
                    tab.logic.add_errors()

            # let the user know that the 2D data cannot be batch processed
            if isinstance(logic_data, Data2D) and is_batch:
                msg = "2D data cannot be batch processed using the P(r) Perspective."
                raise AttributeError(msg)

        # replace the startup tab, so it looks like data has been added to it.
        if self.tabs[0].tab_name == "New Tab":
            self.closeTabByIndex(0)

    def addData(self, data=None, is_batch=False, tab_index=None, is2D=False):
        """
        Add a new tab for passed data
        """

        if tab_index is None:
            tab_index = self.maxIndex
        else:
            self.maxIndex = tab_index

        # Create tab
        tab = InversionWidget(parent=self.parent, data=data, tab_id=tab_index)
        tab.setTabName("New Tab")
        icon = QtGui.QIcon()

        if data is not None and not is_batch:
            tab.setTabName("New Tab")
            tab.is2D = is2D
            tab.logic.data = GuiUtils.dataFromItem(data)
            tab.setTabName(tab.logic.data.name)
            tab.populateDataComboBox(tab.logic.data.name, data)
            tab.calculateAllButton.setVisible(False)
            tab.showResultsButton.setVisible(False)

        # Setting UP batch Mode
        if is_batch:
            tab = self.createBatchTab(batchDataList=data)
            icon.addPixmap(QtGui.QPixmap("src/sas/qtgui/images/icons/layers.svg"))
        self.addTab(tab, icon, tab.tab_name)
        tab.enableButtons()
        self.tabs.append(tab)

        # Show the new tab
        self.setCurrentWidget(tab)
        return tab

    def createBatchTab(self, batchDataList):
        """
        setup for batch tab
        essentially this makes sure a batch tab is set up so that multiple files can be computed
        """
        batchTab = InversionWidget(parent=self.parent, data=batchDataList)
        batchTab.setTabName("Pr Batch")
        batchTab.isBatch = True
        batchTab.setPlotable(False)
        for data in batchDataList:
            batchTab.logic.data = GuiUtils.dataFromItem(data)
            batchTab.populateDataComboBox(name=batchTab.logic.data.name, data_ref=data)
            batchTab.updateDataList(data)
        batchTab.setCurrentData(batchDataList[0])
        return batchTab
