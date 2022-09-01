import logging
import numpy as np

from PyQt5 import QtGui, QtCore, QtWidgets
import sas.qtgui.Utilities.GuiUtils as GuiUtils

# pr inversion GUI elements
from .InversionWidget import InversionWidget

# pr inversion calculation elements
from sas.qtgui.Plotting.PlotterData import Data1D, Data2D

logger = logging.getLogger(__name__)

class InversionWindow(QtWidgets.QTabWidget):

    """
    The main window for the P(r) Inversion perspective.
    """

    name = "Inversion"
    ext = "pr"  # Extension used for saving analyses
    tabsModifiedSignal = QtCore.pyqtSignal()

    estimateSignal = QtCore.pyqtSignal(tuple)
    estimateNTSignal = QtCore.pyqtSignal(tuple)
    estimateDynamicNTSignal = QtCore.pyqtSignal(tuple)
    estimateDynamicSignal = QtCore.pyqtSignal(tuple)
    calculateSignal = QtCore.pyqtSignal(tuple)
    forcePlotDisplaySignal = QtCore.pyqtSignal(list)

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
                data.isSliced = False
                tab = self.addData(data=data, is2D=True)
                tab.tab2D.setEnabled(True)
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

        if self.tabs[0].tab_name == "New Tab":
            self.closeTabByIndex(0)
                ###############
        # Checking for 1D again to mitigate the case when 2D data is last on the data list
        # if isinstance(self.logic.data, Data1D):
        #     self.setCurrentData(data)

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
        tab.set_tab_name("New Tab")
        tab.is2D = is2D

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
            tab.calculateThisButton.setVisible(True)
            tab.setPlotable(False)

            for i in data:
                tab.logic.data = GuiUtils.dataFromItem(i) # Fix this for batch
                tab.populateDataComboBox(name=tab.logic.data.name, data_ref=i)
                tab.updateDataList(i)
            tab.setCurrentData(data[0])
        else:
            tab.calculateAllButton.setVisible(False)
            tab.showResultsButton.setVisible(False)

        self.addTab(tab, icon, tab.tab_name)
        tab.enableButtons()
        self.tabs.append(tab)

        # Show the new tab
        self.setCurrentWidget(tab)
        return tab

