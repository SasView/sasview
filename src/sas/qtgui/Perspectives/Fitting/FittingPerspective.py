import numpy

from PyQt4 import QtCore
from PyQt4 import QtGui

from bumps import options
from bumps import fitters

import sas.qtgui.Utilities.ObjectLibrary as ObjectLibrary

from sas.qtgui.Perspectives.Fitting.FittingWidget import FittingWidget
from sas.qtgui.Perspectives.Fitting.FittingOptions import FittingOptions
from sas.qtgui.Perspectives.Fitting import ModelUtilities

class FittingWindow(QtGui.QTabWidget):
    """
    """
    name = "Fitting" # For displaying in the combo box in DataExplorer
    def __init__(self, parent=None, data=None):
        super(FittingWindow, self).__init__()

        self.parent = parent
        self._data = data

        # List of active fits
        self.tabs = []

        # Max index for adding new, non-clashing tab names
        self.maxIndex = 0

        # Index of the current tab
        self.currentTab = 0

        # The default optimizer
        self.optimizer = 'Levenberg-Marquardt'

        # Dataset inde -> Fitting tab mapping
        self.dataToFitTab = {}

        # The tabs need to be closeable
        self.setTabsClosable(True)

        self.communicate = self.parent.communicator()

        # Initialize the first tab
        self.addFit(None)

        # Deal with signals
        self.tabCloseRequested.connect(self.tabCloses)
        self.communicate.dataDeletedSignal.connect(self.dataDeleted)

        # Perspective window not allowed to close by default
        self._allow_close = False

        # Fit options - uniform for all tabs
        self.fit_options = options.FIT_CONFIG
        self.fit_options_widget = FittingOptions(self, config=self.fit_options)
        self.fit_options.selected_id = fitters.LevenbergMarquardtFit.id

        # Listen to GUI Manager signal updating fit options
        self.fit_options_widget.fit_option_changed.connect(self.onFittingOptionsChange)

        self.menu_manager = ModelUtilities.ModelManager()
        # TODO: reuse these in FittingWidget properly
        self.model_list_box = self.menu_manager.get_model_list()
        self.model_dictionary = self.menu_manager.get_model_dictionary()

        #self.setWindowTitle('Fit panel - Active Fitting Optimizer: %s' % self.optimizer)
        self.updateWindowTitle()

    def updateWindowTitle(self):
        """
        Update the window title with the current optimizer name
        """
        self.optimizer = self.fit_options.selected_name
        self.setWindowTitle('Fit panel - Active Fitting Optimizer: %s' % self.optimizer)


    def setClosable(self, value=True):
        """
        Allow outsiders close this widget
        """
        assert isinstance(value, bool)

        self._allow_close = value

    def closeEvent(self, event):
        """
        Overwrite QDialog close method to allow for custom widget close
        """
        # Invoke fit page events
        for tab in self.tabs:
            tab.close()
        if self._allow_close:
            # reset the closability flag
            self.setClosable(value=False)
            event.accept()
        else:
            # Maybe we should just minimize
            self.setWindowState(QtCore.Qt.WindowMinimized)
            event.ignore()

    def addFit(self, data, is_batch=False):
        """
        Add a new tab for passed data
        """
        tab	= FittingWidget(parent=self.parent, data=data, tab_id=self.maxIndex+1)
        tab.is_batch_fitting = is_batch
        # Add this tab to the object library so it can be retrieved by scripting/jupyter
        tab_name = self.tabName(is_batch=is_batch)
        ObjectLibrary.addObject(tab_name, tab)
        self.tabs.append(tab)
        if data:
            self.updateFitDict(data, tab_name)
        self.maxIndex += 1
        self.addTab(tab, tab_name)

    def updateFitDict(self, item_key, tab_name):
        """
        Create a list if none exists and append if there's already a list
        """
        if item_key in self.dataToFitTab.keys():
            self.dataToFitTab[item_key].append(tab_name)
        else:
            self.dataToFitTab[item_key] = [tab_name]

        #print "CURRENT dict: ", self.dataToFitTab

    def tabName(self, is_batch=False):
        """
        Get the new tab name, based on the number of fitting tabs so far
        """
        page_name = "BatchPage" if is_batch else "FitPage"
        page_name = page_name + str(self.maxIndex)
        return page_name

    def resetTab(self, index):
        """
        Adds a new tab and removes the last tab
        as a way of resetting the fit tabs
        """
        # If data on tab empty - do nothing
        if index in self.tabs and not self.tabs[index].data:
            return
        # Add a new, empy tab
        self.addFit(None)
        # Remove the previous last tab
        self.tabCloses(index)

    def tabCloses(self, index):
        """
        Update local bookkeeping on tab close
        """
        #assert len(self.tabs) >= index
        # don't remove the last tab
        if len(self.tabs) <= 1:
            self.resetTab(index)
            return
        try:
            ObjectLibrary.deleteObjectByRef(self.tabs[index])
            self.removeTab(index)
            del self.tabs[index]
        except IndexError:
            # The tab might have already been deleted previously
            pass

    def closeTabByName(self, tab_name):
        """
        Given name of the fitting tab - close it
        """
        for tab_index in xrange(len(self.tabs)):
            if self.tabText(tab_index) == tab_name:
                self.tabCloses(tab_index)
        pass # debug hook

    def dataDeleted(self, index_list):
        """
        Delete fit tabs referencing given data
        """
        if not index_list or not self.dataToFitTab:
            return
        for index_to_delete in index_list:
            if index_to_delete in self.dataToFitTab.keys():
                for tab_name in self.dataToFitTab[index_to_delete]:
                    # delete tab #index after corresponding data got removed
                    self.closeTabByName(tab_name)
                self.dataToFitTab.pop(index_to_delete)

        #print "CURRENT dict: ", self.dataToFitTab

    def allowBatch(self):
        """
        Tell the caller that we accept multiple data instances
        """
        return True

    def setData(self, data_item=None, is_batch=False):
        """
        Assign new dataset to the fitting instance
        Obtain a QStandardItem object and dissect it to get Data1D/2D
        Pass it over to the calculator
        """
        assert data_item is not None

        if not isinstance(data_item, list):
            msg = "Incorrect type passed to the Fitting Perspective"
            raise AttributeError, msg

        if not isinstance(data_item[0], QtGui.QStandardItem):
            msg = "Incorrect type passed to the Fitting Perspective"
            raise AttributeError, msg

        items = [data_item] if is_batch else data_item

        for data in items:
            # Find the first unassigned tab.
            # If none, open a new tab.
            available_tabs = list(map(lambda tab: tab.acceptsData(), self.tabs))

            if numpy.any(available_tabs):
                first_good_tab = available_tabs.index(True)
                self.tabs[first_good_tab].data = data
                tab_name = str(self.tabText(first_good_tab))
                self.updateFitDict(data, tab_name)
            else:
                self.addFit(data, is_batch=is_batch)

    def onFittingOptionsChange(self, fit_engine):
        """
        React to the fitting algorithm change by modifying window title
        """
        fitter = [f.id for f in options.FITTERS if f.name == str(fit_engine)][0]
        # set the optimizer
        self.fit_options.selected_id = str(fitter)
        # Update the title
        self.updateWindowTitle()

        pass
