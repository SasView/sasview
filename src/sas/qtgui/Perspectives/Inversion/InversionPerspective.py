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

    def closeEvent(self, event):
        """
        Overwrite QDialog close method to allow for custom widget close
        """
        # Close report widgets before closing/minimizing main widget
        self.closeDMax()
        self.closeBatchResults()
        if self._allowClose:
            # reset the closability flag
            self.setClosable(value=False)
            # Tell the MdiArea to close the container if it is visible
            if self.parentWidget():
                self.parentWidget().close()
            event.accept()
        else:
            event.ignore()
            # Maybe we should just minimize
            self.setWindowState(QtCore.Qt.WindowMinimized)

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

    def setCurrentData(self, data_ref):
        """Get the data by reference and display as necessary"""
        if data_ref is None:
            return
        if not isinstance(data_ref, QtGui.QStandardItem):
            msg = "Incorrect type passed to the P(r) Perspective"
            raise AttributeError(msg)
        # Data references
        self._data = data_ref
        self.logic.data = GuiUtils.dataFromItem(data_ref)
        self._calculator = self._dataList[data_ref].get(DICT_KEYS[0])
        self.prPlot = self._dataList[data_ref].get(DICT_KEYS[1])
        self.dataPlot = self._dataList[data_ref].get(DICT_KEYS[2])
        self.performEstimate()

    def updateDynamicGuiValues(self):
        pr = self._calculator
        alpha = self._calculator.suggested_alpha
        self.model.setItem(WIDGETS.W_MAX_DIST,
                            QtGui.QStandardItem("{:.4g}".format(pr.get_dmax())))
        self.regConstantSuggestionButton.setText("{:-3.2g}".format(alpha))
        self.noOfTermsSuggestionButton.setText(
             "{:n}".format(self.nTermsSuggested))

        self.enableButtons()

    def updateGuiValues(self):
        pr = self._calculator
        out = self._calculator.out
        cov = self._calculator.cov
        elapsed = self._calculator.elapsed
        alpha = self._calculator.suggested_alpha
        self.check_q_high(pr.get_qmax())
        self.check_q_low(pr.get_qmin())
        self.model.setItem(WIDGETS.W_BACKGROUND_INPUT,
                           QtGui.QStandardItem("{:.3g}".format(pr.background)))
        self.model.setItem(WIDGETS.W_BACKGROUND_OUTPUT,
                           QtGui.QStandardItem("{:.3g}".format(pr.background)))
        self.model.setItem(WIDGETS.W_COMP_TIME,
                           QtGui.QStandardItem("{:.4g}".format(elapsed)))
        self.model.setItem(WIDGETS.W_MAX_DIST,
                           QtGui.QStandardItem("{:.4g}".format(pr.get_dmax())))
        self.regConstantSuggestionButton.setText("{:.2g}".format(alpha))

        if isinstance(pr.chi2, np.ndarray):
            self.model.setItem(WIDGETS.W_CHI_SQUARED,
                               QtGui.QStandardItem("{:.3g}".format(pr.chi2[0])))
        if out is not None:
            self.model.setItem(WIDGETS.W_RG,
                               QtGui.QStandardItem("{:.3g}".format(pr.rg(out))))
            self.model.setItem(WIDGETS.W_I_ZERO,
                               QtGui.QStandardItem(
                                   "{:.3g}".format(pr.iq0(out))))
            self.model.setItem(WIDGETS.W_OSCILLATION, QtGui.QStandardItem(
                "{:.3g}".format(pr.oscillations(out))))
            self.model.setItem(WIDGETS.W_POS_FRACTION, QtGui.QStandardItem(
                "{:.3g}".format(pr.get_positive(out))))
            if cov is not None:
                self.model.setItem(WIDGETS.W_SIGMA_POS_FRACTION,
                                   QtGui.QStandardItem(
                                       "{:.3g}".format(
                                           pr.get_pos_err(out, cov))))
        if self.prPlot is not None:
            title = self.prPlot.name
            self.prPlot.plot_role = Data1D.ROLE_RESIDUAL
            GuiUtils.updateModelItemWithPlot(self._data, self.prPlot, title)
            self.communicate.plotRequestedSignal.emit([self._data,self.prPlot], None)
        if self.dataPlot is not None:
            title = self.dataPlot.name
            self.dataPlot.plot_role = Data1D.ROLE_DEFAULT
            self.dataPlot.symbol = "Line"
            self.dataPlot.show_errors = False
            GuiUtils.updateModelItemWithPlot(self._data, self.dataPlot, title)
            self.communicate.plotRequestedSignal.emit([self._data,self.dataPlot], None)
        self.enableButtons()

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
        length = len(self.dataList)
        for index in reversed(range(length)):
            if self.dataList.itemData(index) in data_list:
                self.dataList.removeItem(index)
        # Last file removed
        self.dataDeleted = False
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
