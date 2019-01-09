"""
Widget for multi-model constraints.
"""
import os

# numpy methods required for the validator! Don't remove.
# pylint: disable=unused-import,unused-wildcard-import,redefined-builtin
from numpy import *

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
import webbrowser

from sas.qtgui.Perspectives.Fitting import FittingUtilities
import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Perspectives.Fitting.Constraint import Constraint

#ALLOWED_OPERATORS = ['=','<','>','>=','<=']
ALLOWED_OPERATORS = ['=']

# Local UI
from sas.qtgui.Perspectives.Fitting.UI.ComplexConstraintUI import Ui_ComplexConstraintUI

class ComplexConstraint(QtWidgets.QDialog, Ui_ComplexConstraintUI):
    constraintReadySignal = QtCore.pyqtSignal(tuple)
    def __init__(self, parent=None, tabs=None):
        super(ComplexConstraint, self).__init__(parent)

        self.setupUi(self)
        self.setModal(True)

        # disable the context help icon
        windowFlags = self.windowFlags()
        self.setWindowFlags(windowFlags & ~QtCore.Qt.WindowContextHelpButtonHint)

        # Useful globals
        self.tabs = tabs
        self.params = None
        self.tab_names = None
        self.operator = '='
        self._constraint = Constraint()
        self.all_menu   = None

        self.warning = self.lblWarning.text()
        self.setupData()
        self.setupSignals()
        self.setupWidgets()
        self.setupTooltip()

        # Default focus is on OK
        self.cmdOK.setFocus()

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
        self.cmdOK.clicked.connect(self.onApply)
        self.cmdHelp.clicked.connect(self.onHelp)
        self.cmdAddAll.clicked.connect(self.onSetAll)

        self.txtConstraint.editingFinished.connect(self.validateFormula)
        self.cbModel1.currentIndexChanged.connect(self.onModelIndexChange)
        self.cbModel2.currentIndexChanged.connect(self.onModelIndexChange)

        self.cbParam1.currentIndexChanged.connect(self.onParamIndexChange)
        self.cbParam2.currentIndexChanged.connect(self.onParamIndexChange)
        self.cbOperator.currentIndexChanged.connect(self.onOperatorChange)

    def setupWidgets(self):
        """
        Setup widgets based on current parameters
        """
        self.cbModel1.insertItems(0, self.tab_names)
        self.cbModel2.insertItems(0, self.tab_names)

        self.setupParamWidgets()


        self.setupMenu()

    def setupMenu(self):
        # Show Add All button, if necessary
        if self.cbModel1.currentText() ==self.cbModel2.currentText():
            self.cmdAddAll.setVisible(False)
        else:
            self.cmdAddAll.setVisible(True)
        return

    def setupParamWidgets(self):
        """
        Fill out comboboxes and set labels with non-constrained parameters
        """
        self.cbParam1.clear()
        tab_index1 = self.cbModel1.currentIndex()
        items1 = [param for param in self.params[tab_index1] if not self.tabs[tab_index1].paramHasConstraint(param)]
        self.cbParam1.addItems(items1)

        # M2 doesn't have to be non-constrained
        self.cbParam2.clear()
        tab_index2 = self.cbModel2.currentIndex()
        items2 = [param for param in self.params[tab_index2]]
        self.cbParam2.addItems(items2)

        self.txtParam.setText(self.tab_names[tab_index1] + ":" + self.cbParam1.currentText())

        self.cbOperator.clear()
        self.cbOperator.addItems(ALLOWED_OPERATORS)
        self.txtOperator.setText(self.cbOperator.currentText())

        self.txtConstraint.setText(self.tab_names[tab_index2]+"."+self.cbParam2.currentText())

        # disable Apply if no parameters available
        if len(items1)==0:
            self.cmdOK.setEnabled(False)
            self.cmdAddAll.setEnabled(False)
            txt = "No parameters in model "+self.tab_names[0] +\
                " are available for constraining."
            self.lblWarning.setText(txt)
        else:
            self.cmdOK.setEnabled(True)
            self.cmdAddAll.setEnabled(True)
            txt = ""
            self.lblWarning.setText(txt)

    def setupTooltip(self):
        """
        Tooltip for txtConstraint
        """
        p1 = self.tab_names[0] + ":" + self.cbParam1.currentText()
        p2 = self.tab_names[1]+"."+self.cbParam2.currentText()
        tooltip = "E.g.\n%s = 2.0 * (%s)\n" %(p1, p2)
        tooltip += "%s = sqrt(%s) + 5"%(p1, p2)
        self.txtConstraint.setToolTip(tooltip)

    def onParamIndexChange(self, index):
        """
        Respond to parameter combo box changes
        """
        # Find out the signal source
        source = self.sender().objectName()
        param1 = self.cbParam1.currentText()
        param2 = self.cbParam2.currentText()
        if source == "cbParam1":
            self.txtParam.setText(self.tab_names[0] + ":" + param1)
        else:
            self.txtConstraint.setText(self.tab_names[1] + "." + param2)
        # Check if any of the parameters are polydisperse
        params_list = [param1, param2]
        all_pars = [tab.model_parameters for tab in self.tabs]
        is2Ds = [tab.is2D for tab in self.tabs]
        txt = ""
        for pars, is2D in zip(all_pars, is2Ds):
            if any([FittingUtilities.isParamPolydisperse(p, pars, is2D) for p in params_list]):
                # no parameters are pd - reset the text to not show the warning
                txt = self.warning
        self.lblWarning.setText(txt)

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
        self.txtOperator.setText(self.cbOperator.currentText())

    def validateFormula(self):
        """
        Add visual cues when formula is incorrect
        """
        # temporarily disable validation
        return
        #
        formula_is_valid = self.validateConstraint(self.txtConstraint.text())
        if not formula_is_valid:
            self.cmdOK.setEnabled(False)
            self.cmdAddAll.setEnabled(False)
            self.txtConstraint.setStyleSheet("QLineEdit {background-color: red;}")
        else:
            self.cmdOK.setEnabled(True)
            self.cmdAddAll.setEnabled(True)
            self.txtConstraint.setStyleSheet("QLineEdit {background-color: white;}")

    def validateConstraint(self, constraint_text):
        """
        Ensure the constraint has proper form
        """
        # 0. none or empty
        if not constraint_text or not isinstance(constraint_text, str):
            return False

        # M1.scale --> model_str='M1', constraint_text='scale'
        param_str = self.cbParam2.currentText()
        constraint_text = constraint_text.strip()
        model_str = self.cbModel2.currentText()

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
        param = self.cbParam1.currentText()
        value = self.cbParam2.currentText()
        func = self.txtConstraint.text()
        value_ex = self.cbModel2.currentText() + "." + self.cbParam2.currentText()
        model1 = self.cbModel1.currentText()
        operator = self.cbOperator.currentText()

        con = Constraint(self,
                         param=param,
                         value=value,
                         func=func,
                         value_ex=value_ex,
                         operator=operator)

        return (model1, con)

    def onApply(self):
        """
        Respond to Add constraint action.
        Send a signal that the constraint is ready to be applied
        """
        cons_tuple = self.constraint()
        self.constraintReadySignal.emit(cons_tuple)
        # reload the comboboxes
        self.setupParamWidgets()

    def onSetAll(self):
        """
        Set constraints on all identically named parameters between two fitpages
        """
        # loop over parameters in constrained model
        index1 = self.cbModel1.currentIndex()
        index2 = self.cbModel2.currentIndex()
        items1 = [param for param in self.params[index1] if not self.tabs[index1].paramHasConstraint(param)]
        items2 = self.params[index2]
        for item in items1:
            if item not in items2: continue
            param = item
            value = item
            func = self.cbModel2.currentText() + "." + param
            value_ex = self.cbModel1.currentText() + "." + param
            model1 = self.cbModel1.currentText()
            operator = self.cbOperator.currentText()

            con = Constraint(self,
                             param=param,
                             value=value,
                             func=func,
                             value_ex=value_ex,
                             operator=operator)

            self.constraintReadySignal.emit((model1, con))

        # reload the comboboxes
        self.setupParamWidgets()

    def onHelp(self):
        """
        Display related help section
        """
        try:
            help_location = GuiUtils.HELP_DIRECTORY_LOCATION + \
            "/user/qtgui/Perspectives/Fitting/fitting_help.html#simultaneous-fits-with-constraints"
            webbrowser.open('file://' + os.path.realpath(help_location))
        except AttributeError:
            # No manager defined - testing and standalone runs
            pass



