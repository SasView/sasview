import sys
import unittest
import numpy as np
import webbrowser

from unittest.mock import MagicMock, patch

from PyQt5 import QtGui, QtWidgets, QtCore, QtTest

from sas.qtgui.Perspectives.Fitting import FittingUtilities
from sas.qtgui.Perspectives.Fitting.Constraint import Constraint
from sas.qtgui.Perspectives.Fitting.ConstraintWidget import ConstraintWidget
from sas.qtgui.UnitTesting.TestUtils import QtSignalSpy
from sas.qtgui.Utilities.GuiUtils import Communicate

# Local
from sas.qtgui.Perspectives.Fitting.FittingWidget import FittingWidget
from sas.qtgui.Perspectives.Fitting.ComplexConstraint import ComplexConstraint

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)

class dummy_manager(object):
    HELP_DIRECTORY_LOCATION = "html"
    communicate = Communicate()

class ComplexConstraintTest(unittest.TestCase):
    '''Test the ComplexConstraint dialog'''
    def setUp(self):
        '''Create ComplexConstraint dialog'''
        # mockup tabs
        self.tab1 = FittingWidget(dummy_manager())
        self.tab2 = FittingWidget(dummy_manager())
        self.tab3 = FittingWidget(dummy_manager())
        # mock the constraint error mechanism
        FittingUtilities.checkConstraints = MagicMock(return_value=None)
        self.tab1.parent.perspective = MagicMock()
        self.tab2.parent.perspective = MagicMock()
        self.tab3.parent.perspective = MagicMock()

        # set some models on tabs
        category_index = self.tab1.cbCategory.findText("Shape Independent")
        self.tab1.cbCategory.setCurrentIndex(category_index)
        model_index = self.tab1.cbModel.findText("be_polyelectrolyte")
        self.tab1.cbModel.setCurrentIndex(model_index)
        # select some parameters so we can populate the combo box
        for i in range(5):
            self.tab1._model_model.item(i, 0).setCheckState(2)

        category_index = self.tab2.cbCategory.findText("Cylinder")
        self.tab2.cbCategory.setCurrentIndex(category_index)
        model_index = self.tab2.cbModel.findText("barbell")
        self.tab2.cbModel.setCurrentIndex(model_index)
        # set tab2 model name to M2
        self.tab2.kernel_module.name = "M2"

        category_index = self.tab3.cbCategory.findText("Cylinder")
        self.tab3.cbCategory.setCurrentIndex(category_index)
        model_index = self.tab3.cbModel.findText("barbell")
        self.tab3.cbModel.setCurrentIndex(model_index)
        # set tab2 model name to M2
        self.tab3.kernel_module.name = "M3"

        tabs = [self.tab1, self.tab2, self.tab3]
        self.widget = ComplexConstraint(parent=None, tabs=tabs)

    def tearDown(self):
        '''Destroy the GUI'''
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        '''Test the GUI in its default state'''
        assert isinstance(self.widget, QtWidgets.QDialog)
        # Default title
        assert self.widget.windowTitle() == "Complex Constraint"

        # Modal window
        assert self.widget.isModal()

        # initial tab names
        assert self.widget.tab_names == ['M1', 'M2', 'M3']
        assert 'scale' in self.widget.params[0]
        assert 'background' in self.widget.params[1]

    def testLabels(self):
        ''' various labels on the widget '''
        # params related setup
        assert self.widget.txtConstraint.text() == 'M1.scale'
        assert self.widget.txtOperator.text() == '='
        assert self.widget.cbModel1.currentText() == 'M1'
        assert self.widget.cbModel2.currentText() == 'M1'
        # no parameter has been selected for fitting, so left combobox should contain empty text
        assert self.widget.cbParam1.currentText() == 'scale'
        assert self.widget.cbParam2.currentText() == 'scale'
        # now select a parameter for fitting (M1.scale)
        self.tab1._model_model.item(0, 0).setCheckState(QtCore.Qt.Checked)
        # reload widget comboboxes
        self.widget.setupParamWidgets()
        # M1.scale has been selected for fit, should now appear in left combobox
        assert self.widget.cbParam1.currentText() == 'scale'
        # change model in right combobox
        index = self.widget.cbModel2.findText('M2')
        self.widget.cbModel2.setCurrentIndex(index)
        assert self.widget.cbModel2.currentText() == 'M2'
        # add a constraint (M1:scale = M2.scale)
        model, constraint = self.widget.constraint()
        self.tab1.addConstraintToRow(constraint, 0)
        # scale should not appear in right combobox, should now be background
        index = self.widget.cbModel2.findText('M1')
        self.widget.cbModel2.setCurrentIndex(index)
        self.widget.setupParamWidgets()
        assert self.widget.cbParam2.currentText() == 'background'

    def testTooltip(self):
        ''' test the tooltip'''
        tooltip = "E.g. M1:scale = 2.0 * M2.scale\n"
        tooltip += "M1:scale = sqrt(M2.scale) + 5"
        assert self.widget.txtConstraint.toolTip() == tooltip

    def notestValidateFormula(self):
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
        assert not self.widget.validateConstraint("M2.scale_")
        # p1
        assert not self.widget.validateConstraint("M2.scale")

        ### GOOD
        # p2
        assert self.widget.validateConstraint("scale")
        # " p2    "
        assert self.widget.validateConstraint(" scale    ")
        # sqrt(p2)
        assert self.widget.validateConstraint("sqrt(scale)")
        # -p2
        assert self.widget.validateConstraint("-scale")
        # log10(p2) - sqrt(p2) + p2
        assert self.widget.validateConstraint("log10(scale) - sqrt(scale) + scale")
        # log10(    p2    ) +  p2
        assert self.widget.validateConstraint("log10(    scale    ) +  scale  ")

    def testConstraint(self):
        """
        Test the return of specified constraint
        """
        # default data
        c = self.widget.constraint()
        assert c[0] == 'M1'
        assert c[1].func == 'M1.scale'

        # Change parameter and operand
        #self.widget.cbOperator.setCurrentIndex(3)
        self.widget.cbParam2.setCurrentIndex(3)
        c = self.widget.constraint()
        assert c[0] == 'M1'
        assert c[1].func == 'M1.bjerrum_length'
        #self.assertEqual(c[1].operator, '>=')

    def notestOnHelp(self):
        """
        Test the default help renderer
        """
        webbrowser.open = MagicMock()

        # invoke the tested method
        self.widget.onHelp()

        # see that webbrowser open was attempted
        webbrowser.open.assert_called_once()

    def testOnSetAll(self):
        """
        Test the `Add all` option for the constraints
        """
        index = self.widget.cbModel2.findText("M2")
        self.widget.cbModel2.setCurrentIndex(index)
        spy = QtSignalSpy(self.widget,
                          self.widget.constraintReadySignal)
        QtTest.QTest.mouseClick(self.widget.cmdAddAll, QtCore.Qt.LeftButton)
        # Only two constraints should've been added: scale and background
        assert spy.count() == 2


    def testOnApply(self):
        """
        Test the application of constraints
        """
        index = self.widget.cbModel2.findText("M2")
        self.widget.cbModel2.setCurrentIndex(index)
        cstab = MagicMock(spec=ConstraintWidget, constraint_accepted=True)
        self.widget.parent = cstab
        spy = QtSignalSpy(self.widget,
                          self.widget.constraintReadySignal)
        QtTest.QTest.mouseClick(self.widget.cmdOK, QtCore.Qt.LeftButton)
        assert spy.count() == 1
        assert spy.signal(0)[0][0] == "M1"
        assert isinstance(spy.signal(0)[0][1], Constraint)

        # Test the `All` option in the combobox
        self.widget.applyAcrossTabs = MagicMock()
        index = self.widget.cbModel1.findText("All")
        self.widget.cbModel1.setCurrentIndex(index)
        self.widget.onApply()
        self.widget.applyAcrossTabs.assert_called_once_with(
            [self.tab1, self.tab3],
            self.widget.cbParam1.currentText(),
            self.widget.txtConstraint.text(),
        )

    def testApplyAcrossTabs(self):
        """
        Test the application of constraints across tabs
        """
        spy = QtSignalSpy(self.widget,
                          self.widget.constraintReadySignal)
        tabs = [self.tab1, self.tab2]
        param = "scale"
        expr = "M3.scale"
        self.widget.applyAcrossTabs(tabs, param, expr)
        # We should have two calls
        assert spy.count() == 2
