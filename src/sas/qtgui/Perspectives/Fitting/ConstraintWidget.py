import logging
import copy
import re

from twisted.internet import threads

import sas.qtgui.Utilities.GuiUtils as GuiUtils

from PySide6 import QtGui, QtCore, QtWidgets

from sas.sascalc.fit.BumpsFitting import BumpsFit as Fit

import sas.qtgui.Utilities.ObjectLibrary as ObjectLibrary
from sas.qtgui.Perspectives.Fitting.UI.ConstraintWidgetUI import Ui_ConstraintWidgetUI
from sas.qtgui.Perspectives.Fitting.FittingWidget import FittingWidget
from sas.qtgui.Perspectives.Fitting.FitThread import FitThread
from sas.qtgui.Perspectives.Fitting.ConsoleUpdate import ConsoleUpdate
from sas.qtgui.Perspectives.Fitting.ComplexConstraint import ComplexConstraint
from sas.qtgui.Perspectives.Fitting import FittingUtilities
from sas.qtgui.Perspectives.Fitting.Constraint import Constraint

from sas import config

logger = logging.getLogger(__name__)

class DnDTableWidget(QtWidgets.QTableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDragDropOverwriteMode(False)
        self.setDropIndicatorShown(True)

        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)

        self._is_dragged = False

    def isDragged(self):
        """
        Return the drag status
        """
        return self._is_dragged

    def dragEnterEvent(self, event):
        """
        Called automatically on a drag in the TableWidget
        """
        self._is_dragged = True
        event.accept()

    def dragLeaveEvent(self, event):
        """
        Called automatically on a drag stop
        """
        self._is_dragged = False
        event.accept()

    def dropEvent(self, event: QtGui.QDropEvent):
        if not event.isAccepted() and event.source() == self:
            drop_row = self.drop_on(event)
            rows = sorted(set(item.row() for item in self.selectedItems()))
            rows_to_move = [[QtWidgets.QTableWidgetItem(self.item(row_index, column_index)) for column_index in range(self.columnCount())]
                            for row_index in rows]
            for row_index in reversed(rows):
                self.removeRow(row_index)
                if row_index < drop_row:
                    drop_row -= 1

            for row_index, data in enumerate(rows_to_move):
                row_index += drop_row
                self.insertRow(row_index)
                for column_index, column_data in enumerate(data):
                    self.setItem(row_index, column_index, column_data)
            event.accept()
            for row_index in range(len(rows_to_move)):
                self.item(drop_row + row_index, 0).setSelected(True)
                self.item(drop_row + row_index, 1).setSelected(True)
        super().dropEvent(event)
        # Reset the drag flag. Must be done after the drop even got accepted!
        self._is_dragged = False

    def drop_on(self, event):
        index = self.indexAt(event.pos())
        if not index.isValid():
            return self.rowCount()

        return index.row() + 1 if self.is_below(event.pos(), index) else index.row()

    def is_below(self, pos, index):
        rect = self.visualRect(index)
        margin = 2
        if pos.y() - rect.top() < margin:
            return False
        elif rect.bottom() - pos.y() < margin:
            return True

        return rect.contains(pos, True) and not \
            (int(self.model().flags(index)) & QtCore.Qt.ItemIsDropEnabled) and \
            pos.y() >= rect.center().y()


