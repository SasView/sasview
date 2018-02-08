"""
Widget for parameter constraints.
"""
import os
import webbrowser

# numpy methods required for the validator! Don't remove.
# pylint: disable=unused-import,unused-wildcard-import,redefined-builtin
from numpy import *

from PyQt5 import QtWidgets

import sas.qtgui.Utilities.GuiUtils as GuiUtils

# Local UI
from sas.qtgui.Perspectives.Fitting.UI.MultiConstraintUI import Ui_MultiConstraintUI

class MultiConstraint(QtWidgets.QDialog, Ui_MultiConstraintUI):
    """
    Logic class for interacting with MultiConstrainedUI view
    """
    def __init__(self, parent=None, params=None):
        """
        parent: ConstraintWidget object
        params: tuple of strings describing model parameters
        """
        super(MultiConstraint, self).__init__()

        self.setupUi(self)
        self.setFixedSize(self.minimumSizeHint())
        self.setModal(True)
        self.params = params
        self.parent = parent

        self.setupLabels()
        self.setupTooltip()

        # Set param text control to the second parameter passed
        self.txtConstraint.setText(self.params[1])

        self.cmdOK.clicked.connect(self.accept)
        self.cmdHelp.clicked.connect(self.onHelp)
        self.cmdRevert.clicked.connect(self.revert)
        self.txtConstraint.editingFinished.connect(self.validateFormula)

        # Default focus is on OK
        self.cmdOK.setFocus()

    def revert(self):
        """
        Swap parameters in the view
        """
        # Switch parameters
        self.params[1], self.params[0] = self.params[0], self.params[1]
        # Try to swap parameter names in the line edit
        current_text = self.txtConstraint.text()
        new_text = current_text.replace(self.params[0], self.params[1])
        self.txtConstraint.setText(new_text)
        # Update labels and tooltips
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
        if parameter_string_start < 0:
            return False
        parameter_string_end = parameter_string_start + len(param_str)

        # 3. parameter name should be a separate word, but can have "()[]*+-/ " around
        #valid_neighbours = "()[]*+-/ "
        #start_loc = parameter_string_start -1
        #end_loc = parameter_string_end
        #if not any([constraint_text[start_loc] == ch for ch in valid_neighbours]):
        #    return False
        #if end_loc < len(constraint_text):
        #    if not any([constraint_text[end_loc] == ch for ch in valid_neighbours]):
        #        return False

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


