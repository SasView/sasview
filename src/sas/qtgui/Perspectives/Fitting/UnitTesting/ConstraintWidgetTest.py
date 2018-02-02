import sys
import unittest
import numpy as np

from unittest.mock import MagicMock

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5 import QtWebKit

# set up import paths
import path_prepare

import sas.qtgui.Utilities.ObjectLibrary as ObjectLibrary

# Local
from sas.qtgui.Perspectives.Fitting.ConstraintWidget import ConstraintWidget
from sas.qtgui.Perspectives.Fitting.Constraint import Constraint

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)

class ConstraintWidgetTest(unittest.TestCase):
    '''Test the ConstraintWidget dialog'''
    def setUp(self):
        '''Create ConstraintWidget dialog'''
        class dummy_perspective(QtWidgets.QTabWidget):
            tabsModifiedSignal = QtCore.pyqtSignal()
            def __init__(self):
                super(dummy_perspective, self).__init__()
                pass

        self.widget = ConstraintWidget(parent=dummy_perspective())

        # Example constraint object
        self.constraint1 = Constraint(parent=None, param="test", value="7.0", min="0.0", max="inf", func="M1:sld")
        self.constraint2 = Constraint(parent=None, param="poop", value="7.0", min="0.0", max="inf", func="7.0")

    def tearDown(self):
        '''Destroy the GUI'''
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        '''Test the GUI in its default state'''
        self.assertIsInstance(self.widget, QtWidgets.QWidget)
        # Default title
        self.assertEqual(self.widget.windowTitle(), "Constrained and Simultaneous Fit")
        # Dicts
        self.assertIsInstance(self.widget.available_constraints, dict)
        self.assertIsInstance(self.widget.available_tabs, dict)
        # TableWidgets
        self.assertEqual(self.widget.tblTabList.columnCount(), 4)
        self.assertEqual(self.widget.tblConstraints.columnCount(), 1)

    def testLabels(self):
        ''' various labels on the widget '''
        # params related setup
        pass

    def testTooltip(self):
        ''' test the tooltip'''
        pass

    def testIsTabImportable(self):
        ''' tab checks for consistency '''
        test_tab = QtCore.QObject()
        test_tab.data = self.constraint1
        ObjectLibrary.getObject = MagicMock(return_value=test_tab)

        self.assertFalse(self.widget.isTabImportable(None))
        self.assertTrue(self.widget.isTabImportable("FitTab333333"))
        self.assertFalse(self.widget.isTabImportable("BatchTab"))
        self.assertFalse(self.widget.isTabImportable("BatchTab"))

        pass

    def testUpdateFitLine(self):
        ''' See if the fit table row can be updated '''
        pass

    def testUpdateFitList(self):
        ''' see if the fit table can be updated '''
        pass

    def testUpdateConstraintList(self):
        ''' see if the constraint table can be updated '''
        pass


