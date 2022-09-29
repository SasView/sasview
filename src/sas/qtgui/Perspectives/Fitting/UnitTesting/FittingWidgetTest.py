import sys
import unittest
import time
import logging
import os
import inspect
import glob

import pytest

from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import QtTest
from PyQt5 import QtCore
from unittest.mock import MagicMock, patch
from twisted.internet import threads

# set up import paths
import sas.qtgui.path_prepare

# Local
from sas.qtgui.Utilities.GuiUtils import *
from sas.qtgui.Perspectives.Fitting.FittingWidget import *
from sas.qtgui.Perspectives.Fitting.Constraint import Constraint
from sas.qtgui.UnitTesting.TestUtils import QtSignalSpy
from sas.qtgui.Perspectives.Fitting.ModelThread import Calc1D
from sas.qtgui.Perspectives.Fitting.ModelThread import Calc2D

from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.PlotterData import Data2D

from sasmodels.sasview_model import load_custom_model
from sas.sascalc.fit.models import ModelManagerBase, ModelManager

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)

class dummy_manager(object):
    HELP_DIRECTORY_LOCATION = "html"
    communicate = Communicate()

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

def find_plugin_models_mod():
    """
    Modification to sas.sascalc.fit.models.find_plugin_models().
    Instead of searching for user's plugin directory, the path is set at:
    'sas/qtgui/Perspectives/Fitting/plugin_models'
    Modified to test handling of plugin models.
    """
    plugins_dir = [
        os.path.abspath(path) for path in glob.glob("**/plugin_models",recursive=True)
        if os.path.normpath("qtgui/Perspectives/Fitting/plugin_models") in os.path.abspath(path)
    ][0]

    plugins = {}
    for filename in os.listdir(plugins_dir):
        name, ext = os.path.splitext(filename)
        if ext == '.py' and not name == '__init__':
            path = os.path.abspath(os.path.join(plugins_dir, filename))
            model = load_custom_model(path)
            plugins[model.name] = model

    return plugins

class ModelManagerBaseMod(ModelManagerBase):
    """
    Inherits from ModelManagerBase class and is the base class for the ModelManagerMod.
    Modified to test handling of plugin models.
    """
    def _is_plugin_dir_changed(self):
        """
        Originally checked if the plugin directory has changed, returning True if so.
        Now returns False in all cases to test handling of plugin models.
        """
        is_modified = False
        return is_modified

    def plugins_reset(self):
        """
        Returns a dictionary of the models, but will now utilize the find_plugin_models_mod function.
        """
        self.plugin_models = find_plugin_models_mod()
        self.model_dictionary.clear()
        self.model_dictionary.update(self.standard_models)
        self.model_dictionary.update(self.plugin_models)
        return self.get_model_list()

class ModelManagerMod(ModelManager):
    """
    Inherits from ModelManager class which manages the list of available models.
    Modified to test handling of plugin models.
    """
    base = None

    def __init__(self):
        if ModelManagerMod.base is None:
            ModelManagerMod.base = ModelManagerBaseMod()

class FittingWidgetMod(FittingWidget):
    """
    Inherits from FittingWidget class which is the main widget for selecting form and structure factor models.
    Modified to test handling of plugin models.
    """
    def customModels(cls):
        """
        Reads in file names from the modified plugin directory to test handling of plugin models.
        """
        manager = ModelManagerMod()
        manager.update()
        return manager.base.plugin_models

