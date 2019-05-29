import sys
import unittest
import numpy as np

from unittest.mock import MagicMock

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtTest import QTest

# set up import paths
import path_prepare

import sas.qtgui.Utilities.ObjectLibrary as ObjectLibrary
import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Plotting.PlotterData import Data1D

# Local
from sas.qtgui.Perspectives.Fitting.ConstraintWidget import ConstraintWidget
from sas.qtgui.Perspectives.Fitting.Constraint import Constraint
from sas.qtgui.Perspectives.Fitting.FittingPerspective import FittingWindow

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)

class ConstraintWidgetTest(unittest.TestCase):
    '''Test the ConstraintWidget dialog'''
    def setUp(self):
        '''Create ConstraintWidget dialog'''
        class dummy_manager(object):
            def communicator(self):
                return GuiUtils.Communicate()
            communicate = GuiUtils.Communicate()

        '''Create the perspective'''
        self.perspective = FittingWindow(dummy_manager())
        ConstraintWidget.updateSignalsFromTab = MagicMock()

        self.widget = ConstraintWidget(parent=self.perspective)

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
        # Data accept 
        self.assertFalse(self.widget.acceptsData())
        # By default, the constraint table is disabled
        self.assertFalse(self.widget.tblConstraints.isEnabled())

    def testOnFitTypeChange(self):
        ''' test the single/batch fit switch '''
        self.widget.initializeFitList = MagicMock()
        # Assure current type is Single
        self.assertEqual(self.widget.currentType, "FitPage")
        # click on "batch"
        QTest.mouseClick(self.widget.btnBatch, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        # See what the current type is now
        self.assertEqual(self.widget.currentType, "BatchPage")
        # See if the list is getting initialized
        self.assertTrue(self.widget.initializeFitList.called)
        # Go back to single fit
        QTest.mouseClick(self.widget.btnSingle, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        # See what the current type is now
        self.assertEqual(self.widget.currentType, "FitPage")

    def testGetTabsForFit(self):
        ''' Test the fitting tab list '''
        self.assertEqual(self.widget.getTabsForFit(),[])
        # Add some tabs
        pass

    def testIsTabImportable(self):
        ''' tab checks for consistency '''
        test_tab = QtCore.QObject()
        test_tab.data = self.constraint1
        ObjectLibrary.getObject = MagicMock(return_value=test_tab)

        self.assertFalse(self.widget.isTabImportable(None))
        self.assertFalse(self.widget.isTabImportable("BatchTab1"))
        self.assertFalse(self.widget.isTabImportable("BatchTab"))

    def testOnTabCellEdit(self):
        ''' test what happens on monicker edit '''
        # Mock the datafromitem() call from FittingWidget
        data = Data1D(x=[1,2], y=[1,2])
        GuiUtils.dataFromItem = MagicMock(return_value=data)
        item = QtGui.QStandardItem("test")
        self.perspective.addFit([item])

    def testUpdateFitLine(self):
        ''' See if the fit table row can be updated '''
        pass

    def testUpdateFitList(self):
        ''' see if the fit table can be updated '''
        pass

    def testUpdateConstraintList(self):
        ''' see if the constraint table can be updated '''
        pass


