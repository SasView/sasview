import copy

import numpy
from bumps import options
from PySide6 import QtCore, QtGui, QtWidgets

import sas.qtgui.Utilities.GuiUtils as GuiUtils
import sas.qtgui.Utilities.ObjectLibrary as ObjectLibrary
from sas.qtgui.Perspectives.Fitting.Constraint import Constraint
from sas.qtgui.Perspectives.Fitting.ConstraintWidget import ConstraintWidget
from sas.qtgui.Perspectives.Fitting.FittingOptions import FittingOptions
from sas.qtgui.Perspectives.Fitting.FittingWidget import FittingWidget
from sas.qtgui.Perspectives.Fitting.GPUOptions import GPUOptions
from sas.qtgui.Perspectives.perspective import Perspective
from sas.qtgui.Utilities.Reports.reportdata import ReportData
from sas.system.config import config


class FittingWindow(QtWidgets.QTabWidget, Perspective):
    """
    """
    tabsModifiedSignal = QtCore.Signal()
    fittingStartedSignal = QtCore.Signal(list)
    fittingStoppedSignal = QtCore.Signal(list)

    name = "Fitting"
    ext = "fitv"

    @property
    def title(self):
        """ Window title"""
        return "Fitting Perspective"

    def __init__(self, parent=None, data=None):

        super().__init__()

        self.parent = parent
        self._data = data

        # List of active fits
        self.tabs = []

        # Max index for adding new, non-clashing tab names
        self.maxIndex = 1

        # Dataset index -> Fitting tab mapping
        self.dataToFitTab = {}

        # The tabs need to be closeable
        self.setTabsClosable(True)

        # The tabs need to be movabe
        self.setMovable(True)

        # Remember the last tab closed
        self.lastTabClosed = None
        self.installEventFilter(self)

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
        self.fit_options_widget = FittingOptions(config=self.fit_options)
        self.fit_options.selected_id = config.config.FITTING_DEFAULT_OPTIMIZER
        self.optimizer = self.fit_options.selected_name

        # Listen to GUI Manager signal updating fit options
        self.fit_options_widget.fit_option_changed.connect(self.onFittingOptionsChange)

        # GPU Options
        self.gpu_options_widget = GPUOptions()

        self.updateWindowTitle()

        # Add new tab mini-button
        self.plusButton = QtWidgets.QToolButton(self)
        self.plusButton.setText("+")
        self.setCornerWidget(self.plusButton)
        self.plusButton.setToolTip("Add a new Fit Page")
        self.plusButton.clicked.connect(lambda: self.addFit(None))

    def eventFilter(self, widget, event):
        if event.type() == QtCore.QEvent.KeyPress:
            key = event.key()
            # check for Ctrl-T press
            if key == QtCore.Qt.Key_T and event.modifiers() == QtCore.Qt.ControlModifier:
                self.addClosedTab()
                return True
        return QtCore.QObject.eventFilter(self, widget, event)

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

    def clipboard_copy(self):
        if self.currentFittingWidget is not None:
            self.currentFittingWidget.clipboard_copy()

    def clipboard_paste(self):
        if self.currentFittingWidget is not None:
            self.currentFittingWidget.clipboard_paste()

    def excel_clipboard_copy(self):
        if self.currentFittingWidget is not None:
            self.currentFittingWidget.clipboard_copy_excel()

    def latex_clipboard_copy(self):
        if self.currentFittingWidget is not None:
            self.currentFittingWidget.clipboard_copy_latex()

    def save_parameters(self):
        if self.currentFittingWidget is not None:
            self.currentFittingWidget.save_parameters()

    def serializeAll(self):
        return self.serializeAllFitpage()

    def serializeAllFitpage(self):
        # serialize all active fitpages and return
        # a dictionary: {data_id: fitpage_state}
        state = {}
        for i, tab in enumerate(self.tabs):
            tab_state = self.getSerializedFitpage(tab)
            for key, value in tab_state.items():
                if key in state:
                    state[key].update(value)
                else:
                    state[key] = value
        return state

    def serializeCurrentPage(self):
        # serialize current(active) fitpage
        return self.getSerializedFitpage(self.currentTab)

    def getSerializedFitpage(self, tab):
        """
        get serialize requested fit tab
        """
        state = {}
        fitpage_state = tab.getFitPage()
        fitpage_state += tab.getFitModel()
        # put the text into dictionary
        line_dict = {}
        for line in fitpage_state:
            #content = line.split(',')
            if len(line) > 1:
                line_dict[line[0]] = line[1:]

        if 'data_id' not in line_dict:
            return state
        id = line_dict['data_id'][0]
        if not isinstance(id, list):
            id = [id]
        for i in id:
            if 'is_constraint' in line_dict:
                state[i] = line_dict
            elif i in state and 'fit-params' in state[i]:
                state[i]['fit_params'].update(line_dict)
            else:
                state[i] = {'fit_params': [line_dict]}
        return state

    @property
    def preferences(self):
        return [self.fit_options_widget, self.gpu_options_widget]

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

    def updateFromParameters(self, parameters):
        """
        Pass the update parameters to the current fit page
        """
        self.currentTab.createPageForParameters(parameters)

    def updateFromConstraints(self, constraint_dict):
        """
        Updates all tabs with constraints present in *constraint_dict*, where
        *constraint_dict*  keys are the fit page name, and the value is a
        list of constraints. A constraint is represented by a list [value,
        param, value_ex, validate, function] of attributes of a Constraint
        object
        """
        for fit_page_name, constraint_list in constraint_dict.items():
            tab = self.getTabByName(fit_page_name)
            for constraint_param in constraint_list:
                if constraint_param is not None and len(constraint_param) == 5:
                    constraint = Constraint()
                    constraint.value = constraint_param[0]
                    constraint.func = constraint_param[4]
                    constraint.param = constraint_param[1]
                    constraint.value_ex = constraint_param[2]
                    constraint.validate = constraint_param[3]
                    model_key = tab.getModelKey(constraint)
                    tab.addConstraintToRow(constraint=constraint,
                                           row=tab.getRowFromName(
                                               constraint_param[1]),
                                           model_key=model_key)

    def closeEvent(self, event):
        """
        Overwrite QDialog close method to allow for custom widget close
        """
        # Invoke fit page events
        if self._allow_close:
            # reset the closability flag
            self.setClosable(value=False)
            # Tell the MdiArea to close the container if it is visible
            if self.parentWidget():
                self.parentWidget().close()
            event.accept()
        else:
            # Maybe we should just minimize
            self.setWindowState(QtCore.Qt.WindowMinimized)
            event.ignore()

    def addFit(self, data, is_batch=False, tab_index=None):
        """
        Add a new tab for passed data
        """
        if tab_index is None:
            tab_index = self.maxIndex
        else:
            self.maxIndex = tab_index
        tab	= FittingWidget(parent=self.parent, data=data, tab_id=tab_index)
        tab.is_batch_fitting = is_batch

        # Add this tab to the object library so it can be retrieved by scripting/jupyter
        tab_name = self.getTabName(is_batch=is_batch)
        ObjectLibrary.addObject(tab_name, tab)
        self.tabs.append(tab)
        if data:
            self.updateFitDict(data, tab_name)
        self.maxIndex = self.nextAvailableTabIndex()

        icon = QtGui.QIcon()
        if is_batch:
            icon.addPixmap(QtGui.QPixmap("src/sas/qtgui/images/icons/layers.svg"))
        self.addTab(tab, icon, tab_name)
        # Show the new tab
        self.setCurrentWidget(tab)
        # Notify listeners
        self.tabsModifiedSignal.emit()

    def nextAvailableTabIndex(self):
        """
        Returns the index of the next available tab
        """
        return max((tab.tab_id for tab in self.tabs), default=0) + 1

    def addClosedTab(self):
        """
        Recover the deleted tab.
        The tab is held in self.lastTabClosed
        """
        if self.lastTabClosed is None:
            return
        tab = self.lastTabClosed
        icon = QtGui.QIcon()
        # tab_name = self.getTabName()
        tab_name = "FitPage" + str(tab.tab_id)
        ObjectLibrary.addObject(tab_name, tab)
        self.addTab(tab, icon, tab_name)
        # Update the list of tabs
        self.tabs.append(tab)
        # Show the new tab
        self.setCurrentWidget(tab)
        # lastTabClosed is no longer valid
        self.lastTabClosed = None
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

    def closeTabByIndex(self, index):
        """
        Close/delete a tab with the given index.
        No checks on validity of the index.
        """
        try:
            ObjectLibrary.deleteObjectByRef(self.tabs[index])
            self.removeTab(index)
            # can't just delete the tab, since we still hold a reference to it
            # del self.tabs[index]
            # Instead, we just recreate self.tabs without the deleted tab
            self.tabs = [tab for tab in self.tabs if tab is not self.tabs[index]]
            self.tabsModifiedSignal.emit()
        except IndexError:
            # The tab might have already been deleted previously
            pass

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
        # update the last-tab closed information
        # this should be done only for regular fitting
        if not isinstance(self.tabs[index], ConstraintWidget) and \
              not self.tabs[index].is_batch_fitting:
            self.lastTabClosed = self.tabs[index]

        # don't remove the last tab
        if len(self.tabs) <= 1:
            # remove the tab from the tabbed group
            self.resetTab(index)
            return
        self.closeTabByIndex(index)

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
            orig_dict = copy.deepcopy(self.dataToFitTab)
            for tab_key in orig_dict.keys():
                if index_to_delete_str in tab_key:
                    for tab_name in orig_dict[tab_key]:
                        self.closeTabByName(tab_name)
                        # assure that lastTabClosed is null if it references the deleted data
                        if self.lastTabClosed and tab_name == "FitPage"+str(self.lastTabClosed.tab_id):
                                self.lastTabClosed = None
                    self.dataToFitTab.pop(tab_key)

    def allowBatch(self):
        """
        Tell the caller that we accept multiple data instances
        """
        return True

    def allowSwap(self):
        """
        Tell the caller that you can swap data
        """
        return True

    def isSerializable(self):
        """
        Tell the caller that this perspective writes its state
        """
        return True

    def setData(self, data_item=None, is_batch=False, tab_index=None):
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
            tab_ids = [tab.tab_id for tab in self.tabs]

            if tab_index is not None:
                if tab_index not in tab_ids:
                    self.addFit(data, is_batch=is_batch, tab_index=tab_index)
                else:
                    self.setCurrentIndex(tab_index-1)
                    self.swapData(data)
                return
            if numpy.any(available_tabs):
                first_good_tab = available_tabs.index(True)
                self.tabs[first_good_tab].dataFromItems(data)
                tab_name = str(self.tabText(first_good_tab))
                self.updateFitDict(data, tab_name)
            else:
                self.addFit(data, is_batch=is_batch)

    def swapData(self, data):
        """
        Replace the data from the current fitting tab
        """
        if not isinstance(self.currentWidget(), FittingWidget):
            msg = "Current tab is not  a fitting widget"
            raise TypeError(msg)

        if not isinstance(data, QtGui.QStandardItem):
            msg = "Incorrect type passed to the Fitting Perspective"
            raise AttributeError(msg)

        if self.currentTab.is_batch_fitting:
            msg = "Data in Batch Fitting cannot be swapped"
            raise RuntimeError(msg)

        self.currentTab.dataFromItems(data)
        tab_name = str(self.tabText(self.currentIndex()))
        self.updateFitDict(data, tab_name)

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
                tab_object.disableInteractiveElements()

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
                tab_object.enableInteractiveElements()

    def getCurrentStateAsXml(self):
        """
        Returns an XML version of the current state
        """
        state = {}
        for tab in self.tabs:
            pass
        return state

    @property
    def currentTab(self): # TODO: More pythonic name
        """
        Returns the tab widget currently shown
        """
        return self.currentWidget()

    @property
    def currentFittingWidget(self) -> FittingWidget | None:
        current_tab = self.currentTab
        if isinstance(current_tab, FittingWidget):
            return current_tab
        else:
            return None

    def getFitTabs(self):
        """
        Returns the list of fitting tabs
        """
        return [tab for tab in self.tabs if isinstance(tab, FittingWidget)]

    def getActiveConstraintList(self):
        """
        Returns a list of the constraints for all fitting tabs. Constraints
        are a tuple of strings (parameter, expression) e.g. ('M1.scale',
        'M2.scale + 2')
        """
        constraints = []
        for tab in self.getFitTabs():
            tab_name = tab.modelName()
            tab_constraints = tab.getConstraintsForAllModels()
            constraints.extend((tab_name + "." + par, expr) for par, expr in tab_constraints)

        return constraints

    def getSymbolDictForConstraints(self):
        """
        Returns a dictionary containing all the symbols in  all constrained tabs
        and their values.
        """
        symbol_dict = {}
        for tab in self.getFitTabs():
            symbol_dict.update(tab.getSymbolDict())
        return symbol_dict

    def getConstraintTab(self):
        """
        Returns the constraint tab, or None if no constraint tab is active
        """
        if any(isinstance(tab, ConstraintWidget) for tab in self.tabs):
            constraint_tab = next(tab
                                  for tab in self.tabs
                                  if isinstance(tab, ConstraintWidget))
        else:
            constraint_tab = None
        return constraint_tab

    def getTabByName(self, name):
        """
        Returns the tab with with attribute name *name*
        """
        assert isinstance(name, str)
        for tab in self.tabs:
            if hasattr(tab, 'modelName') and tab.modelName() == name:
                return tab
        return None

    @property
    def supports_reports(self) -> bool:
        return True

    def getReport(self) -> ReportData | None:
        """ Get the report from the current tab"""
        fitting_widget = self.currentFittingWidget
        return None if fitting_widget is None else fitting_widget.getReport()

    @property
    def supports_fitting_menu(self) -> bool:
        return True

    @property
    def supports_copy(self) -> bool:
        return True

    @property
    def supports_copy_excel(self) -> bool:
        return True

    @property
    def supports_copy_latex(self) -> bool:
        return True

    @property
    def supports_paste(self) -> bool:
        return True
