import sys
import unittest
import numpy as np
import webbrowser

from unittest.mock import MagicMock

from PyQt5 import QtGui, QtWidgets

# set up import paths
import path_prepare

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
        # set some models on tabs
        category_index = self.tab1.cbCategory.findText("Shape Independent")
        self.tab1.cbCategory.setCurrentIndex(category_index)
        category_index = self.tab2.cbCategory.findText("Cylinder")
        self.tab2.cbCategory.setCurrentIndex(category_index)

        tabs = [self.tab1, self.tab2]
        self.widget = ComplexConstraint(parent=None, tabs=tabs)

    def tearDown(self):
        '''Destroy the GUI'''
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        '''Test the GUI in its default state'''
        self.assertIsInstance(self.widget, QtWidgets.QDialog)
        # Default title
        self.assertEqual(self.widget.windowTitle(), "Complex Constraint")

        # Modal window
        self.assertTrue(self.widget.isModal())

        # initial tab names
        self.assertEqual(self.widget.tab_names, ['M1','M1'])
        self.assertIn('scale', self.widget.params[0])
        self.assertIn('background', self.widget.params[1])

    def testLabels(self):
        ''' various labels on the widget '''
        # params related setup
        self.assertEqual(self.widget.txtConstraint.text(), 'M1.scale')
        self.assertEqual(self.widget.txtOperator.text(), '=')
        self.assertEqual(self.widget.txtName1.text(), 'M1')
        self.assertEqual(self.widget.txtName2.text(), 'M1')

    def testTooltip(self):
        ''' test the tooltip'''
        p1 = self.widget.tab_names[0] + ":" + self.widget.cbParam1.currentText()
        p2 = self.widget.tab_names[1]+"."+self.widget.cbParam2.currentText()

        tooltip = "E.g.\n%s = 2.0 * (%s)\n" %(p1, p2)
        tooltip += "%s = sqrt(%s) + 5"%(p1, p2)
        self.assertEqual(self.widget.txtConstraint.toolTip(), tooltip)

    def testValidateFormula(self):
        ''' assure enablement and color for valid formula '''
        # Invalid string
        self.widget.validateConstraint = MagicMock(return_value=False)
        self.widget.validateFormula()
        style_sheet = "QLineEdit {background-color: red;}"
        self.assertFalse(self.widget.cmdOK.isEnabled())
        self.assertEqual(self.widget.txtConstraint.styleSheet(),style_sheet)

        # Valid string
        self.widget.validateConstraint = MagicMock(return_value=True)
        self.widget.validateFormula()
        style_sheet = "QLineEdit {background-color: white;}"
        self.assertTrue(self.widget.cmdOK.isEnabled())
        self.assertEqual(self.widget.txtConstraint.styleSheet(),style_sheet)

    def testValidateConstraint(self):
        ''' constraint validator test'''
        #### BAD
        # none
        self.assertFalse(self.widget.validateConstraint(None))
        # inf
        self.assertFalse(self.widget.validateConstraint(np.inf))
        # 0
        self.assertFalse(self.widget.validateConstraint(0))
        # ""
        self.assertFalse(self.widget.validateConstraint(""))
        # p2_
        self.assertFalse(self.widget.validateConstraint("M2.scale_"))
        # p1
        self.assertFalse(self.widget.validateConstraint("M2.scale"))

        ### GOOD
        # p2
        self.assertTrue(self.widget.validateConstraint("scale"))
        # " p2    "
        self.assertTrue(self.widget.validateConstraint(" scale    "))
        # sqrt(p2)
        self.assertTrue(self.widget.validateConstraint("sqrt(scale)"))
        # -p2
        self.assertTrue(self.widget.validateConstraint("-scale"))
        # log10(p2) - sqrt(p2) + p2
        self.assertTrue(self.widget.validateConstraint("log10(scale) - sqrt(scale) + scale"))
        # log10(    p2    ) +  p2
        self.assertTrue(self.widget.validateConstraint("log10(    scale    ) +  scale  "))

    def testConstraint(self):
        """
        Test the return of specified constraint
        """
        # default data
        self.assertEqual(self.widget.constraint(), ('M1', 'scale', '=', 'M1.scale'))

        # Change parameter and operand
        self.widget.cbOperator.setCurrentIndex(3)
        self.widget.cbParam1.setCurrentIndex(3)
        self.assertEqual(self.widget.constraint(), ('M1', 'bjerrum_length', '>=', 'M1.scale'))

    def testOnHelp(self):
        """
        Test the default help renderer
        """
        webbrowser.open = MagicMock()

        # invoke the tested method
        self.widget.onHelp()

        # see that webbrowser open was attempted
        webbrowser.open.assert_called_once()