class FittingWidgetTest(unittest.TestCase):
    """Test the fitting widget GUI"""

    def setUp(self):
        """Create the GUI"""
        self.widget = FittingWidgetMod(dummy_manager())
        FittingUtilities.checkConstraints = MagicMock(return_value=None)

    def tearDown(self):
        """Destroy the GUI"""
        self.widget.close()
        del self.widget

    def testDefaults(self):
        """Test the GUI in its default state"""
        assert isinstance(self.widget, QtWidgets.QWidget)
        assert self.widget.windowTitle() == "Fitting"
        assert self.widget.sizePolicy().Policy() == QtWidgets.QSizePolicy.Fixed
        assert isinstance(self.widget.lstParams.model(), QtGui.QStandardItemModel)
        assert isinstance(self.widget.lstPoly.model(), QtGui.QStandardItemModel)
        assert isinstance(self.widget.lstMagnetic.model(), QtGui.QStandardItemModel)
        assert not self.widget.cbModel.isEnabled()
        assert not self.widget.cbStructureFactor.isEnabled()
        assert not self.widget.cmdFit.isEnabled()
        assert self.widget.acceptsData()
        assert not self.widget.data_is_loaded

    def testSelectCategoryDefault(self):
        """
        Test if model categories have been loaded properly
        """
        fittingWindow =  self.widget

        #Test loading from json categories
        category_list = list(fittingWindow.master_category_dict.keys())

        for category in category_list:
            assert fittingWindow.cbCategory.findText(category) != -1

        #Test what is current text in the combobox
        assert fittingWindow.cbCategory.currentText() == CATEGORY_DEFAULT

    def testWidgetWithData(self):
        """
        Test the instantiation of the widget with initial data
        """
        data = Data1D(x=[1,2], y=[1,2])
        GuiUtils.dataFromItem = MagicMock(return_value=data)
        item = QtGui.QStandardItem("test")

        widget_with_data = FittingWidgetMod(dummy_manager(), data=item, tab_id=3)

        assert widget_with_data.data == data
        assert widget_with_data.data_is_loaded
        # self.assertTrue(widget_with_data.cmdFit.isEnabled())
        assert not widget_with_data.acceptsData()

    def testSelectPolydispersity(self):
        """
        Test if models have been loaded properly
        """
        fittingWindow =  self.widget

        assert isinstance(fittingWindow.lstPoly.itemDelegate(), QtWidgets.QStyledItemDelegate)
        #Test loading from json categories
        fittingWindow.SASModelToQModel("cylinder")
        pd_index = fittingWindow.lstPoly.model().index(0,0)
        assert str(pd_index.data()) == "Distribution of radius"
        pd_index = fittingWindow.lstPoly.model().index(1,0)
        assert str(pd_index.data()) == "Distribution of length"

        # test the delegate a bit
        delegate = fittingWindow.lstPoly.itemDelegate()
        assert len(delegate.POLYDISPERSE_FUNCTIONS) == 5
        assert delegate.editableParameters() == [1, 2, 3, 4, 5]
        assert delegate.poly_function == 6
        assert isinstance(delegate.combo_updated, QtCore.pyqtBoundSignal)

    @pytest.mark.xfail(reason="2022-09 already broken")
    def testSelectMagnetism(self):
        """
        Test if models have been loaded properly
        """
        fittingWindow =  self.widget

        assert isinstance(fittingWindow.lstMagnetic.itemDelegate(), QtWidgets.QStyledItemDelegate)
        #Test loading from json categories
        fittingWindow.SASModelToQModel("cylinder")
        mag_index = fittingWindow.lstMagnetic.model().index(0,0)
        assert mag_index.data() == "up_frac_i"
        mag_index = fittingWindow.lstMagnetic.model().index(1,0)
        assert mag_index.data() == "up_frac_f"
        mag_index = fittingWindow.lstMagnetic.model().index(2,0)
        assert mag_index.data() == "up_theta"
        mag_index = fittingWindow.lstMagnetic.model().index(3,0)
        assert mag_index.data() == "up_phi"
        mag_index = fittingWindow.lstMagnetic.model().index(4,0)
        assert mag_index.data() == "sld_M0"
        mag_index = fittingWindow.lstMagnetic.model().index(5,0)
        assert mag_index.data() == "sld_mtheta"
        mag_index = fittingWindow.lstMagnetic.model().index(6,0)
        assert mag_index.data() == "sld_mphi"
        mag_index = fittingWindow.lstMagnetic.model().index(7,0)
        assert mag_index.data() == "sld_solvent_M0"
        mag_index = fittingWindow.lstMagnetic.model().index(8,0)
        assert mag_index.data() == "sld_solvent_mtheta"
        mag_index = fittingWindow.lstMagnetic.model().index(9,0)
        assert mag_index.data() == "sld_solvent_mphi"

        # test the delegate a bit
        delegate = fittingWindow.lstMagnetic.itemDelegate()
        assert delegate.editableParameters() == [1, 2, 3]

    def testSelectStructureFactor(self):
        """
        Test if structure factors have been loaded properly, including plugins also classified as a structure factor.
        """
        fittingWindow =  self.widget

        #Test for existence in combobox
        assert fittingWindow.cbStructureFactor.findText("stickyhardsphere") != -1
        assert fittingWindow.cbStructureFactor.findText("hayter_msa") != -1
        assert fittingWindow.cbStructureFactor.findText("squarewell") != -1
        assert fittingWindow.cbStructureFactor.findText("hardsphere") != -1
        assert fittingWindow.cbStructureFactor.findText("plugin_structure_template") != -1
        assert fittingWindow.cbStructureFactor.findText("plugin_template") == -1

        #Test what is current text in the combobox
        assert fittingWindow.cbCategory.currentText(), "None"

    def testSignals(self):
        """
        Test the widget emitted signals
        """
        pass

    @pytest.mark.xfail(reason="2022-09 already broken")
    def testSelectCategory(self):
        """
        Assure proper behaviour on changing category
        """
        self.widget.show()
        assert self.widget._previous_category_index == 0
        # confirm the model combo contains no models
        assert self.widget.cbModel.count() == 0

        # invoke the method by changing the index
        category_index = self.widget.cbCategory.findText("Shape Independent")
        self.widget.cbCategory.setCurrentIndex(category_index)
        model_index = self.widget.cbModel.findText("be_polyelectrolyte")
        self.widget.cbModel.setCurrentIndex(model_index)

        # test the model combo content
        assert self.widget.cbModel.count() == 30

        # Try to change back to default
        self.widget.cbCategory.setCurrentIndex(0)

        # Observe no such luck
        assert self.widget.cbCategory.currentIndex() == 6
        assert self.widget.cbModel.count() == 30

        # Set the structure factor
        structure_index=self.widget.cbCategory.findText(CATEGORY_STRUCTURE)
        self.widget.cbCategory.setCurrentIndex(structure_index)
        # check the enablement of controls
        assert not self.widget.cbModel.isEnabled()
        assert self.widget.cbStructureFactor.isEnabled()

    def testSelectModel(self):
        """
        Assure proper behaviour on changing model
        """
        self.widget.show()
        # Change the category index so we have some models
        category_index = self.widget.cbCategory.findText("Shape Independent")
        self.widget.cbCategory.setCurrentIndex(category_index)
        model_index = self.widget.cbModel.findText("be_polyelectrolyte")
        self.widget.cbModel.setCurrentIndex(model_index)
        QtWidgets.qApp.processEvents()

        # check the enablement of controls
        assert self.widget.cbModel.isEnabled()
        assert not self.widget.cbStructureFactor.isEnabled()

        # set up the model update spy
        # spy = QtSignalSpy(self.widget._model_model, self.widget._model_model.itemChanged)

        # mock the tested methods
        self.widget.SASModelToQModel = MagicMock()
        self.widget.createDefaultDataset = MagicMock()
        self.widget.calculateQGridForModel = MagicMock()
        # 
        # Now change the model
        self.widget.cbModel.setCurrentIndex(4)
        assert self.widget.cbModel.currentText() == 'dab'

        # No data sent -> no index set, only createDefaultDataset called
        assert self.widget.createDefaultDataset.called
        assert self.widget.SASModelToQModel.called
        assert not self.widget.calculateQGridForModel.called

        # Let's tell the widget that data has been loaded
        self.widget.data_is_loaded = True
        # Reset the sasmodel index
        self.widget.cbModel.setCurrentIndex(2)
        assert self.widget.cbModel.currentText() == 'broad_peak'

        # Observe calculateQGridForModel called
        assert self.widget.calculateQGridForModel.called

    @pytest.mark.xfail(reason="2022-09 already broken")
    def testSelectFactor(self):
        """
        Assure proper behaviour on changing structure factor
        """
        self.widget.show()
        # Change the category index so we have some models
        category_index = self.widget.cbCategory.findText("Cylinder")
        self.widget.cbCategory.setCurrentIndex(category_index)
        # Change the model to one that supports structure factors
        model_index = self.widget.cbModel.findText('cylinder')
        self.widget.cbModel.setCurrentIndex(model_index)

        # Check that the factor combo is active and the default is chosen
        assert self.widget.cbStructureFactor.isEnabled()
        assert self.widget.cbStructureFactor.currentText() == STRUCTURE_DEFAULT

        # We have this many rows in the model
        rowcount = self.widget._model_model.rowCount()
        #self.assertEqual(self.widget._model_model.rowCount(), 8)

        # Change structure factor to something more exciting
        structure_index = self.widget.cbStructureFactor.findText('squarewell')
        self.widget.cbStructureFactor.setCurrentIndex(structure_index)

        # We have 3 more param rows now (radius_effective is removed), and new headings
        assert self.widget._model_model.rowCount() == rowcount+7

        # Switch models
        self.widget.cbModel.setCurrentIndex(0)

        # Observe factor doesn't reset to None
        assert self.widget.cbStructureFactor.currentText() == 'squarewell'

        # Switch category to structure factor
        structure_index=self.widget.cbCategory.findText(CATEGORY_STRUCTURE)
        self.widget.cbCategory.setCurrentIndex(structure_index)
        # Observe the correct enablement
        assert self.widget.cbStructureFactor.isEnabled()
        assert not self.widget.cbModel.isEnabled()
        assert self.widget._model_model.rowCount() == 0

        # Choose the last factor
        last_index = self.widget.cbStructureFactor.count()
        self.widget.cbStructureFactor.setCurrentIndex(last_index-1)
        # Do we have all the rows (incl. radius_effective & heading row)?
        assert self.widget._model_model.rowCount() == 5

        # Are the command buttons properly enabled?
        assert self.widget.cmdPlot.isEnabled()
        assert not self.widget.cmdFit.isEnabled()

    def testReadCategoryInfo(self):
        """
        Check the category file reader
        """
        # Tested in default checks
        pass

    def testUpdateParamsFromModel(self):
        """
        Checks the sasmodel parameter update from QModel items
        """
        # Tested in default checks
        pass

    def testCreateTheoryIndex(self):
        """
        Test the data->QIndex conversion
        """
        # set up the model update spy
        spy = QtSignalSpy(self.widget._model_model, self.widget.communicate.updateTheoryFromPerspectiveSignal)

        self.widget.show()
        # Change the category index so we have some models
        self.widget.cbCategory.setCurrentIndex(1)

        # Create the index
        self.widget.createTheoryIndex(Data1D(x=[1,2], y=[1,2]))

        # Make sure the signal has been emitted
        assert spy.count() == 1

        # Check the argument type
        assert isinstance(spy.called()[0]['args'][0], QtGui.QStandardItem)

    def testCalculateQGridForModel(self):
        """
        Check that the fitting 1D data object is ready
        """

        if config.USING_TWISTED:
            # Mock the thread creation
            threads.deferToThread = MagicMock()
            # Model for theory
            self.widget.SASModelToQModel("cylinder")
            # Call the tested method
            self.widget.calculateQGridForModel()
            time.sleep(1)
            # Test the mock
            assert threads.deferToThread.called
            assert threads.deferToThread.call_args_list[0][0][0].__name__ == "compute"
        else:
            Calc2D.queue = MagicMock()
            # Model for theory
            self.widget.SASModelToQModel("cylinder")
            # Call the tested method
            self.widget.calculateQGridForModel()
            time.sleep(1)
            # Test the mock
            assert Calc2D.queue.called

    def testCalculateResiduals(self):
        """
        Check that the residuals are calculated and plots updated
        """
        test_data = Data1D(x=[1,2], y=[1,2])

        # Model for theory
        self.widget.SASModelToQModel("cylinder")
        # Invoke the tested method
        self.widget.calculateResiduals(test_data)
        # Check the Chi2 value - should be undetermined
        assert self.widget.lblChi2Value.text() == '---'

        # Force same data into logic
        self.widget.logic.data = test_data
        self.widget.calculateResiduals(test_data)
        # Now, the difference is 0, as data is the same
        assert self.widget.lblChi2Value.text() == '---'

        # Change data
        test_data_2 = Data1D(x=[1,2], y=[2.1,3.49])
        self.widget.logic.data = test_data_2
        self.widget.calculateResiduals(test_data)
        # Now, the difference is non-zero
        assert self.widget.lblChi2Value.text() == '---'

    def testSetPolyModel(self):
        """
        Test the polydispersity model setup
        """
        self.widget.show()
        # Change the category index so we have a model with no poly
        category_index = self.widget.cbCategory.findText("Shape Independent")
        self.widget.cbCategory.setCurrentIndex(category_index)
        model_index = self.widget.cbModel.findText("be_polyelectrolyte")
        self.widget.cbModel.setCurrentIndex(model_index)

        # Check the poly model
        assert self.widget._poly_model.rowCount() == 0
        assert self.widget._poly_model.columnCount() == 0

        # Change the category index so we have a model available
        self.widget.cbCategory.setCurrentIndex(2)
        self.widget.cbModel.setCurrentIndex(1)

        # Check the poly model
        assert self.widget._poly_model.rowCount() == 4
        assert self.widget._poly_model.columnCount() == 8

        # Test the header
        assert self.widget.lstPoly.horizontalHeader().count() == 8
        assert not self.widget.lstPoly.horizontalHeader().stretchLastSection()

        # Test tooltips
        assert len(self.widget._poly_model.header_tooltips) == 8

        header_tooltips = ['Select parameter for fitting',
                            'Enter polydispersity ratio (Std deviation/mean).\n'+
                            'For angles this can be either std deviation or half width (for uniform distributions) in degrees',
                            'Enter minimum value for parameter',
                            'Enter maximum value for parameter',
                            'Enter number of points for parameter',
                            'Enter number of sigmas parameter',
                            'Select distribution function',
                            'Select filename with user-definable distribution']
        for column, tooltip in enumerate(header_tooltips):
             assert self.widget._poly_model.headerData( column,
                QtCore.Qt.Horizontal, QtCore.Qt.ToolTipRole) == \
                         header_tooltips[column]

        # Test presence of comboboxes in last column
        for row in range(self.widget._poly_model.rowCount()):
            func_index = self.widget._poly_model.index(row, 6)
            assert isinstance(self.widget.lstPoly.indexWidget(func_index), QtWidgets.QComboBox)
            assert 'Distribution of' in self.widget._poly_model.item(row, 0).text()
        #self.widget.close()

    def testPolyModelChange(self):
        """
        Polydispersity model changed - test all possible scenarios
        """
        self.widget.show()
        # Change the category index so we have a model with polydisp
        category_index = self.widget.cbCategory.findText("Cylinder")
        self.widget.cbCategory.setCurrentIndex(category_index)
        model_index = self.widget.cbModel.findText("barbell")
        self.widget.cbModel.setCurrentIndex(model_index)

        # click on a poly parameter checkbox
        index = self.widget._poly_model.index(0,0)

        # Set the checbox
        self.widget._poly_model.item(0,0).setCheckState(2)
        # Assure the parameter is added
        assert self.widget.poly_params_to_fit == ['radius_bell.width']
        # Check that it's value has not changed (reproduce the polydispersity checkbox bug)
        assert self.widget.poly_params['radius_bell.width'] == 0.0

        # Add another parameter
        self.widget._poly_model.item(2,0).setCheckState(2)
        # Assure the parameters are added
        assert self.widget.poly_params_to_fit == ['radius_bell.width', 'length.width']

        # Change the min/max values
        assert self.widget.kernel_module.details['radius_bell.width'][1] == 0.0
        self.widget._poly_model.item(0,2).setText("1.0")
        assert self.widget.kernel_module.details['radius_bell.width'][1] == 1.0
        # Check that changing the polydispersity min/max value doesn't affect the paramer min/max
        assert self.widget.kernel_module.details['radius_bell'][1] == 0.0

        #self.widget.show()
        #QtWidgets.QApplication.exec_()

        # Change the number of points
        assert self.widget.poly_params['radius_bell.npts'] == 35
        self.widget._poly_model.item(0,4).setText("22")
        assert self.widget.poly_params['radius_bell.npts'] == 22
        # test that sasmodel is updated with the new value
        assert self.widget.kernel_module.getParam('radius_bell.npts') == 22

        # Change the pd value
        assert self.widget.poly_params['radius_bell.width'] == 0.0
        self.widget._poly_model.item(0,1).setText("0.8")
        assert round(abs(self.widget.poly_params['radius_bell.width']-0.8), 7) == 0
        # Test that sasmodel is updated with the new value
        assert round(abs(self.widget.kernel_module.getParam('radius_bell.width')-0.8), 7) == 0

        # Uncheck pd in the fitting widget
        self.widget.chkPolydispersity.setCheckState(2)
        self.widget.chkPolydispersity.click()
        # Should not change the value of the qt model
        assert round(abs(self.widget.poly_params['radius_bell.width']-0.8), 7) == 0
        # sasmodel should be set to 0
        assert round(abs(self.widget.kernel_module.getParam('radius_bell.width')-0.0), 7) == 0

        # try something stupid
        self.widget._poly_model.item(0,4).setText("butt")
        # see that this didn't annoy the control at all
        assert self.widget.poly_params['radius_bell.npts'] == 22

        # Change the number of sigmas
        assert self.widget.poly_params['radius_bell.nsigmas'] == 3
        self.widget._poly_model.item(0,5).setText("222")
        assert self.widget.poly_params['radius_bell.nsigmas'] == 222
        # try something stupid again
        self.widget._poly_model.item(0,4).setText("beer")
        # no efect
        assert self.widget.poly_params['radius_bell.nsigmas'] == 222

    def testOnPolyComboIndexChange(self):
        """
        Test the slot method for polydisp. combo box index change
        """
        self.widget.show()
        # Change the category index so we have a model with polydisp
        category_index = self.widget.cbCategory.findText("Cylinder")
        self.widget.cbCategory.setCurrentIndex(category_index)
        model_index = self.widget.cbModel.findText("barbell")
        self.widget.cbModel.setCurrentIndex(model_index)

        # call method with default settings
        self.widget.onPolyComboIndexChange('gaussian', 0)
        # check values
        assert self.widget.kernel_module.getParam('radius_bell.npts') == 35
        assert self.widget.kernel_module.getParam('radius_bell.nsigmas') == 3
        # Change the index
        self.widget.onPolyComboIndexChange('rectangle', 0)
        # check values
        assert self.widget.poly_params['radius_bell.npts'] == 35
        assert round(abs(self.widget.poly_params['radius_bell.nsigmas']-1.73205), 5) == 0
        # Change the index
        self.widget.onPolyComboIndexChange('lognormal', 0)
        # check values
        assert self.widget.poly_params['radius_bell.npts'] == 80
        assert self.widget.poly_params['radius_bell.nsigmas'] == 8
        # Change the index
        self.widget.onPolyComboIndexChange('schulz', 0)
        # check values
        assert self.widget.poly_params['radius_bell.npts'] == 80
        assert self.widget.poly_params['radius_bell.nsigmas'] == 8

        # mock up file load
        self.widget.loadPolydispArray = MagicMock()
        # Change to 'array'
        self.widget.onPolyComboIndexChange('array', 0)
        # See the mock fire
        assert self.widget.loadPolydispArray.called

    @pytest.mark.xfail(reason="2022-09 already broken - input file issue")
    def testLoadPolydispArray(self):
        """
        Test opening of the load file dialog for 'array' polydisp. function
        """

        # open a non-existent file
        filename = os.path.join("UnitTesting", "testdata_noexist.txt")
        with pytest.raises(OSError):
            os.stat(filename)
        QtWidgets.QFileDialog.getOpenFileName = MagicMock(return_value=(filename,''))
        self.widget.show()
        # Change the category index so we have a model with polydisp
        category_index = self.widget.cbCategory.findText("Cylinder")
        self.widget.cbCategory.setCurrentIndex(category_index)
        model_index = self.widget.cbModel.findText("barbell")
        self.widget.cbModel.setCurrentIndex(model_index)

        self.widget.onPolyComboIndexChange('array', 0)
        # check values - unchanged since the file doesn't exist
        assert self.widget._poly_model.item(0, 1).isEnabled()

        # good file
        # TODO: this depends on the working directory being src/sas/qtgui,
        # TODO: which isn't convenient if you want to run this test suite
        # TODO: individually
        filename = os.path.join("UnitTesting", "testdata.txt")
        try:
            os.stat(filename)
        except OSError:
            assert False, "testdata.txt does not exist"
        QtWidgets.QFileDialog.getOpenFileName = MagicMock(return_value=(filename,''))

        self.widget.onPolyComboIndexChange('array', 0)
        # check values - disabled control, present weights
        assert not self.widget._poly_model.item(0, 1).isEnabled()
        assert self.widget.disp_model.weights[0] == 2.83954
        assert len(self.widget.disp_model.weights) == 19
        assert len(self.widget.disp_model.values) == 19
        assert self.widget.disp_model.values[0] == 0.0
        assert self.widget.disp_model.values[18] == 3.67347

    @pytest.mark.xfail(reason="2022-09 already broken")
    def testSetMagneticModel(self):
        """
        Test the magnetic model setup
        """
        self.widget.show()
        # Change the category index so we have a model available
        category_index = self.widget.cbCategory.findText("Sphere")
        self.widget.cbCategory.setCurrentIndex(category_index)
        model_index = self.widget.cbModel.findText("adsorbed_layer")
        self.widget.cbModel.setCurrentIndex(model_index)

        # Check the magnetic model
        assert self.widget._magnet_model.rowCount() == 9
        assert self.widget._magnet_model.columnCount() == 5

        # Test the header
        assert self.widget.lstMagnetic.horizontalHeader().count() == 5
        assert not self.widget.lstMagnetic.horizontalHeader().stretchLastSection()

        #Test tooltips
        assert len(self.widget._magnet_model.header_tooltips) == 5

        header_tooltips = ['Select parameter for fitting',
                           'Enter parameter value',
                           'Enter minimum value for parameter',
                           'Enter maximum value for parameter',
                           'Unit of the parameter']
        for column, tooltip in enumerate(header_tooltips):
             assert self.widget._magnet_model.headerData(column,
                QtCore.Qt.Horizontal, QtCore.Qt.ToolTipRole) == \
                         header_tooltips[column]

        # Test rows
        for row in range(self.widget._magnet_model.rowCount()):
            func_index = self.widget._magnet_model.index(row, 0)
            assert '_' in self.widget._magnet_model.item(row, 0).text()


    def testAddExtraShells(self):
        """
        Test how the extra shells are presented
        """
        pass

    def testModifyShellsInList(self):
        """
        Test the additional rows added by modifying the shells combobox
        """
        self.widget.show()
        # Change the model to multi shell
        category_index = self.widget.cbCategory.findText("Sphere")
        self.widget.cbCategory.setCurrentIndex(category_index)
        model_index = self.widget.cbModel.findText("core_multi_shell")
        self.widget.cbModel.setCurrentIndex(model_index)

        # Assure we have the combobox available
        cbox_row = self.widget._n_shells_row
        func_index = self.widget._model_model.index(cbox_row, 1)
        assert isinstance(self.widget.lstParams.indexWidget(func_index), QtWidgets.QComboBox)

        # get number of rows before changing shell count
        last_row = self.widget._model_model.rowCount()

        # Change the combo box index
        self.widget.lstParams.indexWidget(func_index).setCurrentIndex(3)

        # Check that the number of rows increased
        # (note that n == 1 by default in core_multi_shell so this increases index by 2)
        more_rows = self.widget._model_model.rowCount() - last_row
        assert more_rows == 4 # 4 new rows: 2 params per index

        # Set to 0
        self.widget.lstParams.indexWidget(func_index).setCurrentIndex(0)
        assert self.widget._model_model.rowCount() == last_row - 2

    @pytest.mark.xfail(reason="2022-09 already broken")
    def testPlotTheory(self):
        """
        See that theory item can produce a chart
        """
        # By default, the compute/plot button is disabled
        assert not self.widget.cmdPlot.isEnabled()
        assert self.widget.cmdPlot.text() == 'Show Plot'

        # Assign a model
        self.widget.show()
        # Change the category index so we have a model available
        category_index = self.widget.cbCategory.findText("Sphere")
        self.widget.cbCategory.setCurrentIndex(category_index)
        model_index = self.widget.cbModel.findText("adsorbed_layer")
        self.widget.cbModel.setCurrentIndex(model_index)

        # Check the enablement/text
        assert self.widget.cmdPlot.isEnabled()
        assert self.widget.cmdPlot.text() == 'Calculate'

        # Spying on plot update signal
        spy = QtSignalSpy(self.widget, self.widget.communicate.plotRequestedSignal)

        # Press Calculate
        QtTest.QTest.mouseClick(self.widget.cmdPlot, QtCore.Qt.LeftButton)

        # Observe cmdPlot caption change
        assert self.widget.cmdPlot.text() == 'Show Plot'

        # Make sure the signal has NOT been emitted
        assert spy.count() == 0

        # Click again
        QtTest.QTest.mouseClick(self.widget.cmdPlot, QtCore.Qt.LeftButton)

        # This time, we got the update signal
        assert spy.count() == 0

    def notestPlotData(self):
        """
        See that data item can produce a chart
        """
        # By default, the compute/plot button is disabled
        assert not self.widget.cmdPlot.isEnabled()
        assert self.widget.cmdPlot.text() == 'Show Plot'

        # Set data
        test_data = Data1D(x=[1,2], y=[1,2])
        item = QtGui.QStandardItem()
        updateModelItem(item, test_data, "test")
        # Force same data into logic
        self.widget.data = item

        # Change the category index so we have a model available
        category_index = self.widget.cbCategory.findText("Sphere")
        self.widget.cbCategory.setCurrentIndex(category_index)

        # Check the enablement/text
        assert self.widget.cmdPlot.isEnabled()
        assert self.widget.cmdPlot.text() == 'Show Plot'

        # Spying on plot update signal
        spy = QtSignalSpy(self.widget, self.widget.communicate.plotRequestedSignal)

        # Press Calculate
        QtTest.QTest.mouseClick(self.widget.cmdPlot, QtCore.Qt.LeftButton)

        # Observe cmdPlot caption did not change
        assert self.widget.cmdPlot.text() == 'Show Plot'

        # Make sure the signal has been emitted == new plot
        assert spy.count() == 1

    def testOnEmptyFit(self):
        """
        Test a 1D/2D fit with no parameters
        """
        # Set data
        test_data = Data1D(x=[1,2], y=[1,2])
        item = QtGui.QStandardItem()
        updateModelItem(item, test_data, "test")
        # Force same data into logic
        self.widget.data = item

        category_index = self.widget.cbCategory.findText("Sphere")
        self.widget.cbCategory.setCurrentIndex(category_index)

        # Test no fitting params
        self.widget.main_params_to_fit = []

        logging.error = MagicMock()

        self.widget.onFit()
        assert logging.error.called_with('no fitting parameters')
        self.widget.close()

    @pytest.mark.xfail(reason="2022-09 already broken")
    def testOnEmptyFit2(self):
        test_data = Data2D(image=[1.0, 2.0, 3.0],
                           err_image=[0.01, 0.02, 0.03],
                           qx_data=[0.1, 0.2, 0.3],
                           qy_data=[0.1, 0.2, 0.3],
                           xmin=0.1, xmax=0.3, ymin=0.1, ymax=0.3,
                           mask=[True, True, True])

        # Force same data into logic
        item = QtGui.QStandardItem()
        updateModelItem(item, test_data, "test")

        # Force same data into logic
        self.widget.data = item
        category_index = self.widget.cbCategory.findText("Sphere")
        self.widget.cbCategory.setCurrentIndex(category_index)

        self.widget.show()

        # Test no fitting params
        self.widget.main_params_to_fit = []

        logging.error = MagicMock()

        self.widget.onFit()
        assert logging.error.called_once()
        assert logging.error.called_with('no fitting parameters')
        self.widget.close()

    def notestOnFit1D(self):
        """
        Test the threaded fitting call
        """
        # Set data
        test_data = Data1D(x=[1,2], y=[1,2])
        item = QtGui.QStandardItem()
        updateModelItem(item, test_data, "test")
        # Force same data into logic
        self.widget.data = item
        category_index = self.widget.cbCategory.findText("Sphere")
        self.widget.cbCategory.setCurrentIndex(category_index)

        self.widget.show()

        # Assing fitting params
        self.widget.main_params_to_fit = ['scale']

        # Spying on status update signal
        update_spy = QtSignalSpy(self.widget, self.widget.communicate.statusBarUpdateSignal)

        with threads.deferToThread as MagicMock:
            self.widget.onFit()
            # thread called
            assert threads.deferToThread.called
            # thread method is 'compute'
            assert threads.deferToThread.call_args_list[0][0][0].__name__ == 'compute'

            # the fit button changed caption and got disabled
            # could fail if machine fast enough to finish
            #self.assertEqual(self.widget.cmdFit.text(), 'Stop fit')
            #self.assertFalse(self.widget.cmdFit.isEnabled())

            # Signal pushed up
            assert update_spy.count() == 1

        self.widget.close()

    def notestOnFit2D(self):
        """
        Test the threaded fitting call
        """
        # Set data
        test_data = Data2D(image=[1.0, 2.0, 3.0],
                           err_image=[0.01, 0.02, 0.03],
                           qx_data=[0.1, 0.2, 0.3],
                           qy_data=[0.1, 0.2, 0.3],
                           xmin=0.1, xmax=0.3, ymin=0.1, ymax=0.3,
                           mask=[True, True, True])

        # Force same data into logic
        item = QtGui.QStandardItem()
        updateModelItem(item, test_data, "test")
        # Force same data into logic
        self.widget.data = item
        category_index = self.widget.cbCategory.findText("Sphere")
        self.widget.cbCategory.setCurrentIndex(category_index)

        self.widget.show()

        # Assing fitting params
        self.widget.main_params_to_fit = ['scale']

        # Spying on status update signal
        update_spy = QtSignalSpy(self.widget, self.widget.communicate.statusBarUpdateSignal)

        with threads.deferToThread as MagicMock:
            self.widget.onFit()
            # thread called
            assert threads.deferToThread.called
            # thread method is 'compute'
            assert threads.deferToThread.call_args_list[0][0][0].__name__ == 'compute'

            # the fit button changed caption and got disabled
            #self.assertEqual(self.widget.cmdFit.text(), 'Stop fit')
            #self.assertFalse(self.widget.cmdFit.isEnabled())

            # Signal pushed up
            assert update_spy.count() == 1

    def testOnHelp(self):
        """
        Test various help pages shown in this widget
        """
        #Mock the webbrowser.open method
        self.widget.parent.showHelp = MagicMock()
        #webbrowser.open = MagicMock()

        # Invoke the action on default tab
        self.widget.onHelp()
        # Check if show() got called
        assert self.widget.parent.showHelp.called
        # Assure the filename is correct
        assert "fitting_help.html" in self.widget.parent.showHelp.call_args[0][0]

        # Change the tab to options
        self.widget.tabFitting.setCurrentIndex(1)
        self.widget.onHelp()
        # Check if show() got called
        assert self.widget.parent.showHelp.call_count == 2
        # Assure the filename is correct
        assert "residuals_help.html" in self.widget.parent.showHelp.call_args[0][0]

        # Change the tab to smearing
        self.widget.tabFitting.setCurrentIndex(2)
        self.widget.onHelp()
        # Check if show() got called
        assert self.widget.parent.showHelp.call_count == 3
        # Assure the filename is correct
        assert "resolution.html" in self.widget.parent.showHelp.call_args[0][0]

        # Change the tab to poly
        self.widget.tabFitting.setCurrentIndex(3)
        self.widget.onHelp()
        # Check if show() got called
        assert self.widget.parent.showHelp.call_count == 4
        # Assure the filename is correct
        assert "polydispersity.html" in self.widget.parent.showHelp.call_args[0][0]

        # Change the tab to magnetism
        self.widget.tabFitting.setCurrentIndex(4)
        self.widget.onHelp()
        # Check if show() got called
        assert self.widget.parent.showHelp.call_count == 5
        # Assure the filename is correct
        assert "magnetism.html" in self.widget.parent.showHelp.call_args[0][0]

    def testReadFitPage(self):
        """
        Read in the fitpage object and restore state
        """
        # Set data
        test_data = Data1D(x=[1,2], y=[1,2])
        item = QtGui.QStandardItem()
        updateModelItem(item, test_data, "test")
        # Force same data into logic
        self.widget.data = item

        # Force same data into logic
        category_index = self.widget.cbCategory.findText('Sphere')

        self.widget.cbCategory.setCurrentIndex(category_index)
        self.widget.main_params_to_fit = ['scale']
        # Invoke the tested method
        fp = self.widget.currentState()

        # Prepare modified fit page
        fp.current_model = 'onion'
        fp.is_polydisperse = True

        # Read in modified state
        self.widget.readFitPage(fp)

        # Check if the widget got updated accordingly
        assert self.widget.cbModel.currentText() == 'onion'
        assert self.widget.chkPolydispersity.isChecked()
        #Check if polidispersity tab is available
        assert self.widget.tabFitting.isTabEnabled(3)

        #Check if magnetism box and tab are disabled when 1D data is loaded
        assert not self.widget.chkMagnetism.isEnabled()
        assert not self.widget.tabFitting.isTabEnabled(4)

    # to be fixed after functionality is ready
    def notestReadFitPage2D(self):
        """
        Read in the fitpage object and restore state
        """
        # Set data

        test_data = Data2D(image=[1.0, 2.0, 3.0],
                           err_image=[0.01, 0.02, 0.03],
                           qx_data=[0.1, 0.2, 0.3],
                           qy_data=[0.1, 0.2, 0.3],
                           xmin=0.1, xmax=0.3, ymin=0.1, ymax=0.3,
                           mask=[True, True, True])

        # Force same data into logic
        self.widget.logic.data = test_data
        self.widget.data_is_loaded = True

        #item = QtGui.QStandardItem()
        #updateModelItem(item, [test_data], "test")
        # Force same data into logic
        #self.widget.logic.data = item
        #self.widget.data_is_loaded = True

        category_index = self.widget.cbCategory.findText("Cylinder")
        self.widget.cbCategory.setCurrentIndex(category_index)

        # Test no fitting params
        self.widget.main_params_to_fit = ['scale']

        # Invoke the tested method
        fp = self.widget.currentState()

        # Prepare modified fit page
        fp.current_model = 'cylinder'
        fp.is_polydisperse = True
        fp.is_magnetic = True
        fp.is2D = True

        # Read in modified state
        self.widget.readFitPage(fp)

        # Check if the widget got updated accordingly
        assert self.widget.cbModel.currentText() == 'cylinder'
        assert self.widget.chkPolydispersity.isChecked()
        assert self.widget.chkPolydispersity.isEnabled()
        #Check if polidispersity tab is available
        assert self.widget.tabFitting.isTabEnabled(3)

        #Check if magnetism box and tab are disabled when 1D data is loaded
        assert self.widget.chkMagnetism.isChecked()
        assert self.widget.chkMagnetism.isEnabled()
        assert self.widget.tabFitting.isTabEnabled(4)

    def testCurrentState(self):
        """
        Set up the fitpage with current state
        """
        # Set data
        test_data = Data1D(x=[1,2], y=[1,2])
        item = QtGui.QStandardItem()
        updateModelItem(item, test_data, "test")
        # Force same data into logic
        self.widget.data = item
        category_index = self.widget.cbCategory.findText("Sphere")
        self.widget.cbCategory.setCurrentIndex(category_index)
        model_index = self.widget.cbModel.findText("adsorbed_layer")
        self.widget.cbModel.setCurrentIndex(model_index)
        self.widget.main_params_to_fit = ['scale']

        # Invoke the tested method
        fp = self.widget.currentState()

        # Test some entries. (Full testing of fp is done in FitPageTest)
        assert isinstance(fp.data, Data1D)
        assert list(fp.data.x) == [1,2]
        assert fp.data_is_loaded
        assert fp.current_category == "Sphere"
        assert fp.current_model == "adsorbed_layer"
        assert fp.main_params_to_fit == ['scale']

    def notestPushFitPage(self):
        """
        Push current state of fitpage onto stack
        """
        # Set data
        test_data = Data1D(x=[1,2], y=[1,2])
        item = QtGui.QStandardItem()
        updateModelItem(item, test_data, "test")
        # Force same data into logic
        self.widget.data = item
        category_index = self.widget.cbCategory.findText("Sphere")
        model_index = self.widget.cbModel.findText("adsorbed_layer")
        self.widget.cbModel.setCurrentIndex(model_index)

        # Asses the initial state of stack
        assert self.widget.page_stack == []

        # Set the undo flag
        self.widget.undo_supported = True
        self.widget.cbCategory.setCurrentIndex(category_index)
        self.widget.main_params_to_fit = ['scale']

        # Check that the stack is updated
        assert len(self.widget.page_stack) == 1

        # Change another parameter
        self.widget._model_model.item(3, 1).setText("3.0")

        # Check that the stack is updated
        assert len(self.widget.page_stack) == 2

    def testPopFitPage(self):
        """
        Pop current state of fitpage from stack
        """
        # TODO: to be added when implementing UNDO/REDO
        pass

    def testOnMainPageChange(self):
        """
        Test update  values of modified parameters in models
        """
        # select model: cylinder / cylinder
        category_index = self.widget.cbCategory.findText("Cylinder")
        self.widget.cbCategory.setCurrentIndex(category_index)

        model_index = self.widget.cbModel.findText("cylinder")
        self.widget.cbModel.setCurrentIndex(model_index)

        # modify the initial value of length (different from default)
        # print self.widget.kernel_module.details['length']

        new_value = "333.0"
        self.widget._model_model.item(5, 1).setText(new_value)

        # name of modified parameter
        name_modified_param = str(self.widget._model_model.item(5, 0).text())

         # Check the model
        assert self.widget._model_model.rowCount() == 7
        assert self.widget._model_model.columnCount() == 5

        # Test the header
        #self.assertEqual(self.widget.lstParams.horizontalHeader().count(), 5)
        #self.assertFalse(self.widget.lstParams.horizontalHeader().stretchLastSection())

        assert len(self.widget._model_model.header_tooltips) == 5
        header_tooltips = ['Select parameter for fitting',
                             'Enter parameter value',
                             'Enter minimum value for parameter',
                             'Enter maximum value for parameter',
                             'Unit of the parameter']
        for column, tooltip in enumerate(header_tooltips):
             assert self.widget._model_model.headerData(column,
                QtCore.Qt.Horizontal, QtCore.Qt.ToolTipRole) == \
                         header_tooltips[column]

        # check that the value has been modified in kernel_module
        assert new_value == \
                         str(self.widget.kernel_module.params[name_modified_param])

        # check that range of variation for this parameter has NOT been changed
        assert new_value not in self.widget.kernel_module.details[name_modified_param]

    def testModelContextMenu(self):
        """
        Test the right click context menu in the parameter table
        """
        # select model: cylinder / cylinder
        category_index = self.widget.cbCategory.findText("Cylinder")
        self.widget.cbCategory.setCurrentIndex(category_index)

        model_index = self.widget.cbModel.findText("cylinder")
        self.widget.cbModel.setCurrentIndex(model_index)

        # no rows selected
        menu = self.widget.modelContextMenu([])
        assert len(menu.actions()) == 0

        # 1 row selected
        menu = self.widget.modelContextMenu([1])
        assert len(menu.actions()) == 4

        # 2 rows selected
        menu = self.widget.modelContextMenu([1,3])
        assert len(menu.actions()) == 5

        # 3 rows selected
        menu = self.widget.modelContextMenu([1,2,3])
        assert len(menu.actions()) == 4

        # over 9000
        with pytest.raises(AttributeError):
            menu = self.widget.modelContextMenu([i for i in range(9001)])
        assert len(menu.actions()) == 4

    def testShowModelContextMenu(self):
        # select model: cylinder / cylinder
        category_index = self.widget.cbCategory.findText("Cylinder")
        self.widget.cbCategory.setCurrentIndex(category_index)

        model_index = self.widget.cbModel.findText("cylinder")
        self.widget.cbModel.setCurrentIndex(model_index)

        # No selection
        logging.error = MagicMock()
        self.widget.showModelDescription = MagicMock()
        # Show the menu
        self.widget.showModelContextMenu(QtCore.QPoint(10,20))

        # Assure the description menu is shown
        assert self.widget.showModelDescription.called
        assert not logging.error.called

        # "select" two rows
        index1 = self.widget.lstParams.model().index(1, 0, QtCore.QModelIndex())
        index2 = self.widget.lstParams.model().index(2, 0, QtCore.QModelIndex())
        selection_model = self.widget.lstParams.selectionModel()
        selection_model.select(index1, selection_model.Select | selection_model.Rows)
        selection_model.select(index2, selection_model.Select | selection_model.Rows)

        QtWidgets.QMenu.exec_ = MagicMock()
        logging.error = MagicMock()
        # Show the menu
        self.widget.showModelContextMenu(QtCore.QPoint(10,20))

        # Assure the menu is shown
        assert not logging.error.called
        assert QtWidgets.QMenu.exec_.called

    def testShowMultiConstraint(self):
        """
        Test the widget update on new multi constraint
        """
        # select model: cylinder / cylinder
        category_index = self.widget.cbCategory.findText("Cylinder")
        self.widget.cbCategory.setCurrentIndex(category_index)

        model_index = self.widget.cbModel.findText("cylinder")
        self.widget.cbModel.setCurrentIndex(model_index)

        # nothing selected
        with pytest.raises(AssertionError):
            self.widget.showMultiConstraint()

        # one row selected
        index = self.widget.lstParams.model().index(1, 0, QtCore.QModelIndex())
        selection_model = self.widget.lstParams.selectionModel()
        selection_model.select(index, selection_model.Select | selection_model.Rows)
        with pytest.raises(AssertionError):
            # should also throw
            self.widget.showMultiConstraint()

        # two rows selected
        index1 = self.widget.lstParams.model().index(1, 0, QtCore.QModelIndex())
        index2 = self.widget.lstParams.model().index(3, 0, QtCore.QModelIndex())
        selection_model = self.widget.lstParams.selectionModel()
        selection_model.select(index1, selection_model.Select | selection_model.Rows)
        selection_model.select(index2, selection_model.Select | selection_model.Rows)

        # return non-OK from dialog
        QtWidgets.QDialog.exec_ = MagicMock()
        self.widget.showMultiConstraint()
        # Check the dialog called
        assert QtWidgets.QDialog.exec_.called

        # return OK from dialog
        QtWidgets.QDialog.exec_ = MagicMock(return_value=QtWidgets.QDialog.Accepted)
        spy = QtSignalSpy(self.widget, self.widget.constraintAddedSignal)

        self.widget.showMultiConstraint()

        # Make sure the signal has been emitted
        assert spy.count() == 1

        # Check the argument value - should be row '1'
        assert spy.called()[0]['args'][0] == [1]

    def testGetRowFromName(self):
        """
        Helper function for parameter table
        """
        # select model: cylinder / cylinder
        category_index = self.widget.cbCategory.findText("Cylinder")
        self.widget.cbCategory.setCurrentIndex(category_index)

        model_index = self.widget.cbModel.findText("cylinder")
        self.widget.cbModel.setCurrentIndex(model_index)

        # several random parameters
        assert self.widget.getRowFromName('scale') == 0
        assert self.widget.getRowFromName('length') == 6

    def testGetParamNames(self):
        """
        Helper function for parameter table
        """
        # select model: cylinder / cylinder
        category_index = self.widget.cbCategory.findText("Cylinder")
        self.widget.cbCategory.setCurrentIndex(category_index)

        model_index = self.widget.cbModel.findText("cylinder")
        self.widget.cbModel.setCurrentIndex(model_index)

        cylinder_params = ['scale','background','sld','sld_solvent','radius','length']
        # assure all parameters are returned
        assert self.widget.getParamNames() == cylinder_params

        # Switch to another model
        model_index = self.widget.cbModel.findText("pringle")
        self.widget.cbModel.setCurrentIndex(model_index)
        QtWidgets.qApp.processEvents()

        # make sure the parameters are different than before
        assert not (self.widget.getParamNames() == cylinder_params)

    def testAddConstraintToRow(self):
        """
        Test the constraint row add operation
        """
        # select model: cylinder / cylinder
        category_index = self.widget.cbCategory.findText("Cylinder")
        self.widget.cbCategory.setCurrentIndex(category_index)

        model_index = self.widget.cbModel.findText("cylinder")
        self.widget.cbModel.setCurrentIndex(model_index)

        # Create a constraint object
        const = Constraint(parent=None, param="scale",value=7.0)
        row = 3

        spy = QtSignalSpy(self.widget, self.widget.constraintAddedSignal)

        # Mock the modelName method
        self.widget.modelName = MagicMock(return_value='M1')

        # Mock a constraint tab
        constraint_tab = MagicMock()
        constraint_tab.constraint_accepted = False
        self.widget.parent.perspective().constraint_tab = constraint_tab

        # call the method tested
        self.widget.addConstraintToRow(constraint=const, row=row)

        # Make sure the signal has been emitted
        assert spy.count() == 1

        # Check the argument value - should be row 'row'
        assert spy.called()[0]['args'][0] == [row]

        # Assure the row has the constraint
        assert self.widget.getConstraintForRow(row) == const
        assert self.widget.rowHasConstraint(row)

        # Check that the constraint tab flag is set to True
        assert constraint_tab.constraint_accepted

        # assign complex constraint now
        const = Constraint(parent=None, param='radius', func='5*sld')
        row = 5
        # call the method tested
        self.widget.addConstraintToRow(constraint=const, row=row)

        # Make sure the signal has been emitted
        assert spy.count() == 2

        # Check the argument value - should be row 'row'
        assert spy.called()[1]['args'][0] == [row]

        # Assure the row has the constraint
        assert self.widget.getConstraintForRow(row) == const
        # and it is a complex constraint
        assert self.widget.rowHasConstraint(row)

        # Now try to add an constraint when the checking function returns an
        # error message
        FittingUtilities.checkConstraints = MagicMock(return_value="foo")

        # Mock the QMessagebox Warning
        QtWidgets.QMessageBox.critical = MagicMock()

        # Call the method tested
        self.widget.addConstraintToRow(constraint=const, row=row)

        # Check that the messagebox was called with the right error message
        QtWidgets.QMessageBox.critical.assert_called_with(
            self.widget,
            "Inconsistent constraint",
            "foo",
            QtWidgets.QMessageBox.Ok,
        )

        # Make sure no signal was emitted
        assert spy.count() == 2
        # Check that constraint tab flag is set to False
        assert not constraint_tab.constraint_accepted


    def testAddSimpleConstraint(self):
        """
        Test the constraint add operation
        """
        # select model: cylinder / cylinder
        category_index = self.widget.cbCategory.findText("Cylinder")
        self.widget.cbCategory.setCurrentIndex(category_index)

        model_index = self.widget.cbModel.findText("cylinder")
        self.widget.cbModel.setCurrentIndex(model_index)

        # select two rows
        row1 = 1
        row2 = 4
        index1 = self.widget.lstParams.model().index(row1, 0, QtCore.QModelIndex())
        index2 = self.widget.lstParams.model().index(row2, 0, QtCore.QModelIndex())
        selection_model = self.widget.lstParams.selectionModel()
        selection_model.select(index1, selection_model.Select | selection_model.Rows)
        selection_model.select(index2, selection_model.Select | selection_model.Rows)

        # define the signal spy
        spy = QtSignalSpy(self.widget, self.widget.constraintAddedSignal)

        # call the method tested
        self.widget.addSimpleConstraint()

        # Make sure the signal has been emitted
        assert spy.count() == 2

        # Check the argument value
        assert spy.called()[0]['args'][0] == [row1]
        assert spy.called()[1]['args'][0] == [row2]

    def testDeleteConstraintOnParameter(self):
        """
        Test the constraint deletion in model/view
        """
        # select model: cylinder / cylinder
        category_index = self.widget.cbCategory.findText("Cylinder")
        self.widget.cbCategory.setCurrentIndex(category_index)

        model_index = self.widget.cbModel.findText("cylinder")
        self.widget.cbModel.setCurrentIndex(model_index)

        row1 = 1
        row2 = 5

        param1 = "background"
        param2 = "radius"

        #default_value1 = "0.001"
        default_value2 = "20"

        # select two rows
        index1 = self.widget.lstParams.model().index(row1, 0, QtCore.QModelIndex())
        index2 = self.widget.lstParams.model().index(row2, 0, QtCore.QModelIndex())
        selection_model = self.widget.lstParams.selectionModel()
        selection_model.select(index1, selection_model.Select | selection_model.Rows)
        selection_model.select(index2, selection_model.Select | selection_model.Rows)

        # add constraints
        self.widget.addSimpleConstraint()

        # deselect the model
        selection_model.clear()

        # select a single row
        selection_model.select(index1, selection_model.Select | selection_model.Rows)

        # delete one of the constraints
        self.widget.deleteConstraintOnParameter(param=param1)

        # see that the other constraint is still present
        cons = self.widget.getConstraintForRow(row2)
        assert cons.param == param2
        assert cons.value == default_value2

        # kill the other constraint
        self.widget.deleteConstraint()

        # see that the other constraint is still present
        assert self.widget.getConstraintsForModel() == [(param2, None)]

    def testGetConstraintForRow(self):
        """
        Helper function for parameter table
        """
        # tested extensively elsewhere
        pass

    def testRowHasConstraint(self):
        """
        Helper function for parameter table
        """
        # select model: cylinder / cylinder
        category_index = self.widget.cbCategory.findText("Cylinder")
        self.widget.cbCategory.setCurrentIndex(category_index)

        model_index = self.widget.cbModel.findText("cylinder")
        self.widget.cbModel.setCurrentIndex(model_index)

        row1 = 1
        row2 = 5

        # select two rows
        index1 = self.widget.lstParams.model().index(row1, 0, QtCore.QModelIndex())
        index2 = self.widget.lstParams.model().index(row2, 0, QtCore.QModelIndex())
        selection_model = self.widget.lstParams.selectionModel()
        selection_model.select(index1, selection_model.Select | selection_model.Rows)
        selection_model.select(index2, selection_model.Select | selection_model.Rows)

        # add constraints
        self.widget.addSimpleConstraint()

        con_list = [False, True, False, False, False, True, False]
        new_list = []
        for row in range(self.widget._model_model.rowCount()):
            new_list.append(self.widget.rowHasConstraint(row))

        assert new_list == con_list

    def testRowHasActiveConstraint(self):
        """
        Helper function for parameter table
        """
        # select model: cylinder / cylinder
        category_index = self.widget.cbCategory.findText("Cylinder")
        self.widget.cbCategory.setCurrentIndex(category_index)

        model_index = self.widget.cbModel.findText("cylinder")
        self.widget.cbModel.setCurrentIndex(model_index)

        row1 = 1
        row2 = 5

        # select two rows
        index1 = self.widget.lstParams.model().index(row1, 0, QtCore.QModelIndex())
        index2 = self.widget.lstParams.model().index(row2, 0, QtCore.QModelIndex())
        selection_model = self.widget.lstParams.selectionModel()
        selection_model.select(index1, selection_model.Select | selection_model.Rows)
        selection_model.select(index2, selection_model.Select | selection_model.Rows)

        # add constraints
        self.widget.addSimpleConstraint()

        # deactivate the first constraint
        constraint_objects = self.widget.getConstraintObjectsForModel()
        constraint_objects[0].active = False

        con_list = [False, False, False, False, False, True, False]
        new_list = []
        for row in range(self.widget._model_model.rowCount()):
            new_list.append(self.widget.rowHasActiveConstraint(row))

        assert new_list == con_list

    def testGetConstraintsForModel(self):
        """
        Test the constraint getter for constraint texts
        """
        # select model: cylinder / cylinder
        category_index = self.widget.cbCategory.findText("Cylinder")
        self.widget.cbCategory.setCurrentIndex(category_index)

        model_index = self.widget.cbModel.findText("cylinder")
        self.widget.cbModel.setCurrentIndex(model_index)

        # no constraints
        assert self.widget.getConstraintsForModel() == []

        row1 = 1
        row2 = 5

        param1 = "background"
        param2 = "radius"

        default_value1 = "0.001"
        default_value2 = "20"

        # select two rows
        index1 = self.widget.lstParams.model().index(row1, 0, QtCore.QModelIndex())
        index2 = self.widget.lstParams.model().index(row2, 0, QtCore.QModelIndex())
        selection_model = self.widget.lstParams.selectionModel()
        selection_model.select(index1, selection_model.Select | selection_model.Rows)
        selection_model.select(index2, selection_model.Select | selection_model.Rows)

        # add constraints
        self.widget.addSimpleConstraint()

        # simple constraints
        # self.assertEqual(self.widget.getConstraintsForModel(), [('background', '0.001'), ('radius', '20')])
        cons = self.widget.getConstraintForRow(row1)
        assert cons.param == param1
        assert cons.value == default_value1
        cons = self.widget.getConstraintForRow(row2)
        assert cons.param == param2
        assert cons.value == default_value2

        objects = self.widget.getConstraintObjectsForModel()
        assert len(objects) == 2
        assert objects[1].value == default_value2
        assert objects[0].param == param1

        row = 0
        param = "scale"
        func = "5*sld"

        # add complex constraint
        const = Constraint(parent=None, param=param, func=func)
        self.widget.addConstraintToRow(constraint=const, row=row)
        #self.assertEqual(self.widget.getConstraintsForModel(),[('scale', '5*sld'), ('background', '0.001'), ('radius', None)])
        cons = self.widget.getConstraintForRow(row2)
        assert cons.param == param2
        assert cons.value == default_value2

        objects = self.widget.getConstraintObjectsForModel()
        assert len(objects) == 3
        assert objects[0].func == func

    def testReplaceConstraintName(self):
        """
        Test the replacement of constraint moniker
        """
        # select model: cylinder / cylinder
        category_index = self.widget.cbCategory.findText("Cylinder")
        self.widget.cbCategory.setCurrentIndex(category_index)

        model_index = self.widget.cbModel.findText("cylinder")
        self.widget.cbModel.setCurrentIndex(model_index)

        old_name = 'M5'
        new_name = 'poopy'
        # add complex constraint
        const = Constraint(parent=None, param='scale', func='%s.5*sld'%old_name)
        row = 0
        self.widget.addConstraintToRow(constraint=const, row=row)

        # Replace 'm5' with 'poopy'
        self.widget.replaceConstraintName(old_name, new_name)

        assert self.widget.getConstraintsForModel() == [('scale', 'poopy.5*sld')]


    def testRetainParametersBetweenModelChange(self):
        """
        Test constantess of model parameters on model change
        """
        # select model: cylinder / cylinder
        category_index = self.widget.cbCategory.findText("Cylinder")
        self.widget.cbCategory.setCurrentIndex(category_index)

        model_index = self.widget.cbModel.findText("cylinder")
        self.widget.cbModel.setCurrentIndex(model_index)

        # modify the initial value of radius (different from default)
        new_value = "333.0"
        self.widget._model_model.item(5, 1).setText(new_value)

        # change parameter in the same category
        model_index = self.widget.cbModel.findText("barbell")
        self.widget.cbModel.setCurrentIndex(model_index)

        # see if radius is the same as set
        row = self.widget.getRowFromName("radius")
        assert self.widget._model_model.item(row, 1).text() == "333"

        # Now, change not just model but a category as well
        # cylinder / cylinder
        category_index = self.widget.cbCategory.findText("Sphere")
        self.widget.cbCategory.setCurrentIndex(category_index)

        model_index = self.widget.cbModel.findText("sphere")
        self.widget.cbModel.setCurrentIndex(model_index)

        # see if radius is still the same
        row = self.widget.getRowFromName("radius")
        assert int(self.widget._model_model.item(row, 1).text()) == 333

    @pytest.mark.xfail(reason="2022-09 already broken")
    def testOnParameterPaste(self):
        """
        Test response of the widget to clipboard content
        paste request
        """
        self.widget.updatePageWithParameters = MagicMock()
        QtWidgets.QMessageBox.exec_ = MagicMock()
        cb = QtWidgets.QApplication.clipboard()

        # test bad clipboard
        cb.setText("bad clipboard")
        self.widget.onParameterPaste()
        QtWidgets.QMessageBox.exec_.assert_called_once()
        self.widget.updatePageWithParameters.assert_not_called()

        # Test correct clipboard
        cb.setText("sasview_parameter_values:model_name,core_shell_bicelle:scale,False,1.0,None,0.0,inf,()")
        self.widget.onParameterPaste()
        self.widget.updatePageWithParameters.assert_called_once()

    def testGetConstraintsForFitting(self):
        """
        Test the deactivation of constraints when trying to fit a single page
        with constraints relying on other pages
        """
        # mock the constraint getter
        self.widget.getComplexConstraintsForModel = MagicMock(return_value=[
            ('scale', 'M2.background')])
        # mock isConstraintMultimodel so that our constraint is multi-model
        self.widget.isConstraintMultimodel = MagicMock(return_value=True)
        # Mock a constraint tab
        constraint_tab = MagicMock()
        self.widget.parent.perspective().constraint_tab = constraint_tab
        # instanciate a constraint
        constraint = Constraint(parent=None, param="scale", value=7.0)
        self.widget.getConstraintForRow = MagicMock(return_value=constraint)
        # mock the messagebox
        QtWidgets.QMessageBox.exec_ = MagicMock()

        # select a model
        category_index = self.widget.cbCategory.findText("Cylinder")
        self.widget.cbCategory.setCurrentIndex(category_index)

        model_index = self.widget.cbModel.findText("cylinder")
        self.widget.cbModel.setCurrentIndex(model_index)

        # Call the method
        self.widget.getConstraintsForFitting()
        # Check that QMessagebox was called
        QtWidgets.QMessageBox.exec_.assert_called_once()
        # Constraint should be inactive
        assert constraint.active == False
        # Check that the uncheckConstraint method was called
        constraint_tab.uncheckConstraint.assert_called_with("M1:scale")

    def testQRangeReset(self):
        ''' Test onRangeReset w/ and w/o data loaded '''
        assert self.widget.options_widget.qmin == \
                         self.widget.options_widget.QMIN_DEFAULT
        assert self.widget.options_widget.qmax == \
                         self.widget.options_widget.QMAX_DEFAULT
        assert self.widget.options_widget.npts == \
                         self.widget.options_widget.NPTS_DEFAULT
        assert self.widget.options_widget.npts == \
                         self.widget.options_widget.npts_fit
        # Set values to non-defaults and check they updated
        self.widget.options_widget.updateMinQ(0.01)
        self.widget.options_widget.updateMaxQ(0.02)
        assert float(self.widget.options_widget.qmin) == 0.01
        assert float(self.widget.options_widget.qmax) == 0.02
        # Click the reset range button and check the values went back to defaults
        self.widget.options_widget.cmdReset.click()
        assert self.widget.options_widget.qmin == \
                         self.widget.options_widget.QMIN_DEFAULT
        assert self.widget.options_widget.qmax == \
                         self.widget.options_widget.QMAX_DEFAULT
        assert self.widget.options_widget.npts == \
                         self.widget.options_widget.NPTS_DEFAULT
        # Load data into tab and check new limits
        data = Data1D(x=[1,2], y=[1,2])
        GuiUtils.dataFromItem = MagicMock(return_value=data)
        item = QtGui.QStandardItem("test")
        widget_with_data = FittingWidget(dummy_manager(), data=item, tab_id=3)
        assert widget_with_data.options_widget.qmin == min(data.x)
        assert widget_with_data.options_widget.qmax == max(data.x)
        assert widget_with_data.options_widget.npts == len(data.x)
        # Set values to non-defaults and check they updated
        self.widget.options_widget.updateMinQ(0.01)
        self.widget.options_widget.updateMaxQ(0.02)
        assert float(self.widget.options_widget.qmin) == 0.01
        assert float(self.widget.options_widget.qmax) == 0.02
        # Click the reset range button and check the values went back to data values
        self.widget.options_widget.cmdReset.click()
        assert widget_with_data.options_widget.qmin == min(data.x)
        assert widget_with_data.options_widget.qmax == max(data.x)
        assert widget_with_data.options_widget.npts == len(data.x)


if __name__ == "__main__":
    unittest.main()
