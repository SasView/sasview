"""
Widget for multi-model constraints.
"""
import os

# numpy methods required for the validator! Don't remove.
# pylint: disable=unused-import,unused-wildcard-import,redefined-builtin
from numpy import *

from PySide6 import QtCore
from PySide6 import QtGui
from PySide6 import QtWidgets
import webbrowser

from sas.qtgui.Perspectives.Fitting import FittingUtilities
import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Perspectives.Fitting.Constraint import Constraint

#ALLOWED_OPERATORS = ['=','<','>','>=','<=']
ALLOWED_OPERATORS = ['=']

# Local UI
from sas.qtgui.Perspectives.Fitting.UI.ComplexConstraintUI import Ui_ComplexConstraintUI

class ComplexConstraint(QtWidgets.QDialog, Ui_ComplexConstraintUI):
    constraintReadySignal = QtCore.Signal(tuple)
    def __init__(self, parent=None, tabs=None):
        super(ComplexConstraint, self).__init__(parent)

        self.setupUi(self)
        self.setModal(True)

        # Useful globals
        self.tabs = tabs
        self.params = None
        self.tab_names = None
        self.operator = '='
        self._constraint = Constraint()
        self.all_menu = None
        self.parent = parent
        self.redefining_warning = ""

        self.warning = self.labelWarning.text()
        self.setupData()
        self.setupSignals()
        self.setupWidgets()
        self.setupTooltip()

        # Default focus is on OK
        self.buttonOK.setFocus()

    def setupData(self):
        """
        Digs into self.tabs and pulls out relevant info
        """
        self.tab_names = [tab.kernel_module.name for tab in self.tabs]
        self.params = [tab.getParamNames() for tab in self.tabs]

    def setupSignals(self):
        """
        Signals from various elements
        """
        self.buttonOK.clicked.connect(self.onApply)
        self.buttonHelp.clicked.connect(self.onHelp)
        self.buttonAddAll.clicked.connect(self.onSetAll)

        self.textComplexConstraint.editingFinished.connect(self.validateFormula)
        self.comboboxModel1.currentIndexChanged.connect(self.onModelIndexChange)
        self.comboboxModel2.currentIndexChanged.connect(self.onModelIndexChange)

        self.comboboxParam1.currentIndexChanged.connect(self.onParamIndexChange)
        self.comboboxParam2.currentIndexChanged.connect(self.onParamIndexChange)
        self.comboboxOperator.currentIndexChanged.connect(self.onOperatorChange)

    def setupWidgets(self):
        """
        Setup widgets based on current parameters
        """
        self.comboboxModel1.insertItems(0, self.tab_names)
        # add an `All` option in the lhs if there are more than 3 tabs
        if len(self.tab_names) > 2:
            self.comboboxModel1.addItem("All")
        self.comboboxModel2.insertItems(0, self.tab_names)

        self.setupParamWidgets()

        self.setupMenu()

    def setupMenu(self):
        # Show Add All button, if necessary
        if self.comboboxModel1.currentText() ==self.comboboxModel2.currentText():
            self.buttonAddAll.setVisible(False)
        else:
            self.buttonAddAll.setVisible(True)
        return

    def setupParamWidgets(self):
        """
        Fill out comboboxes and set labels with non-constrained parameters
        """
        # Store previously select parameter
        previous_param1 = self.comboboxParam1.currentText()
        # Clear the combobox
        self.comboboxParam1.clear()
        # Populate the left combobox parameter arbitrarily with the parameters
        # from the first tab if `All` option is selected
        if self.comboboxModel1.currentText() == "All":
            items1 = self.tabs[1].main_params_to_fit + self.tabs[1].poly_params_to_fit
        else:
            tab_index1 = self.comboboxModel1.currentIndex()
            items1 = self.tabs[tab_index1].main_params_to_fit + self.tabs[tab_index1].poly_params_to_fit
        self.comboboxParam1.addItems(items1)
        # Show the previously selected parameter if available
        if previous_param1 in items1:
            index1 = self.comboboxParam1.findText(previous_param1)
            self.comboboxParam1.setCurrentIndex(index1)

        # Store previously select parameter
        previous_param2 = self.comboboxParam2.currentText()
        self.comboboxParam2.clear()
        tab_index2 = self.comboboxModel2.currentIndex()
        items2 = [param for param in self.params[tab_index2]]
        # The following can be used if it is judged preferable that constrained
        # parameters are not used in the definition of a new constraint
        #items2 = [param for param in self.params[tab_index2] if not self.tabs[tab_index2].paramHasConstraint(param)]

        self.comboboxParam2.addItems(items2)
        # Show the previously selected parameter if available
        if previous_param2 in items2:
            index2 = self.comboboxParam2.findText(previous_param2)
            self.comboboxParam2.setCurrentIndex(index2)

        self.textParamComplexConstraint.setText(self.comboboxModel1.currentText() + ":"
                              + self.comboboxParam1.currentText())

        self.comboboxOperator.clear()
        self.comboboxOperator.addItems(ALLOWED_OPERATORS)
        self.labelOperatorComplexConstraint.setText(self.comboboxOperator.currentText())

        self.textComplexConstraint.setText(self.tab_names[tab_index2]+"."+self.comboboxParam2.currentText())

        # disable Apply if no parameters available
        if len(items1)==0:
            self.buttonOK.setEnabled(False)
            self.buttonAddAll.setEnabled(False)
            txt = "No parameters in model "+self.tab_names[0] +\
                " are available for constraining.\n"+\
                "Please select at least one parameter for fitting when adding a constraint."
        else:
            txt = self.redefining_warning
            self.buttonOK.setEnabled(True)
            self.buttonAddAll.setEnabled(True)
        self.labelWarning.setText(txt)

        # disable Aplly all if `All` option on lhs has been selected
        if self.comboboxModel1.currentText() == "All":
            self.buttonAddAll.setEnabled(False)
        else:
            self.buttonAddAll.setEnabled(True)

    def setupTooltip(self):
        """
        Tooltip for textComplexConstraint
        """
        tooltip = "E.g. M1:scale = 2.0 * M2.scale\n"
        tooltip += "M1:scale = sqrt(M2.scale) + 5"
        self.textComplexConstraint.setToolTip(tooltip)

    def onParamIndexChange(self, index):
        """
        Respond to parameter combo box changes
        """
        # Find out the signal source
        source = self.sender().objectName()
        param1 = self.comboboxParam1.currentText()
        param2 = self.comboboxParam2.currentText()
        if source == "comboboxParam1":
            self.textParamComplexConstraint.setText(self.comboboxModel1.currentText() + ":" + param1)
        else:
            self.textComplexConstraint.setText(self.comboboxModel2.currentText() + "." + param2)
        # Check if any of the parameters are polydisperse
        params_list = [param1, param2]
        all_pars = [tab.model_parameters for tab in self.tabs]
        is2Ds = [tab.is2D for tab in self.tabs]
        txt = self.redefining_warning
        for pars, is2D in zip(all_pars, is2Ds):
            if any([FittingUtilities.isParamPolydisperse(p, pars, is2D) for p in params_list]):
                # no parameters are pd - reset the text to not show the warning
                txt = self.warning
        self.labelWarning.setText(txt)

    def onModelIndexChange(self, index):
        """
        Respond to mode combo box changes
        """
        # disable/enable Add All
        self.setupMenu()
        # Reload parameters
        self.setupParamWidgets()

    def onOperatorChange(self, index):
        """
        Respond to operator combo box changes
        """
        self.labelOperatorComplexConstraint.setText(self.comboboxOperator.currentText())

    def validateFormula(self):
        """
        Add visual cues when formula is incorrect
        """
        # temporarily disable validation, as not yet fully operational
        return

        formula_is_valid = self.validateConstraint(self.textComplexConstraint.text())
        if not formula_is_valid:
            self.buttonOK.setEnabled(False)
            self.buttonAddAll.setEnabled(False)
            self.textComplexConstraint.setStyleSheet("QLineEdit {background-color: red;}")
        else:
            self.buttonOK.setEnabled(True)
            self.buttonAddAll.setEnabled(True)
            self.textComplexConstraint.setStyleSheet("QLineEdit {background-color: white;}")

    def validateConstraint(self, constraint_text):
        """
        Ensure the constraint has proper form
        """
        # 0. none or empty
        if not constraint_text or not isinstance(constraint_text, str):
            return False

        # M1.scale --> model_str='M1', constraint_text='scale'
        param_str = self.comboboxParam2.currentText()
        constraint_text = constraint_text.strip()
        model_str = self.comboboxModel2.currentText()

        # 0. Has to contain the model name
        if model_str != model_str:
            return False

        # Remove model name from constraint
        constraint_text = constraint_text.replace(model_str+".",'')

        # 1. just the parameter
        if param_str == constraint_text:
            return True

        # 2. ensure the text contains parameter name
        parameter_string_start = constraint_text.find(param_str)
        if parameter_string_start < 0:
            return False

        # 3. replace parameter name with "1" and try to evaluate the expression
        try:
            expression_to_evaluate = constraint_text.replace(param_str, "1.0")
            eval(expression_to_evaluate)
        except Exception:
            # Too many cases to cover individually, just a blanket
            # Exception should be sufficient
            # Note that in current numpy things like sqrt(-1) don't
            # raise but just return warnings
            return False

        return True

    def constraint(self):
        """
        Return the generated constraint
        """
        param = self.comboboxParam1.currentText()
        value = self.comboboxParam2.currentText()
        func = self.textComplexConstraint.text()
        value_ex = (self.comboboxModel1.currentText() + "."
                    + self.comboboxParam1.currentText())
        model1 = self.comboboxModel1.currentText()
        operator = self.comboboxOperator.currentText()

        con = Constraint(self,
                         param=param,
                         value=value,
                         func=func,
                         value_ex=value_ex,
                         operator=operator)

        return (model1, con)

    def constraintIsRedefined(self, cons_tuple):
        """
        Warn the user when a constraint is being redefined
        """
        # get the the parameter that is being redefined
        param = cons_tuple[1].param
        # get a list of all constrained parameters
        tab_index1 = self.comboboxModel1.currentIndex()
        items = [param for param in self.params[tab_index1] if self.tabs[tab_index1].paramHasConstraint(param)]
        # loop over the list of constrained parameters to check for redefinition
        for item in items:
            if item == param:
                return True
        return False

    def onApply(self):
        """
        Respond to Add constraint action.
        Send a signal that the constraint is ready to be applied
        """
        # if the combobox is set to `All` just call `applyAcrossTabs` and
        # return
        if self.comboboxModel1.currentText() == "All":
            # exclude the tab on the lhs
            tabs = [tab for tab in self.tabs if
                    tab.kernel_module.name != self.comboboxModel2.currentText()]
            self.applyAcrossTabs(tabs, self.comboboxParam1.currentText(),
                                 self.textComplexConstraint.text())
            self.setupParamWidgets()
            return

        cons_tuple = self.constraint()
        #check if constraint has been redefined
        if self.constraintIsRedefined(cons_tuple):
            txt = "Warning: parameter " + \
                  cons_tuple[0] + "." + cons_tuple[1].param +\
                  " has been redefined."
            self.redefining_warning = txt
        else:
            self.redefining_warning = ""
        self.constraintReadySignal.emit(cons_tuple)
        # reload the comboboxes
        if self.parent.constraint_accepted:
            self.setupParamWidgets()

    def applyAcrossTabs(self, tabs, param, expr):
        """
        Apply constraints across tabs, e.g. all `scale` parameters
        constrained to an expression. *tabs* is a list of active fit tabs
        for which the parameter string *param* will be constrained to the
        *expr* string.
        """
        for tab in tabs:
            if hasattr(tab, "kernel_module"):
                if (param in tab.kernel_module.params or
                    param in tab.poly_params or
                    param in tab.magnet_params):
                    value_ex = tab.kernel_module.name + "." +param
                    constraint = Constraint(param=param,
                                            value=param,
                                            func=expr,
                                            value_ex=value_ex,
                                            operator="=")
                    self.constraintReadySignal.emit((tab.kernel_module.name,
                                                     constraint))

    def onSetAll(self):
        """
        Set constraints on all identically named parameters between two fitpages
        """
        # loop over parameters in constrained model
        index1 = self.comboboxModel1.currentIndex()
        index2 = self.comboboxModel2.currentIndex()
        items1 = self.tabs[index1].main_params_to_fit + self.tabs[index1].poly_params_to_fit
        items2 = self.tabs[index2].main_params_to_fit + self.tabs[index2].poly_params_to_fit
        # create an empty list to store redefined constraints
        redefined_constraints = []
        for item in items1:
            if item not in items2: continue
            param = item
            value = item
            func = self.comboboxModel2.currentText() + "." + param
            value_ex = self.comboboxModel1.currentText() + "." + param
            model1 = self.comboboxModel1.currentText()
            operator = self.comboboxOperator.currentText()

            con = Constraint(self,
                             param=param,
                             value=value,
                             func=func,
                             value_ex=value_ex,
                             operator=operator)

            # check for redefined constraints and add them to the list
            if self.constraintIsRedefined((model1, con)):
                redefined_constraints.append(model1 + "." + param)
            # warn the user if constraints have been redefined
            if redefined_constraints:
                constraint_txt = ""
                for redefined_constraint in redefined_constraints:
                    constraint_txt += redefined_constraint + ", "
                txt = "Warning: parameters " +\
                    constraint_txt[:-2] +\
                    " have been redefined."
                if len(redefined_constraints) == 1:
                    txt = txt.replace("parameters", "parameter")
                    txt = txt.replace("has", "been")
                self.redefining_warning = txt
            else:
                self.redefining_warning = ""
            self.constraintReadySignal.emit((model1, con))

        # reload the comboboxes
        self.setupParamWidgets()

    def onHelp(self):
        """
        Display related help section
        """
        tree_location = "/user/qtgui/Perspectives/Fitting/"
        helpfile = "fitting_help.html#simultaneous-fits-with-constraints"
        help_location = tree_location + helpfile
        self.parent.parent.parent.showHelp(help_location)
