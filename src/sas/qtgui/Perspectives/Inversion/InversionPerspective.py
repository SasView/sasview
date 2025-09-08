import logging

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

# sas-global
import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Perspectives.Inversion.InversionWidget import InversionWidget

# Batch calculation display
from sas.qtgui.Perspectives.perspective import Perspective

# pr inversion calculation elements
from sas.qtgui.Plotting.PlotterData import Data1D

# pr inversion GUI elements
from .InversionLogic import InversionLogic

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

    def __init__(self, parent=None,data=None):
        super().__init__()


        self.setWindowTitle("P(r) Inversion Perspective")

        # Max index for adding new, non-clashing tab names
        self.maxIndex = 1
        # Needed for Batch inversion
        self.parent = parent
        self.communicate = self.parent.communicate
        #self.communicate = self.parent.communicator()
        self.communicate.dataDeletedSignal.connect(self.removeData)
        self.tabCloseRequested.connect(self.tabCloses)

        # List of active Pr Tabs
        self.tabs: list[InversionWidget] = []
        self.setTabsClosable(True)


        # The window should not close
        self._allowClose = False

        # Visible data items
        # current QStandardItem showing on the panel
        self._data = data



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

        self.logic = InversionLogic()


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
        # If we're removing the last tab, create a new empty tab.
        if len(self.tabs) <= 1:
            self.addData(None)
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
        tab_ids = [tab.tab_id for tab in self.tabs]
        batch_warned = False
        for index, _ in enumerate(tab_ids):
            tab_state, warn_batch = self.getSerializePage(index)
            if not batch_warned and warn_batch:
                batch_warned = True
                _ = QtWidgets.QMessageBox.warning(self, "Batch Serialisation", """Saving of projects with batch inversion
tabs is currently not supported. Support will be added in a later version of SasView but please note
that in the meantime, these tabs will be excluded from the saved project.""")
            state.update(tab_state)
        return state

    def serializeCurrentPage(self):
        # serialize current (active) page
        return self.getSerializePage(self.currentIndex())

    def getSerializePage(self, index=None) -> tuple[dict, bool]:
        """
        Serialize and return a dictionary of {tab_id: inversion-state}
        Return original dictionary if no data
        """
        state = {}
        # If any tabs are batch tabs, these are not supported for serialisation so this needs to be true.
        if index is None:
            index = self.currentIndex()
        # If data on tab empty - do nothing TODO: Reinstate this check.
        tab = self.tabs[index]
        if tab.currentResult.logic.data_is_loaded:
            if tab.is_batch:
                return {}, True
            tab_data = tab.getPage()
            data_id = tab_data.pop('data_id', '')
            state[data_id] = {'pr_params': tab_data}
        return state, False


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
        if self.currentTab.dmaxWindow is not None:
            self.currentTab.dmaxWindow.close()

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




    ######################################################################
    # GUI Interaction Events


    def help(self):
        """
        Open the P(r) Inversion help browser
        """
        tree_location = "/user/qtgui/Perspectives/Inversion/pr_help.html"

        # Actual file anchor will depend on the combo box index
        # Note that we can be clusmy here, since bad current_fitter_id
        # will just make the page displayed from the top
        self.parent.showHelp(tree_location)







    ######################################################################
    # Response Actions

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

#        if is_batch:
#            # Just create a new fit tab. No empty batchFit tabs
#            self.addData(data_item, is_batch=is_batch)
#            return


        items = [data_item] if (is_batch and len(data_item)>1) else data_item
        for data in items:
            logic_data = GuiUtils.dataFromItem(data)
            if logic_data is not None and not isinstance(logic_data, Data1D):
                msg = "Inversion cannot be computed with 2D data."
                raise ValueError(msg)


            # Find the first unassigned tab.
            # If none, open a new tab.
            available_tabs = [tab.acceptsData() for tab in self.tabs]
            tab_ids = [tab.tab_id for tab in self.tabs]
            if tab_index is not None:
                if tab_index not in tab_ids:
                    self.addData(data = data, is_batch=is_batch, tab_index=tab_index)
                else:
                    self.setCurrentIndex(tab_index-1)
                    self.swapData(data = data,tab_index=self.currentIndex())
                    return
            #debug Batch mode, gives none Type has no attribute name
            if not is_batch and np.any(available_tabs):
                first_good_tab = available_tabs.index(True)
                self.tabs[first_good_tab].data = data
                self.tabs[first_good_tab].updateTab(data = data, tab_id=first_good_tab)

            else:
                self.addData(data = data, is_batch=is_batch, tab_index = tab_index)





    def swapData(self, data = None, tab_index=None):
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
        self.currentTab.updateTab(data = data, tab_id= tab_index)




    @property
    def currentTab(self) -> InversionWidget:
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

    def removeData(self, data_list: list[QtGui.QStandardItem]):
        # We need this list because we can't modify the tabs list while looping over it.
        tabs_to_remove: list[InversionWidget] = []
        for datum in data_list:
            for tab in self.tabs:
                if any([result.logic.data_item == datum for result in tab.results]):
                    tabs_to_remove.append(tab)
        for to_remove in tabs_to_remove:
            self.closeTabByName(to_remove.tab_name)

    def addData(self, data=None, is_batch=False, tab_index=None):

        """
        Add a new tab for passed data
        """

        if tab_index is None:
            tab_index = self.maxIndex
        else:
            self.maxIndex = tab_index

        # Create tab
        # tab = InversionWidget(parent=self.parent, data=data, tab_id=tab_index)
        tab_name = self.getTabName(is_batch=is_batch)
        tab = InversionWidget(self, self.parent, data, tab_index, tab_name)
        #ObjectLibrary.addObject(tab_name, tab)
        icon = QtGui.QIcon()
        # Setting UP batch Mode for 1D data
        if is_batch:
            icon.addPixmap(QtGui.QPixmap("src/sas/qtgui/images/icons/layers.svg"))
        if data is not None:
            tab.updateTab(data = data, tab_id=tab_index)

        self.addTab(tab, icon, tab.tab_name)
        tab.enableButtons()
        self.tabs.append(tab)

        # the new tab
        self.maxIndex = max([tab.tab_id for tab in self.tabs], default=0) + 1
        self.setCurrentWidget(tab)

    def updateFromParameters(self, params):
        inversion_widget = self.currentWidget()
        if isinstance(inversion_widget, InversionWidget):
            inversion_widget.updateFromParameters(params)
