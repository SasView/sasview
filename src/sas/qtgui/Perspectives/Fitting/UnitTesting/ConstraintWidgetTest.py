import sys
import unittest
import numpy as np

from unittest.mock import MagicMock

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtTest import QTest, QSignalSpy

# set up import paths
import path_prepare

import sas.qtgui.Utilities.ObjectLibrary as ObjectLibrary
import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Perspectives.Fitting import FittingUtilities
from sas.qtgui.Plotting.PlotterData import Data1D

# Local
from sas.qtgui.Perspectives.Fitting.ConstraintWidget import ConstraintWidget
from sas.qtgui.Perspectives.Fitting.Constraint import Constraint
from sas.qtgui.Perspectives.Fitting.FittingPerspective import FittingWindow
from sas.qtgui.Perspectives.Fitting.FittingWidget import FittingWidget

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

            def __init__(self):
                self._perspective = dummy_perspective()

            def perspective(self):
                return self._perspective

        class dummy_perspective(object):

            def __init__(self):
                self.symbol_dict = {}
                self.constraint_list = []
                self.constraint_tab = None

            def getActiveConstraintList(self):
                return self.constraint_list

            def getSymbolDictForConstraints(self):
                return self.symbol_dict

            def getConstraintTab(self):
                return self.constraint_tab

        '''Create the perspective'''
        self.perspective = FittingWindow(dummy_manager())
        ConstraintWidget.updateSignalsFromTab = MagicMock()

        self.widget = ConstraintWidget(parent=self.perspective)

        # Example constraint object
        self.constraint1 = Constraint(parent=None, param="scale", value="7.0",
                                      min="0.0", max="inf", func="M1.sld",
                                      value_ex="M1.scale")
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
        self.assertEqual(self.widget.getTabsForFit(), [])
        # add one tab
        self.widget.tabs_for_fitting = {"foo": True}
        self.assertEqual(self.widget.getTabsForFit(), ['foo'])
        # add two tabs
        self.widget.tabs_for_fitting = {"foo": True, "bar": True}
        self.assertEqual(self.widget.getTabsForFit(), ['foo', 'bar'])
        # disable one tab
        self.widget.tabs_for_fitting = {"foo": False, "bar": True}
        self.assertEqual(self.widget.getTabsForFit(), ['bar'])

    def testIsTabImportable(self):
        ''' tab checks for consistency '''
        test_tab = MagicMock(spec=FittingWidget)
        test_tab.data_is_loaded = False
        test_tab.kernel_module = None
        ObjectLibrary.getObject = MagicMock(return_value=test_tab)

        self.assertFalse(self.widget.isTabImportable(None))
        self.assertFalse(self.widget.isTabImportable("BatchTab1"))
        self.widget.currentType = "Batch"
        self.assertFalse(self.widget.isTabImportable("BatchTab"))
        self.widget.currentType = "test"
        self.assertFalse(self.widget.isTabImportable("test_tab"))
        test_tab.data_is_loaded = True
        self.assertTrue(self.widget.isTabImportable("test_tab"))

    def testOnTabCellEdit(self):
        ''' test what happens on monicker edit '''
        # Mock a tab
        test_tab = MagicMock(spec=FittingWidget)
        test_tab.data_is_loaded = False
        test_tab.kernel_module = MagicMock()
        ObjectLibrary.getObject = MagicMock(return_value=test_tab)
        self.widget.updateFitLine("test_tab")

        # disable the tab
        self.widget.tblTabList.item(0, 0).setCheckState(0)
        self.assertEqual(self.widget.tabs_for_fitting["test_tab"], False)
        self.assertFalse(self.widget.cmdFit.isEnabled())
        # enable the tab
        self.widget.tblTabList.item(0, 0).setCheckState(2)
        self.assertEqual(self.widget.tabs_for_fitting["test_tab"], True)
        self.assertTrue(self.widget.cmdFit.isEnabled())

    def testUpdateFitLine(self):
        ''' See if the fit table row can be updated '''
        # mock a tab
        test_tab = MagicMock(spec=FittingWidget)
        test_tab.data_is_loaded = False
        test_tab.kernel_module = MagicMock()
        test_tab.kernel_module.name = "M1"
        ObjectLibrary.getObject = MagicMock(return_value=test_tab)

        # Add a tab without an constraint
        self.widget.updateFitLine("test_tab")
        self.assertEqual(self.widget.tblTabList.rowCount(), 1)
        # Constraint tab should be empty
        self.assertEqual(self.widget.tblConstraints.rowCount(), 0)

        # Add a second tab with an active constraint
        test_tab.getComplexConstraintsForModel = MagicMock(
            return_value=[('scale', self.constraint1.func)])
        test_tab.getFullConstraintNameListForModel = MagicMock(
            return_value=[('scale', self.constraint1.func)])
        test_tab.getConstraintObjectsForModel = MagicMock(
            return_value=[self.constraint1])
        self.widget.updateFitLine("test_tab")
        # We should have 2 tabs in the model tab
        self.assertEqual(self.widget.tblTabList.rowCount(), 2)
        # One constraint in the constraint tab
        self.assertEqual(self.widget.tblConstraints.rowCount(), 1)
        # Constraint should be active
        self.assertEqual(self.widget.tblConstraints.item(0, 0).checkState(), 2)
        # Check the text
        self.assertEqual(self.widget.tblConstraints.item(0, 0).text(),
                         test_tab.kernel_module.name +
                         ":scale = " +
                         self.constraint1.func)
        # Add a tab with a non active constraint
        test_tab.getComplexConstraintsForModel = MagicMock(return_value=[])
        self.widget.updateFitLine("test_tab")
        # There should be two constraints now
        self.assertEqual(self.widget.tblConstraints.rowCount(), 2)
        # Added constraint should not be checked since it isn't active
        self.assertEqual(self.widget.tblConstraints.item(1, 0).checkState(), 0)

    def testUpdateFitList(self):
        ''' see if the fit table can be updated '''
        # mock a tab
        test_tab = MagicMock(spec=FittingWidget)
        test_tab.data_is_loaded = False
        test_tab.kernel_module = MagicMock()
        ObjectLibrary.getObject = MagicMock(return_value=test_tab)

        # Fit button should be disabled if no tabs are present
        ObjectLibrary.listObjects =MagicMock(return_value=False)
        self.widget.initializeFitList()
        self.assertEqual(self.widget.available_tabs, {})
        self.assertEqual(self.widget.available_constraints, {})
        self.assertEqual(self.widget.tblConstraints.rowCount(), 0)
        self.assertEqual(self.widget.tblTabList.rowCount(), 0)
        self.assertFalse(self.widget.cmdFit.isEnabled())

        # Add a tab
        self.widget.isTabImportable = MagicMock(return_value=True)
        ObjectLibrary.listObjects = MagicMock(return_value=[test_tab])
        self.widget.updateFitLine = MagicMock()
        self.widget.updateSignalsFromTab = MagicMock()
        self.widget.initializeFitList()
        self.widget.updateFitLine.assert_called_once()
        self.widget.updateSignalsFromTab.assert_called_once()
        self.assertTrue(self.widget.cmdFit.isEnabled())

        # Check if the tab list gets ordered
        self.widget.isTabImportable = MagicMock(return_value=True)
        ObjectLibrary.listObjects = MagicMock(return_value=[test_tab])
        self.widget.updateFitLine = MagicMock()
        self.widget.updateSignalsFromTab = MagicMock()
        self.widget._row_order = [test_tab]
        self.widget.orderedSublist = MagicMock()
        self.widget.initializeFitList()
        self.widget.orderedSublist.assert_called_with([test_tab], [test_tab])


    def testOnAcceptConstraint(self):
        ''' test if a constraint can be added '''
        # mock a tab
        test_tab = MagicMock(spec=FittingWidget)
        test_tab.addConstraintToRow = MagicMock()
        test_tab.getRowFromName = MagicMock(return_value=1)
        test_tab.changeCheckboxStatus = MagicMock()

        # mock the getObjectByName method
        self.widget.getObjectByName = MagicMock(return_value=test_tab)

        # add a constraint
        constraint_tuple = ('M1', self.constraint1)
        self.widget.onAcceptConstraint(constraint_tuple)

        # check the getObjectByName call
        self.widget.getObjectByName.assert_called_with('M1')

        # check the tab method calls
        test_tab.getRowFromName.assert_called_with(self.constraint1.param)
        test_tab.addConstraintToRow.assert_called_with(self.constraint1, 1)
        test_tab.changeCheckboxStatus.assert_called_with(1, True)

    def testFitComplete(self):
        ''' test the handling of fit results'''
        self.widget.getTabsForFit = MagicMock(return_value=[[None], [None]])
        spy = QSignalSpy(self.widget.parent.communicate.statusBarUpdateSignal)
        # test handling of fit error
        # result is None
        result = None
        self.widget.fitComplete(result)
        self.assertEqual(spy[0][0], 'Fitting failed.')
        # Result has failed
        result = MagicMock(return_value= "foo")
        results = [[[result]], 1.5]
        result.success = False
        result.mesg = ["foo", None]
        self.widget.fitComplete(results)
        self.assertEqual(spy[1][0], 'Fitting failed with the following '
                                    'message: foo')

        # test a successful fit
        result.success = True
        test_tab = MagicMock()
        test_tab.kernel_module.name = 'M1'
        test_tab.fitComplete = MagicMock()
        result.model.name = 'M1'
        self.widget.tabs_for_fitting = {"test_tab": test_tab}
        ObjectLibrary.getObject = MagicMock(return_value=test_tab)
        self.widget.fitComplete(results)
        self.assertEqual(test_tab.fitComplete.call_args[0][0][1], 1.5)
        self.assertEqual(test_tab.fitComplete.call_args[0][0][0],
                         [[result]])
        self.assertEqual(spy[2][0], 'Fitting completed successfully in: 1.5 '
                                    's.\n')

    def testBatchFitComplete(self):
        ''' test the handling of batch fit results'''
        self.widget.getTabsForFit = MagicMock(return_value=[[None], [None]])
        spy = QSignalSpy(self.widget.parent.communicate.statusBarUpdateSignal)
        spy_data = QSignalSpy(
            self.widget.parent.communicate.sendDataToGridSignal)
        # test handling of fit error
        # result is None
        result = None
        self.widget.batchComplete(result)
        self.assertEqual(spy[0][0], 'Fitting failed.')
        # Result has failed
        result = MagicMock(return_value= "foo")
        results = [[[result]], 1.5]
        result.success = False
        result.mesg = ["foo", None]
        self.widget.batchComplete(results)
        self.assertEqual(spy[1][0], 'Fitting failed with the following '
                                    'message: foo')

        # test a successful fit
        result.success = True
        self.widget.batchComplete(results)
        self.assertEqual(spy[2][0], 'Fitting completed successfully in: 1.5 '
                                    's.\n')
        self.assertEqual(spy_data[0][0], [[result], 'ConstSimulPage'])

    def testUncheckConstraints(self):
        '''Tests the unchecking of constraints'''
        # mock a tab
        test_tab = MagicMock(spec=FittingWidget)
        test_tab.data_is_loaded = False
        test_tab.kernel_module = MagicMock()
        test_tab.kernel_module.name = "M1"
        ObjectLibrary.getObject = MagicMock(return_value=test_tab)

        # Add a tab with an active constraint
        test_tab.getComplexConstraintsForModel = MagicMock(
            return_value=[('scale', self.constraint1.func)])
        test_tab.getFullConstraintNameListForModel = MagicMock(
            return_value=[('scale', self.constraint1.func)])
        test_tab.getConstraintObjectsForModel = MagicMock(
            return_value=[self.constraint1])
        test_tab.getConstraintForRow = MagicMock(return_value=self.constraint1)
        self.widget.updateFitLine("test_tab")
        self.widget.parent.getTabByName = MagicMock(return_value=test_tab)
        perspective = self.widget.parent.parent.perspective()
        perspective.symbol_dict = {"M1.scale": 1, "M1.radius": 1}
        self.widget.initializeFitList = MagicMock()

        # Constraint should be checked
        self.assertEqual(self.widget.tblConstraints.item(0, 0).checkState(), 2)

        self.widget.uncheckConstraint('M1:scale')
        # Should be unchecked in tblConstraint
        self.assertEqual(self.widget.tblConstraints.item(0, 0).checkState(), 0)
        # Constraint should be deactivated
        self.assertEqual(self.constraint1.active, False)

    def testOnConstraintChange(self):
        ''' test edition of the constraint list '''
        # mock a tab
        test_tab = MagicMock(spec=FittingWidget)
        test_tab.data_is_loaded = False
        test_tab.kernel_module = MagicMock()
        test_tab.kernel_module.name = "M1"
        test_tab.getRowFromName = MagicMock(return_value=0)
        ObjectLibrary.getObject = MagicMock(return_value=test_tab)

        # Add a constraint to the tab
        test_tab.getComplexConstraintsForModel = MagicMock(
            return_value=[('scale', self.constraint1.func)])
        test_tab.getFullConstraintNameListForModel = MagicMock(
            return_value=[('scale', self.constraint1.func)])
        test_tab.getConstraintObjectsForModel = MagicMock(
            return_value=[self.constraint1])

        self.widget.updateFitLine("test_tab")

        self.widget.initializeFitList = MagicMock()
        QtWidgets.QMessageBox.critical = MagicMock()

        # Change the constraint to one with no equal sign
        self.widget.tblConstraints.item(0, 0).setText("foo")

        msg = ("Incorrect operator in constraint definition. Please use = "
               "sign to define constraints.")
        (QtWidgets.QMessageBox.critical.
         assert_called_with(self.widget, "Inconsistent constraint", msg,
                            QtWidgets.QMessageBox.Ok))
        # Check the reloading of the view
        self.widget.initializeFitList.assert_called_once()

        self.widget.initializeFitList.reset_mock()
        # Change the constraint to one with no colons in constrained parameter
        self.widget.tblConstraints.item(0, 0).setText("foo = bar")
        msg = ("Incorrect constrained parameter definition. Please use colons"
               " to separate model and parameter on the rhs of the definition, "
               "e.g. M1:scale")
        (QtWidgets.QMessageBox.critical.
         assert_called_with(self.widget, "Inconsistent constraint", msg,
                            QtWidgets.QMessageBox.Ok))
        # Check the reloading of the view
        self.widget.initializeFitList.assert_called_once()

        self.widget.initializeFitList.reset_mock()
        perspective = self.widget.parent.parent.perspective()
        # Change the constraint to one with an unknown symbol or with several
        # parameters on the rhs of the constraint definition
        self.widget.tblConstraints.item(0, 0).setText("M1:foo = bar")
        msg = ("Unknown parameter M1.foo used in constraint. Please use "
               "a single known parameter in the rhs of the constraint "
               "definition, e.g. M1:scale = M1.radius + 2")
        (QtWidgets.QMessageBox.critical.
         assert_called_with(self.widget, "Inconsistent constraint", msg,
                            QtWidgets.QMessageBox.Ok))
        # Check the reloading of the view
        self.widget.initializeFitList.assert_called_once()

        self.widget.initializeFitList.reset_mock()
        # Check replacement of a constraint
        perspective.symbol_dict = {"M1.scale": 1, "M1.radius": 1}

        self.widget.tblConstraints.item(0, 0).setText("M1:radius = bar")
        constraint = Constraint(param="radius", func="bar",
                                value_ex="M1.radius")
        target = test_tab.addConstraintToRow.call_args[1]
        self.assertEqual(target["constraint"].value_ex, constraint.value_ex)
        self.assertEqual(target["constraint"].func, constraint.func)
        self.assertEqual(target["constraint"].param, constraint.param)
        self.assertEqual(target["row"], 0)
        target = test_tab.deleteConstraintOnParameter.call_args[0]
        self.assertEqual(target[0], "scale")
        # Check the reloading of the view
        self.widget.initializeFitList.assert_called_once()

        self.widget.initializeFitList.reset_mock()
        # Check the checkbox
        self.widget.tblConstraints.item(0, 0).setText("M1:scale = M1.sld")
        self.assertEqual(test_tab.modifyViewOnRow.call_args[0][0], 0)
        font = QtGui.QFont()
        font.setItalic(True)
        self.assertEqual(test_tab.modifyViewOnRow.call_args[1]["font"],
                         font)
        brush = QtGui.QBrush(QtGui.QColor('blue'))
        self.assertEqual(test_tab.modifyViewOnRow.call_args[1]["brush"],
                         brush)
        # Check the reloading of the view
        self.widget.initializeFitList.assert_called_once()

        self.widget.initializeFitList.reset_mock()
        # Uncheck the checkbox
        self.widget.tblConstraints.item(0, 0).setCheckState(0)
        self.assertEqual(test_tab.modifyViewOnRow.call_args[0][0], 0)
        self.assertTrue(not test_tab.modifyViewOnRow.call_args[1])
        self.assertEqual(self.constraint1.active, False)
        # Check the reloading of the view
        self.widget.initializeFitList.assert_called_once()
