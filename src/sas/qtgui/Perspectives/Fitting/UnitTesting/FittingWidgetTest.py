import glob
import logging
import os
import time
import webbrowser
from unittest.mock import MagicMock

import pytest
from PySide6 import QtCore, QtGui, QtTest, QtWidgets
from twisted.internet import threads

from sasmodels.sasview_model import load_custom_model

# Local
from sas import config
from sas.qtgui.Perspectives.Fitting import FittingUtilities, FittingWidget
from sas.qtgui.Perspectives.Fitting.Constraint import Constraint
from sas.qtgui.Perspectives.Fitting.ModelThread import Calc2D
from sas.qtgui.Plotting.PlotterData import Data1D, Data2D
from sas.qtgui.UnitTesting.TestUtils import QtSignalSpy
from sas.qtgui.Utilities import GuiUtils
from sas.sascalc.fit.models import ModelManager, ModelManagerBase


class dummy_manager:
    HELP_DIRECTORY_LOCATION = "html"
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

class FittingWidgetMod(FittingWidget.FittingWidget):
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

class FittingWidgetTest:
    """Test the fitting widget GUI"""

    @pytest.fixture(autouse=True)
    def widget(self, qapp, mocker):
        '''Create/Destroy the GUI'''
        w = FittingWidgetMod(dummy_manager())
        mocker.patch.object(FittingUtilities, 'checkConstraints', return_value=None)
        yield w
        """Destroy the GUI"""
        w.close()
        del w

    def testDefaults(self, widget):
        """Test the GUI in its default state"""
        assert isinstance(widget, QtWidgets.QWidget)
        assert widget.windowTitle() == "Fitting"
        assert widget.sizePolicy().Policy() == QtWidgets.QSizePolicy.Fixed
        assert isinstance(widget.lstParams.model(), QtGui.QStandardItemModel)
        assert isinstance(widget.lstPoly.model(), QtGui.QStandardItemModel)
        assert isinstance(widget.lstMagnetic.model(), QtGui.QStandardItemModel)
        assert not widget.cbModel.isEnabled()
        assert not widget.cbStructureFactor.isEnabled()
        assert not widget.cmdFit.isEnabled()
        assert widget.acceptsData()
        assert not widget.data_is_loaded

    def testSelectCategoryDefault(self, widget):
        """
        Test if model categories have been loaded properly
        """
        fittingWindow =  widget

        #Test loading from json categories
        category_list = list(fittingWindow.master_category_dict.keys())

        for category in category_list:
            assert fittingWindow.cbCategory.findText(category) != -1

        #Test what is current text in the combobox
        assert fittingWindow.cbCategory.currentText() == FittingWidget.CATEGORY_DEFAULT

    def testWidgetWithData(self, widget, mocker):
        """
        Test the instantiation of the widget with initial data
        """
        data = Data1D(x=[1,2], y=[1,2])
        mocker.patch.object(GuiUtils, 'dataFromItem', return_value=data)
        item = QtGui.QStandardItem("test")

        widget_with_data = FittingWidgetMod(dummy_manager(), data=item, tab_id=3)

        assert widget_with_data.data == data
        assert widget_with_data.data_is_loaded
        # assert widget_with_data.cmdFit.isEnabled()
        assert not widget_with_data.acceptsData()

    def testSelectPolydispersity(self, widget):
        """
        Test if models have been loaded properly
        """
        fittingWindow =  widget

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
    def testSelectMagnetism(self, widget):
        """
        Test if models have been loaded properly
        """
        fittingWindow =  widget

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

    def testSelectStructureFactor(self, widget):
        """
        Test if structure factors have been loaded properly, including plugins also classified as a structure factor.
        """
        fittingWindow =  widget

        #Test for existence in combobox
        assert fittingWindow.cbStructureFactor.findText("stickyhardsphere") != -1
        assert fittingWindow.cbStructureFactor.findText("hayter_msa") != -1
        assert fittingWindow.cbStructureFactor.findText("squarewell") != -1
        assert fittingWindow.cbStructureFactor.findText("hardsphere") != -1
        assert fittingWindow.cbStructureFactor.findText("plugin_structure_template") != -1
        assert fittingWindow.cbStructureFactor.findText("plugin_template") == -1

        #Test what is current text in the combobox
        assert fittingWindow.cbCategory.currentText(), "None"

    def testSignals(self, widget):
        """
        Test the widget emitted signals
        """
        pass

    @pytest.mark.xfail(reason="2022-09 already broken")
    def testSelectCategory(self, widget):
        """
        Assure proper behaviour on changing category
        """
        widget.show()
        assert widget._previous_category_index == 0
        # confirm the model combo contains no models
        assert widget.cbModel.count() == 0

        # invoke the method by changing the index
        category_index = widget.cbCategory.findText("Shape Independent")
        widget.cbCategory.setCurrentIndex(category_index)
        model_index = widget.cbModel.findText("be_polyelectrolyte")
        widget.cbModel.setCurrentIndex(model_index)

        # test the model combo content
        assert widget.cbModel.count() == 30

        # Try to change back to default
        widget.cbCategory.setCurrentIndex(0)

        # Observe no such luck
        assert widget.cbCategory.currentIndex() == 6
        assert widget.cbModel.count() == 30

        # Set the structure factor
        structure_index=widget.cbCategory.findText(FittingWidget.CATEGORY_STRUCTURE)
        widget.cbCategory.setCurrentIndex(structure_index)
        # check the enablement of controls
        assert not widget.cbModel.isEnabled()
        assert widget.cbStructureFactor.isEnabled()

    def testSelectModel(self, widget, mocker):
        """
        Assure proper behaviour on changing model
        """
        widget.show()
        # Change the category index so we have some models
        category_index = widget.cbCategory.findText("Shape Independent")
        widget.cbCategory.setCurrentIndex(category_index)
        model_index = widget.cbModel.findText("be_polyelectrolyte")
        widget.cbModel.setCurrentIndex(model_index)
        QtWidgets.qApp.processEvents()

        # check the enablement of controls
        assert widget.cbModel.isEnabled()
        assert not widget.cbStructureFactor.isEnabled()

        # set up the model update spy
        # spy = QtSignalSpy(widget._model_model, widget._model_model.itemChanged)

        # mock the tested methods
        mocker.patch.object(widget, 'SASModelToQModel')
        mocker.patch.object(widget, 'createDefaultDataset')
        mocker.patch.object(widget, 'calculateQGridForModel')
        #
        # Now change the model
        widget.cbModel.setCurrentIndex(4)
        assert widget.cbModel.currentText() == 'dab'

        # No data sent -> no index set, only createDefaultDataset called
        assert widget.createDefaultDataset.called
        assert widget.SASModelToQModel.called
        assert not widget.calculateQGridForModel.called

        # Let's tell the widget that data has been loaded
        widget.data_is_loaded = True
        # Reset the sasmodel index
        widget.cbModel.setCurrentIndex(2)
        assert widget.cbModel.currentText() == 'broad_peak'

        # Observe calculateQGridForModel called
        assert widget.calculateQGridForModel.called

    @pytest.mark.xfail(reason="2022-09 already broken")
    def testSelectFactor(self, widget):
        """
        Assure proper behaviour on changing structure factor
        """
        widget.show()
        # Change the category index so we have some models
        category_index = widget.cbCategory.findText("Cylinder")
        widget.cbCategory.setCurrentIndex(category_index)
        # Change the model to one that supports structure factors
        model_index = widget.cbModel.findText('cylinder')
        widget.cbModel.setCurrentIndex(model_index)

        # Check that the factor combo is active and the default is chosen
        assert widget.cbStructureFactor.isEnabled()
        assert widget.cbStructureFactor.currentText() == FittingWidget.STRUCTURE_DEFAULT

        # We have this many rows in the model
        rowcount = widget._model_model.rowCount()
        #assert widget._model_model.rowCount() == 8

        # Change structure factor to something more exciting
        structure_index = widget.cbStructureFactor.findText('squarewell')
        widget.cbStructureFactor.setCurrentIndex(structure_index)

        # We have 3 more param rows now (radius_effective is removed), and new headings
        assert widget._model_model.rowCount() == rowcount+7

        # Switch models
        widget.cbModel.setCurrentIndex(0)

        # Observe factor doesn't reset to None
        assert widget.cbStructureFactor.currentText() == 'squarewell'

        # Switch category to structure factor
        structure_index=widget.cbCategory.findText(FittingWidget.CATEGORY_STRUCTURE)
        widget.cbCategory.setCurrentIndex(structure_index)
        # Observe the correct enablement
        assert widget.cbStructureFactor.isEnabled()
        assert not widget.cbModel.isEnabled()
        assert widget._model_model.rowCount() == 0

        # Choose the last factor
        last_index = widget.cbStructureFactor.count()
        widget.cbStructureFactor.setCurrentIndex(last_index-1)
        # Do we have all the rows (incl. radius_effective & heading row)?
        assert widget._model_model.rowCount() == 5

        # Are the command buttons properly enabled?
        assert widget.cmdPlot.isEnabled()
        assert not widget.cmdFit.isEnabled()

    def testReadCategoryInfo(self, widget):
        """
        Check the category file reader
        """
        # Tested in default checks
        pass

    def testUpdateParamsFromModel(self, widget):
        """
        Checks the sasmodel parameter update from QModel items
        """
        # Tested in default checks
        pass

    def testCreateTheoryIndex(self, widget):
        """
        Test the data->QIndex conversion
        """
        # set up the model update spy
        spy = QtSignalSpy(widget._model_model, widget.communicate.updateTheoryFromPerspectiveSignal)

        widget.show()
        # Change the category index so we have some models
        widget.cbCategory.setCurrentIndex(1)

        # Create the index
        widget.createTheoryIndex(Data1D(x=[1,2], y=[1,2]))

        # Make sure the signal has been emitted
        assert spy.count() == 1

        # Check the argument type
        assert isinstance(spy.called()[0]['args'][0], QtGui.QStandardItem)

    def testCalculateQGridForModel(self, widget, mocker):
        """
        Check that the fitting 1D data object is ready
        """

        if config.USING_TWISTED:
            # Mock the thread creation
            mocker.patch.object(threads, 'deferToThread')
            # Model for theory
            widget.SASModelToQModel("cylinder")
            # Call the tested method
            widget.calculateQGridForModel()
            time.sleep(1)
            # Test the mock
            assert threads.deferToThread.called
            assert threads.deferToThread.call_args_list[0][0][0].__name__ == "compute"
        else:
            mocker.patch.object(Calc2D, 'queue')
            # Model for theory
            widget.SASModelToQModel("cylinder")
            # Call the tested method
            widget.calculateQGridForModel()
            time.sleep(1)
            # Test the mock
            assert Calc2D.queue.called

    def testCalculateResiduals(self, widget):
        """
        Check that the residuals are calculated and plots updated
        """
        test_data = Data1D(x=[1,2], y=[1,2])

        # Model for theory
        widget.SASModelToQModel("cylinder")
        # Invoke the tested method
        widget.calculateResiduals(test_data)
        # Check the Chi2 value - should be undetermined
        assert widget.lblChi2Value.text() == '---'

        # Force same data into logic
        widget.logic.data = test_data
        widget.calculateResiduals(test_data)
        # Now, the difference is 0, as data is the same
        assert widget.lblChi2Value.text() == '---'

        # Change data
        test_data_2 = Data1D(x=[1,2], y=[2.1,3.49])
        widget.logic.data = test_data_2
        widget.calculateResiduals(test_data)
        # Now, the difference is non-zero
        assert widget.lblChi2Value.text() == '---'

    def testSetPolyModel(self, widget):
        """
        Test the polydispersity model setup
        """
        widget.show()
        # Change the category index so we have a model with no poly
        category_index = widget.cbCategory.findText("Shape Independent")
        widget.cbCategory.setCurrentIndex(category_index)
        model_index = widget.cbModel.findText("be_polyelectrolyte")
        widget.cbModel.setCurrentIndex(model_index)

        # Check the poly model
        assert widget._poly_model.rowCount() == 0
        assert widget._poly_model.columnCount() == 0

        # Change the category index so we have a model available
        widget.cbCategory.setCurrentIndex(2)
        widget.cbModel.setCurrentIndex(1)

        # Check the poly model
        assert widget._poly_model.rowCount() == 4
        assert widget._poly_model.columnCount() == 8

        # Test the header
        assert widget.lstPoly.horizontalHeader().count() == 8
        assert not widget.lstPoly.horizontalHeader().stretchLastSection()

        # Test tooltips
        assert len(widget._poly_model.header_tooltips) == 8

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
             assert widget._poly_model.headerData( column,
                QtCore.Qt.Horizontal, QtCore.Qt.ToolTipRole) == \
                         header_tooltips[column]

        # Test presence of comboboxes in last column
        for row in range(widget._poly_model.rowCount()):
            func_index = widget._poly_model.index(row, 6)
            assert isinstance(widget.lstPoly.indexWidget(func_index), QtWidgets.QComboBox)
            assert 'Distribution of' in widget._poly_model.item(row, 0).text()
        #widget.close()

    def testPolyModelChange(self, widget):
        """
        Polydispersity model changed - test all possible scenarios
        """
        widget.show()
        # Change the category index so we have a model with polydisp
        category_index = widget.cbCategory.findText("Cylinder")
        widget.cbCategory.setCurrentIndex(category_index)
        model_index = widget.cbModel.findText("barbell")
        widget.cbModel.setCurrentIndex(model_index)

        # click on a poly parameter checkbox
        index = widget._poly_model.index(0,0)

        # Set the checbox
        widget._poly_model.item(0,0).setCheckState(2)
        # Assure the parameter is added
        assert widget.poly_params_to_fit == ['radius_bell.width']
        # Check that it's value has not changed (reproduce the polydispersity checkbox bug)
        assert widget.poly_params['radius_bell.width'] == 0.0

        # Add another parameter
        widget._poly_model.item(2,0).setCheckState(2)
        # Assure the parameters are added
        assert widget.poly_params_to_fit == ['radius_bell.width', 'length.width']

        # Change the min/max values
        assert widget.logic.kernel_module.details['radius_bell.width'][1] == 0.0
        widget._poly_model.item(0,2).setText("1.0")
        assert widget.logic.kernel_module.details['radius_bell.width'][1] == 1.0
        # Check that changing the polydispersity min/max value doesn't affect the paramer min/max
        assert widget.logic.kernel_module.details['radius_bell'][1] == 0.0

        #widget.show()
        #QtWidgets.QApplication.exec_()

        # Change the number of points
        assert widget.poly_params['radius_bell.npts'] == 35
        widget._poly_model.item(0,4).setText("22")
        assert widget.poly_params['radius_bell.npts'] == 22
        # test that sasmodel is updated with the new value
        assert widget.logic.kernel_module.getParam('radius_bell.npts') == 22

        # Change the pd value
        assert widget.poly_params['radius_bell.width'] == 0.0
        widget._poly_model.item(0,1).setText("0.8")
        assert widget.poly_params['radius_bell.width'] == pytest.approx(0.8, abs=1e-7)
        # Test that sasmodel is updated with the new value
        assert widget.logic.kernel_module.getParam('radius_bell.width') == pytest.approx(0.8, abs=1e-7)

        # Uncheck pd in the fitting widget
        widget.chkPolydispersity.setCheckState(2)
        widget.chkPolydispersity.click()
        # Should not change the value of the qt model
        assert widget.poly_params['radius_bell.width'] == pytest.approx(0.8, abs=1e-7)
        # sasmodel should be set to 0
        assert widget.logic.kernel_module.getParam('radius_bell.width') == pytest.approx(0.0, abs=1e-7)

        # try something stupid
        widget._poly_model.item(0,4).setText("butt")
        # see that this didn't annoy the control at all
        assert widget.poly_params['radius_bell.npts'] == 22

        # Change the number of sigmas
        assert widget.poly_params['radius_bell.nsigmas'] == 3
        widget._poly_model.item(0,5).setText("222")
        assert widget.poly_params['radius_bell.nsigmas'] == 222
        # try something stupid again
        widget._poly_model.item(0,4).setText("beer")
        # no efect
        assert widget.poly_params['radius_bell.nsigmas'] == 222

    def testOnPolyComboIndexChange(self, widget, mocker):
        """
        Test the slot method for polydisp. combo box index change
        """
        widget.show()
        # Change the category index so we have a model with polydisp
        category_index = widget.cbCategory.findText("Cylinder")
        widget.cbCategory.setCurrentIndex(category_index)
        model_index = widget.cbModel.findText("barbell")
        widget.cbModel.setCurrentIndex(model_index)

        # call method with default settings
        widget.onPolyComboIndexChange('gaussian', 0)
        # check values
        assert widget.logic.kernel_module.getParam('radius_bell.npts') == 35
        assert widget.logic.kernel_module.getParam('radius_bell.nsigmas') == 3
        # Change the index
        widget.onPolyComboIndexChange('rectangle', 0)
        # check values
        assert widget.poly_params['radius_bell.npts'] == 35
        assert widget.poly_params['radius_bell.nsigmas'] == pytest.approx(1.73205, abs=1e-5)
        # Change the index
        widget.onPolyComboIndexChange('lognormal', 0)
        # check values
        assert widget.poly_params['radius_bell.npts'] == 80
        assert widget.poly_params['radius_bell.nsigmas'] == 8
        # Change the index
        widget.onPolyComboIndexChange('schulz', 0)
        # check values
        assert widget.poly_params['radius_bell.npts'] == 80
        assert widget.poly_params['radius_bell.nsigmas'] == 8

        # mock up file load
        mocker.patch.object(widget, 'loadPolydispArray')
        # Change to 'array'
        widget.onPolyComboIndexChange('array', 0)
        # See the mock fire
        assert widget.loadPolydispArray.called

    @pytest.mark.xfail(reason="2022-09 already broken - input file issue")
    def testLoadPolydispArray(self, widget, mocker):
        """
        Test opening of the load file dialog for 'array' polydisp. function
        """

        # open a non-existent file
        filename = os.path.join("UnitTesting", "testdata_noexist.txt")
        with pytest.raises(OSError):
            os.stat(filename)
        mocker.patch.object(QtWidgets.QFileDialog, 'getOpenFileName', return_value=(filename,''))
        widget.show()
        # Change the category index so we have a model with polydisp
        category_index = widget.cbCategory.findText("Cylinder")
        widget.cbCategory.setCurrentIndex(category_index)
        model_index = widget.cbModel.findText("barbell")
        widget.cbModel.setCurrentIndex(model_index)

        widget.onPolyComboIndexChange('array', 0)
        # check values - unchanged since the file doesn't exist
        assert widget._poly_model.item(0, 1).isEnabled()

        # good file
        # TODO: this depends on the working directory being src/sas/qtgui,
        # TODO: which isn't convenient if you want to run this test suite
        # TODO: individually
        filename = os.path.join("UnitTesting", "testdata.txt")
        try:
            os.stat(filename)
        except OSError:
            assert False, "testdata.txt does not exist"
        mocker.patch.object(QtWidgets.QFileDialog, 'getOpenFileName', return_value=(filename,''))

        widget.onPolyComboIndexChange('array', 0)
        # check values - disabled control, present weights
        assert not widget._poly_model.item(0, 1).isEnabled()
        assert widget.disp_model.weights[0] == 2.83954
        assert len(widget.disp_model.weights) == 19
        assert len(widget.disp_model.values) == 19
        assert widget.disp_model.values[0] == 0.0
        assert widget.disp_model.values[18] == 3.67347

    @pytest.mark.xfail(reason="2022-09 already broken")
    def testSetMagneticModel(self, widget):
        """
        Test the magnetic model setup
        """
        widget.show()
        # Change the category index so we have a model available
        category_index = widget.cbCategory.findText("Sphere")
        widget.cbCategory.setCurrentIndex(category_index)
        model_index = widget.cbModel.findText("adsorbed_layer")
        widget.cbModel.setCurrentIndex(model_index)

        # Check the magnetic model
        assert widget._magnet_model.rowCount() == 9
        assert widget._magnet_model.columnCount() == 5

        # Test the header
        assert widget.lstMagnetic.horizontalHeader().count() == 5
        assert not widget.lstMagnetic.horizontalHeader().stretchLastSection()

        #Test tooltips
        assert len(widget._magnet_model.header_tooltips) == 5

        header_tooltips = ['Select parameter for fitting',
                           'Enter parameter value',
                           'Enter minimum value for parameter',
                           'Enter maximum value for parameter',
                           'Unit of the parameter']
        for column, tooltip in enumerate(header_tooltips):
             assert widget._magnet_model.headerData(column,
                QtCore.Qt.Horizontal, QtCore.Qt.ToolTipRole) == \
                         header_tooltips[column]

        # Test rows
        for row in range(widget._magnet_model.rowCount()):
            func_index = widget._magnet_model.index(row, 0)
            assert '_' in widget._magnet_model.item(row, 0).text()


    def testAddExtraShells(self, widget):
        """
        Test how the extra shells are presented
        """
        pass

    def testModifyShellsInList(self, widget):
        """
        Test the additional rows added by modifying the shells combobox
        """
        widget.show()
        # Change the model to multi shell
        category_index = widget.cbCategory.findText("Sphere")
        widget.cbCategory.setCurrentIndex(category_index)
        model_index = widget.cbModel.findText("core_multi_shell")
        widget.cbModel.setCurrentIndex(model_index)

        # Assure we have the combobox available
        cbox_row = widget._n_shells_row
        func_index = widget._model_model.index(cbox_row, 1)
        assert isinstance(widget.lstParams.indexWidget(func_index), QtWidgets.QComboBox)

        # get number of rows before changing shell count
        last_row = widget._model_model.rowCount()

        # Change the combo box index
        widget.lstParams.indexWidget(func_index).setCurrentIndex(3)

        # Check that the number of rows increased
        # (note that n == 1 by default in core_multi_shell so this increases index by 2)
        more_rows = widget._model_model.rowCount() - last_row
        assert more_rows == 4 # 4 new rows: 2 params per index

        # Set to 0
        widget.lstParams.indexWidget(func_index).setCurrentIndex(0)
        assert widget._model_model.rowCount() == last_row - 2

    @pytest.mark.xfail(reason="2022-09 already broken")
    def testPlotTheory(self, widget):
        """
        See that theory item can produce a chart
        """
        # By default, the compute/plot button is disabled
        assert not widget.cmdPlot.isEnabled()
        assert widget.cmdPlot.text() == 'Show Plot'

        # Assign a model
        widget.show()
        # Change the category index so we have a model available
        category_index = widget.cbCategory.findText("Sphere")
        widget.cbCategory.setCurrentIndex(category_index)
        model_index = widget.cbModel.findText("adsorbed_layer")
        widget.cbModel.setCurrentIndex(model_index)

        # Check the enablement/text
        assert widget.cmdPlot.isEnabled()
        assert widget.cmdPlot.text() == 'Calculate'

        # Spying on plot update signal
        spy = QtSignalSpy(widget, widget.communicate.plotRequestedSignal)

        # Press Calculate
        QtTest.QTest.mouseClick(widget.cmdPlot, QtCore.Qt.LeftButton)

        # Observe cmdPlot caption change
        assert widget.cmdPlot.text() == 'Show Plot'

        # Make sure the signal has NOT been emitted
        assert spy.count() == 0

        # Click again
        QtTest.QTest.mouseClick(widget.cmdPlot, QtCore.Qt.LeftButton)

        # This time, we got the update signal
        assert spy.count() == 0

    def notestPlotData(self, widget):
        """
        See that data item can produce a chart
        """
        # By default, the compute/plot button is disabled
        assert not widget.cmdPlot.isEnabled()
        assert widget.cmdPlot.text() == 'Show Plot'

        # Set data
        test_data = Data1D(x=[1,2], y=[1,2])
        item = QtGui.QStandardItem()
        GuiUtils.updateModelItem(item, test_data, "test")
        # Force same data into logic
        widget.data = item

        # Change the category index so we have a model available
        category_index = widget.cbCategory.findText("Sphere")
        widget.cbCategory.setCurrentIndex(category_index)

        # Check the enablement/text
        assert widget.cmdPlot.isEnabled()
        assert widget.cmdPlot.text() == 'Show Plot'

        # Spying on plot update signal
        spy = QtSignalSpy(widget, widget.communicate.plotRequestedSignal)

        # Press Calculate
        QtTest.QTest.mouseClick(widget.cmdPlot, QtCore.Qt.LeftButton)

        # Observe cmdPlot caption did not change
        assert widget.cmdPlot.text() == 'Show Plot'

        # Make sure the signal has been emitted == new plot
        assert spy.count() == 1

    def testOnEmptyFit(self, widget, mocker):
        """
        Test a 1D/2D fit with no parameters
        """
        # Set data
        test_data = Data1D(x=[1,2], y=[1,2])
        item = QtGui.QStandardItem()
        GuiUtils.updateModelItem(item, test_data, "test")
        # Force same data into logic
        widget.data = item

        category_index = widget.cbCategory.findText("Sphere")
        widget.cbCategory.setCurrentIndex(category_index)

        # Test no fitting params
        widget.main_params_to_fit = []

        mocker.patch.object(logging, 'error')

        widget.onFit()
        assert logging.error.called_with('no fitting parameters')
        widget.close()

    @pytest.mark.xfail(reason="2022-09 already broken")
    def testOnEmptyFit2(self, widget, mocker):
        test_data = Data2D(image=[1.0, 2.0, 3.0],
                           err_image=[0.01, 0.02, 0.03],
                           qx_data=[0.1, 0.2, 0.3],
                           qy_data=[0.1, 0.2, 0.3],
                           xmin=0.1, xmax=0.3, ymin=0.1, ymax=0.3,
                           mask=[True, True, True])

        # Force same data into logic
        item = QtGui.QStandardItem()
        GuiUtils.updateModelItem(item, test_data, "test")

        # Force same data into logic
        widget.data = item
        category_index = widget.cbCategory.findText("Sphere")
        widget.cbCategory.setCurrentIndex(category_index)

        widget.show()

        # Test no fitting params
        widget.main_params_to_fit = []

        mocker.patch.object(logging, 'error')

        widget.onFit()
        assert logging.error.called_once()
        assert logging.error.called_with('no fitting parameters')
        widget.close()

    def notestOnFit1D(self, widget, mocker):
        """
        Test the threaded fitting call
        """
        # Set data
        test_data = Data1D(x=[1,2], y=[1,2])
        item = QtGui.QStandardItem()
        GuiUtils.updateModelItem(item, test_data, "test")
        # Force same data into logic
        widget.data = item
        category_index = widget.cbCategory.findText("Sphere")
        widget.cbCategory.setCurrentIndex(category_index)

        widget.show()

        # Assing fitting params
        widget.main_params_to_fit = ['scale']

        # Spying on status update signal
        update_spy = QtSignalSpy(widget, widget.communicate.statusBarUpdateSignal)

        mocker.patch.object(threads, 'deferToThread')
        widget.onFit()
        # thread called
        assert threads.deferToThread.called
        # thread method is 'compute'
        assert threads.deferToThread.call_args_list[0][0][0].__name__ == 'compute'

        # the fit button changed caption and got disabled
        # could fail if machine fast enough to finish
        #assert widget.cmdFit.text() == 'Stop fit'
        #assert not widget.cmdFit.isEnabled()

        # Signal pushed up
        assert update_spy.count() == 1

        widget.close()

    def notestOnFit2D(self, widget):
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
        GuiUtils.updateModelItem(item, test_data, "test")
        # Force same data into logic
        widget.data = item
        category_index = widget.cbCategory.findText("Sphere")
        widget.cbCategory.setCurrentIndex(category_index)

        widget.show()

        # Assing fitting params
        widget.main_params_to_fit = ['scale']

        # Spying on status update signal
        update_spy = QtSignalSpy(widget, widget.communicate.statusBarUpdateSignal)

        with threads.deferToThread as MagicMock:
            widget.onFit()
            # thread called
            assert threads.deferToThread.called
            # thread method is 'compute'
            assert threads.deferToThread.call_args_list[0][0][0].__name__ == 'compute'

            # the fit button changed caption and got disabled
            #assert widget.cmdFit.text() == 'Stop fit'
            #assert not widget.cmdFit.isEnabled()

            # Signal pushed up
            assert update_spy.count() == 1

    def testOnHelp(self, widget, mocker):
        """
        Test various help pages shown in this widget
        """
        #Mock the webbrowser.open method
        mocker.patch.object(widget.parent, 'showHelp', create=True)
        mocker.patch.object(webbrowser, 'open')

        # Invoke the action on default tab
        widget.onHelp()
        # Check if show() got called
        assert widget.parent.showHelp.called
        # Assure the filename is correct
        assert "fitting_help.html" in widget.parent.showHelp.call_args[0][0]

        # Change the tab to options
        widget.tabFitting.setCurrentIndex(1)
        widget.onHelp()
        # Check if show() got called
        assert widget.parent.showHelp.call_count == 2
        # Assure the filename is correct
        assert "residuals_help.html" in widget.parent.showHelp.call_args[0][0]

        # Change the tab to smearing
        widget.tabFitting.setCurrentIndex(2)
        widget.onHelp()
        # Check if show() got called
        assert widget.parent.showHelp.call_count == 3
        # Assure the filename is correct
        assert "resolution.html" in widget.parent.showHelp.call_args[0][0]

        # Change the tab to poly
        widget.tabFitting.setCurrentIndex(3)
        widget.onHelp()
        # Check if show() got called
        assert widget.parent.showHelp.call_count == 4
        # Assure the filename is correct
        assert "polydispersity.html" in widget.parent.showHelp.call_args[0][0]

        # Change the tab to magnetism
        widget.tabFitting.setCurrentIndex(4)
        widget.onHelp()
        # Check if show() got called
        assert widget.parent.showHelp.call_count == 5
        # Assure the filename is correct
        assert "magnetism.html" in widget.parent.showHelp.call_args[0][0]

    def testReadFitPage(self, widget):
        """
        Read in the fitpage object and restore state
        """
        # Set data
        test_data = Data1D(x=[1,2], y=[1,2])
        item = QtGui.QStandardItem()
        GuiUtils.updateModelItem(item, test_data, "test")
        # Force same data into logic
        widget.data = item

        # Force same data into logic
        category_index = widget.cbCategory.findText('Sphere')

        widget.cbCategory.setCurrentIndex(category_index)
        widget.main_params_to_fit = ['scale']
        # Invoke the tested method
        fp = widget.currentState()

        # Prepare modified fit page
        fp.current_model = 'onion'
        fp.is_polydisperse = True

        # Read in modified state
        widget.readFitPage(fp)

        # Check if the widget got updated accordingly
        assert widget.cbModel.currentText() == 'onion'
        assert widget.chkPolydispersity.isChecked()
        #Check if polidispersity tab is available
        assert widget.tabFitting.isTabEnabled(3)

        #Check if magnetism box and tab are disabled when 1D data is loaded
        assert not widget.chkMagnetism.isEnabled()
        assert not widget.tabFitting.isTabEnabled(4)

    # to be fixed after functionality is ready
    def notestReadFitPage2D(self, widget):
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
        widget.logic.data = test_data
        widget.data_is_loaded = True

        #item = QtGui.QStandardItem()
        #GuiUtils.updateModelItem(item, [test_data], "test")
        # Force same data into logic
        #widget.logic.data = item
        #widget.data_is_loaded = True

        category_index = widget.cbCategory.findText("Cylinder")
        widget.cbCategory.setCurrentIndex(category_index)

        # Test no fitting params
        widget.main_params_to_fit = ['scale']

        # Invoke the tested method
        fp = widget.currentState()

        # Prepare modified fit page
        fp.current_model = 'cylinder'
        fp.is_polydisperse = True
        fp.is_magnetic = True
        fp.is2D = True

        # Read in modified state
        widget.readFitPage(fp)

        # Check if the widget got updated accordingly
        assert widget.cbModel.currentText() == 'cylinder'
        assert widget.chkPolydispersity.isChecked()
        assert widget.chkPolydispersity.isEnabled()
        #Check if polidispersity tab is available
        assert widget.tabFitting.isTabEnabled(3)

        #Check if magnetism box and tab are disabled when 1D data is loaded
        assert widget.chkMagnetism.isChecked()
        assert widget.chkMagnetism.isEnabled()
        assert widget.tabFitting.isTabEnabled(4)

    def testCurrentState(self, widget):
        """
        Set up the fitpage with current state
        """
        # Set data
        test_data = Data1D(x=[1,2], y=[1,2])
        item = QtGui.QStandardItem()
        GuiUtils.updateModelItem(item, test_data, "test")
        # Force same data into logic
        widget.data = item
        category_index = widget.cbCategory.findText("Sphere")
        widget.cbCategory.setCurrentIndex(category_index)
        model_index = widget.cbModel.findText("adsorbed_layer")
        widget.cbModel.setCurrentIndex(model_index)
        widget.main_params_to_fit = ['scale']

        # Invoke the tested method
        fp = widget.currentState()

        # Test some entries. (Full testing of fp is done in FitPageTest)
        assert isinstance(fp.data, Data1D)
        assert list(fp.data.x) == [1,2]
        assert fp.data_is_loaded
        assert fp.current_category == "Sphere"
        assert fp.current_model == "adsorbed_layer"
        assert fp.main_params_to_fit == ['scale']

    def notestPushFitPage(self, widget):
        """
        Push current state of fitpage onto stack
        """
        # Set data
        test_data = Data1D(x=[1,2], y=[1,2])
        item = QtGui.QStandardItem()
        GuiUtils.updateModelItem(item, test_data, "test")
        # Force same data into logic
        widget.data = item
        category_index = widget.cbCategory.findText("Sphere")
        model_index = widget.cbModel.findText("adsorbed_layer")
        widget.cbModel.setCurrentIndex(model_index)

        # Asses the initial state of stack
        assert widget.page_stack == []

        # Set the undo flag
        widget.undo_supported = True
        widget.cbCategory.setCurrentIndex(category_index)
        widget.main_params_to_fit = ['scale']

        # Check that the stack is updated
        assert len(widget.page_stack) == 1

        # Change another parameter
        widget._model_model.item(3, 1).setText("3.0")

        # Check that the stack is updated
        assert len(widget.page_stack) == 2

    def testPopFitPage(self, widget):
        """
        Pop current state of fitpage from stack
        """
        # TODO: to be added when implementing UNDO/REDO
        pass

    def testOnMainPageChange(self, widget):
        """
        Test update  values of modified parameters in models
        """
        # select model: cylinder / cylinder
        category_index = widget.cbCategory.findText("Cylinder")
        widget.cbCategory.setCurrentIndex(category_index)

        model_index = widget.cbModel.findText("cylinder")
        widget.cbModel.setCurrentIndex(model_index)

        # modify the initial value of length (different from default)
        # print widget.kernel_module.details['length']

        new_value = "333.0"
        widget._model_model.item(5, 1).setText(new_value)

        # name of modified parameter
        name_modified_param = str(widget._model_model.item(5, 0).text())

         # Check the model
        assert widget._model_model.rowCount() == 7
        assert widget._model_model.columnCount() == 5

        # Test the header
        #assert widget.lstParams.horizontalHeader().count() == 5
        #assert not widget.lstParams.horizontalHeader().stretchLastSection()

        assert len(widget._model_model.header_tooltips) == 5
        header_tooltips = ['Select parameter for fitting',
                             'Enter parameter value',
                             'Enter minimum value for parameter',
                             'Enter maximum value for parameter',
                             'Unit of the parameter']
        for column, tooltip in enumerate(header_tooltips):
             assert widget._model_model.headerData(column,
                QtCore.Qt.Horizontal, QtCore.Qt.ToolTipRole) == \
                         header_tooltips[column]

        # check that the value has been modified in kernel_module
        assert new_value == \
                         str(widget.logic.kernel_module.params[name_modified_param])

        # check that range of variation for this parameter has NOT been changed
        assert new_value not in widget.logic.kernel_module.details[name_modified_param]

    def testModelContextMenu(self, widget):
        """
        Test the right click context menu in the parameter table
        """
        # select model: cylinder / cylinder
        category_index = widget.cbCategory.findText("Cylinder")
        widget.cbCategory.setCurrentIndex(category_index)

        model_index = widget.cbModel.findText("cylinder")
        widget.cbModel.setCurrentIndex(model_index)

        # no rows selected
        menu = widget.modelContextMenu([])
        assert len(menu.actions()) == 0

        # 1 row selected
        menu = widget.modelContextMenu([1])
        assert len(menu.actions()) == 4

        # 2 rows selected
        menu = widget.modelContextMenu([1,3])
        assert len(menu.actions()) == 5

        # 3 rows selected
        menu = widget.modelContextMenu([1,2,3])
        assert len(menu.actions()) == 4

        # over 9000
        with pytest.raises(AttributeError):
            menu = widget.modelContextMenu([i for i in range(9001)])
        assert len(menu.actions()) == 4

    def testShowModelContextMenu(self, widget, mocker):
        # select model: cylinder / cylinder
        category_index = widget.cbCategory.findText("Cylinder")
        widget.cbCategory.setCurrentIndex(category_index)

        model_index = widget.cbModel.findText("cylinder")
        widget.cbModel.setCurrentIndex(model_index)

        # No selection
        mocker.patch.object(logging, 'error')
        mocker.patch.object(widget, 'showModelDescription')
        # Show the menu
        widget.showModelContextMenu(QtCore.QPoint(10,20))

        # Assure the description menu is shown
        assert widget.showModelDescription.called
        assert not logging.error.called

        # "select" two rows
        index1 = widget.lstParams.model().index(1, 0, QtCore.QModelIndex())
        index2 = widget.lstParams.model().index(2, 0, QtCore.QModelIndex())
        selection_model = widget.lstParams.selectionModel()
        selection_model.select(index1, selection_model.Select | selection_model.Rows)
        selection_model.select(index2, selection_model.Select | selection_model.Rows)

        mocker.patch.object(QtWidgets.QMenu, 'exec_')
        mocker.patch.object(logging, 'error')
        # Show the menu
        widget.showModelContextMenu(QtCore.QPoint(10,20))

        # Assure the menu is shown
        assert not logging.error.called
        assert QtWidgets.QMenu.exec_.called

    def testShowMultiConstraint(self, widget, mocker):
        """
        Test the widget update on new multi constraint
        """
        # select model: cylinder / cylinder
        category_index = widget.cbCategory.findText("Cylinder")
        widget.cbCategory.setCurrentIndex(category_index)

        model_index = widget.cbModel.findText("cylinder")
        widget.cbModel.setCurrentIndex(model_index)

        # nothing selected
        with pytest.raises(AssertionError):
            widget.showMultiConstraint()

        # one row selected
        index = widget.lstParams.model().index(1, 0, QtCore.QModelIndex())
        selection_model = widget.lstParams.selectionModel()
        selection_model.select(index, selection_model.Select | selection_model.Rows)
        with pytest.raises(AssertionError):
            # should also throw
            widget.showMultiConstraint()

        # two rows selected
        index1 = widget.lstParams.model().index(1, 0, QtCore.QModelIndex())
        index2 = widget.lstParams.model().index(3, 0, QtCore.QModelIndex())
        selection_model = widget.lstParams.selectionModel()
        selection_model.select(index1, selection_model.Select | selection_model.Rows)
        selection_model.select(index2, selection_model.Select | selection_model.Rows)

        # return non-OK from dialog
        mocker.patch.object(QtWidgets.QDialog, 'exec_')
        widget.showMultiConstraint()
        # Check the dialog called
        assert QtWidgets.QDialog.exec_.called

        # return OK from dialog
        mocker.patch.object(QtWidgets.QDialog, 'exec_', return_value=QtWidgets.QDialog.Accepted)
        spy = QtSignalSpy(widget, widget.constraintAddedSignal)

        widget.showMultiConstraint()

        # Make sure the signal has been emitted
        assert spy.count() == 1

        # Check the argument value - should be row '1'
        assert spy.called()[0]['args'][0] == [1]

    def testGetRowFromName(self, widget):
        """
        Helper function for parameter table
        """
        # select model: cylinder / cylinder
        category_index = widget.cbCategory.findText("Cylinder")
        widget.cbCategory.setCurrentIndex(category_index)

        model_index = widget.cbModel.findText("cylinder")
        widget.cbModel.setCurrentIndex(model_index)

        # several random parameters
        assert widget.getRowFromName('scale') == 0
        assert widget.getRowFromName('length') == 6

    def testGetParamNames(self, widget):
        """
        Helper function for parameter table
        """
        # select model: cylinder / cylinder
        category_index = widget.cbCategory.findText("Cylinder")
        widget.cbCategory.setCurrentIndex(category_index)

        model_index = widget.cbModel.findText("cylinder")
        widget.cbModel.setCurrentIndex(model_index)

        cylinder_params = ['scale','background','sld','sld_solvent','radius','length']
        # assure all parameters are returned
        assert widget.getParamNames() == cylinder_params

        # Switch to another model
        model_index = widget.cbModel.findText("pringle")
        widget.cbModel.setCurrentIndex(model_index)
        QtWidgets.qApp.processEvents()

        # make sure the parameters are different than before
        assert not (widget.getParamNames() == cylinder_params)

    def testAddConstraintToRow(self, widget, mocker):
        """
        Test the constraint row add operation
        """
        # select model: cylinder / cylinder
        category_index = widget.cbCategory.findText("Cylinder")
        widget.cbCategory.setCurrentIndex(category_index)

        model_index = widget.cbModel.findText("cylinder")
        widget.cbModel.setCurrentIndex(model_index)

        # Create a constraint object
        const = Constraint(parent=None, param="scale",value=7.0)
        row = 3

        spy = QtSignalSpy(widget, widget.constraintAddedSignal)

        # Mock the modelName method
        mocker.patch.object(widget, 'modelName', return_value='M1')

        # Mock a constraint tab
        constraint_tab = MagicMock()
        constraint_tab.constraint_accepted = False
        widget.parent.perspective().constraint_tab = constraint_tab

        # call the method tested
        widget.addConstraintToRow(constraint=const, row=row)

        # Make sure the signal has been emitted
        assert spy.count() == 1

        # Check the argument value - should be row 'row'
        assert spy.called()[0]['args'][0] == [row]

        # Assure the row has the constraint
        assert widget.getConstraintForRow(row) == const
        assert widget.rowHasConstraint(row)

        # Check that the constraint tab flag is set to True
        assert constraint_tab.constraint_accepted

        # assign complex constraint now
        const = Constraint(parent=None, param='radius', func='5*sld')
        row = 5
        # call the method tested
        widget.addConstraintToRow(constraint=const, row=row)

        # Make sure the signal has been emitted
        assert spy.count() == 2

        # Check the argument value - should be row 'row'
        assert spy.called()[1]['args'][0] == [row]

        # Assure the row has the constraint
        assert widget.getConstraintForRow(row) == const
        # and it is a complex constraint
        assert widget.rowHasConstraint(row)

        # Now try to add an constraint when the checking function returns an
        # error message
        mocker.patch.object(FittingUtilities, 'checkConstraints', return_value="foo")

        # Mock the QMessagebox Warning
        mocker.patch.object(QtWidgets.QMessageBox, 'critical')

        # Call the method tested
        widget.addConstraintToRow(constraint=const, row=row)

        # Check that the messagebox was called with the right error message
        QtWidgets.QMessageBox.critical.assert_called_with(
            widget,
            "Inconsistent constraint",
            "foo",
            QtWidgets.QMessageBox.Ok,
        )

        # Make sure no signal was emitted
        assert spy.count() == 2
        # Check that constraint tab flag is set to False
        assert not constraint_tab.constraint_accepted


    def testAddSimpleConstraint(self, widget):
        """
        Test the constraint add operation
        """
        # select model: cylinder / cylinder
        category_index = widget.cbCategory.findText("Cylinder")
        widget.cbCategory.setCurrentIndex(category_index)

        model_index = widget.cbModel.findText("cylinder")
        widget.cbModel.setCurrentIndex(model_index)

        # select two rows
        row1 = 1
        row2 = 4
        index1 = widget.lstParams.model().index(row1, 0, QtCore.QModelIndex())
        index2 = widget.lstParams.model().index(row2, 0, QtCore.QModelIndex())
        selection_model = widget.lstParams.selectionModel()
        selection_model.select(index1, selection_model.Select | selection_model.Rows)
        selection_model.select(index2, selection_model.Select | selection_model.Rows)

        # define the signal spy
        spy = QtSignalSpy(widget, widget.constraintAddedSignal)

        # call the method tested
        widget.addSimpleConstraint()

        # Make sure the signal has been emitted
        assert spy.count() == 2

        # Check the argument value
        assert spy.called()[0]['args'][0] == [row1]
        assert spy.called()[1]['args'][0] == [row2]

    def testDeleteConstraintOnParameter(self, widget):
        """
        Test the constraint deletion in model/view
        """
        # select model: cylinder / cylinder
        category_index = widget.cbCategory.findText("Cylinder")
        widget.cbCategory.setCurrentIndex(category_index)

        model_index = widget.cbModel.findText("cylinder")
        widget.cbModel.setCurrentIndex(model_index)

        row1 = 1
        row2 = 5

        param1 = "background"
        param2 = "radius"

        #default_value1 = "0.001"
        default_value2 = "20"

        # select two rows
        index1 = widget.lstParams.model().index(row1, 0, QtCore.QModelIndex())
        index2 = widget.lstParams.model().index(row2, 0, QtCore.QModelIndex())
        selection_model = widget.lstParams.selectionModel()
        selection_model.select(index1, selection_model.Select | selection_model.Rows)
        selection_model.select(index2, selection_model.Select | selection_model.Rows)

        # add constraints
        widget.addSimpleConstraint()

        # deselect the model
        selection_model.clear()

        # select a single row
        selection_model.select(index1, selection_model.Select | selection_model.Rows)

        # delete one of the constraints
        widget.deleteConstraintOnParameter(param=param1)

        # see that the other constraint is still present
        cons = widget.getConstraintForRow(row2)
        assert cons.param == param2
        assert cons.value == default_value2

        # kill the other constraint
        widget.deleteConstraint()

        # see that the other constraint is still present
        assert widget.getConstraintsForModel() == [(param2, None)]

    def testGetConstraintForRow(self, widget):
        """
        Helper function for parameter table
        """
        # tested extensively elsewhere
        pass

    def testRowHasConstraint(self, widget):
        """
        Helper function for parameter table
        """
        # select model: cylinder / cylinder
        category_index = widget.cbCategory.findText("Cylinder")
        widget.cbCategory.setCurrentIndex(category_index)

        model_index = widget.cbModel.findText("cylinder")
        widget.cbModel.setCurrentIndex(model_index)

        row1 = 1
        row2 = 5

        # select two rows
        index1 = widget.lstParams.model().index(row1, 0, QtCore.QModelIndex())
        index2 = widget.lstParams.model().index(row2, 0, QtCore.QModelIndex())
        selection_model = widget.lstParams.selectionModel()
        selection_model.select(index1, selection_model.Select | selection_model.Rows)
        selection_model.select(index2, selection_model.Select | selection_model.Rows)

        # add constraints
        widget.addSimpleConstraint()

        con_list = [False, True, False, False, False, True, False]
        new_list = []
        for row in range(widget._model_model.rowCount()):
            new_list.append(widget.rowHasConstraint(row))

        assert new_list == con_list

    def testRowHasActiveConstraint(self, widget):
        """
        Helper function for parameter table
        """
        # select model: cylinder / cylinder
        category_index = widget.cbCategory.findText("Cylinder")
        widget.cbCategory.setCurrentIndex(category_index)

        model_index = widget.cbModel.findText("cylinder")
        widget.cbModel.setCurrentIndex(model_index)

        row1 = 1
        row2 = 5

        # select two rows
        index1 = widget.lstParams.model().index(row1, 0, QtCore.QModelIndex())
        index2 = widget.lstParams.model().index(row2, 0, QtCore.QModelIndex())
        selection_model = widget.lstParams.selectionModel()
        selection_model.select(index1, selection_model.Select | selection_model.Rows)
        selection_model.select(index2, selection_model.Select | selection_model.Rows)

        # add constraints
        widget.addSimpleConstraint()

        # deactivate the first constraint
        constraint_objects = widget.getConstraintObjectsForModel()
        constraint_objects[0].active = False

        con_list = [False, False, False, False, False, True, False]
        new_list = []
        for row in range(widget._model_model.rowCount()):
            new_list.append(widget.rowHasActiveConstraint(row))

        assert new_list == con_list

    def testGetConstraintsForModel(self, widget):
        """
        Test the constraint getter for constraint texts
        """
        # select model: cylinder / cylinder
        category_index = widget.cbCategory.findText("Cylinder")
        widget.cbCategory.setCurrentIndex(category_index)

        model_index = widget.cbModel.findText("cylinder")
        widget.cbModel.setCurrentIndex(model_index)

        # no constraints
        assert widget.getConstraintsForModel() == []

        row1 = 1
        row2 = 5

        param1 = "background"
        param2 = "radius"

        default_value1 = "0.001"
        default_value2 = "20"

        # select two rows
        index1 = widget.lstParams.model().index(row1, 0, QtCore.QModelIndex())
        index2 = widget.lstParams.model().index(row2, 0, QtCore.QModelIndex())
        selection_model = widget.lstParams.selectionModel()
        selection_model.select(index1, selection_model.Select | selection_model.Rows)
        selection_model.select(index2, selection_model.Select | selection_model.Rows)

        # add constraints
        widget.addSimpleConstraint()

        # simple constraints
        # assert widget.getConstraintsForModel(), [('background', '0.001') == ('radius', '20')]
        cons = widget.getConstraintForRow(row1)
        assert cons.param == param1
        assert cons.value == default_value1
        cons = widget.getConstraintForRow(row2)
        assert cons.param == param2
        assert cons.value == default_value2

        objects = widget.getConstraintObjectsForModel()
        assert len(objects) == 2
        assert objects[1].value == default_value2
        assert objects[0].param == param1

        row = 0
        param = "scale"
        func = "5*sld"

        # add complex constraint
        const = Constraint(parent=None, param=param, func=func)
        widget.addConstraintToRow(constraint=const, row=row)
        #assert widget.getConstraintsForModel() == [('scale', '5*sld'), ('background', '0.001'), ('radius', None)]
        cons = widget.getConstraintForRow(row2)
        assert cons.param == param2
        assert cons.value == default_value2

        objects = widget.getConstraintObjectsForModel()
        assert len(objects) == 3
        assert objects[0].func == func

    def testReplaceConstraintName(self, widget):
        """
        Test the replacement of constraint moniker
        """
        # select model: cylinder / cylinder
        category_index = widget.cbCategory.findText("Cylinder")
        widget.cbCategory.setCurrentIndex(category_index)

        model_index = widget.cbModel.findText("cylinder")
        widget.cbModel.setCurrentIndex(model_index)

        old_name = 'M5'
        new_name = 'poopy'
        # add complex constraint
        const = Constraint(parent=None, param='scale', func='%s.5*sld'%old_name)
        row = 0
        widget.addConstraintToRow(constraint=const, row=row)

        # Replace 'm5' with 'poopy'
        widget.replaceConstraintName(old_name, new_name)

        assert widget.getConstraintsForModel() == [('scale', 'poopy.5*sld')]


    def testRetainParametersBetweenModelChange(self, widget):
        """
        Test constantess of model parameters on model change
        """
        # select model: cylinder / cylinder
        category_index = widget.cbCategory.findText("Cylinder")
        widget.cbCategory.setCurrentIndex(category_index)

        model_index = widget.cbModel.findText("cylinder")
        widget.cbModel.setCurrentIndex(model_index)

        # modify the initial value of radius (different from default)
        new_value = "333.0"
        widget._model_model.item(5, 1).setText(new_value)

        # change parameter in the same category
        model_index = widget.cbModel.findText("barbell")
        widget.cbModel.setCurrentIndex(model_index)

        # see if radius is the same as set
        row = widget.getRowFromName("radius")
        assert widget._model_model.item(row, 1).text() == "333"

        # Now, change not just model but a category as well
        # cylinder / cylinder
        category_index = widget.cbCategory.findText("Sphere")
        widget.cbCategory.setCurrentIndex(category_index)

        model_index = widget.cbModel.findText("sphere")
        widget.cbModel.setCurrentIndex(model_index)

        # see if radius is still the same
        row = widget.getRowFromName("radius")
        assert int(widget._model_model.item(row, 1).text()) == 333

    @pytest.mark.xfail(reason="2022-09 already broken")
    def testOnParameterPaste(self, widget, mocker):
        """
        Test response of the widget to clipboard content
        paste request
        """
        mocker.patch.object(widget, 'updatePageWithParameters')
        mocker.patch.object(QtWidgets.QMessageBox, 'exec_')
        cb = QtWidgets.QApplication.clipboard()

        # test bad clipboard
        cb.setText("bad clipboard")
        widget.onParameterPaste()
        QtWidgets.QMessageBox.exec_.assert_called_once()
        widget.updatePageWithParameters.assert_not_called()

        # Test correct clipboard
        cb.setText("sasview_parameter_values:model_name,core_shell_bicelle:scale,False,1.0,None,0.0,inf,()")
        widget.onParameterPaste()
        widget.updatePageWithParameters.assert_called_once()

    def testGetConstraintsForFitting(self, widget, mocker):
        """
        Test the deactivation of constraints when trying to fit a single page
        with constraints relying on other pages
        """
        # mock the constraint getter
        widget.getComplexConstraintsForModel = MagicMock(return_value=[
            ('scale', 'M2.background')])
        # mock isConstraintMultimodel so that our constraint is multi-model
        mocker.patch.object(widget, 'isConstraintMultimodel', return_value=True)
        # Mock a constraint tab
        constraint_tab = MagicMock()
        widget.parent.perspective().constraint_tab = constraint_tab
        # instanciate a constraint
        constraint = Constraint(parent=None, param="scale", value=7.0)
        mocker.patch.object(widget, 'getConstraintForRow', return_value=constraint)
        # mock the messagebox
        mocker.patch.object(QtWidgets.QMessageBox, 'exec_')

        # select a model
        category_index = widget.cbCategory.findText("Cylinder")
        widget.cbCategory.setCurrentIndex(category_index)

        model_index = widget.cbModel.findText("cylinder")
        widget.cbModel.setCurrentIndex(model_index)

        # Call the method
        widget.getConstraintsForFitting()
        # Check that QMessagebox was called
        QtWidgets.QMessageBox.exec_.assert_called_once()
        # Constraint should be inactive
        assert constraint.active is False
        # Check that the uncheckConstraint method was called
        constraint_tab.uncheckConstraint.assert_called_with("M1:scale")

    def testQRangeReset(self, widget, mocker):
        ''' Test onRangeReset w/ and w/o data loaded '''
        assert widget.options_widget.qmin == \
                         widget.options_widget.QMIN_DEFAULT
        assert widget.options_widget.qmax == \
                         widget.options_widget.QMAX_DEFAULT
        assert widget.options_widget.npts == \
                         widget.options_widget.NPTS_DEFAULT
        assert widget.options_widget.npts == \
                         widget.options_widget.npts_fit
        # Set values to non-defaults and check they updated
        widget.options_widget.updateMinQ(0.01)
        widget.options_widget.updateMaxQ(0.02)
        assert float(widget.options_widget.qmin) == 0.01
        assert float(widget.options_widget.qmax) == 0.02
        # Click the reset range button and check the values went back to defaults
        widget.options_widget.cmdReset.click()
        assert widget.options_widget.qmin == \
                         widget.options_widget.QMIN_DEFAULT
        assert widget.options_widget.qmax == \
                         widget.options_widget.QMAX_DEFAULT
        assert widget.options_widget.npts == \
                         widget.options_widget.NPTS_DEFAULT
        # Load data into tab and check new limits
        data = Data1D(x=[1,2], y=[1,2])
        mocker.patch.object(GuiUtils, 'dataFromItem', return_value=data)
        item = QtGui.QStandardItem("test")
        widget_with_data = FittingWidget.FittingWidget(dummy_manager(), data=item, tab_id=3)
        assert widget_with_data.options_widget.qmin == min(data.x)
        assert widget_with_data.options_widget.qmax == max(data.x)
        assert widget_with_data.options_widget.npts == len(data.x)
        # Set values to non-defaults and check they updated
        widget.options_widget.updateMinQ(0.01)
        widget.options_widget.updateMaxQ(0.02)
        assert float(widget.options_widget.qmin) == 0.01
        assert float(widget.options_widget.qmax) == 0.02
        # Click the reset range button and check the values went back to data values
        widget.options_widget.cmdReset.click()
        assert widget_with_data.options_widget.qmin == min(data.x)
        assert widget_with_data.options_widget.qmax == max(data.x)
        assert widget_with_data.options_widget.npts == len(data.x)
