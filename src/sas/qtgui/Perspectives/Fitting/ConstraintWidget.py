import logging

from twisted.internet import threads

import sas.qtgui.Utilities.GuiUtils as GuiUtils
import sas.qtgui.Utilities.LocalConfig as LocalConfig

from PyQt5 import QtGui, QtCore, QtWidgets

from sas.sascalc.fit.BumpsFitting import BumpsFit as Fit

import sas.qtgui.Utilities.ObjectLibrary as ObjectLibrary
from sas.qtgui.Perspectives.Fitting.UI.ConstraintWidgetUI import Ui_ConstraintWidgetUI
from sas.qtgui.Perspectives.Fitting.FittingWidget import FittingWidget
from sas.qtgui.Perspectives.Fitting.FitThread import FitThread
from sas.qtgui.Perspectives.Fitting.ConsoleUpdate import ConsoleUpdate
from sas.qtgui.Perspectives.Fitting.ComplexConstraint import ComplexConstraint
from sas.qtgui.Perspectives.Fitting.Constraint import Constraint

class ConstraintWidget(QtWidgets.QWidget, Ui_ConstraintWidgetUI):
    """
    Constraints Dialog to select the desired parameter/model constraints.
    """

    def __init__(self, parent=None):
        super(ConstraintWidget, self).__init__()
        self.parent = parent
        self.setupUi(self)
        self.currentType = "FitPage"
        # Page id for fitting
        # To keep with previous SasView values, use 300 as the start offset
        self.page_id = 301

        # Remember previous content of modified cell
        self.current_cell = ""

        # Tabs used in simultaneous fitting
        # tab_name : True/False
        self.tabs_for_fitting = {}

        # Set up the widgets
        self.initializeWidgets()

        # Set up signals/slots
        self.initializeSignals()

        # Create the list of tabs
        self.initializeFitList()

    def acceptsData(self):
        """ Tells the caller this widget doesn't accept data """
        return False

    def initializeWidgets(self):
        """
        Set up various widget states
        """
        labels = ['FitPage', 'Model', 'Data', 'Mnemonic']
        # tab widget - headers
        self.editable_tab_columns = [labels.index('Mnemonic')]
        self.tblTabList.setColumnCount(len(labels))
        self.tblTabList.setHorizontalHeaderLabels(labels)
        self.tblTabList.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        self.tblTabList.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tblTabList.customContextMenuRequested.connect(self.showModelContextMenu)

        # disabled constraint 
        labels = ['Constraint']
        self.tblConstraints.setColumnCount(len(labels))
        self.tblConstraints.setHorizontalHeaderLabels(labels)
        self.tblConstraints.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.tblConstraints.setEnabled(False)

        self.tblConstraints.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tblConstraints.customContextMenuRequested.connect(self.showConstrContextMenu)

    def initializeSignals(self):
        """
        Set up signals/slots for this widget
        """
        # simple widgets
        self.btnSingle.toggled.connect(self.onFitTypeChange)
        self.btnBatch.toggled.connect(self.onFitTypeChange)
        self.cbCases.currentIndexChanged.connect(self.onSpecialCaseChange)
        self.cmdFit.clicked.connect(self.onFit)
        self.cmdHelp.clicked.connect(self.onHelp)

        # QTableWidgets
        self.tblTabList.cellChanged.connect(self.onTabCellEdit)
        self.tblTabList.cellDoubleClicked.connect(self.onTabCellEntered)
        self.tblConstraints.cellChanged.connect(self.onConstraintChange)

        # External signals
        self.parent.tabsModifiedSignal.connect(self.initializeFitList)

    def updateSignalsFromTab(self, tab=None):
        """
        Intercept update signals from fitting tabs
        """
        if tab is None:
            return
        tab_object = ObjectLibrary.getObject(tab)

        # Disconnect all local slots
        tab_object.disconnect()

        # Reconnect tab signals to local slots
        tab_object.constraintAddedSignal.connect(self.initializeFitList)
        tab_object.newModelSignal.connect(self.initializeFitList)

    def onFitTypeChange(self, checked):
        """
        Respond to the fit type change
        single fit/batch fit
        """
        source = self.sender().objectName()
        self.currentType = "BatchPage" if source == "btnBatch" else "FitPage"
        self.initializeFitList()

    def onSpecialCaseChange(self, index):
        """
        Respond to the combobox change for special case constraint sets
        """
        pass

    def getTabsForFit(self):
        """
        Returns list of tab names selected for fitting
        """
        return [tab for tab in self.tabs_for_fitting if self.tabs_for_fitting[tab]]

    def onFit(self):
        """
        Perform the constrained/simultaneous fit
        """
        # Find out all tabs to fit
        tabs_to_fit = self.getTabsForFit()

        # Single fitter for the simultaneous run
        fitter = Fit()
        fitter.fitter_id = self.page_id

        # Notify the parent about fitting started
        self.parent.fittingStartedSignal.emit(tabs_to_fit)

        # prepare fitting problems for each tab
        #
        page_ids = []
        fitter_id = 0
        sim_fitter_list=[fitter]
        # Prepare the fitter object
        try:
            for tab in tabs_to_fit:
                tab_object = ObjectLibrary.getObject(tab)
                if tab_object is None:
                    # No such tab!
                    return
                sim_fitter_list, fitter_id = tab_object.prepareFitters(fitter=sim_fitter_list[0], fit_id=fitter_id)
                page_ids.append([tab_object.page_id])
        except ValueError:
            # No parameters selected in one of the tabs
            no_params_msg = "Fitting can not be performed.\n" +\
                            "Not all tabs chosen for fitting have parameters selected for fitting."
            QtWidgets.QMessageBox.question(self,
                                           'Warning',
                                            no_params_msg,
                                            QtWidgets.QMessageBox.Ok)

            return

        # Create the fitting thread, based on the fitter
        completefn = self.onBatchFitComplete if self.currentType=='BatchPage' else self.onFitComplete

        if LocalConfig.USING_TWISTED:
            handler = None
            updater = None
        else:
            handler = ConsoleUpdate(parent=self.parent,
                                    manager=self,
                                    improvement_delta=0.1)
            updater = handler.update_fit

        batch_inputs = {}
        batch_outputs = {}

        # new fit thread object
        calc_fit = FitThread(handler=handler,
                             fn=sim_fitter_list,
                             batch_inputs=batch_inputs,
                             batch_outputs=batch_outputs,
                             page_id=page_ids,
                             updatefn=updater,
                             completefn=completefn)

        if LocalConfig.USING_TWISTED:
            # start the trhrhread with twisted
            calc_thread = threads.deferToThread(calc_fit.compute)
            calc_thread.addCallback(completefn)
            calc_thread.addErrback(self.onFitFailed)
        else:
            # Use the old python threads + Queue
            calc_fit.queue()
            calc_fit.ready(2.5)


        #disable the Fit button
        self.cmdFit.setText('Running...')
        self.parent.communicate.statusBarUpdateSignal.emit('Fitting started...')
        self.cmdFit.setEnabled(False)

    def onHelp(self):
        """
        Show the "Fitting" section of help
        """
        tree_location = "/user/sasgui/perspectives/fitting/"

        helpfile = "fitting_help.html#simultaneous-fit-mode"
        help_location = tree_location + helpfile

        # OMG, really? Crawling up the object hierarchy...
        self.parent.parent.showHelp(help_location)

    def onTabCellEdit(self, row, column):
        """
        Respond to check/uncheck and to modify the model moniker actions
        """
        item = self.tblTabList.item(row, column)
        if column == 0:
            # Update the tabs for fitting list
            tab_name = item.text()
            self.tabs_for_fitting[tab_name] = (item.checkState() == QtCore.Qt.Checked)
            # Enable fitting only when there are models to fit
            self.cmdFit.setEnabled(any(self.tabs_for_fitting.values()))

        if column not in self.editable_tab_columns:
            return
        new_moniker = item.data(0)

        # The new name should be validated on the fly, with QValidator
        # but let's just assure it post-factum
        is_good_moniker = self.validateMoniker(new_moniker)
        if not is_good_moniker:
            self.tblTabList.blockSignals(True)
            item.setBackground(QtCore.Qt.red)
            self.tblTabList.blockSignals(False)
            self.cmdFit.setEnabled(False)
            return
        self.tblTabList.blockSignals(True)
        item.setBackground(QtCore.Qt.white)
        self.tblTabList.blockSignals(False)
        self.cmdFit.setEnabled(True)
        if not self.current_cell:
            return
        # Remember the value
        if self.current_cell not in self.available_tabs:
            return
        temp_tab = self.available_tabs[self.current_cell]
        # Remove the key from the dictionaries
        self.available_tabs.pop(self.current_cell, None)
        # Change the model name
        model = temp_tab.kernel_module
        model.name = new_moniker
        # Replace constraint name
        temp_tab.replaceConstraintName(self.current_cell, new_moniker)
        # Replace constraint name in the remaining tabs
        for tab in self.available_tabs.values():
            tab.replaceConstraintName(self.current_cell, new_moniker)
        # Reinitialize the display
        self.initializeFitList()

    def onConstraintChange(self, row, column):
        """
        Modify the constraint's "active" instance variable.
        """
        item = self.tblConstraints.item(row, column)
        if column == 0:
            # Update the tabs for fitting list
            constraint = self.available_constraints[row]
            constraint.active = (item.checkState() == QtCore.Qt.Checked)

    def onTabCellEntered(self, row, column):
        """
        Remember the original tab list cell data.
        Needed for reverting back on bad validation
        """
        if column != 3:
            return
        self.current_cell = self.tblTabList.item(row, column).data(0)

    def onFitComplete(self, result):
        """
        Respond to the successful fit complete signal
        """
        #re-enable the Fit button
        self.cmdFit.setText("Fit")
        self.cmdFit.setEnabled(True)

        # Notify the parent about completed fitting
        self.parent.fittingStoppedSignal.emit(self.getTabsForFit())

        # Assure the fitting succeeded
        if result is None or not result:
            msg = "Fitting failed. Please ensure correctness of chosen constraints."
            self.parent.communicate.statusBarUpdateSignal.emit(msg)
            return

        # get the elapsed time
        elapsed = result[1]

        # result list
        results = result[0][0]

        # Find out all tabs to fit
        tabs_to_fit = [tab for tab in self.tabs_for_fitting if self.tabs_for_fitting[tab]]

        # update all involved tabs
        for i, tab in enumerate(tabs_to_fit):
            tab_object = ObjectLibrary.getObject(tab)
            if tab_object is None:
                # No such tab. removed while job was running
                return
            # Make sure result and target objects are the same (same model moniker)
            if tab_object.kernel_module.name == results[i].model.name:
                tab_object.fitComplete(([[results[i]]], elapsed))

        msg = "Fitting completed successfully in: %s s.\n" % GuiUtils.formatNumber(elapsed)
        self.parent.communicate.statusBarUpdateSignal.emit(msg)

    def onBatchFitComplete(self, result):
        """
        Respond to the successful batch fit complete signal
        """
        #re-enable the Fit button
        self.cmdFit.setText("Fit")
        self.cmdFit.setEnabled(True)

        # Notify the parent about completed fitting
        self.parent.fittingStoppedSignal.emit(self.getTabsForFit())

        # get the elapsed time
        elapsed = result[1]

        # ADD THE BATCH FIT VIEW HERE
        #

        msg = "Fitting completed successfully in: %s s.\n" % GuiUtils.formatNumber(elapsed)
        self.parent.communicate.statusBarUpdateSignal.emit(msg)

    def onFitFailed(self, reason):
        """
        Respond to fitting failure.
        """
        #re-enable the Fit button
        self.cmdFit.setText("Fit")
        self.cmdFit.setEnabled(True)

        # Notify the parent about completed fitting
        self.parent.fittingStoppedSignal.emit(self.getTabsForFit())

        msg = "Fitting failed: %s s.\n" % reason
        self.parent.communicate.statusBarUpdateSignal.emit(msg)
 
    def isTabImportable(self, tab):
        """
        Determines if the tab can be imported and included in the widget
        """
        if not isinstance(tab, str): return False
        if not self.currentType in tab: return False
        object = ObjectLibrary.getObject(tab)
        if not isinstance(object, FittingWidget): return False
        if object.data is None: return False
        return True

    def showModelContextMenu(self, position):
        """
        Show context specific menu in the tab table widget.
        """
        menu = QtWidgets.QMenu()
        rows = [s.row() for s in self.tblTabList.selectionModel().selectedRows()]
        num_rows = len(rows)
        if num_rows <= 0:
            return
        # Select for fitting
        param_string = "Fit Page " if num_rows==1 else "Fit Pages "

        self.actionSelect = QtWidgets.QAction(self)
        self.actionSelect.setObjectName("actionSelect")
        self.actionSelect.setText(QtCore.QCoreApplication.translate("self", "Select "+param_string+" for fitting"))
        # Unselect from fitting
        self.actionDeselect = QtWidgets.QAction(self)
        self.actionDeselect.setObjectName("actionDeselect")
        self.actionDeselect.setText(QtCore.QCoreApplication.translate("self", "De-select "+param_string+" from fitting"))

        self.actionRemoveConstraint = QtWidgets.QAction(self)
        self.actionRemoveConstraint.setObjectName("actionRemoveConstrain")
        self.actionRemoveConstraint.setText(QtCore.QCoreApplication.translate("self", "Remove all constraints on selected models"))

        self.actionMutualMultiConstrain = QtWidgets.QAction(self)
        self.actionMutualMultiConstrain.setObjectName("actionMutualMultiConstrain")
        self.actionMutualMultiConstrain.setText(QtCore.QCoreApplication.translate("self", "Mutual constrain of parameters in selected models..."))

        menu.addAction(self.actionSelect)
        menu.addAction(self.actionDeselect)
        menu.addSeparator()

        if num_rows >= 2:
            menu.addAction(self.actionMutualMultiConstrain)

        # Define the callbacks
        self.actionMutualMultiConstrain.triggered.connect(self.showMultiConstraint)
        self.actionSelect.triggered.connect(self.selectModels)
        self.actionDeselect.triggered.connect(self.deselectModels)
        try:
            menu.exec_(self.tblTabList.viewport().mapToGlobal(position))
        except AttributeError as ex:
            logging.error("Error generating context menu: %s" % ex)
        return

    def showConstrContextMenu(self, position):
        """
        Show context specific menu in the tab table widget.
        """
        menu = QtWidgets.QMenu()
        rows = [s.row() for s in self.tblConstraints.selectionModel().selectedRows()]
        num_rows = len(rows)
        if num_rows <= 0:
            return
        # Select for fitting
        param_string = "constraint " if num_rows==1 else "constraints "

        self.actionSelect = QtWidgets.QAction(self)
        self.actionSelect.setObjectName("actionSelect")
        self.actionSelect.setText(QtCore.QCoreApplication.translate("self", "Select "+param_string+" for fitting"))
        # Unselect from fitting
        self.actionDeselect = QtWidgets.QAction(self)
        self.actionDeselect.setObjectName("actionDeselect")
        self.actionDeselect.setText(QtCore.QCoreApplication.translate("self", "De-select "+param_string+" from fitting"))

        self.actionRemoveConstraint = QtWidgets.QAction(self)
        self.actionRemoveConstraint.setObjectName("actionRemoveConstrain")
        self.actionRemoveConstraint.setText(QtCore.QCoreApplication.translate("self", "Remove "+param_string))

        menu.addAction(self.actionSelect)
        menu.addAction(self.actionDeselect)
        menu.addSeparator()
        menu.addAction(self.actionRemoveConstraint)

        # Define the callbacks
        self.actionRemoveConstraint.triggered.connect(self.deleteConstraint)
        self.actionSelect.triggered.connect(self.selectConstraints)
        self.actionDeselect.triggered.connect(self.deselectConstraints)
        try:
            menu.exec_(self.tblConstraints.viewport().mapToGlobal(position))
        except AttributeError as ex:
            logging.error("Error generating context menu: %s" % ex)
        return

    def selectConstraints(self):
        """
        Selected constraints are chosen for fitting
        """
        status = QtCore.Qt.Checked
        self.setRowSelection(self.tblConstraints, status)

    def deselectConstraints(self):
        """
        Selected constraints are removed for fitting
        """
        status = QtCore.Qt.Unchecked
        self.setRowSelection(self.tblConstraints, status)

    def selectModels(self):
        """
        Selected models are chosen for fitting
        """
        status = QtCore.Qt.Checked
        self.setRowSelection(self.tblTabList, status)

    def deselectModels(self):
        """
        Selected models are removed for fitting
        """
        status = QtCore.Qt.Unchecked
        self.setRowSelection(self.tblTabList, status)

    def selectedParameters(self, widget):
        """ Returns list of selected (highlighted) parameters """
        return [s.row() for s in widget.selectionModel().selectedRows()]

    def setRowSelection(self, widget, status=QtCore.Qt.Unchecked):
        """
        Selected models are chosen for fitting
        """
        # Convert to proper indices and set requested enablement
        for row in self.selectedParameters(widget):
            widget.item(row, 0).setCheckState(status)

    def deleteConstraint(self):#, row):
        """
        Delete all selected constraints.
        """
        # Removing rows from the table we're iterating over,
        # so prepare a list of data first
        constraints_to_delete = []
        for row in self.selectedParameters(self.tblConstraints):
            constraints_to_delete.append(self.tblConstraints.item(row, 0).data(0))
        for constraint in constraints_to_delete:
            moniker = constraint[:constraint.index(':')]
            param = constraint[constraint.index(':')+1:constraint.index('=')].strip()
            tab = self.available_tabs[moniker]
            tab.deleteConstraintOnParameter(param)
        # Constraints removed - refresh the table widget
        self.initializeFitList()

    def uneditableItem(self, data=""):
        """
        Returns an uneditable Table Widget Item
        """
        item = QtWidgets.QTableWidgetItem(data)
        item.setFlags( QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled )
        return item

    def updateFitLine(self, tab):
        """
        Update a single line of the table widget with tab info
        """
        fit_page = ObjectLibrary.getObject(tab)
        model = fit_page.kernel_module
        if model is None:
            return
        tab_name = tab
        model_name = model.id
        moniker = model.name
        model_data = fit_page.data
        model_filename = model_data.filename
        self.available_tabs[moniker] = fit_page

        # Update the model table widget
        pos = self.tblTabList.rowCount()
        self.tblTabList.insertRow(pos)
        item = self.uneditableItem(tab_name)
        item.setFlags(item.flags() ^ QtCore.Qt.ItemIsUserCheckable)
        if tab_name in self.tabs_for_fitting:
            state = QtCore.Qt.Checked if self.tabs_for_fitting[tab_name] else QtCore.Qt.Unchecked
            item.setCheckState(state)
        else:
            item.setCheckState(QtCore.Qt.Checked)
            self.tabs_for_fitting[tab_name] = True

        # Disable signals so we don't get infinite call recursion
        self.tblTabList.blockSignals(True)
        self.tblTabList.setItem(pos, 0, item)
        self.tblTabList.setItem(pos, 1, self.uneditableItem(model_name))
        self.tblTabList.setItem(pos, 2, self.uneditableItem(model_filename))
        # Moniker is editable, so no option change
        item = QtWidgets.QTableWidgetItem(moniker)
        self.tblTabList.setItem(pos, 3, item)
        self.tblTabList.blockSignals(False)

        # Check if any constraints present in tab
        constraint_names = fit_page.getComplexConstraintsForModel()
        constraints = fit_page.getConstraintObjectsForModel()
        if not constraints: 
            return
        self.tblConstraints.setEnabled(True)
        self.tblConstraints.blockSignals(True)
        for constraint, constraint_name in zip(constraints, constraint_names):
            # Create the text for widget item
            label = moniker + ":"+ constraint_name[0] + " = " + constraint_name[1]
            pos = self.tblConstraints.rowCount()
            self.available_constraints[pos] = constraint

            # Show the text in the constraint table
            item = self.uneditableItem(label)
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Checked)
            self.tblConstraints.insertRow(pos)
            self.tblConstraints.setItem(pos, 0, item)
        self.tblConstraints.blockSignals(False)

    def initializeFitList(self):
        """
        Fill the list of model/data sets for fitting/constraining
        """
        # look at the object library to find all fit tabs
        # Show the content of the current "model"
        objects = ObjectLibrary.listObjects()

        # Tab dict
        # moniker -> (kernel_module, data)
        self.available_tabs = {}
        # Constraint dict
        # moniker -> [constraints]
        self.available_constraints = {}

        # Reset the table widgets
        self.tblTabList.setRowCount(0)
        self.tblConstraints.setRowCount(0)

        # Fit disabled
        self.cmdFit.setEnabled(False)

        if not objects:
            return

        tabs = [tab for tab in ObjectLibrary.listObjects() if self.isTabImportable(tab)]
        for tab in tabs:
            self.updateFitLine(tab)
            self.updateSignalsFromTab(tab)
            # We have at least 1 fit page, allow fitting
            self.cmdFit.setEnabled(True)

    def validateMoniker(self, new_moniker=None):
        """
        Check new_moniker for correctness.
        It must be non-empty.
        It must not be the same as other monikers.
        """
        if not new_moniker:
            return False

        for existing_moniker in self.available_tabs:
            if existing_moniker == new_moniker and existing_moniker != self.current_cell:
                return False

        return True

    def getObjectByName(self, name):
        """
        Given name of the fit, returns associated fit object
        """
        for object_name in ObjectLibrary.listObjects():
            object = ObjectLibrary.getObject(object_name)
            if isinstance(object, FittingWidget):
                try:
                    if object.kernel_module.name == name:
                        return object
                except AttributeError:
                    # Disregard atribute errors - empty fit widgets
                    continue
        return None

    def showMultiConstraint(self):
        """
        Invoke the complex constraint editor
        """
        selected_rows = self.selectedParameters(self.tblTabList)
        assert(len(selected_rows)==2)

        tab_list = [ObjectLibrary.getObject(self.tblTabList.item(s, 0).data(0)) for s in selected_rows]
        # Create and display the widget for param1 and param2
        cc_widget = ComplexConstraint(self, tabs=tab_list)
        if cc_widget.exec_() != QtWidgets.QDialog.Accepted:
            return

        constraint = Constraint()
        model1, param1, operator, constraint_text = cc_widget.constraint()

        constraint.func = constraint_text
        constraint.param = param1
        # Find the right tab
        constrained_tab = self.getObjectByName(model1)
        if constrained_tab is None:
            return

        # Find the constrained parameter row
        constrained_row = constrained_tab.getRowFromName(param1)

        # Update the tab
        constrained_tab.addConstraintToRow(constraint, constrained_row)
