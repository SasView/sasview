"""
Widget for multi-model constraints.
"""
import os
from numpy import *

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
import webbrowser

import sas.qtgui.Utilities.GuiUtils as GuiUtils
ALLOWED_OPERATORS = ['=','<','>','>=','<=']

# Local UI
from sas.qtgui.Perspectives.Fitting.UI.ComplexConstraintUI import Ui_ComplexConstraintUI

class ComplexConstraint(QtWidgets.QDialog, Ui_ComplexConstraintUI):
    def __init__(self, parent=None, tabs=None):
        super(ComplexConstraint, self).__init__()

        self.setupUi(self)
        #self.setFixedSize(self.minimumSizeHint())
        self.setModal(True)

        # Useful globals
        self.tabs = tabs
        self.params = None
        self.tab_names = None
        self.operator = '='

        self.setupData()
        self.setupWidgets()
        self.setupSignals()
        #self.setupTooltip()

        self.setFixedSize(self.minimumSizeHint())

    def setupData(self):
        """
        Digs into self.tabs and pulls out relevant info
        """
        self.tab_names = [tab.kernel_module.name for tab in self.tabs]
        self.params = [tab.getParamNames() for tab in self.tabs]
        pass

    def setupSignals(self):
        """
        Signals from various elements
        """
        self.cmdOK.clicked.connect(self.accept)
        self.cmdHelp.clicked.connect(self.onHelp)
        self.cmdRevert.clicked.connect(self.onRevert)
        #self.txtConstraint.editingFinished.connect(self.validateFormula)

        self.cbParam1.currentIndexChanged.connect(self.onParamIndexChange)
        self.cbParam2.currentIndexChanged.connect(self.onParamIndexChange)
        self.cbOperator.currentIndexChanged.connect(self.onOperatorChange)

    def setupWidgets(self):
        """
        Setup widgets based on current parameters
        """
        self.txtName1.setText(self.tab_names[0])
        self.txtName2.setText(self.tab_names[1])

        self.cbParam1.clear()
        self.cbParam1.addItems(self.params[0])
        self.cbParam2.clear()
        self.cbParam2.addItems(self.params[1])

        self.txtParam.setText(self.tab_names[0] + ":" + self.cbParam1.currentText())

        self.cbOperator.clear()
        self.cbOperator.addItems(ALLOWED_OPERATORS)
        self.txtOperator.setText(self.cbOperator.currentText())

        self.txtConstraint.setText(self.tab_names[1]+"."+self.cbParam2.currentText())

    def setupTooltip(self):
        """
        Tooltip for txtConstraint
        """
        tooltip = "E.g.\n%s = 2.0 * (%s)\n" %(self.params[0], self.params[1])
        tooltip += "%s = sqrt(%s) + 5"%(self.params[0], self.params[1])
        self.txtConstraint.setToolTip(tooltip)

    def onParamIndexChange(self, index):
        """
        Respond to parameter combo box changes
        """
        # Find out the signal source
        source = self.sender().objectName()
        if source == "cbParam1":
            self.txtParam.setText(self.tab_names[0] + ":" + self.cbParam1.currentText())
        else:
            self.txtConstraint.setText(self.cbParam2.currentText())
        pass

    def onOperatorChange(self, index):
        """
        Respond to operator combo box changes
        """
        self.txtOperator.setText(self.cbOperator.currentText())

    def onRevert(self):
        """
        switch M1 <-> M2
        """
        # Switch parameters
        self.params[1], self.params[0] = self.params[0], self.params[1]
        self.tab_names[1], self.tab_names[0] = self.tab_names[0], self.tab_names[1]
        # Try to swap parameter names in the line edit
        current_text = self.txtConstraint.text()
        new_text = current_text.replace(self.cbParam1.currentText(), self.cbParam2.currentText())
        self.txtConstraint.setText(new_text)
        # Update labels and tooltips
        index1 = self.cbParam1.currentIndex()
        index2 = self.cbParam2.currentIndex()
        indexOp = self.cbOperator.currentIndex()
        self.setupWidgets()

        # Original indices
        self.cbParam1.setCurrentIndex(index2)
        self.cbParam2.setCurrentIndex(index1)
        self.cbOperator.setCurrentIndex(indexOp)
        #self.setupTooltip()

    def validateFormula(self):
        """
        Add visual cues when formula is incorrect
        """
        formula_is_valid = False
        formula_is_valid = self.validateConstraint(self.txtConstraint.text())
        if not formula_is_valid:
            self.cmdOK.setEnabled(False)
            self.txtConstraint.setStyleSheet("QLineEdit {background-color: red;}")
        else:
            self.cmdOK.setEnabled(True)
            self.txtConstraint.setStyleSheet("QLineEdit {background-color: white;}")

    def validateConstraint(self, constraint_text):
        """
        Ensure the constraint has proper form
        """
        # 0. none or empty
        if not constraint_text or not isinstance(constraint_text, str):
            return False

        param_str = str(self.params[1])
        constraint_text = constraint_text.strip()

        # 1. just the parameter
        if param_str == constraint_text:
            return True

        # 2. ensure the text contains parameter name
        parameter_string_start = constraint_text.find(param_str)
        if parameter_string_start < 0:
            return False
        parameter_string_end = parameter_string_start + len(param_str)

        # 3. parameter name should be a separate word, but can have "()[]*+-/ " around
        valid_neighbours = "()[]*+-/ "
        has_only_parameter = False
        start_loc = parameter_string_start -1
        end_loc = parameter_string_end
        if not any([constraint_text[start_loc] == char for char in valid_neighbours]):
            return False
        if end_loc < len(constraint_text):
            if not any([constraint_text[end_loc] == char for char in valid_neighbours]):
                return False

        # 4. replace parameter name with "1" and try to evaluate the expression
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

    def onHelp(self):
        """
        Display related help section
        """
        try:
            help_location = GuiUtils.HELP_DIRECTORY_LOCATION + \
            "/user/sasgui/perspectives/fitting/fitting_help.html#simultaneous-fits-with-constraints"
            webbrowser.open('file://' + os.path.realpath(help_location))
        except AttributeError:
            # No manager defined - testing and standalone runs
            pass



