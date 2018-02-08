import numpy

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from bumps import options
from bumps import fitters

import sas.qtgui.Utilities.LocalConfig as LocalConfig
import sas.qtgui.Utilities.ObjectLibrary as ObjectLibrary

from sas.qtgui.Perspectives.Fitting.FittingWidget import FittingWidget
from sas.qtgui.Perspectives.Fitting.ConstraintWidget import ConstraintWidget
from sas.qtgui.Perspectives.Fitting.FittingOptions import FittingOptions
from sas.qtgui.Perspectives.Fitting.GPUOptions import GPUOptions

class FittingWindow(QtWidgets.QTabWidget):
    """
    """
    tabsModifiedSignal = QtCore.pyqtSignal()
    fittingStartedSignal = QtCore.pyqtSignal(list)
    fittingStoppedSignal = QtCore.pyqtSignal(list)

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

        # Dataset index -> Fitting tab mapping
        self.dataToFitTab = {}

        # The tabs need to be closeable
        self.setTabsClosable(True)

        # The tabs need to be movabe
        self.setMovable(True)

        self.communicate = self.parent.communicator()

        # Initialize the first tab
        self.addFit(None)

        # Deal with signals
        self.tabCloseRequested.connect(self.tabCloses)
        self.communicate.dataDeletedSignal.connect(self.dataDeleted)
        self.fittingStartedSignal.connect(self.onFittingStarted)
        self.fittingStoppedSignal.connect(self.onFittingStopped)

        # Perspective window not allowed to close by default
        self._allow_close = False

        # Fit options - uniform for all tabs
        self.fit_options = options.FIT_CONFIG
        self.fit_options_widget = FittingOptions(self, config=self.fit_options)
        self.fit_options.selected_id = fitters.LevenbergMarquardtFit.id

        # Listen to GUI Manager signal updating fit options
        self.fit_options_widget.fit_option_changed.connect(self.onFittingOptionsChange)

        # GPU Options
        self.gpu_options_widget = GPUOptions(self)

        self.updateWindowTitle()

    def updateWindowTitle(self):
        """
        Update the window title with the current optimizer name
        """
        self.optimizer = self.fit_options.selected_name
        self.setWindowTitle('Fit panel - Active Fitting Optimizer: %s' % self.optimizer)


    def setClosable(self, value=True):
        """
        Allow outsiders to close this widget
        """
        assert isinstance(value, bool)

        self._allow_close = value

    def closeEvent(self, event):
        """
        Overwrite QDialog close method to allow for custom widget close
        """
        # Invoke fit page events
        if self._allow_close:
            # reset the closability flag
            self.setClosable(value=False)
            # Tell the MdiArea to close the container
            self.parentWidget().close()
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
        tab_name = self.getTabName(is_batch=is_batch)
        ObjectLibrary.addObject(tab_name, tab)
        self.tabs.append(tab)
        if data:
            self.updateFitDict(data, tab_name)
        self.maxIndex += 1
        icon = QtGui.QIcon()
        if is_batch:
            icon.addPixmap(QtGui.QPixmap("src/sas/qtgui/images/icons/layers.svg"))
        self.addTab(tab, icon, tab_name)
        # Show the new tab
        self.setCurrentIndex(self.maxIndex-1)
        # Notify listeners
        self.tabsModifiedSignal.emit()

    def addConstraintTab(self):
        """
        Add a new C&S fitting tab
        """
        tabs = [isinstance(tab, ConstraintWidget) for tab in self.tabs]
        if any(tabs):
            # We already have a C&S tab: show it
            self.setCurrentIndex(tabs.index(True))
            return
        tab	= ConstraintWidget(parent=self)
        # Add this tab to the object library so it can be retrieved by scripting/jupyter
        tab_name = self.getCSTabName() # TODO update the tab name scheme
        ObjectLibrary.addObject(tab_name, tab)
        self.tabs.append(tab)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("src/sas/qtgui/images/icons/link.svg"))
        self.addTab(tab, icon, tab_name)

        # This will be the last tab, so set the index accordingly
        self.setCurrentIndex(self.count()-1)

    def updateFitDict(self, item_key, tab_name):
        """
        Create a list if none exists and append if there's already a list
        """
        item_key_str = str(item_key)
        if item_key_str in list(self.dataToFitTab.keys()):
            self.dataToFitTab[item_key_str].append(tab_name)
        else:
            self.dataToFitTab[item_key_str] = [tab_name]

    def getTabName(self, is_batch=False):
        """
        Get the new tab name, based on the number of fitting tabs so far
        """
        page_name = "BatchPage" if is_batch else "FitPage"
        page_name = page_name + str(self.maxIndex)
        return page_name

    def getCSTabName(self):
        """
        Get the new tab name, based on the number of fitting tabs so far
        """
        page_name = "Const. & Simul. Fit"
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
            self.tabsModifiedSignal.emit()
        except IndexError:
            # The tab might have already been deleted previously
            pass

    def closeTabByName(self, tab_name):
        """
        Given name of the fitting tab - close it
        """
        for tab_index in range(len(self.tabs)):
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
            index_to_delete_str = str(index_to_delete)
            if index_to_delete_str in list(self.dataToFitTab.keys()):
                for tab_name in self.dataToFitTab[index_to_delete_str]:
                    # delete tab #index after corresponding data got removed
                    self.closeTabByName(tab_name)
                self.dataToFitTab.pop(index_to_delete_str)

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
            raise AttributeError(msg)

        if not isinstance(data_item[0], QtGui.QStandardItem):
            msg = "Incorrect type passed to the Fitting Perspective"
            raise AttributeError(msg)

        if is_batch:
            # Just create a new fit tab. No empty batchFit tabs
            self.addFit(data_item, is_batch=is_batch)
            return

        items = [data_item] if is_batch else data_item
        for data in items:
            # Find the first unassigned tab.
            # If none, open a new tab.
            available_tabs = [tab.acceptsData() for tab in self.tabs]

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

    def onFittingStarted(self, tabs_for_fitting=None):
        """
        Notify tabs listed in tabs_for_fitting
        that the fitting thread started
        """
        assert(isinstance(tabs_for_fitting, list))
        assert(len(tabs_for_fitting)>0)

        for tab_object in self.tabs:
            if not isinstance(tab_object, FittingWidget):
                continue
            page_name = "Page%s"%tab_object.tab_id
            if any([page_name in tab for tab in tabs_for_fitting]):
                tab_object.setFittingStarted()

        pass

    def onFittingStopped(self, tabs_for_fitting=None):
        """
        Notify tabs listed in tabs_for_fitting
        that the fitting thread stopped
        """
        assert(isinstance(tabs_for_fitting, list))
        assert(len(tabs_for_fitting)>0)

        for tab_object in self.tabs:
            if not isinstance(tab_object, FittingWidget):
                continue
            page_name = "Page%s"%tab_object.tab_id
            if any([page_name in tab for tab in tabs_for_fitting]):
                tab_object.setFittingStopped()

        pass
