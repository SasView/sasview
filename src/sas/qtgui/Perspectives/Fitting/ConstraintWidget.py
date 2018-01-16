import os
import sys

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from PyQt5 import QtGui, QtCore, QtWidgets

import sas.qtgui.Utilities.ObjectLibrary as ObjectLibrary

from sas.qtgui.Perspectives.Fitting.UI.ConstraintWidgetUI import Ui_ConstraintWidgetUI
from sas.qtgui.Perspectives.Fitting.FittingWidget import FittingWidget

class ConstraintWidget(QtWidgets.QWidget, Ui_ConstraintWidgetUI):
    """
    Constraints Dialog to select the desired parameter/model constraints.
    """

    def __init__(self, parent=None):
        super(ConstraintWidget, self).__init__()
        self.parent = parent
        self.setupUi(self)
        self.currentType = "FitPage"

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
        labels = ['FitPage', 'Model', 'Data', 'Mnemonics']
        # tab widget - headers
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
        self.btnSingle.toggled.connect(self.onFitTypeChange)
        self.btnBatch.toggled.connect(self.onFitTypeChange)
        self.cbCases.currentIndexChanged.connect(self.onSpecialCaseChange)
        self.cmdFit.clicked.connect(self.onFit)
        self.cmdHelp.clicked.connect(self.onHelp)
        self.parent.tabsModifiedSignal.connect(self.initializeFitList)

    def updateSignalsFromTab(self, tab=None):
        """
        Intercept update signals from fitting tabs
        """
        if tab is not None:
            ObjectLibrary.getObject(tab).constraintAddedSignal.connect(self.initializeFitList)
            ObjectLibrary.getObject(tab).newModelSignal.connect(self.initializeFitList)

    def onFitTypeChange(self, checked):
        """
        Respond to the fit type change
        single fit/batch fit
        """
        pass

    def onSpecialCaseChange(self, index):
        """
        Respond to the combobox change for special case constraint sets
        """
        pass

    def onFit(self):
        """
        Perform the constrained/simultaneous fit
        """
        pass

    def onHelp(self):
        """
        Display the help page
        """
        pass

    def isTabImportable(self, tab):
        """
        Determines if the tab can be imported and included in the widget
        """
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
        to_string = "to its current value" if num_rows==1 else "to their current values"

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

        #menu.addAction(self.actionRemoveConstraint)
        if num_rows >= 2:
            menu.addAction(self.actionMutualMultiConstrain)

        # Define the callbacks
        #self.actionConstrain.triggered.connect(self.addSimpleConstraint)
        #self.actionRemoveConstraint.triggered.connect(self.deleteConstraint)
        #self.actionMutualMultiConstrain.triggered.connect(self.showMultiConstraint)
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
        to_string = "to its current value" if num_rows==1 else "to their current values"

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
        #self.actionConstrain.triggered.connect(self.addSimpleConstraint)
        self.actionRemoveConstraint.triggered.connect(self.deleteConstraint)
        #self.actionMutualMultiConstrain.triggered.connect(self.showMultiConstraint)
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

    def updateFitLine(self, tab):
        """
        Update a single line of the table widget with tab info
        """
        model = ObjectLibrary.getObject(tab).kernel_module
        if model is None:
            return
        tab_name = tab
        model_name = model.id
        moniker = model.name
        model_data = ObjectLibrary.getObject(tab).data
        model_filename = model_data.filename
        self.available_tabs[moniker] = ObjectLibrary.getObject(tab)

        # Update the model table widget
        item = QtWidgets.QTableWidgetItem(tab_name)
        item.setCheckState(QtCore.Qt.Checked)
        pos = self.tblTabList.rowCount()
        self.tblTabList.insertRow(pos)
        self.tblTabList.setItem(pos, 0, item)
        self.tblTabList.setItem(pos, 1, QtWidgets.QTableWidgetItem(model_name))
        self.tblTabList.setItem(pos, 2, QtWidgets.QTableWidgetItem(model_filename))
        self.tblTabList.setItem(pos, 3, QtWidgets.QTableWidgetItem(moniker))

        #self.available_tabs[pos] = (model, model_data)
        #self.available_tabs[moniker] = tab

        # Check if any constraints present in tab
        constraints = ObjectLibrary.getObject(tab).getConstraintsForModel()
        if not constraints: 
            return
        self.tblConstraints.setEnabled(True)
        for constraint in constraints:
            # Create the text for widget item
            label = moniker + ":"+ constraint[0] + " = " + constraint[1]

            # Show the text in the constraint table
            item = QtWidgets.QTableWidgetItem(label)
            item.setCheckState(QtCore.Qt.Checked)
            pos = self.tblConstraints.rowCount()
            self.tblConstraints.insertRow(pos)
            self.tblConstraints.setItem(pos, 0, item)
            self.available_constraints[pos] = constraints

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
