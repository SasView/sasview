import sys
import unittest
import webbrowser

import pytest

from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import QtTest
from PyQt5 import QtCore
from unittest.mock import MagicMock

# set up import paths
import sas.qtgui.path_prepare

# Local
import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Perspectives.Fitting.Constraint import Constraint
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Perspectives.Fitting.FittingPerspective import FittingWindow

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)


class FittingPerspectiveTest(unittest.TestCase):
    '''Test the Fitting Perspective'''
    def setUp(self):
        class dummy_manager(object):
            def communicator(self):
                return GuiUtils.Communicate()
            communicate = GuiUtils.Communicate()

        '''Create the perspective'''
        self.widget = FittingWindow(dummy_manager())

    def tearDown(self):
        '''Destroy the perspective'''
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        '''Test the GUI in its default state'''
        assert isinstance(self.widget, QtWidgets.QWidget)
        assert "Fit panel" in self.widget.windowTitle()
        assert self.widget.optimizer == "Levenberg-Marquardt"
        assert len(self.widget.tabs) == 1
        assert self.widget.maxIndex == 2
        assert self.widget.getTabName() == "FitPage2"

    def testAddTab(self):
        '''Add a tab and test it'''

        # Add an empty tab
        self.widget.addFit(None)
        assert len(self.widget.tabs) == 2
        assert self.widget.getTabName() == "FitPage3"
        assert self.widget.maxIndex == 3
        # Add an empty batch tab
        self.widget.addFit(None, is_batch=True)
        assert len(self.widget.tabs) == 3
        assert self.widget.getTabName(2) == "BatchPage4"
        assert self.widget.maxIndex == 4

    def testAddCSTab(self):
        ''' Add a constraint/simult tab'''
        self.widget.addConstraintTab()
        assert len(self.widget.tabs) == 2
        assert self.widget.getCSTabName() == "Const. & Simul. Fit"

    def testResetTab(self):
        ''' Remove data from last tab'''
        assert len(self.widget.tabs) == 1
        assert self.widget.getTabName() == "FitPage2"
        assert self.widget.maxIndex == 2

        # Attempt to remove the last tab
        self.widget.resetTab(0)

        # see that the tab didn't disappear, just changed the name/id
        assert len(self.widget.tabs) == 1
        assert self.widget.getTabName() == "FitPage3"
        assert self.widget.maxIndex == 3

        # Now, add data
        data = Data1D(x=[1,2], y=[1,2])
        GuiUtils.dataFromItem = MagicMock(return_value=data)
        item = QtGui.QStandardItem("test")
        self.widget.setData([item])
        # Assert data is on widget
        assert len(self.widget.tabs[0].all_data) == 1
        # Reset the tab
        self.widget.resetTab(0)
        # See that the tab contains data no more
        assert len(self.widget.tabs[0].all_data) == 0

    def testCloseTab(self):
        '''Delete a tab and test'''
        # Add an empty tab
        self.widget.addFit(None)

        # Remove the original tab
        self.widget.tabCloses(1)
        assert len(self.widget.tabs) == 1
        assert self.widget.maxIndex == 3
        assert self.widget.getTabName() == "FitPage3"

        # Attemtp to remove the last tab
        self.widget.tabCloses(1)
        # The tab should still be there
        assert len(self.widget.tabs) == 1
        assert self.widget.maxIndex == 4
        assert self.widget.getTabName() == "FitPage4"

    def testAllowBatch(self):
        '''Assure the perspective allows multiple datasets'''
        assert self.widget.allowBatch()

    def testSetData(self):
        ''' Assure that setting data is correct'''
        with pytest.raises(AssertionError):
            self.widget.setData(None)

        with pytest.raises(AttributeError):
            self.widget.setData("BOOP")

        # Mock the datafromitem() call from FittingWidget
        data = Data1D(x=[1,2], y=[1,2])
        GuiUtils.dataFromItem = MagicMock(return_value=data)

        item = QtGui.QStandardItem("test")
        self.widget.setData([item])

        # First tab should accept data
        assert len(self.widget.tabs) == 1

        # Add another set of data
        self.widget.setData([item])

        # Now we should have two tabs
        assert len(self.widget.tabs) == 2

        # Add two more items in a list
        self.widget.setData([item, item])

        # Check for 4 tabs
        assert len(self.widget.tabs) == 4

    def testSwapData(self):
        '''Assure that data swapping is correct'''

        # Mock the datafromitem() call from FittingWidget
        data1 = Data1D(x=[3,4], y=[3,4])
        GuiUtils.dataFromItem = MagicMock(return_value=data1)

        # Add a new tab
        item = QtGui.QStandardItem("test")
        self.widget.setData([item])

        # Create a new dataset and mock the datafromitemcall()
        data2 = Data1D(x=[1,2], y=[1,2])
        GuiUtils.dataFromItem = MagicMock(return_value=data2)

        # Swap the data
        self.widget.swapData(item)

        # Check that data has been swapped
        assert self.widget.tabs[0].data == data2

        # We should only have one tab
        assert len(self.widget.tabs) == 1

        # send something stupid as data
        item = "foo"

        # It should raise an AttributeError
        with pytest.raises(AttributeError):
            self.widget.swapData(item)

        # Create a batch tab
        item = QtGui.QStandardItem("test")
        self.widget.addFit(None, is_batch=True)

        # It should raise an exception
        with pytest.raises(RuntimeError):
            self.widget.swapData(item)

        # Create a non valid tab
        self.widget.addConstraintTab()

        # It should raise a TypeError
        with pytest.raises(TypeError):
            self.widget.swapData(item)

    def testSetBatchData(self):
        ''' Assure that setting batch data is correct'''

        # Mock the datafromitem() call from FittingWidget
        data1 = Data1D(x=[1,2], y=[1,2])
        data2 = Data1D(x=[1,2], y=[1,2])
        data_batch = [data1, data2]
        GuiUtils.dataFromItem = MagicMock(return_value=data1)

        item = QtGui.QStandardItem("test")
        self.widget.setData([item, item], is_batch=True)

        # First tab should not accept data
        assert len(self.widget.tabs) == 2

        # Add another set of data
        self.widget.setData([item, item], is_batch=True)

        # Now we should have two batch tabs
        assert len(self.widget.tabs) == 3

        # Check the names of the new tabs
        assert self.widget.tabText(1) == "BatchPage2"
        assert self.widget.tabText(2) == "BatchPage3"

    def testGetFitTabs(self):
        '''test the fit tab getter method'''
        # Add an empty tab
        self.widget.addFit(None)
        # Get the tabs
        tabs = self.widget.getFitTabs()
        assert isinstance(tabs, list)
        assert len(tabs) == 2

    def testGetActiveConstraintList(self):
        '''test the active constraint getter'''
        # Add an empty tab
        self.widget.addFit(None)
        # mock the getConstraintsForModel method of the FittingWidget tab of
        # the first tab
        tab = self.widget.tabs[0]
        tab.getConstraintsForModel = MagicMock(return_value=[("scale",
                                                               "M2.scale +2")])
        # mock the getConstraintsForModel method of the FittingWidget tab of
        # the second tab
        tab = self.widget.tabs[1]
        tab.getConstraintsForModel = MagicMock(return_value=[("scale",
                                                               "M2.background "
                                                               "+2")])
        constraints = self.widget.getActiveConstraintList()

        # we should have 2 constraints
        assert len(constraints) == 2
        assert constraints == [("M1.scale", "M2.scale +2"),
                                       ('M2.scale', 'M2.background +2')]

    def testGetSymbolDictForConstraints(self):
        '''test the symbol dict getter'''
        # Add an empty tab
        self.widget.addFit(None)
        # mock the getSymbolDict method of the first tab
        tab = self.widget.tabs[0]
        tab.getSymbolDict = MagicMock(return_value={"M1.scale": 1})
        # mock the getSymbolDict method of the second tab
        tab = self.widget.tabs[1]
        tab.getSymbolDict = MagicMock(return_value={"M2.scale": 1})

        symbols = self.widget.getSymbolDictForConstraints()
        # we should have 2 symbols
        assert len(symbols) == 2
        assert list(symbols.keys()) == ["M1.scale", "M2.scale"]

    def testGetConstraintTab(self):
        '''test the constraint tab getter'''
        # no constraint tab is present, should return None
        constraint_tab = self.widget.getConstraintTab()
        assert constraint_tab == None

        # add a constraint tab
        self.widget.addConstraintTab()
        constraint_tab = self.widget.getConstraintTab()
        assert constraint_tab == self.widget.tabs[1]

    def testSerialization(self):
        ''' Serialize fit pages and check data '''
        assert hasattr(self.widget, 'isSerializable')
        assert self.widget.isSerializable()
        data = Data1D(x=[1,2], y=[1,2])
        GuiUtils.dataFromItem = MagicMock(return_value=data)
        item = QtGui.QStandardItem("test")
        self.widget.setData([item])
        tab = self.widget.tabs[0]
        cbCat = tab.cbCategory
        cbModel = tab.cbModel
        cbCat.setCurrentIndex(cbCat.findText("Cylinder"))
        cbModel.setCurrentIndex(cbModel.findText("barbell"))
        data_id = str(self.widget.currentTabDataId()[0])
        # check values - disabled control, present weights
        rowcount = tab._model_model.rowCount()
        assert rowcount == 8
        state_default = self.widget.serializeAll()
        state_all = self.widget.serializeAllFitpage()
        state_cp = self.widget.serializeCurrentPage()
        page = self.widget.getSerializedFitpage(self.widget.currentTab)
        # Pull out params from state
        params = state_all[data_id]['fit_params'][0]
        # Tests
        assert len(state_all) == len(state_default)
        assert len(state_cp) == len(page)
        assert len(state_all) == 1
        # getPage should include an extra param 'data_id' removed by serialize
        assert len(params) != len(page)
        assert len(params) == 28
        assert page.get('data_id', None) == None

    def testUpdateFromConstraints(self):
        '''tests the method that parses the loaded project dict and retuens a dict with constrains across all fit pages'''
        # create a constraint dict with one constraint for fit pages 1 and 2
        constraint_dict = {'M1': [['scale', 'scale', 'M1.scale', True,
                                 'M2.scale']],
                           'M2': [['background', 'background',
                                   'M2.background', True, 'M1.background']]}
        # add a second tab
        self.widget.addFit(None)
        tab1 = self.widget.tabs[0]
        tab2 = self.widget.tabs[1]
        # mock the getRowFromName methods from both tabs
        tab1.getRowFromName = MagicMock(return_value=0)
        tab2.getRowFromName = MagicMock(return_value=1)
        # mock the addConstraintToRow method of both tabs
        tab1.addConstraintToRow = MagicMock()
        tab2.addConstraintToRow = MagicMock()
        # add the constraints
        self.widget.updateFromConstraints(constraint_dict)
        # check that getRowFromName was called correctly on both tabs
        tab1.getRowFromName.assert_called_with("scale")
        tab2.getRowFromName.assert_called_with("background")
        # check that addConstraintToRow was called correctly
        constraint1 = Constraint(param='scale',
                                 value='scale',
                                 value_ex="M1.scale",
                                 func="M2.scale")
        constraint2 = Constraint(param='background',
                                 value='background',
                                 value_ex="M2.background",
                                 func="M1.background")
        tab1_call_dict = tab1.addConstraintToRow.call_args[1]
        tab2_call_dict = tab2.addConstraintToRow.call_args[1]
        assert vars(tab1_call_dict['constraint']) == vars(constraint1)
        assert vars(tab2_call_dict['constraint']) == vars(constraint2)
        assert tab1_call_dict['row'] == 0
        assert tab2_call_dict['row'] == 1

    def testGetTabByName(self):
        '''test getting a tab by its name'''
        # add a second tab
        self.widget.addFit(None)
        # get the second tab
        tab = self.widget.getTabByName('M2')
        assert tab == self.widget.tabs[1]
        # get some unexisting tab
        tab = self.widget.getTabByName('foo')
        assert not tab

if __name__ == "__main__":
    unittest.main()
