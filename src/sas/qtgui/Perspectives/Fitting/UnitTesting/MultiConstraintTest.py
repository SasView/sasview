import sys
import unittest
import numpy as np
import webbrowser

from unittest.mock import MagicMock

from PyQt5 import QtGui, QtWidgets

# set up import paths
import sas.qtgui.path_prepare

# Local
from sas.qtgui.Perspectives.Fitting.MultiConstraint import MultiConstraint

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)

class MultiConstraintTest(unittest.TestCase):
    '''Test the MultiConstraint dialog'''
    def setUp(self):
        '''Create MultiConstraint dialog'''
        params = ['p1', 'p2']
        self.p1 = params[0]
        self.p2 = params[1]
        self.widget = MultiConstraint(parent=None, params=params)

    def tearDown(self):
        '''Destroy the GUI'''
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        '''Test the GUI in its default state'''
        assert isinstance(self.widget, QtWidgets.QDialog)
        # Default title
        assert self.widget.windowTitle() == "2 parameter constraint"

        # modal window
        assert self.widget.isModal()

    def testLabels(self):
        ''' various labels on the widget '''
        # params related setup
        assert self.widget.txtParam1.text() == self.p1
        assert self.widget.txtParam1_2.text() == self.p1
        assert self.widget.txtParam2.text() == self.p2

    def testTooltip(self):
        ''' test the tooltip'''
        tooltip = "E.g.\n%s = 2.0 * (%s)\n" %(self.p1, self.p2)
        tooltip += "%s = sqrt(%s) + 5"%(self.p1, self.p2)
        assert self.widget.txtConstraint.toolTip() == tooltip

    def testValidateFormula(self):
        ''' assure enablement and color for valid formula '''
        # Invalid string
        self.widget.validateConstraint = MagicMock(return_value=False)
        self.widget.validateFormula()
        style_sheet = "QLineEdit {background-color: red;}"
        assert not self.widget.cmdOK.isEnabled()
        assert self.widget.txtConstraint.styleSheet() == style_sheet

        # Valid string
        self.widget.validateConstraint = MagicMock(return_value=True)
        self.widget.validateFormula()
        style_sheet = "QLineEdit {background-color: white;}"
        assert self.widget.cmdOK.isEnabled()
        assert self.widget.txtConstraint.styleSheet() == style_sheet

    def testValidateConstraint(self):
        ''' constraint validator test'''
        #### BAD
        # none
        assert not self.widget.validateConstraint(None)
        # inf
        assert not self.widget.validateConstraint(np.inf)
        # 0
        assert not self.widget.validateConstraint(0)
        # ""
        assert not self.widget.validateConstraint("")
        # p2_
        assert not self.widget.validateConstraint("p2_")
        # p1
        assert not self.widget.validateConstraint("p1")

        ### GOOD
        # p2
        assert self.widget.validateConstraint("p2")
        # " p2    "
        assert self.widget.validateConstraint(" p2    ")
        # sqrt(p2)
        assert self.widget.validateConstraint("sqrt(p2)")
        # -p2
        assert self.widget.validateConstraint("-p2")
        # log10(p2) - sqrt(p2) + p2
        assert self.widget.validateConstraint("log10(p2) - sqrt(p2) + p2")
        # log10(    p2    ) +  p2
        assert self.widget.validateConstraint("log10(    p2    ) +  p2  ")

    def testOnHelp(self):
        """
        Test the default help renderer
        """
        webbrowser.open = MagicMock()

        # invoke the tested method
        self.widget.onHelp()

        # see that webbrowser open was attempted
        webbrowser.open.assert_called_once()
