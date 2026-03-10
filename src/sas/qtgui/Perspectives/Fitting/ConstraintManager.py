"""
ConstraintManager: Handles constraint management for fitting parameters.

This module separates constraint-related logic from the FittingWidget UI,
managing constraint creation, validation, editing, and deletion.
"""

import logging

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from sas.qtgui.Perspectives.Fitting import FittingUtilities
from sas.qtgui.Perspectives.Fitting.Constraint import Constraint
from sas.qtgui.Perspectives.Fitting.MultiConstraint import MultiConstraint

logger = logging.getLogger(__name__)


class ConstraintManager:
    """
    Controller class that manages constraints separately from the UI.

    This class handles:
    - Adding/removing/editing constraints
    - Validating constraints
    - Querying constraint status
    - Managing constraint UI dialogs
    """

    def __init__(self, widget):
        """
        Initialize the ConstraintManager.

        Parameters
        ----------
        widget : FittingWidget
            The parent FittingWidget instance for accessing UI state and models
        """
        self.widget = widget

    @property
    def model_dict(self):
        """Convenience accessor for the widget's model dictionary."""
        return self.widget.model_dict

    @property
    def lst_dict(self):
        """Convenience accessor for the widget's list dictionary."""
        return self.widget.lst_dict

    def showMultiConstraint(self, current_list: QtWidgets.QTreeView | None = None) -> None:
        """
        Show the constraint widget and receive the expression.

        Parameters
        ----------
        current_list : QtWidgets.QTreeView | None
            The list widget to operate on (defaults to lstParams)
        """
        if current_list is None:
            current_list = self.widget.lstParams
        model = current_list.model()

        # Find the model key
        model_key = "standard"
        for key, val in self.model_dict.items():
            if val == model:
                model_key = key
                break

        selected_rows = current_list.selectionModel().selectedRows()
        # There have to be only two rows selected. The caller takes care of that
        # but let's check the correctness.
        assert len(selected_rows) == 2

        params_list = [s.data() for s in selected_rows]
        # Create and display the widget for param1 and param2
        mc_widget = MultiConstraint(self.widget, params=params_list)

        # Check if any of the parameters are polydisperse
        if not np.any([FittingUtilities.isParamPolydisperse(p, self.widget.logic.model_parameters,
                                                             is2D=self.widget.is2D) for p in params_list]):
            # no parameters are pd - reset the text to not show the warning
            mc_widget.lblWarning.setText("")

        if mc_widget.exec_() != QtWidgets.QDialog.Accepted:
            return

        constraint = Constraint()
        c_text = mc_widget.txtConstraint.text()

        # widget.params[0] is the parameter we're constraining
        constraint.param = mc_widget.params[0]
        # parameter should have the model name preamble
        model_name = self.widget.logic.kernel_module.name
        # param_used is the parameter we're using in constraining function
        param_used = mc_widget.params[1]
        # Replace param_used with model_name.param_used
        updated_param_used = model_name + "." + param_used
        new_func = c_text.replace(param_used, updated_param_used)
        constraint.func = new_func
        constraint.value_ex = updated_param_used

        # Which row is the constrained parameter in?
        row = self.widget.getRowFromName(constraint.param)

        # what is the parameter to constraint to?
        constraint.value = param_used

        # Should the new constraint be validated?
        constraint.validate = mc_widget.validate

        # Create a new item and add the Constraint object as a child
        self.addConstraintToRow(constraint=constraint, row=row, model_key=model_key)

    def addConstraintToRow(self, constraint: Constraint | None = None, row: int = 0,
                          model_key: str = "standard") -> None:
        """
        Add the constraint object to the requested row.

        The constraint is first checked for errors, and a message box interrupting
        flow is displayed with the reason for failure if validation fails.

        Parameters
        ----------
        constraint : Constraint | None
            The constraint object to add
        row : int
            The row number to add the constraint to
        model_key : str
            The model key ('standard', 'poly', or 'magnet')
        """
        # Create a new item and add the Constraint object as a child
        assert isinstance(constraint, Constraint)
        model = self.model_dict[model_key]
        assert 0 <= row <= model.rowCount()
        assert self.widget.isCheckable(row, model_key=model_key)

        # Error checking
        # First, get a list of constraints and symbols
        constraint_list = self.widget.parent.perspective().getActiveConstraintList()
        symbol_dict = self.widget.parent.perspective().getSymbolDictForConstraints()

        if model_key == 'poly' and 'Distribution' in constraint.param:
            constraint.param = self.widget.polydispersity_widget.polyNameToParam(constraint.param)

        constraint_list.append((self.widget.modelName() + '.' + constraint.param,
                                constraint.func))

        # Call the error checking function
        errors = FittingUtilities.checkConstraints(symbol_dict, constraint_list)

        # get the constraint tab
        constraint_tab = self.widget.parent.perspective().getConstraintTab()

        if errors:
            # Display the message box
            QtWidgets.QMessageBox.critical(
                self.widget,
                "Inconsistent constraint",
                errors,
                QtWidgets.QMessageBox.Ok)
            # Check if there is a constraint tab
            if constraint_tab:
                # Set the constraint_accepted flag to False to inform the
                # constraint tab that the constraint was not accepted
                constraint_tab.constraint_accepted = False
            return

        item = QtGui.QStandardItem()
        item.setData(constraint)
        model.item(row, 1).setChild(0, item)

        # Set min/max to the value constrained
        self.widget.constraintAddedSignal.emit([row], model_key)

        # Show visual hints for the constraint
        font = QtGui.QFont()
        font.setItalic(True)
        brush = QtGui.QBrush(QtGui.QColor('blue'))
        self.widget.modifyViewOnRow(row, font=font, brush=brush, model_key=model_key)

        # update the main parameter list so the constrained parameter gets
        # updated when fitting
        self.widget.checkboxSelected(model.item(row, 0), model_key=model_key)
        self.widget.communicator.statusBarUpdateSignal.emit('Constraint added')

        if constraint_tab:
            # Set the constraint_accepted flag to True to inform the
            # constraint tab that the constraint was accepted
            constraint_tab.constraint_accepted = True

    def addSimpleConstraint(self) -> None:
        """
        Add a constraint on a single parameter, fixing it to its current value.
        """
        model_key = self.widget.tabToKey[self.widget.tabFitting.currentIndex()]
        model = self.model_dict[model_key]
        current_list = self.lst_dict[model_key]
        delegate = current_list.itemDelegate()

        # Get correct min/max column indices based on model type
        if model_key == 'poly':
            min_col = delegate.poly_min
            max_col = delegate.poly_max
        elif model_key == 'magnet':
            min_col = delegate.mag_min
            max_col = delegate.mag_max
        else:
            min_col = delegate.param_min
            max_col = delegate.param_max

        for row in self.widget.selectedParameters(model_key=model_key):
            param = model.item(row, 0).text()
            # Convert display name to actual parameter name for poly
            if model_key == 'poly':
                param = self.widget.polydispersity_widget.polyNameToParam(param)
            value = model.item(row, 1).text()
            min_t = model.item(row, min_col).text()
            max_t = model.item(row, max_col).text()

            # Create a Constraint object
            constraint = Constraint(param=param, value=value, min=min_t, max=max_t)
            constraint.active = False

            # Create a new item and add the Constraint object as a child
            item = QtGui.QStandardItem()
            item.setData(constraint)
            model.item(row, 1).setChild(0, item)

            # Assumed correctness from the validator
            value_float = float(value)
            # BUMPS calculates log(max-min) without any checks, so let's assign minor range
            min_v = value_float - (value_float / 10000.0)
            max_v = value_float + (value_float / 10000.0)

            # Set min/max to the value constrained
            model.item(row, min_col).setText(str(min_v))
            model.item(row, max_col).setText(str(max_v))
            self.widget.constraintAddedSignal.emit([row], model_key)

            # Show visual hints for the constraint
            font = QtGui.QFont()
            font.setItalic(True)
            brush = QtGui.QBrush(QtGui.QColor('blue'))
            self.widget.modifyViewOnRow(row, font=font, brush=brush, model_key=model_key)

        self.widget.communicator.statusBarUpdateSignal.emit('Constraint added')

    def editConstraint(self) -> None:
        """
        Edit constraints for selected parameters.
        """
        current_list = self.widget.tabToList[self.widget.tabFitting.currentIndex()]
        model_key = self.widget.tabToKey[self.widget.tabFitting.currentIndex()]

        params_list = [s.data() for s in current_list.selectionModel().selectedRows()
                   if self.widget.isCheckable(s.row(), model_key=model_key)]
        assert len(params_list) == 1

        row = current_list.selectionModel().selectedRows()[0].row()
        constraint = self.getConstraintForRow(row, model_key=model_key)

        # Create and display the widget for param1 and param2
        mc_widget = MultiConstraint(self.widget, params=params_list, constraint=constraint)

        # Check if any of the parameters are polydisperse
        if not np.any([FittingUtilities.isParamPolydisperse(p, self.widget.logic.model_parameters,
                                                             is2D=self.widget.is2D) for p in params_list]):
            # no parameters are pd - reset the text to not show the warning
            mc_widget.lblWarning.setText("")

        if mc_widget.exec_() != QtWidgets.QDialog.Accepted:
            return

        constraint = Constraint()
        c_text = mc_widget.txtConstraint.text()

        # widget.params[0] is the parameter we're constraining
        constraint.param = mc_widget.params[0]
        # parameter should have the model name preamble
        model_name = self.widget.logic.kernel_module.name
        # param_used is the parameter we're using in constraining function
        param_used = mc_widget.params[1]
        # Replace param_used with model_name.param_used
        updated_param_used = model_name + "." + param_used
        # Update constraint with new values
        constraint.func = c_text
        constraint.value_ex = updated_param_used
        constraint.value = param_used
        # Should the new constraint be validated?
        constraint.validate = mc_widget.validate

        # Which row is the constrained parameter in?
        if model_key == 'poly' and 'Distribution' in constraint.param:
            constraint.param = self.widget.polydispersity_widget.polyNameToParam(constraint.param)
        row = self.widget.getRowFromName(constraint.param)

        # Create a new item and add the Constraint object as a child
        self.addConstraintToRow(constraint=constraint, row=row, model_key=model_key)

    def deleteConstraint(self) -> None:
        """
        Delete constraints from selected parameters.
        """
        current_list = self.widget.tabToList[self.widget.tabFitting.currentIndex()]
        model_key = self.widget.tabToKey[self.widget.tabFitting.currentIndex()]
        params = [s.data() for s in current_list.selectionModel().selectedRows()
                   if self.widget.isCheckable(s.row(), model_key=model_key)]

        for param in params:
            if model_key == 'poly':
                param = self.widget.polydispersity_widget.polyNameToParam(param)
            self.deleteConstraintOnParameter(param=param, model_key=model_key)

    def deleteConstraintOnParameter(self, param: str | None = None, model_key: str = "standard") -> None:
        """
        Delete the constraint on model parameter 'param'.

        Parameters
        ----------
        param : str | None
            The parameter name to delete constraints from (None deletes all)
        model_key : str
            The model key ('standard', 'poly', or 'magnet')
        """
        param_list = self.lst_dict[model_key]
        model = self.model_dict[model_key]
        delegate = param_list.itemDelegate()

        # Get correct min/max column indices based on model type
        if model_key == 'poly':
            min_col = delegate.poly_min
            max_col = delegate.poly_max
        elif model_key == 'magnet':
            min_col = delegate.mag_min
            max_col = delegate.mag_max
        else:
            min_col = delegate.param_min
            max_col = delegate.param_max

        for row in range(model.rowCount()):
            if not self.widget.isCheckable(row, model_key=model_key):
                continue
            if not self.rowHasConstraint(row, model_key=model_key):
                continue

            # Get the Constraint object from of the model item
            item = model.item(row, 1)
            constraint = self.getConstraintForRow(row, model_key=model_key)

            if constraint is None:
                continue
            if not isinstance(constraint, Constraint):
                continue
            if param and constraint.param != param:
                continue

            # Now we got the right row. Delete the constraint and clean up
            # Retrieve old values and put them on the model
            if constraint.min is not None:
                model.item(row, min_col).setText(constraint.min)

            if constraint.max is not None:
                model.item(row, max_col).setText(constraint.max)

            # Remove constraint item
            item.removeRow(0)
            self.widget.constraintAddedSignal.emit([row], model_key)
            self.widget.modifyViewOnRow(row, model_key=model_key)

        self.widget.communicator.statusBarUpdateSignal.emit('Constraint removed')

    def getConstraintForRow(self, row: int, model_key: str = "standard") -> Constraint | None:
        """
        For the given row, return its constraint, if any (otherwise None).

        Parameters
        ----------
        row : int
            The row number
        model_key : str
            The model key ('standard', 'poly', or 'magnet')

        Returns
        -------
        Constraint | None
            The constraint object or None if no constraint exists
        """
        model = self.model_dict[model_key]
        if not self.widget.isCheckable(row, model_key=model_key):
            return None
        item = model.item(row, 1)
        try:
            return item.child(0).data()
        except AttributeError:
            return None

    def paramHasConstraint(self, param: str | None = None) -> bool:
        """
        Find out if the given parameter in all the models has a constraint child.

        Parameters
        ----------
        param : str | None
            The parameter name to check

        Returns
        -------
        bool
            True if parameter has a constraint
        """
        if param is None:
            return False
        if param not in self.widget.allParamNames():
            return False

        for model_key in self.model_dict:
            for row in range(self.model_dict[model_key].rowCount()):
                param_name = self.model_dict[model_key].item(row, 0).text()
                if model_key == 'poly':
                    param_name = self.widget.polydispersity_widget.polyNameToParam(param_name)
                if param_name != param:
                    continue
                return self.rowHasConstraint(row, model_key=model_key)

        # nothing found
        return False

    def rowHasConstraint(self, row: int, model_key: str = "standard") -> bool:
        """
        Find out if row of the main model has a constraint child.

        Parameters
        ----------
        row : int
            The row number
        model_key : str
            The model key ('standard', 'poly', or 'magnet')

        Returns
        -------
        bool
            True if row has a constraint
        """
        model = self.model_dict[model_key]

        if not self.widget.isCheckable(row, model_key=model_key):
            return False
        item = model.item(row, 1)
        if not item.hasChildren():
            return False
        c = item.child(0).data()
        if isinstance(c, Constraint):
            return True
        return False

    def rowHasActiveConstraint(self, row: int, model_key: str = "standard") -> bool:
        """
        Find out if row of the main model has an active constraint child.

        Parameters
        ----------
        row : int
            The row number
        model_key : str
            The model key ('standard', 'poly', or 'magnet')

        Returns
        -------
        bool
            True if row has an active constraint
        """
        model = self.model_dict[model_key]
        if not self.widget.isCheckable(row, model_key=model_key):
            return False
        item = model.item(row, 1)
        if not item.hasChildren():
            return False
        c = item.child(0).data()
        if isinstance(c, Constraint) and c.active:
            return True
        return False

    def rowHasActiveComplexConstraint(self, row: int, model_key: str = "standard") -> bool:
        """
        Find out if row of the main model has an active, nontrivial constraint child.

        Parameters
        ----------
        row : int
            The row number
        model_key : str
            The model key ('standard', 'poly', or 'magnet')

        Returns
        -------
        bool
            True if row has an active complex constraint
        """
        model = self.model_dict[model_key]
        if not self.widget.isCheckable(row, model_key=model_key):
            return False
        item = model.item(row, 1)
        if not item.hasChildren():
            return False
        c = item.child(0).data()
        if isinstance(c, Constraint) and c.func and c.active:
            return True
        return False

    def getConstraintsForAllModels(self) -> list[tuple[str, str]]:
        """
        Return a list of tuples with constraints for all models.

        Each tuple contains constraints mapped as:
        ('constrained parameter', 'function to constrain')
        e.g. [('sld','5*sld_solvent')]

        Returns
        -------
        list[tuple[str, str]]
            List of (parameter, function) tuples
        """
        params = []
        for model_key in self.model_dict:
            model = self.model_dict[model_key]
            param_number = model.rowCount()
            if model_key == 'poly':
                params += [(self.widget.polydispersity_widget.polyNameToParam(model.item(s, 0).text()),
                           model.item(s, 1).child(0).data().func)
                           for s in range(param_number) if self.rowHasActiveConstraint(s, model_key=model_key)]
            else:
                params += [(model.item(s, 0).text(),
                           model.item(s, 1).child(0).data().func)
                           for s in range(param_number) if self.rowHasActiveConstraint(s, model_key=model_key)]
        return params

    def getComplexConstraintsForAllModels(self) -> list[tuple[str, str]]:
        """
        Return a list of tuples containing all the constraints for a given FitPage.

        Returns
        -------
        list[tuple[str, str]]
            List of (parameter, function) tuples
        """
        constraints = []
        for model_key in self.model_dict:
            constraints += self.getComplexConstraintsForModel(model_key=model_key)
        return constraints

    def getComplexConstraintsForModel(self, model_key: str) -> list[tuple[str, str]]:
        """
        Return a list of tuples with constraints for a specific model.

        Each tuple contains constraints mapped as:
        ('constrained parameter', 'function to constrain')
        e.g. [('sld','5*M2.sld_solvent')].
        Only for constraints with defined VALUE

        Parameters
        ----------
        model_key : str
            The model key ('standard', 'poly', or 'magnet')

        Returns
        -------
        list[tuple[str, str]]
            List of (parameter, function) tuples
        """
        model = self.model_dict[model_key]
        params = []
        param_number = model.rowCount()

        for s in range(param_number):
            if self.rowHasActiveComplexConstraint(s, model_key):
                if model.item(s, 0).data(role=QtCore.Qt.UserRole):
                    parameter_name = str(model.item(s, 0).data(role=QtCore.Qt.UserRole))
                else:
                    parameter_name = str(model.item(s, 0).data(0))
                params.append((parameter_name, model.item(s, 1).child(0).data().func))
        return params

    def getFullConstraintNameListForModel(self, model_key: str) -> list[tuple[str, str]]:
        """
        Return a list of tuples with all constraints for a specific model.

        Each tuple contains constraints mapped as:
        ('constrained parameter', 'function to constrain')
        e.g. [('sld','5*M2.sld_solvent')].
        Returns a list of all constraints, not only active ones.

        Parameters
        ----------
        model_key : str
            The model key ('standard', 'poly', or 'magnet')

        Returns
        -------
        list[tuple[str, str]]
            List of (parameter, function) tuples
        """
        model = self.model_dict[model_key]
        param_number = model.rowCount()
        params = list()

        for s in range(param_number):
            if self.rowHasConstraint(s, model_key=model_key):
                param_name = model.item(s, 0).text()
                if model_key == 'poly':
                    param_name = self.widget.polydispersity_widget.polyNameToParam(model.item(s, 0).text())
                params.append((param_name, model.item(s, 1).child(0).data().func))
        return params

    def getConstraintObjectsForAllModels(self) -> list[Constraint]:
        """
        Return a list of constraint objects for a given FitPage.

        Returns
        -------
        list[Constraint]
            List of Constraint objects
        """
        constraints = []
        for model_key in self.model_dict:
            constraints += self.getConstraintObjectsForModel(model_key=model_key)
        return constraints

    def getConstraintObjectsForModel(self, model_key: str) -> list[Constraint]:
        """
        Return Constraint objects present on the whole model.

        Parameters
        ----------
        model_key : str
            The model key ('standard', 'poly', or 'magnet')

        Returns
        -------
        list[Constraint]
            List of Constraint objects
        """
        model = self.model_dict[model_key]
        param_number = model.rowCount()
        constraints = [model.item(s, 1).child(0).data()
                       for s in range(param_number) if self.rowHasConstraint(s, model_key=model_key)]
        return constraints

    def getConstraintsForFitting(self) -> list[tuple[str, str]]:
        """
        Return a list of constraints in format ready for use in fitting.

        Handles multi-model constraints by prompting the user to deactivate them.

        Returns
        -------
        list[tuple[str, str]]
            List of (parameter, function) tuples

        Raises
        ------
        ValueError
            If user cancels fitting due to multi-model constraints
        """
        # Get constraints
        constraints = []
        for model_key in self.model_dict:
            constraints += self.getComplexConstraintsForModel(model_key=model_key)

        # See if there are any constraints across models
        multi_constraints = [cons for cons in constraints
                            if self.widget.isConstraintMultimodel(cons[1])]

        if multi_constraints:
            # Let users choose what to do
            msg = "The current fit contains constraints relying on other fit pages.\n"
            msg += ("Parameters with those constraints are:\n" +
                    '\n'.join([cons[0] for cons in multi_constraints]))
            msg += ("\n\nWould you like to deactivate these constraints or "
                    "cancel fitting?")
            msgbox = QtWidgets.QMessageBox(self.widget)
            msgbox.setIcon(QtWidgets.QMessageBox.Warning)
            msgbox.setText(msg)
            msgbox.setWindowTitle("Existing Constraints")

            # custom buttons
            button_remove = QtWidgets.QPushButton("Deactivate")
            msgbox.addButton(button_remove, QtWidgets.QMessageBox.YesRole)
            button_cancel = QtWidgets.QPushButton("Cancel")
            msgbox.addButton(button_cancel, QtWidgets.QMessageBox.RejectRole)
            retval = msgbox.exec_()

            if retval == QtWidgets.QMessageBox.RejectRole:
                # cancel fit
                raise ValueError("Fitting cancelled")
            else:
                constraint_tab = self.widget.parent.perspective().getConstraintTab()
                for cons in multi_constraints:
                    # deactivate the constraint
                    row = self.widget.getRowFromName(cons[0])
                    model_key = self.widget.getModelKeyFromName(cons[0])
                    self.getConstraintForRow(row, model_key=model_key).active = False
                    # uncheck in the constraint tab
                    if constraint_tab:
                        constraint_tab.uncheckConstraint(
                            self.widget.logic.kernel_module.name + ':' + cons[0])
                # re-read the constraints
                constraints = self.getComplexConstraintsForModel(model_key=model_key)

        return constraints
