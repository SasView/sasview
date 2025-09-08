from unittest.mock import MagicMock

import pytest
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtTest import QSignalSpy, QTest

import sas.qtgui.Utilities.GuiUtils as GuiUtils
import sas.qtgui.Utilities.ObjectLibrary as ObjectLibrary
from sas.qtgui.MainWindow.GuiManager import GuiManager
from sas.qtgui.Perspectives.Fitting.Constraint import Constraint

# Local
from sas.qtgui.Perspectives.Fitting.ConstraintWidget import ConstraintWidget
from sas.qtgui.Perspectives.Fitting.FittingPerspective import FittingWindow
from sas.qtgui.Perspectives.Fitting.FittingWidget import FittingWidget


class ConstraintWidgetTest:
    '''Test the ConstraintWidget dialog'''

    @pytest.fixture(autouse=True)
    def widget(self, qapp, mocker):
        '''Create/Destroy the ConstraintWidget'''

        '''Create ConstraintWidget dialog'''
        class dummy_manager:
            def communicator(self):
                return GuiUtils.Communicate()
            communicate = GuiUtils.Communicate()

            def __init__(self):
                self._perspective = dummy_perspective()

            def perspective(self):
                return self._perspective

        class dummy_perspective:

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

        # need to ensure that categories exist first
        GuiManager.addCategories()

        '''Create the perspective'''
        perspective = FittingWindow(dummy_manager())
        mocker.patch.object(ConstraintWidget, 'updateSignalsFromTab')

        w = ConstraintWidget(parent=perspective)

        # Example constraint object
        self.constraint1 = Constraint(parent=None, param="scale", value="7.0",
                                      min="0.0", max="inf", func="M1.sld",
                                      value_ex="M1.scale")
        self.constraint2 = Constraint(parent=None, param="poop", value="7.0", min="0.0", max="inf", func="7.0")

        yield w

        '''Destroy the GUI'''
        self.constraint1 = None
        self.constraint2 = None
        w.close()

    def testDefaults(self, widget, mocker):
        '''Test the GUI in its default state'''
        assert isinstance(widget, QtWidgets.QWidget)
        # Default title
        assert widget.windowTitle() == "Constrained and Simultaneous Fit"
        # Dicts
        assert isinstance(widget.available_constraints, dict)
        assert isinstance(widget.available_tabs, dict)
        # TableWidgets
        assert widget.tblTabList.columnCount() == 4
        assert widget.tblConstraints.columnCount() == 1
        # Data accept
        assert not widget.acceptsData()
        # By default, the constraint table is disabled
        assert not widget.tblConstraints.isEnabled()

    def testOnFitTypeChange(self, widget, mocker):
        ''' test the single/batch fit switch '''
        mocker.patch.object(widget, 'initializeFitList')
        # Assure current type is Single
        assert widget.currentType == "FitPage"
        # click on "batch"
        QTest.mouseClick(widget.btnBatch, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        # See what the current type is now
        assert widget.currentType == "BatchPage"
        # See if the list is getting initialized
        assert widget.initializeFitList.called
        # Go back to single fit
        QTest.mouseClick(widget.btnSingle, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        # See what the current type is now
        assert widget.currentType == "FitPage"

    def testGetTabsForFit(self, widget):
        ''' Test the fitting tab list '''
        assert widget.getTabsForFit() == []
        # add one tab
        widget.tabs_for_fitting = {"foo": True}
        assert widget.getTabsForFit() == ['foo']
        # add two tabs
        widget.tabs_for_fitting = {"foo": True, "bar": True}
        assert widget.getTabsForFit() == ['foo', 'bar']
        # disable one tab
        widget.tabs_for_fitting = {"foo": False, "bar": True}
        assert widget.getTabsForFit() == ['bar']

    def testIsTabImportable(self, widget, mocker):
        ''' tab checks for consistency '''
        test_tab = MagicMock(spec=FittingWidget)
        test_tab.data_is_loaded = False
        test_tab.logic.kernel_module = None
        mocker.patch.object(ObjectLibrary, 'getObject', return_value=test_tab)

        assert not widget.isTabImportable(None)
        assert not widget.isTabImportable("BatchTab1")
        widget.currentType = "Batch"
        assert not widget.isTabImportable("BatchTab")
        widget.currentType = "test"
        assert not widget.isTabImportable("test_tab")
        test_tab.data_is_loaded = True
        assert widget.isTabImportable("test_tab")

    @pytest.mark.xfail(reason="2022-09 already broken")
    def testOnTabCellEdit(self, widget, mocker):
        ''' test what happens on monicker edit '''
        # Mock a tab
        test_tab = MagicMock(spec=FittingWidget)
        test_tab.data_is_loaded = False
        mocker.patch.object(test_tab, 'kernel_module')
        mocker.patch.object(ObjectLibrary, 'getObject', return_value=test_tab)
        widget.updateFitLine("test_tab")

        # disable the tab
        widget.tblTabList.item(0, 0).setCheckState(0)
        assert widget.tabs_for_fitting["test_tab"] is False
        assert not widget.cmdFit.isEnabled()
        # enable the tab
        widget.tblTabList.item(0, 0).setCheckState(2)
        assert widget.tabs_for_fitting["test_tab"] is True
        assert widget.cmdFit.isEnabled()

    def testUpdateFitLine(self, widget, mocker):
        ''' See if the fit table row can be updated '''
        # mock a tab
        test_tab = MagicMock(spec=FittingWidget)
        test_tab.data_is_loaded = False
        mocker.patch.object(test_tab, 'kernel_module', create=True)
        test_tab.logic.kernel_module.name = "M1"
        mocker.patch.object(ObjectLibrary, 'getObject', return_value=test_tab)

        # Add a tab without an constraint
        widget.updateFitLine("test_tab")
        assert widget.tblTabList.rowCount() == 1
        # Constraint tab should be empty
        assert widget.tblConstraints.rowCount() == 0

        # Add a second tab with an active constraint
        test_tab.getComplexConstraintsForModel = MagicMock(
            return_value=[('scale', self.constraint1.func)])
        test_tab.getFullConstraintNameListForModel = MagicMock(
            return_value=[('scale', self.constraint1.func)])
        test_tab.getConstraintObjectsForModel = MagicMock(
            return_value=[self.constraint1])
        widget.updateFitLine("test_tab")
        # We should have 2 tabs in the model tab
        assert widget.tblTabList.rowCount() == 2
        # One constraint in the constraint tab
        assert widget.tblConstraints.rowCount() == 1
        # Constraint should be active
        assert widget.tblConstraints.item(0, 0).checkState() == 2
        # Check the text
        assert widget.tblConstraints.item(0, 0).text() == \
                         test_tab.logic.kernel_module.name + \
                         ":scale = " + \
                         self.constraint1.func
        # Add a tab with a non active constraint
        mocker.patch.object(test_tab, 'getComplexConstraintsForModel', return_value=[])
        widget.updateFitLine("test_tab")
        # There should be two constraints now
        assert widget.tblConstraints.rowCount() == 2
        # Added constraint should not be checked since it isn't active
        assert widget.tblConstraints.item(1, 0).checkState() == 0

    def testUpdateFitList(self, widget, mocker):
        ''' see if the fit table can be updated '''
        # mock a tab
        test_tab = MagicMock(spec=FittingWidget)
        test_tab.data_is_loaded = False
        mocker.patch.object(test_tab, 'kernel_module', create=True)
        mocker.patch.object(ObjectLibrary, 'getObject', return_value=test_tab)

        # Fit button should be disabled if no tabs are present
        ObjectLibrary.listObjects =MagicMock(return_value=False)
        widget.initializeFitList()
        assert widget.available_tabs == {}
        assert widget.available_constraints == {}
        assert widget.tblConstraints.rowCount() == 0
        assert widget.tblTabList.rowCount() == 0
        assert not widget.cmdFit.isEnabled()

        # Add a tab
        mocker.patch.object(widget, 'isTabImportable', return_value=True)
        mocker.patch.object(ObjectLibrary, 'listObjects', return_value=[test_tab])
        mocker.patch.object(widget, 'updateFitLine')
        mocker.patch.object(widget, 'updateSignalsFromTab')
        widget.initializeFitList()
        widget.updateFitLine.assert_called_once()
        widget.updateSignalsFromTab.assert_called_once()
        assert widget.cmdFit.isEnabled()

        # Check if the tab list gets ordered
        mocker.patch.object(widget, 'isTabImportable', return_value=True)
        mocker.patch.object(ObjectLibrary, 'listObjects', return_value=[test_tab])
        mocker.patch.object(widget, 'updateFitLine')
        mocker.patch.object(widget, 'updateSignalsFromTab')
        widget._row_order = [test_tab]
        mocker.patch.object(widget, 'orderedSublist')
        widget.initializeFitList()
        widget.orderedSublist.assert_called_with([test_tab], [test_tab])


    def testOnAcceptConstraint(self, widget, mocker):
        ''' test if a constraint can be added '''
        # mock a tab
        test_tab = MagicMock(spec=FittingWidget)
        mocker.patch.object(test_tab, 'addConstraintToRow')
        mocker.patch.object(test_tab, 'getRowFromName', return_value=1)
        mocker.patch.object(test_tab, 'changeCheckboxStatus')

        # mock the getObjectByName method
        mocker.patch.object(widget, 'getObjectByName', return_value=test_tab)

        # add a constraint
        constraint_tuple = ('M1', self.constraint1)
        widget.onAcceptConstraint(constraint_tuple)

        # check the getObjectByName call
        widget.getObjectByName.assert_called_with('M1')

        # check the tab method calls
        test_tab.getRowFromName.assert_called_with(self.constraint1.param)
        test_tab.addConstraintToRow.assert_called_with(self.constraint1, 1)
        test_tab.changeCheckboxStatus.assert_called_with(1, True)

    def testFitComplete(self, widget, mocker):
        ''' test the handling of fit results'''
        mocker.patch.object(widget, 'getTabsForFit', return_value=[[None], [None]])
        spy = QSignalSpy(widget.parent.communicate.statusBarUpdateSignal)
        # test handling of fit error
        # result is None
        result = None
        widget.fitComplete(result)
        assert spy[0][0] == 'Fitting failed.'
        # Result has failed
        result = MagicMock(return_value= "foo")
        results = [[[result]], 1.5]
        result.success = False
        result.mesg = ["foo", None]
        widget.fitComplete(results)
        assert spy[1][0] == 'Fitting failed with the following ' \
                                    'message: foo'

        # test a successful fit
        result.success = True
        test_tab = MagicMock()
        test_tab.logic.kernel_module.name = 'M1'
        mocker.patch.object(test_tab, 'fitComplete')
        result.model.name = 'M1'
        widget.tabs_for_fitting = {"test_tab": test_tab}
        mocker.patch.object(ObjectLibrary, 'getObject', return_value=test_tab)
        widget.fitComplete(results)
        assert test_tab.fitComplete.call_args[0][0][1] == 1.5
        assert test_tab.fitComplete.call_args[0][0][0] == \
                         [[result]]
        assert spy[2][0] == 'Fitting completed successfully in: 1.5 ' \
                                    's.\n'

    def testBatchFitComplete(self, widget, mocker):
        ''' test the handling of batch fit results'''
        mocker.patch.object(widget, 'getTabsForFit', return_value=[[None], [None]])
        spy = QSignalSpy(widget.parent.communicate.statusBarUpdateSignal)
        spy_data = QSignalSpy(
            widget.parent.communicate.sendDataToGridSignal)
        # test handling of fit error
        # result is None
        result = None
        widget.batchComplete(result)
        assert spy[0][0] == 'Fitting failed.'
        # Result has failed
        result = MagicMock(return_value= "foo")
        results = [[[result]], 1.5]
        result.success = False
        result.mesg = ["foo", None]
        widget.batchComplete(results)
        assert spy[1][0] == 'Fitting failed with the following ' \
                                    'message: foo'

        # test a successful fit
        result.success = True
        widget.batchComplete(results)
        assert spy[2][0] == 'Fitting completed successfully in: 1.5 ' \
                                    's.\n'
        assert spy_data[0][0] == [[result], 'ConstSimulPage']

    def testUncheckConstraints(self, widget, mocker):
        '''Tests the unchecking of constraints'''
        # mock a tab
        test_tab = MagicMock(spec=FittingWidget)
        test_tab.data_is_loaded = False
        mocker.patch.object(test_tab, 'kernel_module', create=True)
        test_tab.logic.kernel_module.name = "M1"
        mocker.patch.object(ObjectLibrary, 'getObject', return_value=test_tab)

        # Add a tab with an active constraint
        test_tab.getComplexConstraintsForModel = MagicMock(
            return_value=[('scale', self.constraint1.func)])
        test_tab.getFullConstraintNameListForModel = MagicMock(
            return_value=[('scale', self.constraint1.func)])
        test_tab.getConstraintObjectsForModel = MagicMock(
            return_value=[self.constraint1])
        mocker.patch.object(test_tab, 'getConstraintForRow', return_value=self.constraint1)
        widget.updateFitLine("test_tab")
        mocker.patch.object(widget.parent, 'getTabByName', return_value=test_tab)
        perspective = widget.parent.parent.perspective()
        perspective.symbol_dict = {"M1.scale": 1, "M1.radius": 1}
        mocker.patch.object(widget, 'initializeFitList')

        # Constraint should be checked
        assert widget.tblConstraints.item(0, 0).checkState() == 2

        widget.uncheckConstraint('M1:scale')
        # Should be unchecked in tblConstraint
        assert widget.tblConstraints.item(0, 0).checkState() == 0
        # Constraint should be deactivated
        assert self.constraint1.active is False

    def testOnConstraintChange(self, widget, mocker):
        ''' test edition of the constraint list '''
        # mock a tab
        test_tab = MagicMock(spec=FittingWidget)
        test_tab.data_is_loaded = False
        mocker.patch.object(test_tab, 'kernel_module', create=True)
        test_tab.logic.kernel_module.name = "M1"
        mocker.patch.object(test_tab, 'getRowFromName', return_value=0)
        mocker.patch.object(ObjectLibrary, 'getObject', return_value=test_tab)

        # Add a constraint to the tab
        test_tab.getComplexConstraintsForModel = MagicMock(
            return_value=[('scale', self.constraint1.func)])
        test_tab.getFullConstraintNameListForModel = MagicMock(
            return_value=[('scale', self.constraint1.func)])
        test_tab.getConstraintObjectsForModel = MagicMock(
            return_value=[self.constraint1])

        widget.updateFitLine("test_tab")

        mocker.patch.object(widget, 'initializeFitList')
        mocker.patch.object(QtWidgets.QMessageBox, 'critical')

        # Change the constraint to one with no equal sign
        widget.tblConstraints.item(0, 0).setText("foo")

        msg = ("Incorrect operator in constraint definition. Please use = "
               "sign to define constraints.")
        (QtWidgets.QMessageBox.critical.
         assert_called_with(widget, "Inconsistent constraint", msg,
                            QtWidgets.QMessageBox.Ok))
        # Check the reloading of the view
        widget.initializeFitList.assert_called_once()

        widget.initializeFitList.reset_mock()
        # Change the constraint to one with no colons in constrained parameter
        widget.tblConstraints.item(0, 0).setText("foo = bar")
        msg = ("Incorrect constrained parameter definition. Please use colons"
               " to separate model and parameter on the rhs of the definition, "
               "e.g. M1:scale")
        (QtWidgets.QMessageBox.critical.
         assert_called_with(widget, "Inconsistent constraint", msg,
                            QtWidgets.QMessageBox.Ok))
        # Check the reloading of the view
        widget.initializeFitList.assert_called_once()

        widget.initializeFitList.reset_mock()
        perspective = widget.parent.parent.perspective()
        # Change the constraint to one with an unknown symbol or with several
        # parameters on the rhs of the constraint definition
        widget.tblConstraints.item(0, 0).setText("M1:foo = bar")
        msg = ("Unknown parameter M1.foo used in constraint. Please use "
               "a single known parameter in the rhs of the constraint "
               "definition, e.g. M1:scale = M1.radius + 2")
        (QtWidgets.QMessageBox.critical.
         assert_called_with(widget, "Inconsistent constraint", msg,
                            QtWidgets.QMessageBox.Ok))
        # Check the reloading of the view
        widget.initializeFitList.assert_called_once()

        widget.initializeFitList.reset_mock()
        # Check replacement of a constraint
        perspective.symbol_dict = {"M1.scale": 1, "M1.radius": 1}

        widget.tblConstraints.item(0, 0).setText("M1:radius = bar")
        constraint = Constraint(param="radius", func="bar",
                                value_ex="M1.radius")
        target = test_tab.addConstraintToRow.call_args[1]
        assert target["constraint"].value_ex == constraint.value_ex
        assert target["constraint"].func == constraint.func
        assert target["constraint"].param == constraint.param
        assert target["row"] == 0
        target = test_tab.deleteConstraintOnParameter.call_args[0]
        assert target[0] == "scale"
        # Check the reloading of the view
        widget.initializeFitList.assert_called_once()

        widget.initializeFitList.reset_mock()
        # Check the checkbox
        widget.tblConstraints.item(0, 0).setText("M1:scale = M1.sld")
        assert test_tab.modifyViewOnRow.call_args[0][0] == 0
        font = QtGui.QFont()
        font.setItalic(True)
        assert test_tab.modifyViewOnRow.call_args[1]["font"] == \
                         font
        brush = QtGui.QBrush(QtGui.QColor('blue'))
        assert test_tab.modifyViewOnRow.call_args[1]["brush"] == \
                         brush
        # Check the reloading of the view
        widget.initializeFitList.assert_called_once()

        widget.initializeFitList.reset_mock()
        # Uncheck the checkbox
        widget.tblConstraints.item(0, 0).setCheckState(0)
        assert test_tab.modifyViewOnRow.call_args[0][0] == 0
        assert not test_tab.modifyViewOnRow.call_args[1]
        assert self.constraint1.active is False
        # Check the reloading of the view
        widget.initializeFitList.assert_called_once()
