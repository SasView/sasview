import logging
import numpy as np

from PyQt5 import QtGui, QtCore, QtWidgets

# sas-global
import sas.qtgui.Utilities.GuiUtils as GuiUtils

# pr inversion GUI elements
from .InversionUtils import WIDGETS
from .InversionWidget import InversionWidget
from .InversionLogic import InversionLogic

# pr inversion calculation elements
from sas.sascalc.pr.invertor import Invertor
from sas.qtgui.Plotting.PlotterData import Data1D
# Batch calculation display
from sas.qtgui.Utilities.GridPanel import BatchInversionOutputPanel


def is_float(value):
    """Converts text input values to floats. Empty strings throw ValueError"""
    try:
        return float(value)
    except ValueError:
        return 0.0


NUMBER_OF_TERMS = 10
REGULARIZATION = 0.0001
BACKGROUND_INPUT = 0.0
MAX_DIST = 140.0
DICT_KEYS = ["Calculator", "PrPlot", "DataPlot"]

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

    def __init__(self, parent=None, data=None):
        super(InversionWindow, self).__init__()

        self.setWindowTitle("P(r) Inversion Perspective")
        self._manager = parent
        # Needed for Batch fitting
        self.parent = parent
        self._parent = parent
        self.communicate = parent.communicator()
        self.communicate.dataDeletedSignal.connect(self.removeData)

        self.logic = InversionLogic()

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
        self._calculator = Invertor()
        # Default to background estimate
        self._calculator.est_bck = True
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
        self.tabCloseRequested.connect(self.tabCloses)

        # Batch fitting parameters
        self.isBatch = False
        self.batchResultsWindow = None
        self.batchResults = {}

        # Max index for adding new, non-clashing tab names
        self.maxIndex = 1

        # The tabs need to be closeable
        self.setTabsClosable(True)

        # The tabs need to be movabe
        self.setMovable(True)

        self.communicate = self.parent.communicator()

        # Initialize the first tab
        self.addData(None)

    ######################################################################
    # Base Perspective Class Definitions

    def communicator(self):
        return self.communicate

    def allowBatch(self):
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

    #####

    def resetTab(self, index):
        """
        Adds a new tab and removes the last tab
        as a way of resetting the fit tabs
        """
        # If data on tab empty - do nothing
        if index in self.tabs and not self.tabs[index].data:
            return
        # Add a new, empy tab
        #self.addData(None)
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
            print("[ DEBUG ] IndexError line 192")
            # The tab might have already been deleted previously
        pass
        #######

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

    def populateDataComboBox(self, name, data_ref):
        """
        Append a new name to the data combobox
        :param name: data name
        :param data_ref: QStandardItem reference for data set to be added
        """
        for i in self.tabs:
            i.dataList.addItem(name, data_ref)

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

        if is_batch:
            tab = self.addData(name="Pr Batch", data=None, is_batch=is_batch)

        for data in data_item:
            # if data in self._dataList.keys():
            #     # Don't add data if it's already in
            #     continue
            # Create initial internal mappings
            self.logic.data = GuiUtils.dataFromItem(data)
            if not isinstance(self.logic.data, Data1D):
                msg = "P(r) perspective cannot be computed with 2D data."
                logger.error(msg)
                raise ValueError(msg)
            # Estimate q range
            qmin, qmax = self.logic.computeDataRange()
            self._calculator.set_qmin(qmin)
            self._calculator.set_qmax(qmax)
            if np.size(self.logic.data.dy) == 0 or np.all(self.logic.data.dy) == 0:
                self.logic.add_errors()
            self.updateDataList(data)
            if is_batch:
                tab.populateDataComboBox(name=self.logic.data.name, data_ref=data)
            if not is_batch:
                self.addData(name=self.logic.data.name, data=data, is_batch=is_batch, tab_index=None)

        # Checking for 1D again to mitigate the case when 2D data is last on the data list
        # if isinstance(self.logic.data, Data1D):
        #     self.setCurrentData(data)

    def updateDataList(self, dataRef):
        """Save the current data state of the window into self._data_list"""
        if dataRef is None:
            return
        self._dataList[dataRef] = {
            DICT_KEYS[0]: self._calculator,
            DICT_KEYS[1]: self.prPlot,
            DICT_KEYS[2]: self.dataPlot
        }
        # Update batch results window when finished
        self.batchResults[self.logic.data.name] = self._calculator
        print(self._calculator)
        #
        # if self.batchResultsWindow is not None: # enable when batch is fixed
        #       self.showBatchOutput()

    def getState(self):
        """
        Collects all active params into a dictionary of {name: value}
        :return: {name: value}
        """
        # If no measurement performed, calculate using base params
        # if self.chiDofValue.text() == '':
        #     self._calculator.out, self._calculator.cov = self._calculator.invert()
        return {
            'alpha': self._calculator.alpha,
            'background': self._calculator.background,
            'chi2': self._calculator.chi2,
            'cov': self._calculator.cov,
            'd_max': self._calculator.d_max,
            'elapsed': self._calculator.elapsed,
            'err': self._calculator.err,
            'est_bck': self._calculator.est_bck,
            'iq0': self._calculator.iq0(self._calculator.out),
            'nerr': self._calculator.nerr,
            'nfunc': self.getNFunc(),
            'npoints': self._calculator.npoints,
            'ny': self._calculator.ny,
            'out': self._calculator.out,
            'oscillations': self._calculator.oscillations(self._calculator.out),
            'pos_frac': self._calculator.get_positive(self._calculator.out),
            'pos_err': self._calculator.get_pos_err(self._calculator.out,
                                                    self._calculator.cov),
            'q_max': self._calculator.q_max,
            'q_min': self._calculator.q_min,
            'rg': self._calculator.rg(self._calculator.out),
            'slit_height': self._calculator.slit_height,
            'slit_width': self._calculator.slit_width,
            'suggested_alpha': self._calculator.suggested_alpha,
            'x': self._calculator.x,
            'y': self._calculator.y,
        }

    def getNFunc(self):
        """Get the n_func value from the GUI object"""
        try:
            nfunc = int(self.noOfTermsInput.text())
        except ValueError:
            logger.error("Incorrect number of terms specified: %s"
                         % self.noOfTermsInput.text())
            self.noOfTermsInput.setText(str(NUMBER_OF_TERMS))
            nfunc = NUMBER_OF_TERMS
        return nfunc

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
            self.communicate.plotRequestedSignal.emit([self._data, self.prPlot], None)
        if self.dataPlot is not None:
            title = self.dataPlot.name
            self.dataPlot.plot_role = Data1D.ROLE_DEFAULT
            self.dataPlot.symbol = "Line"
            self.dataPlot.show_errors = False
            GuiUtils.updateModelItemWithPlot(self._data, self.dataPlot, title)
            self.communicate.plotRequestedSignal.emit([self._data, self.dataPlot], None)
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
            self.updateGuiValues()
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

    def addData(self, name=None, data=None, is_batch=False, tab_index=None):
        """
        Add a new tab for passed data
        """
        if tab_index is None:
            tab_index = self.maxIndex
        else:
            self.maxIndex = tab_index

        # Create tab
        tab = InversionWidget(parent=self.parent, data=data, tab_id=tab_index)

        # set name to "New Pr Tab" if no name is set to the data set
        if name is None:
            tab.name = "New Pr Tab"
        else:
            tab.name = name

        # if the length of the name is over 23 shorten it and add ellipsis
        if len(tab.name) >= 23:
            tab.name = tab.name[:20] + "..."

        if data is not None and not is_batch:
            tab.populateDataComboBox(self.logic.data.name, data)

        # self.maxIndex = max([tab.tab_id for tab in self.tabs], default=0) + 1  # ERROR: list index out of range
        icon = QtGui.QIcon()
        if is_batch:
            tab.name = "Pr Batch"
            tab.is_batch_fitting = is_batch
            icon.addPixmap(QtGui.QPixmap("src/sas/qtgui/images/icons/layers.svg"))
            tab.calculateAllButton.setVisible(True)
            tab.calculateAllButton.setEnabled(True)
            tab.startNextBatchItem()
        self.addTab(tab, icon, tab.name)
        self.tabs.append(tab)

        # Show the new tab
        self.setCurrentWidget(tab)
        return tab