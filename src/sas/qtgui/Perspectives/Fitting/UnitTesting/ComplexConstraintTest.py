import webbrowser

import numpy as np
import pytest
from PySide6 import QtCore, QtTest, QtWidgets

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.MainWindow.GuiManager import GuiManager
from sas.qtgui.Perspectives.Fitting import FittingUtilities
from sas.qtgui.Perspectives.Fitting.ComplexConstraint import ComplexConstraint
from sas.qtgui.Perspectives.Fitting.Constraint import Constraint
from sas.qtgui.Perspectives.Fitting.ConstraintWidget import ConstraintWidget

# Local
from sas.qtgui.Perspectives.Fitting.FittingWidget import FittingWidget
from sas.qtgui.UnitTesting.TestUtils import QtSignalSpy


class ComplexConstraintTest:
    @pytest.fixture(autouse=True)
    def widget(self, qapp, mocker):
        '''Create/Destroy the ComplexConstraint'''
        class dummy_manager:
            HELP_DIRECTORY_LOCATION = "html"
            communicate = GuiUtils.Communicate()

        '''Create ComplexConstraint dialog'''
        # need to ensure that categories exist first
        GuiManager.addCategories()

        # mockup tabs
        tab1 = FittingWidget(dummy_manager())
        tab2 = FittingWidget(dummy_manager())
        tab3 = FittingWidget(dummy_manager())
        # mock the constraint error mechanism
        mocker.patch.object(FittingUtilities, 'checkConstraints', return_value=None)
        mocker.patch.object(tab1.parent, 'perspective', create=True)
        mocker.patch.object(tab2.parent, 'perspective', create=True)
        mocker.patch.object(tab3.parent, 'perspective', create=True)

        # set some models on tabs
        category_index = tab1.cbCategory.findText("Shape Independent")
        tab1.cbCategory.setCurrentIndex(category_index)
        model_index = tab1.cbModel.findText("be_polyelectrolyte")
        tab1.cbModel.setCurrentIndex(model_index)
        # select some parameters so we can populate the combo box
        for i in range(5):
            tab1._model_model.item(i, 0).setCheckState(2)

        category_index = tab2.cbCategory.findText("Cylinder")
        tab2.cbCategory.setCurrentIndex(category_index)
        model_index = tab2.cbModel.findText("barbell")
        tab2.cbModel.setCurrentIndex(model_index)
        # set tab2 model name to M2
        tab2.logic.kernel_module.name = "M2"

        category_index = tab3.cbCategory.findText("Cylinder")
        tab3.cbCategory.setCurrentIndex(category_index)
        model_index = tab3.cbModel.findText("barbell")
        tab3.cbModel.setCurrentIndex(model_index)
        # set tab2 model name to M2
        tab3.logic.kernel_module.name = "M3"

        tabs = [tab1, tab2, tab3]
        w = ComplexConstraint(parent=None, tabs=tabs)

        yield w

        w.close()


    '''Test the ComplexConstraint dialog'''
    def testDefaults(self, widget):
        '''Test the GUI in its default state'''
        assert isinstance(widget, QtWidgets.QDialog)
        # Default title
        assert widget.windowTitle() == "Complex Constraint"

        # Modal window
        assert widget.isModal()

        # initial tab names
        assert widget.tab_names == ['M1', 'M2', 'M3']
        assert 'scale' in widget.params[0]
        assert 'background' in widget.params[1]

    def testLabels(self, widget):
        ''' various labels on the widget '''
        # params related setup
        assert widget.txtConstraint.text() == 'M1.scale'
        assert widget.txtOperator.text() == '='
        assert widget.cbModel1.currentText() == 'M1'
        assert widget.cbModel2.currentText() == 'M1'
        # no parameter has been selected for fitting, so left combobox should contain empty text
        assert widget.cbParam1.currentText() == 'scale'
        assert widget.cbParam2.currentText() == 'scale'
        # now select a parameter for fitting (M1.scale)
        widget.tabs[0]._model_model.item(0, 0).setCheckState(QtCore.Qt.Checked)
        # reload widget comboboxes
        widget.setupParamWidgets()
        # M1.scale has been selected for fit, should now appear in left combobox
        assert widget.cbParam1.currentText() == 'scale'
        # change model in right combobox
        index = widget.cbModel2.findText('M2')
        widget.cbModel2.setCurrentIndex(index)
        assert widget.cbModel2.currentText() == 'M2'
        # add a constraint (M1:scale = M2.scale)
        model, constraint = widget.constraint()
        widget.tabs[0].addConstraintToRow(constraint, 0)
        # scale should not appear in right combobox, should now be background
        index = widget.cbModel2.findText('M1')
        widget.cbModel2.setCurrentIndex(index)
        widget.setupParamWidgets()
        assert widget.cbParam2.currentText() == 'background'

    def testTooltip(self, widget):
        ''' test the tooltip'''
        tooltip = "E.g. M1:scale = 2.0 * M2.scale\n"
        tooltip += "M1:scale = sqrt(M2.scale) + 5"
        assert widget.txtConstraint.toolTip() == tooltip

    def notestValidateFormula(self, widget, mocker):
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
        assert not widget.validateConstraint("M2.scale_")
        # p1
        assert not widget.validateConstraint("M2.scale")

        ### GOOD
        # p2
        assert widget.validateConstraint("scale")
        # " p2    "
        assert widget.validateConstraint(" scale    ")
        # sqrt(p2)
        assert widget.validateConstraint("sqrt(scale)")
        # -p2
        assert widget.validateConstraint("-scale")
        # log10(p2) - sqrt(p2) + p2
        assert widget.validateConstraint("log10(scale) - sqrt(scale) + scale")
        # log10(    p2    ) +  p2
        assert widget.validateConstraint("log10(    scale    ) +  scale  ")

    def testConstraint(self, widget):
        """
        Test the return of specified constraint
        """
        # default data
        c = widget.constraint()
        assert c[0] == 'M1'
        assert c[1].func == 'M1.scale'

        # Change parameter and operand
        #widget.cbOperator.setCurrentIndex(3)
        widget.cbParam2.setCurrentIndex(3)
        c = widget.constraint()
        assert c[0] == 'M1'
        assert c[1].func == 'M1.bjerrum_length'
        #assert c[1].operator == '>='

    def notestOnHelp(self, widget, mocker):
        """
        Test the default help renderer
        """
        mocker.patch.object(webbrowser, 'open')

        # invoke the tested method
        widget.onHelp()

        # see that webbrowser open was attempted
        webbrowser.open.assert_called_once()

    def testOnSetAll(self, widget):
        """
        Test the `Add all` option for the constraints
        """
        index = widget.cbModel2.findText("M2")
        widget.cbModel2.setCurrentIndex(index)
        spy = QtSignalSpy(widget,
                            widget.constraintReadySignal)
        QtTest.QTest.mouseClick(widget.cmdAddAll, QtCore.Qt.LeftButton)
        # Only two constraints should've been added: scale and background
        assert spy.count() == 2


    def testOnApply(self, widget, mocker):
        """
        Test the application of constraints
        """
        index = widget.cbModel2.findText("M2")
        widget.cbModel2.setCurrentIndex(index)
        mocker.patch.object(widget, 'parent', spec=ConstraintWidget, constraint_accepted=True)
        spy = QtSignalSpy(widget,
                            widget.constraintReadySignal)
        QtTest.QTest.mouseClick(widget.cmdOK, QtCore.Qt.LeftButton)
        assert spy.count() == 1
        assert spy.signal(0)[0][0] == "M1"
        assert isinstance(spy.signal(0)[0][1], Constraint)

        # Test the `All` option in the combobox
        mocker.patch.object(widget, 'applyAcrossTabs')
        index = widget.cbModel1.findText("All")
        widget.cbModel1.setCurrentIndex(index)
        widget.onApply()
        widget.applyAcrossTabs.assert_called_once_with(
            [widget.tabs[0], widget.tabs[2]],
            widget.cbParam1.currentText(),
            widget.txtConstraint.text(),
        )

    def testApplyAcrossTabs(self, widget):
        """
        Test the application of constraints across tabs
        """
        spy = QtSignalSpy(widget,
                            widget.constraintReadySignal)
        tabs = [widget.tabs[0], widget.tabs[1]]
        param = "scale"
        expr = "M3.scale"
        widget.applyAcrossTabs(tabs, param, expr)
        # We should have two calls
        assert spy.count() == 2
