import sys
import webbrowser

import numpy as np
import pytest
from PySide6 import QtWidgets

# Local
from sas.qtgui.Perspectives.Fitting.MultiConstraint import MultiConstraint

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)

class MultiConstraintTest:
    '''Test the MultiConstraint dialog'''

    @pytest.fixture(autouse=True)
    def widget(self, qapp):
        '''Create/Destroy the MultiConstraint'''
        params = ['p1', 'p2']
        self.p1 = params[0]
        self.p2 = params[1]
        w = MultiConstraint(parent=None, params=params)
        yield w
        w.close()

    def testDefaults(self, widget):
        '''Test the GUI in its default state'''
        assert isinstance(widget, QtWidgets.QDialog)
        # Default title
        assert widget.windowTitle() == "2 parameter constraint"

        # modal window
        assert widget.isModal()

    def testLabels(self, widget):
        ''' various labels on the widget '''
        # params related setup
        assert widget.txtParam1.text() == self.p1
        assert widget.txtParam1_2.text() == self.p1
        assert widget.txtParam2.text() == self.p2

    def testTooltip(self, widget):
        ''' test the tooltip'''
        tooltip = "E.g.\n%s = 2.0 * (%s)\n" %(self.p1, self.p2)
        tooltip += "%s = sqrt(%s) + 5"%(self.p1, self.p2)
        assert widget.txtConstraint.toolTip() == tooltip

    def testValidateFormula(self, widget, mocker):
        ''' assure enablement and color for valid formula '''
        # Invalid string
        mocker.patch.object(widget, 'validateConstraint', return_value=False)
        widget.validateFormula()
        style_sheet = "QLineEdit {background-color: red;}"
        assert not widget.cmdOK.isEnabled()
        assert widget.txtConstraint.styleSheet() == style_sheet

        # Valid string
        mocker.patch.object(widget, 'validateConstraint', return_value=True)
        widget.validateFormula()
        style_sheet = "QLineEdit {background-color: white;}"
        assert widget.cmdOK.isEnabled()
        assert widget.txtConstraint.styleSheet() == style_sheet

    def testValidateConstraint(self, widget):
        ''' constraint validator test'''
        #### BAD
        # none
        assert not widget.validateConstraint(None)
        # inf
        assert not widget.validateConstraint(np.inf)
        # 0
        assert not widget.validateConstraint(0)
        # ""
        assert not widget.validateConstraint("")
        # p2_
        assert not widget.validateConstraint("p2_")
        # p1
        assert not widget.validateConstraint("p1")

        ### GOOD
        # p2
        assert widget.validateConstraint("p2")
        # " p2    "
        assert widget.validateConstraint(" p2    ")
        # sqrt(p2)
        assert widget.validateConstraint("sqrt(p2)")
        # -p2
        assert widget.validateConstraint("-p2")
        # log10(p2) - sqrt(p2) + p2
        assert widget.validateConstraint("log10(p2) - sqrt(p2) + p2")
        # log10(    p2    ) +  p2
        assert widget.validateConstraint("log10(    p2    ) +  p2  ")

    def testOnHelp(self, widget, mocker):
        """
        Test the default help renderer
        """
        mocker.patch.object(webbrowser, 'open')

        # invoke the tested method
        widget.onHelp()

        # see that webbrowser open was attempted
        webbrowser.open.assert_called_once()
