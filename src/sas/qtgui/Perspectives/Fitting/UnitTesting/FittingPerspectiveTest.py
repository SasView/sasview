import pytest
from PySide6 import QtGui, QtWidgets

# Local
import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.MainWindow.GuiManager import GuiManager
from sas.qtgui.Perspectives.Fitting.Constraint import Constraint
from sas.qtgui.Perspectives.Fitting.FittingPerspective import FittingWindow
from sas.qtgui.Plotting.PlotterData import Data1D


class FittingPerspectiveTest:
    '''Test the Fitting Perspective'''

    @pytest.fixture(autouse=True, scope='function')
    def widget(self, qapp):
        '''Create/Destroy the perspective'''
        class dummy_manager:
            def communicator(self):
                return GuiUtils.Communicate()
            communicate = GuiUtils.Communicate()

        '''Create the perspective'''
        # need to ensure that categories exist first
        GuiManager.addCategories()

        w = FittingWindow(dummy_manager())
        yield w
        w.close()
        del w

    def testDefaults(self, widget):
        '''Test the GUI in its default state'''
        assert isinstance(widget, QtWidgets.QWidget)
        assert "Fit panel" in widget.windowTitle()
        assert widget.optimizer == "Levenberg-Marquardt"
        assert len(widget.tabs) == 1
        assert widget.maxIndex == 2
        assert widget.getTabName() == "FitPage2"

    def testAddTab(self, widget):
        '''Add a tab and test it'''

        # Add an empty tab
        widget.addFit(None)
        assert len(widget.tabs) == 2
        assert widget.getTabName() == "FitPage3"
        assert widget.maxIndex == 3
        # Add an empty batch tab
        widget.addFit(None, is_batch=True)
        assert len(widget.tabs) == 3
        assert widget.getTabName(2) == "BatchPage4"
        assert widget.maxIndex == 4

    def testAddCSTab(self, widget):
        ''' Add a constraint/simult tab'''
        widget.addConstraintTab()
        assert len(widget.tabs) == 2
        assert widget.getCSTabName() == "Const. & Simul. Fit"

    def testResetTab(self, widget, mocker):
        ''' Remove data from last tab'''
        assert len(widget.tabs) == 1
        assert widget.getTabName() == "FitPage2"
        assert widget.maxIndex == 2

        # Attempt to remove the last tab
        widget.resetTab(0)

        # see that the tab didn't disappear, just changed the name/id
        assert len(widget.tabs) == 1
        assert widget.getTabName() == "FitPage3"
        assert widget.maxIndex == 3

        # Now, add data
        data = Data1D(x=[1,2], y=[1,2])
        mocker.patch.object(GuiUtils, 'dataFromItem', return_value=data)
        item = QtGui.QStandardItem("test")
        widget.setData([item])
        # Assert data is on widget
        assert len(widget.tabs[0].all_data) == 1
        # Reset the tab
        widget.resetTab(0)
        # See that the tab contains data no more
        assert len(widget.tabs[0].all_data) == 0

    def testCloseTab(self, widget):
        '''Delete a tab and test'''
        # Add an empty tab
        widget.addFit(None)

        # Remove the original tab
        widget.tabCloses(1)
        assert len(widget.tabs) == 1
        assert widget.maxIndex == 3
        assert widget.getTabName() == "FitPage3"

        # Attemtp to remove the last tab
        widget.tabCloses(1)
        # The tab should still be there
        assert len(widget.tabs) == 1
        assert widget.maxIndex == 4
        assert widget.getTabName() == "FitPage4"

    def testAllowBatch(self, widget):
        '''Assure the perspective allows multiple datasets'''
        assert widget.allowBatch()

    #@pytest.mark.skip()
    def testSetData(self, widget, qtbot, mocker):
        ''' Assure that setting data is correct'''
        with pytest.raises(AssertionError):
            widget.setData(None)

        with pytest.raises(AttributeError):
            widget.setData("BOOP")

        # Mock the datafromitem() call from FittingWidget
        data = Data1D(x=[1,2], y=[1,2])
        mocker.patch.object(GuiUtils, 'dataFromItem', return_value=data)

        item = QtGui.QStandardItem("test")
        widget.setData([item])

        # First tab should accept data
        assert len(widget.tabs) == 1

        # Add another set of data
        widget.setData([item])

        # Now we should have two tabs
        assert len(widget.tabs) == 2

        # Add two more items in a list
        widget.setData([item, item])

        # Check for 4 tabs
        assert len(widget.tabs) == 4

    def testSwapData(self, widget, mocker):
        '''Assure that data swapping is correct'''

        # Mock the datafromitem() call from FittingWidget
        data1 = Data1D(x=[3,4], y=[3,4])
        mocker.patch.object(GuiUtils, 'dataFromItem', return_value=data1)

        # Add a new tab
        item = QtGui.QStandardItem("test")
        widget.setData([item])

        # Create a new dataset and mock the datafromitemcall()
        data2 = Data1D(x=[1,2], y=[1,2])
        mocker.patch.object(GuiUtils, 'dataFromItem', return_value=data2)

        # Swap the data
        widget.swapData(item)

        # Check that data has been swapped
        assert widget.tabs[0].data == data2

        # We should only have one tab
        assert len(widget.tabs) == 1

        # send something stupid as data
        item = "foo"

        # It should raise an AttributeError
        with pytest.raises(AttributeError):
            widget.swapData(item)

        # Create a batch tab
        item = QtGui.QStandardItem("test")
        widget.addFit(None, is_batch=True)

        # It should raise an exception
        with pytest.raises(RuntimeError):
            widget.swapData(item)

        # Create a non valid tab
        widget.addConstraintTab()

        # It should raise a TypeError
        with pytest.raises(TypeError):
            widget.swapData(item)

    def testSetBatchData(self, widget, mocker):
        ''' Assure that setting batch data is correct'''

        # Mock the datafromitem() call from FittingWidget
        data1 = Data1D(x=[1,2], y=[1,2])
        data2 = Data1D(x=[1,2], y=[1,2])
        data_batch = [data1, data2]
        mocker.patch.object(GuiUtils, 'dataFromItem', return_value=data1)

        item = QtGui.QStandardItem("test")
        widget.setData([item, item], is_batch=True)

        # First tab should not accept data
        assert len(widget.tabs) == 2

        # Add another set of data
        widget.setData([item, item], is_batch=True)

        # Now we should have two batch tabs
        assert len(widget.tabs) == 3

        # Check the names of the new tabs
        assert widget.tabText(1) == "BatchPage2"
        assert widget.tabText(2) == "BatchPage3"

    def testGetFitTabs(self, widget):
        '''test the fit tab getter method'''
        # Add an empty tab
        widget.addFit(None)
        # Get the tabs
        tabs = widget.getFitTabs()
        assert isinstance(tabs, list)
        assert len(tabs) == 2

    def testGetActiveConstraintList(self, widget, mocker):
        '''test the active constraint getter'''
        # Add an empty tab
        widget.addFit(None)
        # mock the getConstraintsForModel method of the FittingWidget tab of
        # the first tab
        tab = widget.tabs[0]
        mocker.patch.object(tab, 'getConstraintsForModel',
                            return_value=[("scale", "M2.scale +2")])
        # mock the getConstraintsForModel method of the FittingWidget tab of
        # the second tab
        tab = widget.tabs[1]
        mocker.patch.object(tab, 'getConstraintsForModel',
                            return_value=[("scale", "M2.background +2")])
        constraints = widget.getActiveConstraintList()

        # we should have 2 constraints
        assert len(constraints) == 2
        assert constraints == [("M1.scale", "M2.scale +2"),
                                       ('M2.scale', 'M2.background +2')]

    def testGetSymbolDictForConstraints(self, widget, mocker):
        '''test the symbol dict getter'''
        # Add an empty tab
        widget.addFit(None)
        # mock the getSymbolDict method of the first tab
        tab = widget.tabs[0]
        mocker.patch.object(tab, 'getSymbolDict', return_value={"M1.scale": 1})
        # mock the getSymbolDict method of the second tab
        tab = widget.tabs[1]
        mocker.patch.object(tab, 'getSymbolDict', return_value={"M2.scale": 1})

        symbols = widget.getSymbolDictForConstraints()
        # we should have 2 symbols
        assert len(symbols) == 2
        assert list(symbols.keys()) == ["M1.scale", "M2.scale"]

    @pytest.mark.xfail(reason="2022-09 already broken")
    # Generates a RuntimeError:
    # src/sas/qtgui/Perspectives/Fitting/ConstraintWidget.py:240: RuntimeError
    # wrapped C/C++ object of type FittingWidget has been deleted
    # A previous tab, 'FitPage3', is still receiving signals but
    # appears to have been garbage collected
    def testGetConstraintTab(self, widget, qtbot):
        '''test the constraint tab getter'''
        # no constraint tab is present, should return None
        constraint_tab = widget.getConstraintTab()
        assert constraint_tab is None

        # add a constraint tab
        widget.addConstraintTab()
        constraint_tab = widget.getConstraintTab()
        assert constraint_tab == widget.tabs[1]

    def testSerialization(self, widget, mocker):
        ''' Serialize fit pages and check data '''
        assert hasattr(widget, 'isSerializable')
        assert widget.isSerializable()
        data = Data1D(x=[1,2], y=[1,2])
        mocker.patch.object(GuiUtils, 'dataFromItem', return_value=data)
        item = QtGui.QStandardItem("test")
        widget.setData([item])
        tab = widget.tabs[0]
        cbCat = tab.cbCategory
        cbModel = tab.cbModel
        cbCat.setCurrentIndex(cbCat.findText("Cylinder"))
        cbModel.setCurrentIndex(cbModel.findText("barbell"))
        data_id = str(widget.currentTabDataId()[0])
        # check values - disabled control, present weights
        rowcount = tab._model_model.rowCount()
        assert rowcount == 8
        state_default = widget.serializeAll()
        state_all = widget.serializeAllFitpage()
        state_cp = widget.serializeCurrentPage()
        page = widget.getSerializedFitpage(widget.currentTab)
        # Pull out params from state
        params = state_all[data_id]['fit_params'][0]
        # Tests
        assert len(state_all) == len(state_default)
        assert len(state_cp) == len(page)
        assert len(state_all) == 1
        # getPage should include an extra param 'data_id' removed by serialize
        assert len(params) != len(page)
        assert len(params) == 28
        assert page.get('data_id', None) is None

    def testUpdateFromConstraints(self, widget, mocker):
        '''tests the method that parses the loaded project dict and retuens a dict with constrains across all fit pages'''
        # create a constraint dict with one constraint for fit pages 1 and 2
        constraint_dict = {'M1': [['scale', 'scale', 'M1.scale', True,
                                 'M2.scale']],
                           'M2': [['background', 'background',
                                   'M2.background', True, 'M1.background']]}
        # add a second tab
        widget.addFit(None)
        tab1 = widget.tabs[0]
        tab2 = widget.tabs[1]
        # mock the getRowFromName methods from both tabs
        mocker.patch.object(tab1, 'getRowFromName', return_value=0)
        mocker.patch.object(tab2, 'getRowFromName', return_value=1)
        # mock the addConstraintToRow method of both tabs
        mocker.patch.object(tab1, 'addConstraintToRow')
        mocker.patch.object(tab2, 'addConstraintToRow')
        # add the constraints
        widget.updateFromConstraints(constraint_dict)
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

    def testGetTabByName(self, widget):
        '''test getting a tab by its name'''
        # add a second tab
        widget.addFit(None)
        # get the second tab
        tab = widget.getTabByName('M2')
        assert tab == widget.tabs[1]
        # get some unexisting tab
        tab = widget.getTabByName('foo')
        assert not tab
