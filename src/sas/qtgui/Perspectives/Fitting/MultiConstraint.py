"""
Widget for parameter constraints.
"""
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

        self.cmdOK.clicked.connect(self.accept)
        self.cmdRevert.clicked.connect(self.revert)

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

        pass

