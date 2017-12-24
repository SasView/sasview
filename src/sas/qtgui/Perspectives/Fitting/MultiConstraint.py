"""
Widget for parameter constraints.
"""
from numpy import *

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

import sas.qtgui.Utilities.GuiUtils as GuiUtils

# Local UI
from sas.qtgui.Perspectives.Fitting.UI.MultiConstraintUI import Ui_MultiConstraintUI

class MultiConstraint(QtWidgets.QDialog, Ui_MultiConstraintUI):
    def __init__(self, parent=None, params=None):
        super(MultiConstraint, self).__init__()

        self.setupUi(self)
        self.setFixedSize(self.minimumSizeHint())
        self.setModal(True)
        self.params = params

        self.setupLabels()
        self.setupTooltip()

        # Set param text control to the second parameter passed
        self.txtConstraint.setText(self.params[1])

        self.cmdOK.clicked.connect(self.accept)
        self.cmdRevert.clicked.connect(self.revert)
        self.txtConstraint.editingFinished.connect(self.validateFormula)

    def revert(self):
        """
        switch M1 <-> M2
        """
        self.params[1], self.params[0] = self.params[0], self.params[1]
        self.setupLabels()
        self.setupTooltip()

    def setupLabels(self):
        """
        Setup labels based on current parameters
        """
        l1 = self.params[0]
        l2 = self.params[1]
        self.txtParam1.setText(l1)
        self.txtParam1_2.setText(l1)
        self.txtParam2.setText(l2)

    def setupTooltip(self):
        """
        Tooltip for txtConstraint
        """
        tooltip = "E.g.\n%s = 2.0 * (%s)\n" %(self.params[0], self.params[1])
        tooltip += "%s = sqrt(%s) + 5"%(self.params[0], self.params[1])
        self.txtConstraint.setToolTip(tooltip)

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
        has_parameter_name = (parameter_string_start > -1)
        if not has_parameter_name:
            return False
        parameter_string_end = parameter_string_start + len(param_str)

        # 3. parameter name should be a separate word, but can have "()[]*+-/" around
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



