import logging
import numpy as np


from PySide6 import QtGui, QtCore, QtWidgets

# sas-global

import sas.qtgui.Utilities.GuiUtils as GuiUtils

# pr inversion GUI elements
from .InversionUtils import WIDGETS
from .UI.TabbedInversionUI import Ui_PrInversion
from .InversionLogic import InversionLogic

# pr inversion calculation elements

from sas.sascalc.pr.invertor import Invertor
from sas.qtgui.Plotting.PlotterData import Data1D, Data2D
# Batch calculation display
from sas.qtgui.Utilities.GridPanel import BatchInversionOutputPanel
from sas.qtgui.Perspectives.perspective import Perspective
from sas.qtgui.Perspectives.Inversion.InversionWidget import InversionWidget, DICT_KEYS, NUMBER_OF_TERMS, REGULARIZATION



logger = logging.getLogger(__name__)

class InversionWindow(QtWidgets.QTabWidget, Perspective):
    """
    The main window for the P(r) Inversion perspective.
    This is the main window where the tabs for each of the widgets are shown

    """


    name = "Inversion"
    ext = "pr"

    @property
    def title(self):
        return "P(r) Inversion"

    @property
    def title(self):
        return "P(r) Inversion"


    def __init__(self, parent=None,data=None):
        super().__init__()


        self.setWindowTitle("P(r) Inversion Perspective")

        # Max index for adding new, non-clashing tab names
        self.maxIndex = 1
        # Needed for Batch inversion
        self.parent = parent
        self.communicate = self.parent.communicate
        self.tabCloseRequested.connect(self.tabCloses)

        # List of active Pr Tabs
        self.tabs = []
        self.setTabsClosable(True)


        # The window should not close
        self._allowClose = False

        # Visible data items
        # current QStandardItem showing on the panel
        self._data = data
        
        # Reference to Dmax window for self._data
        self.dmaxWindow = None
        # p(r) calculator for self._data
        self._calculator = None

        # plots of self._data
        self.prPlot = None
        self.dataPlot = None
        # suggested nTerms



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

        # Batch parameters
        self.is_batch = False
        self.batchResultsWindow = None
        self.batchResults = {}




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
        as a way of resetting the tabs
        """
        # If data on tab empty - do nothing
        if index in self.tabs and not self.tabs[index].data:
            return
        # Add a new, empy tab
        self.addData(None)
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

        except IndexError:
            # The tab might have already been deleted previously
            pass


    def closeTabByName(self, tab_name):
        """
        Given name of the tab - close it
        """
        for tab_index in range(len(self.tabs)):
            if self.tabText(tab_index) == tab_name:
                self.tabCloses(tab_index)
        pass # debug hook
    ######################################################################

    def serializeAll(self):
        """
        Serialize the inversion state so data can be saved
        serialize all active inversion pages and return
        a dictionary: {data-id: {self.name: {inversion-state}}}
        """
        state = {}
        index = [tab.tab_id for tab in self.tabs]
        try:          
            for i in index:              
                state.update(self.getSerializePage(i))
        except TypeError:
            return
        return state

    def serializeCurrentPage(self):
        # serialize current (active) page
        return self.getSerializePage(self.currentIndex())

    def getSerializePage(self, index=None):
        """
        Serialize and return a dictionary of {data_id: inversion-state}
        Return original dictionary if no data
        """
        state = {}
        if index is None:
            index = self.currentIndex()
        # If data on tab empty - do nothing
        try:
            tab = self.tabs[index]        
            if tab.logic.data_is_loaded:
                tab_data = tab.getPage()
                data_id = tab_data.pop('data_id', '')
                state[data_id] = {'pr_params': tab_data}
            return state
        except:
             return
            

    def updateFromParameters(self, params: dict, tab_name):
        """ Update the perspective using a dictionary of parameters
        e.g. those loaded via open project or open analysis menu items"""
        raise NotImplementedError("Update from parameters not implemented yet.")


    ######################################################################
    # Base Perspective Class Definitions


    @property
    def supports_reports(self):
        return True
        
    @property
    def supports_fitting(self):
        return False

    def communicator(self):
        return self.filesWidget.communicate


    def allowBatch(self):
        """
        Tell the caller we accept batch mode
        """
        return True

    def allowSwap(self):
        """
        Tell the caller we accept swapping data
        """
        return True

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

    def getTabName(self, is_batch=False):
        """
        Get the new tab name, based on the number of fitting tabs so far
        """
        page_name = "PrBatchPage" if is_batch else "PrPage"
        page_name = page_name + str(self.maxIndex)
        return page_name


    def acceptAlpha(self):
        """Send estimated alpha to input"""
        self.model.setItem(WIDGETS.W_REGULARIZATION, QtGui.QStandardItem(
            self.regConstantSuggestionButton.text()))

    def displayChange(self, data_index=0):
        """Switch to another item in the data list"""
        if self.dataDeleted:
            return
        self.updateDataList(self._data)
        self.setCurrentData(self.dataList.itemData(data_index))

    ######################################################################
    # GUI Interaction Events

    def updateCalculator(self):
        """Update all p(r) params"""
        self._calculator.set_x(self.logic.data.x)
        self._calculator.set_y(self.logic.data.y)
        self._calculator.set_err(self.logic.data.dy)
        self.set_background(self.backgroundInput.text())

    def set_background(self, value):
        self._calculator.background = float(value)

    def model_changed(self):
        """Update the values when user makes changes"""
        if not self.mapper:
            msg = "Unable to update P{r}. The connection between the main GUI "
            msg += "and P(r) was severed. Attempting to restart P(r)."
            logger.warning(msg)
            self.setClosable(True)
            self.close()
            InversionWindow.__init__(self.parent(), list(self._dataList.keys()))
            exit(0)
        if self.dmaxWindow is not None:
            self.dmaxWindow.nfunc = self.getNFunc()
            self.dmaxWindow.pr_state = self._calculator
        self.mapper.toLast()

    def help(self):
        """
        Open the P(r) Inversion help browser
        """
        tree_location = "/user/qtgui/Perspectives/Inversion/pr_help.html"

        # Actual file anchor will depend on the combo box index
        # Note that we can be clusmy here, since bad current_fitter_id
        # will just make the page displayed from the top
        self._manager.showHelp(tree_location)

    def toggleBgd(self):
        """
        Toggle the background between manual and estimated
        """
        self.model.blockSignals(True)
        value = 1 if self.estimateBgd.isChecked() else 0
        itemt = QtGui.QStandardItem(str(value == 1).lower())
        self.model.setItem(WIDGETS.W_ESTIMATE, itemt)
        itemt = QtGui.QStandardItem(str(value == 0).lower())
        self.model.setItem(WIDGETS.W_MANUAL_INPUT, itemt)
        self._calculator.set_est_bck(value)
        self.backgroundInput.setEnabled(self._calculator.est_bck == 0)
        self.model.blockSignals(False)

    def openExplorerWindow(self):
        """
        Open the Explorer window to see correlations between params and results
        """
        from .DMaxExplorerWidget import DmaxWindow
        self.dmaxWindow = DmaxWindow(pr_state=self._calculator,
                                     nfunc=self.getNFunc(),
                                     parent=self)
        self.dmaxWindow.show()

    def showBatchOutput(self):
        """
        Display the batch output in tabular form
        :param output_data: Dictionary mapping name -> P(r) instance
        """
        if self.batchResultsWindow is None:
            self.batchResultsWindow = BatchInversionOutputPanel(
                parent=self._parent, output_data=self.batchResults)
        else:
            self.batchResultsWindow.setupTable(self.batchResults)
        self.batchResultsWindow.show()

    def stopCalculation(self):
        """ Stop all threads, return to the base state and update GUI """
        self.stopCalcThread()
        self.stopEstimationThread()
        self.stopEstimateNTThread()
        # Show any batch calculations that successfully completed
        if self.isBatch and self.batchResultsWindow is not None:
            self.showBatchOutput()
        self.isBatch = False
        self.isCalculating = False
        self.updateGuiValues()

    def check_q_low(self, q_value=None):
        """ Validate the low q value """
        if not q_value:
            q_value = float(self.minQInput.text()) if self.minQInput.text() else '0.0'
        q_min = min(self._calculator.x) if any(self._calculator.x) else -1 * np.inf
        q_max = self._calculator.get_qmax() if self._calculator.get_qmax() is not None else np.inf
        if q_value > q_max:
            # Value too high - coerce to max q
            self.model.setItem(WIDGETS.W_QMIN, QtGui.QStandardItem("{:.4g}".format(q_max)))
        elif q_value < q_min:
            # Value too low - coerce to min q
            self.model.setItem(WIDGETS.W_QMIN, QtGui.QStandardItem("{:.4g}".format(q_min)))
        else:
            # Valid Q - set model item
            self.model.setItem(WIDGETS.W_QMIN, QtGui.QStandardItem("{:.4g}".format(q_value)))
            self._calculator.set_qmin(q_value)

    def check_q_high(self, q_value=None):
        """ Validate the value of high q sent by the slider """
        if not q_value:
            q_value = float(self.maxQInput.text()) if self.maxQInput.text() else '1.0'
        q_max = max(self._calculator.x) if any(self._calculator.x) else np.inf
        q_min = self._calculator.get_qmin() if self._calculator.get_qmin() is not None else -1 * np.inf
        if q_value > q_max:
            # Value too high - coerce to max q
            self.model.setItem(WIDGETS.W_QMAX, QtGui.QStandardItem("{:.4g}".format(q_max)))
        elif q_value < q_min:
            # Value too low - coerce to min q
            self.model.setItem(WIDGETS.W_QMAX, QtGui.QStandardItem("{:.4g}".format(q_min)))
        else:
            # Valid Q - set model item
            self.model.setItem(WIDGETS.W_QMAX, QtGui.QStandardItem("{:.4g}".format(q_value)))
            self._calculator.set_qmax(q_value)

    ######################################################################
    # Response Actions

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



        items = [data_item] if (is_batch and len(data_item)>1) else data_item
        for data in items:
            logic_data = GuiUtils.dataFromItem(data)
            is_2Ddata = isinstance(logic_data, Data2D)
            if is_2Ddata and is_batch:
                 msg = "2D Data cannot be inverted as Batch"
                 raise RuntimeError(msg)
            else:    
                # Find the first unassigned tab.
                # If none, open a new tab.
                available_tabs = [tab.acceptsData() for tab in self.tabs]
                tab_ids = [tab.tab_id for tab in self.tabs]
                if tab_index is not None:
                    if tab_index not in tab_ids: 
                        self.addData(data = data, is2D=is_2Ddata, is_batch=is_batch, tab_index=tab_index)
                    else:
                        self.setCurrentIndex(tab_index-1)                
                        self.swapData(data = data, is2D = is_2Ddata,tab_index=self.currentIndex())
                        return
                #debug Batch mode, gives none Type has no attribute name
                if not is_batch and np.any(available_tabs):
                    first_good_tab = available_tabs.index(True)
                    self.tabs[first_good_tab].data = data
                    self.tabs[first_good_tab].updateTab(data = data, is2D = is_2Ddata, tab_index=first_good_tab) 

                else:
                    self.addData(data = data, is2D=is_2Ddata, is_batch=is_batch, tab_index = tab_index)               





    def swapData(self, data = None, is2D = False,tab_index=None):
        """
        Replace the data from the current tab
        """
        if not isinstance(self.currentWidget(), InversionWidget):
            msg = "Current tab is not  an Inversion widget"
            raise TypeError(msg)

        if not isinstance(data, QtGui.QStandardItem):
            msg = "Incorrect type passed to the Inversion Perspective"
            raise AttributeError(msg)

        if self.currentTab.is_batch:
            msg = "Data in Batch Inversion cannot be swapped"
            raise RuntimeError(msg)

        self.currentTab.data = data
        self.currentTab.updateTab(data = data, is2D = is2D,tab_index= tab_index)




    @property
    def currentTab(self): # TODO: More pythonic name
        """
        Returns the tab widget currently shown
        """
        return self.currentWidget()

    def currentTabDataId(self):
        """
        Returns the data ID of the current tab
        """
        tab_id = []
        if not self.currentTab.data:
            return tab_id
        for item in self.currentTab.all_data:
            data = GuiUtils.dataFromItem(item)
            tab_id.append(data.id)

        return tab_id




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
        tab_name = self.getTabName(is_batch=is_batch)
        tab.tab_name=tab_name
        #ObjectLibrary.addObject(tab_name, tab)
        icon = QtGui.QIcon()
        # Setting UP batch Mode for 1D data
        if is_batch and not is2D:
            tab.setPlotable(False)
            for element in data:
                tab.logic.data = GuiUtils.dataFromItem(element)
                tab.populateDataComboBox(name=tab.logic.data.name, data_ref=element)
                tab.updateDataList(element)
                tab.logic.add_errors()
                tab.setQ()
            tab.setCurrentData(data[0])
            icon.addPixmap(QtGui.QPixmap("src/sas/qtgui/images/icons/layers.svg"))
        else:        
            if data is not None:               
                tab.updateTab(data = data, is2D = is2D, tab_index=tab_index)
                
        tab.is_batch = is_batch                
        self.addTab(tab, icon, tab.tab_name)
        tab.enableButtons()
        self.tabs.append(tab)

        # the new tab
        self.maxIndex = max([tab.tab_id for tab in self.tabs], default=0) + 1
        self.setCurrentWidget(tab)



   
