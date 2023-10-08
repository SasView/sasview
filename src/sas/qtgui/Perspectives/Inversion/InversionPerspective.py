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
        self._manager = parent

        # Max index for adding new, non-clashing tab names
        self.maxIndex = 1
        # Needed for Batch inversion
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
        return self.communicate

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

    def setData(self, data_item=None, is_batch=False, tab_index=None):
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
                        self.swapData(data = data, is2D = is_2Ddata)
                        return
                #debug Batch mode, gives none Type has no attribute name
                if not is_batch and np.any(available_tabs):
                    first_good_tab = available_tabs.index(True)
                    self.tabs[first_good_tab].data = data
                    self.tabs[first_good_tab].updateTab(data = data, is2D = is_2Ddata) 

                else:
                    self.addData(data = data, is2D=is_2Ddata, is_batch=is_batch, tab_index = tab_index)               





    def swapData(self, data = None, is2D = False):
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
        self.currentTab.updateTab(data = data, is2D = is2D)




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
                tab.updateTab(data = data, is2D = is2D)
                
        tab.is_batch = is_batch                
        self.addTab(tab, icon, tab.tab_name)
        tab.enableButtons()
        self.tabs.append(tab)

        # Show the new tab
        self.maxIndex = max([tab.tab_id for tab in self.tabs], default=0) + 1
        self.setCurrentWidget(tab)



   