class ConstraintWidget(QtWidgets.QWidget, Ui_ConstraintWidgetUI):
    """
    Constraints Dialog to select the desired parameter/model constraints.
    """
    fitCompleteSignal = QtCore.Signal(tuple)
    batchCompleteSignal = QtCore.Signal(tuple)
    fitFailedSignal = QtCore.Signal(tuple)

    def __init__(self, parent=None):
        super(ConstraintWidget, self).__init__()

        self.parent = parent
        self.setupUi(self)

        self.currentType = "FitPage"
        # Page id for fitting
        # To keep with previous SasView values, use 300 as the start offset
        self.page_id = 301
        self.tab_id = self.page_id
        # fitpage order in the widget
        self._row_order = []
        self.weighting_ratios = {}

        # Set the table widget into layout
        self.tblTabList = DnDTableWidget(self)
        self.tblLayout.addWidget(self.tblTabList)

        # Are we chain fitting?
        self.is_chain_fitting = False

        # Are we modifying weight
        self.is_weight_modified = False

        # Is the fit job running?
        self.is_running = False
        self.calc_fit = None

        # Remember previous content of modified cell
        self.current_cell = ""

        # Tabs used in simultaneous fitting
        # tab_name : True/False
        self.tabs_for_fitting = {}

        # Flag that warns ComplexConstraint widget if the constraint has been
        # accepted
        self.constraint_accepted = True

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
        # disable special cases until properly defined
        self.label.setVisible(False)
        self.cbCases.setVisible(False)

        self.sim_fit_labels = ['FitPage', 'Model', 'Data', 'Mnemonic']
        # tab widget - headers
        self.editable_tab_columns = [self.sim_fit_labels.index('Mnemonic')]

        if self.is_weight_modified:
            self.sim_fit_labels.append('Weighting')
            self.editable_tab_columns.append(self.sim_fit_labels.index('Weighting'))

        self.tblTabList.setColumnCount(len(self.sim_fit_labels))
        self.tblTabList.setHorizontalHeaderLabels(self.sim_fit_labels)
        self.tblTabList.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        self.tblTabList.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tblTabList.customContextMenuRequested.connect(self.showModelContextMenu)

        # Single Fit is the default, so disable chainfit
        self.chkChain.setVisible(False)

        # disabled constraint
        labels = ['Constraint']
        self.tblConstraints.setColumnCount(len(labels))
        self.tblConstraints.setHorizontalHeaderLabels(labels)
        self.tblConstraints.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.tblConstraints.setEnabled(False)
        header = self.tblConstraints.horizontalHeaderItem(0)
        header.setToolTip("Double click a row below to edit the constraint.")

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
        self.cmdAdd.clicked.connect(self.showMultiConstraint)
        self.chkChain.toggled.connect(self.onChainFit)
        self.chkWeight.toggled.connect(self.onWeightModify)

        # QTableWidgets
        self.tblTabList.cellChanged.connect(self.onTabCellEdit)
        self.tblTabList.cellDoubleClicked.connect(self.onTabCellEntered)
        self.tblConstraints.cellChanged.connect(self.onConstraintChange)

        # Internal signals
        self.fitCompleteSignal.connect(self.fitComplete)
        self.batchCompleteSignal.connect(self.batchComplete)
        self.fitFailedSignal.connect(self.fitFailed)

        # External signals
        self.parent.tabsModifiedSignal.connect(self.initializeFitList)

    def updateSignalsFromTab(self, tab=None):
        """
        Intercept update signals from fitting tabs
        """
        if tab is None:
            return
        tab_object = ObjectLibrary.getObject(tab)

        # Disconnect all local slots, if connected
        # None of the methods below seem to work with Qt6.2.4
        # 1.
        # if tab_object.receivers(tab_object.newModelSignal) > 0:
        # 2.
        # newModelSignal =QtCore.QMetaMethod.fromSignal(tab_object.newModelSignal)
        # if tab_object.isSignalConnected(newModelSignal):
        # 3.
        # m_obj = tab_object.metaObject()
        # is_connected = m_obj.isSignalConnected(m_obj.method(m_obj.indexOfSignal("newModelSignal()")))

        try:
            tab_object.newModelSignal.disconnect()
        except RuntimeError:
            # need to pass here since no known PySide6 method of checking if signal is connected
            # seems to work here. Need to upgrade to more recent version of PySide6 but this 
            # currently causes other issues.
            pass
        try:
            tab_object.constraintAddedSignal.disconnect()
        except RuntimeError:
            pass

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
        self.chkChain.setVisible(source=="btnBatch")
        self.chkWeight.setVisible(source!="btnBatch")
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

    def onChainFit(self, is_checked):
        """
        Respond to selecting the Chain Fit checkbox
        """
        self.is_chain_fitting = is_checked

    def onWeightModify(self, is_checked):
        """
        Respond to selecting the Modify weighting checkbox
        """
        self.is_weight_modified = is_checked
        self.initializeWidgets()
        self.initializeFitList()

    def onFit(self):
        """
        Perform the constrained/simultaneous fit
        """
        # Stop if we're running
        if self.is_running:
            self.is_running = False
            #re-enable the Fit button
            self.cmdFit.setStyleSheet('QPushButton {color: black;}')
            self.cmdFit.setText("Fit")
            # stop the fitpages
            self.calc_fit.stop()
            return

        # Find out all tabs to fit
        tabs_to_fit = self.getTabsForFit()

        # Single fitter for the simultaneous run
        fitter = Fit()
        fitter.fitter_id = self.page_id

        # prepare fitting problems for each tab
        page_ids = []
        fitter_id = 0
        sim_fitter_list=[fitter]

        # Determine weights for each data-set
        # Need to determine if it is best to use (1/sigma) or (1/relative_error) for this
        weights = {}
        for tab in tabs_to_fit:
            tab_object = ObjectLibrary.getObject(tab)
            #weight = FittingUtilities.getWeight(tab_object.data, tab_object.is2D, flag=tab_object.weighting)
            weight = FittingUtilities.getRelativeError(tab_object.data, tab_object.is2D, flag=tab_object.weighting)
            weights[tab] = weight

        # Calc increase factor for the errors in each dataset
        weight_increase_dict = FittingUtilities.calcWeightIncrease(weights,
                                                                   self.weighting_ratios,
                                                                   self.is_weight_modified)
        logger.info("Simultaneous fit - Data set weights: ")
        for item in weight_increase_dict.items():
            logger.info(item)

        # Prepare the fitter object
        try:
            for tab in tabs_to_fit:
                if not self.isTabImportable(tab): continue
                tab_object = ObjectLibrary.getObject(tab)
                if tab_object is None:
                    # No such tab!
                    return
                weight_increase = weight_increase_dict[tab]
                sim_fitter_list, fitter_id = tab_object.prepareFitters(fitter=sim_fitter_list[0], fit_id=fitter_id,
                                                                       weight_increase=weight_increase)
                page_ids.append([tab_object.page_id])
        except ValueError:
            # No parameters selected in one of the tabs
            no_params_msg = "Fitting cannot be performed.\n" +\
                            "Not all tabs chosen for fitting have parameters selected for fitting."
            QtWidgets.QMessageBox.warning(self, 'Warning', no_params_msg, QtWidgets.QMessageBox.Ok)
            return

        # Create the fitting thread, based on the fitter
        completefn = self.onBatchFitComplete if self.currentType=='BatchPage' else self.onFitComplete

        if config.USING_TWISTED:
            handler = None
            updater = None
        else:
            handler = ConsoleUpdate(parent=self.parent,
                                    manager=self,
                                    improvement_delta=0.1)
            updater = handler.update_fit

        batch_inputs = {}
        batch_outputs = {}

        # Notify the parent about fitting started
        self.parent.fittingStartedSignal.emit(tabs_to_fit)

        # new fit thread object
        self.calc_fit = FitThread(handler=handler,
                                  fn=sim_fitter_list,
                                  batch_inputs=batch_inputs,
                                  batch_outputs=batch_outputs,
                                  page_id=page_ids,
                                  updatefn=updater,
                                  completefn=completefn,
                                  reset_flag=self.is_chain_fitting)

        if config.USING_TWISTED:
            # start the trhrhread with twisted
            self.calc_fit = threads.deferToThread(self.calc_fit.compute)
            self.calc_fit.addCallback(completefn)
            self.calc_fit.addErrback(self.onFitFailed)
        else:
            # Use the old python threads + Queue
            self.calc_fit.queue()
            self.calc_fit.ready(2.5)

        # modify the Fit button
        self.cmdFit.setStyleSheet('QPushButton {color: red;}')
        self.cmdFit.setText('Stop fit')
        self.parent.communicate.statusBarUpdateSignal.emit('Fitting started...')
        self.is_running = True

    def onHelp(self):
        """
        Show the "Fitting" section of help
        """
        tree_location = "/user/qtgui/Perspectives/Fitting/"

        helpfile = "fitting_help.html#simultaneous-fit-mode"
        help_location = tree_location + helpfile

        # OMG, really? Crawling up the object hierarchy...
        #
        # It's the top level that needs to do the show help.
        # Perhaps better to address directly, but it does need to
        # be that object. I don't like that the type is hidden. :LW
        self.parent.parent.showHelp(help_location)

    def onTabCellEdit(self, row, column):
        """
        Respond to check/uncheck and to modify the model moniker and weighting actions
        """
        # If this "Edit" is just a response from moving rows around,
        # update the tab order and leave
        if self.tblTabList.isDragged():
            self._row_order = []
            for i in range(self.tblTabList.rowCount()):
                self._row_order.append(self.tblTabList.item(i,0).data(0))
            return

        if column not in self.editable_tab_columns:
            return

        item = self.tblTabList.item(row, column)

        if column == self.sim_fit_labels.index('FitPage'):
            # Update the tabs for fitting list
            tab_name = item.text()
            self.tabs_for_fitting[tab_name] = (item.checkState() == QtCore.Qt.Checked)
            # Enable fitting only when there are models to fit
            self.cmdFit.setEnabled(any(self.tabs_for_fitting.values()))
            return

        elif column == self.sim_fit_labels.index('Mnemonic'):
            new_moniker = item.data(0)
            # The new name should be validated on the fly, with QValidator
            # but let's just assure it post-factum
            is_good_moniker = self.validateMoniker(new_moniker)
            if not is_good_moniker:
                self.tblTabList.blockSignals(True)
                item.setBackground(QtCore.Qt.red)
                self.tblTabList.blockSignals(False)
                self.cmdFit.setEnabled(False)
                if new_moniker == "":
                    msg = "Please use a non-empty name."
                else:
                    msg = "Please use a unique name."
                self.parent.communicate.statusBarUpdateSignal.emit(msg)
                item.setToolTip(msg)
                return

            self.tblTabList.blockSignals(True)
            item.setBackground(QtCore.Qt.white)
            self.tblTabList.blockSignals(False)
            self.cmdFit.setEnabled(True)
            item.setToolTip("")
            msg = "Fitpage name changed to {}.".format(new_moniker)
            self.parent.communicate.statusBarUpdateSignal.emit(msg)

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

        elif column == self.sim_fit_labels.index('Weighting'):
            new_weighting = item.data(0)

            # Check input
            try:
                float(new_weighting)
            except ValueError:
                # Unacceptable input
                self.tblTabList.blockSignals(True)
                item.setBackground(QtCore.Qt.red)
                self.tblTabList.blockSignals(False)
                self.cmdFit.setEnabled(False)
                msg = "Weighting must be a numerical value (integer or float)."
                self.parent.communicate.statusBarUpdateSignal.emit(msg)
                item.setToolTip(msg)
                return

            # Update value if acceptable input
            self.tblTabList.blockSignals(True)
            item.setBackground(QtCore.Qt.white)
            self.tblTabList.blockSignals(False)
            self.cmdFit.setEnabled(True)
            fit_page_column = self.sim_fit_labels.index('FitPage')
            self.weighting_ratios[self.tblTabList.item(row, fit_page_column).data(0)] = new_weighting

        # Reinitialize the display
        self.initializeFitList()

    def onConstraintChange(self, row, column):
        """
        Modify the constraint when the user edits the constraint list.
        If the user changes the constrained parameter, the constraint is erased
        and a new one is created.
        Checking is performed on the constrained entered by the user.
        In case of an error during checking, a warning message box is shown
        and the constraint is cancelled by reloading the view.
        View is also reloaded when the user is finished for consistency.
        """
        item = self.tblConstraints.item(row, column)
        # Extract information from the constraint object
        constraint = self.available_constraints[row]
        model = constraint.value_ex[:constraint.value_ex.index(".")]
        param = constraint.param
        function = constraint.func
        tab = self.available_tabs[model]
        # Extract information from the text in the table
        constraint_text = item.data(0)
        # Basic sanity check of the string
        # First check if we have an acceptable sign
        if "=" not in constraint_text:
            msg = ("Incorrect operator in constraint definition. Please use = "
                   "sign to define constraints.")
            QtWidgets.QMessageBox.critical(
                self,
                "Inconsistent constraint",
                msg,
                QtWidgets.QMessageBox.Ok)
            self.initializeFitList()
            return

        # Then check if the parameter is correctly defined with colons
        # separating model and parameter name
        lhs, rhs = re.split(" *= *", item.data(0).strip(), 1)
        if ":" not in lhs:
            msg = ("Incorrect constrained parameter definition. Please use "
                   "colons to separate model and parameter on the rhs of the "
                   "definition, e.g. M1:scale")
            QtWidgets.QMessageBox.critical(
                self,
                "Inconsistent constraint",
                msg,
                QtWidgets.QMessageBox.Ok)
            self.initializeFitList()
            return
        # We can parse the string
        new_param = lhs.split(":", 1)[1].strip()
        new_model = lhs.split(":", 1)[0].strip()
        # Check that the symbol is known so we don't get an unknown tab
        # All the conditional statements could be grouped in one or
        # alternatively we could check with expression.py, but we would still
        # need to do some checks to parse the string
        symbol_dict = (self.parent.parent.perspective().
                       getSymbolDictForConstraints())
        qualified_par = f"{new_model}.{new_param}"
        if qualified_par not in symbol_dict:
            msg = (f"Unknown parameter {qualified_par} used in constraint."
                   " Please use a single known parameter in the rhs of the "
                   "constraint definition, e.g. M1:scale = M1.radius + 2")
            QtWidgets.QMessageBox.critical(
                self,
                "Inconsistent constraint",
                msg,
                QtWidgets.QMessageBox.Ok)
            self.initializeFitList()
            return
        new_function = rhs
        new_tab = self.available_tabs[new_model]
        model_key = tab.getModelKeyFromName(param)
        # Make sure we are dealing with fit tabs
        assert isinstance(tab, FittingWidget)
        assert isinstance(new_tab, FittingWidget)
        # Now check if the user has redefined the constraint and reapply it
        if new_function != function or new_model != model or new_param != param:
            # Apply the new constraint
            constraint = Constraint(param=new_param, func=new_function,
                                    value_ex=new_model + "." + new_param)
            model_key = tab.getModelKeyFromName(new_param)
            new_tab.addConstraintToRow(constraint=constraint,
                                       row=tab.getRowFromName(new_param), model_key=model_key)
            # If the constraint is valid and we are changing model or
            # parameter, delete the old constraint
            if (self.constraint_accepted and new_model != model or
                    new_param != param):
                tab.deleteConstraintOnParameter(param)
            # Reload the view
            self.initializeFitList()
            return
        # activate/deactivate constraint if the user has changed the checkbox
        # state
        constraint.active = (item.checkState() == QtCore.Qt.Checked)
        # Update the fitting widget whenever a constraint is
        # activated/deactivated
        if item.checkState() == QtCore.Qt.Checked:
            font = QtGui.QFont()
            font.setItalic(True)
            brush = QtGui.QBrush(QtGui.QColor('blue'))
            tab.modifyViewOnRow(tab.getRowFromName(new_param), font=font,
                                brush=brush, model_key=model_key)
        else:
            tab.modifyViewOnRow(tab.getRowFromName(new_param), model_key=model_key)
        # reload the view so the user gets a consistent feedback on the
        # constraints
        self.initializeFitList()

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
        Send the fit complete signal to main thread
        """
        # Complete signal only accepts a tuple, so send an empty tuple
        # when fit throws an error.

        if result is None:
            result = ()
        self.fitCompleteSignal.emit(result)

    def fitComplete(self, result):
        """
        Respond to the successful fit complete signal
        """
        #re-enable the Fit button
        self.cmdFit.setStyleSheet('QPushButton {color: black;}')
        self.cmdFit.setText("Fit")
        self.is_running = False

        # Notify the parent about completed fitting
        self.parent.fittingStoppedSignal.emit(self.getTabsForFit())

        # Assure the fitting succeeded
        if result is None or not result:
            msg = "Fitting failed."
            self.parent.communicate.statusBarUpdateSignal.emit(msg)
            return

        # Get the results list
        results = result[0][0]
        if isinstance(result[0], str):
            msg = ("Fitting failed with the following message: " +
                   result[0])
            self.parent.communicate.statusBarUpdateSignal.emit(msg)
            return
        if not results[0].success:
            if isinstance(results[0].mesg[0], str):
                msg = ("Fitting failed with the following message: " +
                       results[0].mesg[0])
            else:
                msg = ("Fitting failed. Please ensure correctness of " +
                       "chosen constraints.")
            self.parent.communicate.statusBarUpdateSignal.emit(msg)
            return

        # get the elapsed time
        elapsed = result[1]

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
        Send the fit complete signal to main thread
        """
        self.batchCompleteSignal.emit(result)

    def batchComplete(self, result):
        """
        Respond to the successful batch fit complete signal
        """
        #re-enable the Fit button
        self.cmdFit.setStyleSheet('QPushButton {color: black;}')
        self.cmdFit.setText("Fit")
        self.is_running = False

        # Notify the parent about completed fitting
        self.parent.fittingStoppedSignal.emit(self.getTabsForFit())
        if result is None:
            msg = "Fitting failed."
            self.parent.communicate.statusBarUpdateSignal.emit(msg)
            return

        # get the elapsed time
        elapsed = result[1]

        # Get the results list
        results = result[0][0]
        # Warn the user if fitting has been unsuccessful
        if not results[0].success:
            if isinstance(results[0].mesg[0], str):
                msg = ("Fitting failed with the following message: " +
                       results[0].mesg[0])
            else:
                msg = ("Fitting failed. Please ensure correctness of " +
                       "chosen constraints.")
            self.parent.communicate.statusBarUpdateSignal.emit(msg)
            return

        # Show the grid panel
        page_name = "ConstSimulPage"
        results = copy.deepcopy(result[0])
        results.append(page_name)
        self.parent.communicate.sendDataToGridSignal.emit(results)

        msg = "Fitting completed successfully in: %s s.\n" % GuiUtils.formatNumber(elapsed)
        self.parent.communicate.statusBarUpdateSignal.emit(msg)

    def onFitFailed(self, reason):
        """
        Send the fit failed signal to main thread
        """
        self.fitFailedSignal.emit(reason)

    def fitFailed(self, reason):
        """
        Respond to fitting failure.
        """
        #re-enable the Fit button
        self.cmdFit.setStyleSheet('QPushButton {color: black;}')
        self.cmdFit.setText("Fit")
        self.is_running = False

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
        if not object.data_is_loaded : return False
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

        self.actionSelect = QtGui.QAction(self)
        self.actionSelect.setObjectName("actionSelect")
        self.actionSelect.setText(QtCore.QCoreApplication.translate("self", "Select "+param_string+" for fitting"))
        # Unselect from fitting
        self.actionDeselect = QtGui.QAction(self)
        self.actionDeselect.setObjectName("actionDeselect")
        self.actionDeselect.setText(QtCore.QCoreApplication.translate("self", "De-select "+param_string+" from fitting"))

        self.actionRemoveConstraint = QtGui.QAction(self)
        self.actionRemoveConstraint.setObjectName("actionRemoveConstrain")
        self.actionRemoveConstraint.setText(QtCore.QCoreApplication.translate("self", "Remove all constraints on selected models"))

        self.actionMutualMultiConstrain = QtGui.QAction(self)
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

        self.actionSelect = QtGui.QAction(self)
        self.actionSelect.setObjectName("actionSelect")
        self.actionSelect.setText(QtCore.QCoreApplication.translate("self", "Select "+param_string+" for fitting"))
        # Unselect from fitting
        self.actionDeselect = QtGui.QAction(self)
        self.actionDeselect.setObjectName("actionDeselect")
        self.actionDeselect.setText(QtCore.QCoreApplication.translate("self", "De-select "+param_string+" from fitting"))

        self.actionRemoveConstraint = QtGui.QAction(self)
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
            model_key = tab.getModelKeyFromName(param)
            tab.deleteConstraintOnParameter(param, model_key=model_key)

        # Constraints removed - refresh the table widget
        self.initializeFitList()

    def uneditableItem(self, data=""):
        """
        Returns an uneditable Table Widget Item
        """
        item = QtWidgets.QTableWidgetItem(data)
        item.setFlags( QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled )
        return item

    def updateFitLine(self, tab, model_key="standard"):
        """
        Update a single line of the table widget with tab info
        """
        fit_page = ObjectLibrary.getObject(tab)
        model = fit_page.kernel_module

        if model is None:
            logging.warning("No model selected")
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
        # Weighting is editable, so no option change
        self.tblTabList.setItem(pos, 3, item)
        # Initial definition
        if tab_name not in self.weighting_ratios.keys():
            self.weighting_ratios[tab_name] = "1.0"
        item = QtWidgets.QTableWidgetItem(self.weighting_ratios[tab_name])
        self.tblTabList.setItem(pos, 4, item)
        self.tblTabList.blockSignals(False)

        # Check if any constraints present in tab
        constraint_names = fit_page.getComplexConstraintsForAllModels()
        constraints = fit_page.getConstraintObjectsForAllModels()

        active_constraint_names = []
        constraint_names = []
        constraints = []
        for model_key in fit_page.model_dict.keys():
            active_constraint_names += fit_page.getComplexConstraintsForModel(model_key=model_key)
            constraint_names += fit_page.getFullConstraintNameListForModel(model_key=model_key)
            constraints += fit_page.getConstraintObjectsForModel(model_key=model_key)

        if not constraints:
            return

        self.tblConstraints.setEnabled(True)
        self.tblConstraints.blockSignals(True)
        for constraint, constraint_name in zip(constraints, constraint_names):
            if not constraint_name and len(constraint_name) < 2:
                continue
            if constraint_name[0] is None or constraint_name[1] is None:
                continue
            # Create the text for widget item
            label = moniker + ":" + constraint_name[0] + " = " + constraint_name[1]
            pos = self.tblConstraints.rowCount()
            self.available_constraints[pos] = constraint

            # Show the text in the constraint table
            item = QtWidgets.QTableWidgetItem(label)
            item.setFlags(QtCore.Qt.ItemIsSelectable
                          | QtCore.Qt.ItemIsEnabled
                          | QtCore.Qt.ItemIsUserCheckable
                          | QtCore.Qt.ItemIsEditable)
            # Why was this set to non-interactive??
            if constraint_name in active_constraint_names:
                item.setCheckState(QtCore.Qt.Checked)
            else:
                item.setCheckState(QtCore.Qt.Unchecked)
            self.tblConstraints.insertRow(pos)
            self.tblConstraints.setItem(pos, 0, item)
        self.tblConstraints.blockSignals(False)

    def initializeFitList(self, row=0, model_key="standard"):
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
        if len(tabs) < 1:
            self.cmdAdd.setEnabled(False)
        else:
            self.cmdAdd.setEnabled(True)

        if not self._row_order:
            # Initialize tab order list
            self._row_order = tabs
        else:
            tabs = self.orderedSublist(self._row_order, tabs)
            self._row_order = tabs

        for tab in tabs:
            self.updateFitLine(tab, model_key=model_key)
            self.updateSignalsFromTab(tab)
            # We have at least 1 fit page, allow fitting
            self.cmdFit.setEnabled(True)

    def orderedSublist(self, order_list, target_list):
        """
        Orders the target_list such that any elements
        present in order_list show up first and in the order
        from order_list.
        """
        tmp_list = []
        # 1. get the non-matching elements
        nonmatching = list(set(target_list) - set(order_list))
        # 2: start with matching tabs, in the correct order
        for elem in order_list:
            if elem in target_list:
                tmp_list.append(elem)
        # 3. add the remaning tabs in any order
        ordered_list = tmp_list + nonmatching
        return ordered_list

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

    def onAcceptConstraint(self, con_tuple):
        """
        Receive constraint tuple from the ComplexConstraint dialog and adds
        constraint.
        Checks the constraints for errors and displays a warning message
        interrupting flow if any are found
        """
        #"M1, M2, M3" etc
        model_name, constraint = con_tuple
        constrained_tab = self.getObjectByName(model_name)
        if constrained_tab is None:
            return

        # Find the constrained parameter row
        constrained_row = constrained_tab.getRowFromName(constraint.param)
        model_key = constrained_tab.getModelKeyFromName(constraint.param)

        # Update the tab
        constrained_tab.addConstraintToRow(constraint, constrained_row, model_key=model_key)
        if not self.constraint_accepted:
            return

        # Select this parameter for adjusting/fitting
        # constrained_tab.selectCheckbox(constrained_row, model=model)

    def showMultiConstraint(self):
        """
        Invoke the complex constraint editor
        """
        selected_rows = self.selectedParameters(self.tblTabList)

        tab_list = [ObjectLibrary.getObject(self.tblTabList.item(s, 0).data(0)) for s in range(self.tblTabList.rowCount())]
        # Create and display the widget for param1 and param2
        cc_widget = ComplexConstraint(self, tabs=tab_list)
        cc_widget.constraintReadySignal.connect(self.onAcceptConstraint)

        if cc_widget.exec_() != QtWidgets.QDialog.Accepted:
            return

    def getFitPage(self):
        """
        Retrieves the state of this page
        """
        param_list = []

        param_list.append(['is_constraint', 'True'])
        param_list.append(['data_id', "cs_tab"+str(self.page_id)])
        param_list.append(['current_type', self.currentType])
        param_list.append(['is_chain_fitting', str(self.is_chain_fitting)])
        param_list.append(['special_case', self.cbCases.currentText()])

        return param_list

    def getFitModel(self):
        """
        Retrieves current model
        """
        model_list = []

        checked_models = {}
        for row in range(self.tblTabList.rowCount()):
            model_name = self.tblTabList.item(row,1).data(0)
            active = self.tblTabList.item(row,0).checkState()# == QtCore.Qt.Checked
            checked_models[model_name] = str(active)

        checked_constraints = {}
        for row in range(self.tblConstraints.rowCount()):
            model_name = self.tblConstraints.item(row,0).data(0)
            active = self.tblConstraints.item(row,0).checkState()# == QtCore.Qt.Checked
            checked_constraints[model_name] = str(active)

        model_list.append(['checked_models', checked_models])
        model_list.append(['checked_constraints', checked_constraints])
        return model_list

    def createPageForParameters(self, parameters=None):
        """
        Update the page with passed parameter values
        """
        # checked models
        if not 'checked_models' in parameters:
            return
        models = parameters['checked_models'][0]
        for model, check_state in models.items():
            for row in range(self.tblTabList.rowCount()):
                model_name = self.tblTabList.item(row,1).data(0)
                if model_name != model:
                    continue
                # check/uncheck item
                # check_state is a string: "CheckState.Checked" or "CheckState.Unchecked"
                if 'Unchecked' in check_state:
                    self.tblTabList.item(row,0).setCheckState(QtCore.Qt.Unchecked)
                else:
                    self.tblTabList.item(row,0).setCheckState(QtCore.Qt.Checked)

        if not 'checked_constraints' in parameters:
            return
        # checked constraints
        models = parameters['checked_constraints'][0]
        for model, check_state in models.items():
            for row in range(self.tblConstraints.rowCount()):
                model_name = self.tblConstraints.item(row,0).data(0)
                if model_name != model:
                    continue
                # check/uncheck item
                if 'Unchecked' in check_state:
                    self.tblConstraints.item(row, 0).setCheckState(QtCore.Qt.Unchecked)
                else:
                    self.tblConstraints.item(row, 0).setCheckState(QtCore.Qt.Checked)

        # fit/batch radio
        isBatch = parameters['current_type'][0] == 'BatchPage'
        if isBatch:
            self.btnBatch.toggle()

        # chain
        is_chain = parameters['is_chain_fitting'][0] == 'True'
        if isBatch:
            self.chkChain.setChecked(is_chain)

    def getReport(self):
        """
        Wrapper for non-existent functionality.
        Tell the user to use the reporting tool
        on separate fit pages.
        """
        msg = "Please use Report Results directly on fit pages"
        msg += " involved in the Constrained and Simultaneous fitting process."
        msgbox = QtWidgets.QMessageBox(self)
        msgbox.setIcon(QtWidgets.QMessageBox.Warning)
        msgbox.setText(msg)
        msgbox.setWindowTitle("Fit Report")
        _ = msgbox.exec_()
        return

    def uncheckConstraint(self, name):
        """
        Unchecks the constraint in tblConstraint with *name* slave
        parameter and deactivates the constraint.
        """
        for row in range(self.tblConstraints.rowCount()):
            constraint = self.tblConstraints.item(row, 0).data(0)
            # slave parameter has model name and parameter separated
            # by colon e.g `M1:scale` so no need to parse the constraint
            # string.
            if name in constraint:
                self.tblConstraints.item(row, 0).setCheckState(QtCore.Qt.Unchecked)
                # deactivate the constraint
                tab = self.parent.getTabByName(name[:name.index(":")])
                row = tab.getRowFromName(name[name.index(":") + 1:])
                model_key = tab.getModelKey(constraint)
                tab.getConstraintForRow(row, model_key=model_key).active = False
