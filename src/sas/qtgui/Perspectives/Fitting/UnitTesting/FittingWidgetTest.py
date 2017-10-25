import sys
import unittest
import time

from PyQt4 import QtGui
from PyQt4 import QtTest
from PyQt4 import QtCore
from mock import MagicMock
from twisted.internet import threads

# set up import paths
import sas.qtgui.path_prepare

# Local
from sas.qtgui.Utilities.GuiUtils import *
from sas.qtgui.Perspectives.Fitting.FittingWidget import *
from sas.qtgui.UnitTesting.TestUtils import QtSignalSpy

from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.PlotterData import Data2D

#if not QtGui.QApplication.instance():
app = QtGui.QApplication(sys.argv)

class dummy_manager(object):
    HELP_DIRECTORY_LOCATION = "html"
    communicate = Communicate()

class FittingWidgetTest(unittest.TestCase):
    """Test the fitting widget GUI"""

    def setUp(self):
        """Create the GUI"""
        self.widget = FittingWidget(dummy_manager())

    def tearDown(self):
        """Destroy the GUI"""
        self.widget.close()
        del self.widget

    def testDefaults(self):
        """Test the GUI in its default state"""
        self.assertIsInstance(self.widget, QtGui.QWidget)
        self.assertEqual(self.widget.windowTitle(), "Fitting")
        self.assertEqual(self.widget.sizePolicy().Policy(), QtGui.QSizePolicy.Fixed)
        self.assertIsInstance(self.widget.lstParams.model(), QtGui.QStandardItemModel)
        self.assertIsInstance(self.widget.lstPoly.model(), QtGui.QStandardItemModel)
        self.assertIsInstance(self.widget.lstMagnetic.model(), QtGui.QStandardItemModel)
        self.assertFalse(self.widget.cbModel.isEnabled())
        self.assertFalse(self.widget.cbStructureFactor.isEnabled())
        self.assertFalse(self.widget.cmdFit.isEnabled())
        self.assertTrue(self.widget.acceptsData())
        self.assertFalse(self.widget.data_is_loaded)

    def testSelectCategoryDefault(self):
        """
        Test if model categories have been loaded properly
        """
        fittingWindow =  self.widget

        #Test loading from json categories
        category_list = fittingWindow.master_category_dict.keys()

        for category in category_list:
            self.assertNotEqual(fittingWindow.cbCategory.findText(category),-1)

        #Test what is current text in the combobox
        self.assertEqual(fittingWindow.cbCategory.currentText(), CATEGORY_DEFAULT)

    def testWidgetWithData(self):
        """
        Test the instantiation of the widget with initial data
        """
        data = Data1D(x=[1,2], y=[1,2])
        GuiUtils.dataFromItem = MagicMock(return_value=data)
        item = QtGui.QStandardItem("test")

        widget_with_data = FittingWidget(dummy_manager(), data=item, tab_id=3)

        self.assertEqual(widget_with_data.data, data)
        self.assertTrue(widget_with_data.data_is_loaded)
        # self.assertTrue(widget_with_data.cmdFit.isEnabled())
        self.assertFalse(widget_with_data.acceptsData())

    def testSelectPolydispersity(self):
        """
        Test if models have been loaded properly
        """
        fittingWindow =  self.widget

        self.assertIsInstance(fittingWindow.lstPoly.itemDelegate(), QtGui.QStyledItemDelegate)
        #Test loading from json categories
        fittingWindow.SASModelToQModel("cylinder")
        pd_index = fittingWindow.lstPoly.model().index(0,0)
        self.assertEqual(str(pd_index.data().toString()), "Distribution of radius")
        pd_index = fittingWindow.lstPoly.model().index(1,0)
        self.assertEqual(str(pd_index.data().toString()), "Distribution of length")

        # test the delegate a bit
        delegate = fittingWindow.lstPoly.itemDelegate()
        self.assertEqual(len(delegate.POLYDISPERSE_FUNCTIONS), 5)
        self.assertEqual(delegate.editableParameters(), [1, 2, 3, 4, 5])
        self.assertEqual(delegate.poly_function, 6)
        self.assertIsInstance(delegate.combo_updated, QtCore.pyqtBoundSignal)

    def testSelectMagnetism(self):
        """
        Test if models have been loaded properly
        """
        fittingWindow =  self.widget

        self.assertIsInstance(fittingWindow.lstMagnetic.itemDelegate(), QtGui.QStyledItemDelegate)
        #Test loading from json categories
        fittingWindow.SASModelToQModel("cylinder")
        mag_index = fittingWindow.lstMagnetic.model().index(0,0)
        self.assertEqual(str(mag_index.data().toString()), "up:frac_i")
        mag_index = fittingWindow.lstMagnetic.model().index(1,0)
        self.assertEqual(str(mag_index.data().toString()), "up:frac_f")
        mag_index = fittingWindow.lstMagnetic.model().index(2,0)
        self.assertEqual(str(mag_index.data().toString()), "up:angle")
        mag_index = fittingWindow.lstMagnetic.model().index(3,0)
        self.assertEqual(str(mag_index.data().toString()), "M0:sld")
        mag_index = fittingWindow.lstMagnetic.model().index(4,0)
        self.assertEqual(str(mag_index.data().toString()), "mtheta:sld")
        mag_index = fittingWindow.lstMagnetic.model().index(5,0)
        self.assertEqual(str(mag_index.data().toString()), "mphi:sld")
        mag_index = fittingWindow.lstMagnetic.model().index(6,0)
        self.assertEqual(str(mag_index.data().toString()), "M0:sld_solvent")
        mag_index = fittingWindow.lstMagnetic.model().index(7,0)
        self.assertEqual(str(mag_index.data().toString()), "mtheta:sld_solvent")
        mag_index = fittingWindow.lstMagnetic.model().index(8,0)
        self.assertEqual(str(mag_index.data().toString()), "mphi:sld_solvent")

        # test the delegate a bit
        delegate = fittingWindow.lstMagnetic.itemDelegate()
        self.assertEqual(delegate.editableParameters(), [1, 2, 3])
        self.assertIsInstance(delegate.combo_updated, QtCore.pyqtBoundSignal)

    def testSelectStructureFactor(self):
        """
        Test if structure factors have been loaded properly
        """
        fittingWindow =  self.widget

        #Test for existence in combobox
        self.assertNotEqual(fittingWindow.cbStructureFactor.findText("stickyhardsphere"),-1)
        self.assertNotEqual(fittingWindow.cbStructureFactor.findText("hayter_msa"),-1)
        self.assertNotEqual(fittingWindow.cbStructureFactor.findText("squarewell"),-1)
        self.assertNotEqual(fittingWindow.cbStructureFactor.findText("hardsphere"),-1)

        #Test what is current text in the combobox
        self.assertTrue(fittingWindow.cbCategory.currentText(), "None")

    def testSignals(self):
        """
        Test the widget emitted signals
        """
        pass

    def testSelectCategory(self):
        """
        Assure proper behaviour on changing category
        """
        self.widget.show()
        self.assertEqual(self.widget._previous_category_index, 0)
        # confirm the model combo contains no models
        self.assertEqual(self.widget.cbModel.count(), 0)

        # invoke the method by changing the index
        category_index = self.widget.cbCategory.findText("Shape Independent")
        self.widget.cbCategory.setCurrentIndex(category_index)

        # test the model combo content
        self.assertEqual(self.widget.cbModel.count(), 29)

        # Try to change back to default
        self.widget.cbCategory.setCurrentIndex(0)

        # Observe no such luck
        self.assertEqual(self.widget.cbCategory.currentIndex(), 6)
        self.assertEqual(self.widget.cbModel.count(), 29)

        # Set the structure factor
        structure_index=self.widget.cbCategory.findText(CATEGORY_STRUCTURE)
        self.widget.cbCategory.setCurrentIndex(structure_index)
        # check the enablement of controls
        self.assertFalse(self.widget.cbModel.isEnabled())
        self.assertTrue(self.widget.cbStructureFactor.isEnabled())

    def testSelectModel(self):
        """
        Assure proper behaviour on changing model
        """
        self.widget.show()
        # Change the category index so we have some models
        category_index = self.widget.cbCategory.findText("Shape Independent")
        self.widget.cbCategory.setCurrentIndex(category_index)

        # check the enablement of controls
        self.assertTrue(self.widget.cbModel.isEnabled())
        self.assertFalse(self.widget.cbStructureFactor.isEnabled())

        # set up the model update spy
        # spy = QtSignalSpy(self.widget._model_model, self.widget._model_model.itemChanged)

        # mock the tested methods
        self.widget.SASModelToQModel = MagicMock()
        self.widget.createDefaultDataset = MagicMock()
        self.widget.calculateQGridForModel = MagicMock()
        # 
        # Now change the model
        self.widget.cbModel.setCurrentIndex(3)
        self.assertEqual(self.widget.cbModel.currentText(),'dab')

        # No data sent -> no index set, only createDefaultDataset called
        self.assertTrue(self.widget.createDefaultDataset.called)
        self.assertTrue(self.widget.SASModelToQModel.called)
        self.assertFalse(self.widget.calculateQGridForModel.called)

        # Let's tell the widget that data has been loaded
        self.widget.data_is_loaded = True
        # Reset the sasmodel index
        self.widget.cbModel.setCurrentIndex(1)
        self.assertEqual(self.widget.cbModel.currentText(),'broad_peak')

        # Observe calculateQGridForModel called
        self.assertTrue(self.widget.calculateQGridForModel.called)

    def testSelectFactor(self):
        """
        Assure proper behaviour on changing structure factor
        """
        self.widget.show()
        # Change the category index so we have some models
        category_index = self.widget.cbCategory.findText("Shape Independent")
        self.widget.cbCategory.setCurrentIndex(category_index)
        # Change the model to one that supports structure factors
        model_index = self.widget.cbModel.findText('fractal_core_shell')
        self.widget.cbModel.setCurrentIndex(model_index)

        # Check that the factor combo is active and the default is chosen
        self.assertTrue(self.widget.cbStructureFactor.isEnabled())
        self.assertEqual(self.widget.cbStructureFactor.currentText(), STRUCTURE_DEFAULT)

        # We have this many rows in the model
        rowcount = self.widget._model_model.rowCount()
        #self.assertEqual(self.widget._model_model.rowCount(), 8)

        # Change structure factor to something more exciting
        structure_index = self.widget.cbStructureFactor.findText('squarewell')
        self.widget.cbStructureFactor.setCurrentIndex(structure_index)

        # We have 4 more rows now
        self.assertEqual(self.widget._model_model.rowCount(), rowcount+4)

        # Switch models
        self.widget.cbModel.setCurrentIndex(0)

        # Observe factor reset to None
        self.assertEqual(self.widget.cbStructureFactor.currentText(), STRUCTURE_DEFAULT)

        # Switch category to structure factor
        structure_index=self.widget.cbCategory.findText(CATEGORY_STRUCTURE)
        self.widget.cbCategory.setCurrentIndex(structure_index)
        # Observe the correct enablement
        self.assertTrue(self.widget.cbStructureFactor.isEnabled())
        self.assertFalse(self.widget.cbModel.isEnabled())
        self.assertEqual(self.widget._model_model.rowCount(), 0)

        # Choose the last factor
        last_index = self.widget.cbStructureFactor.count()
        self.widget.cbStructureFactor.setCurrentIndex(last_index-1)
        # Do we have all the rows?
        self.assertEqual(self.widget._model_model.rowCount(), 4)

        # Are the command buttons properly enabled?
        self.assertTrue(self.widget.cmdPlot.isEnabled())
        self.assertFalse(self.widget.cmdFit.isEnabled())

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
        self.assertEqual(spy.count(), 1)

        # Check the argument type
        self.assertIsInstance(spy.called()[0]['args'][0], QtGui.QStandardItem)

    def testCalculateQGridForModel(self):
        """
        Check that the fitting 1D data object is ready
        """
        # Mock the thread creation
        threads.deferToThread = MagicMock()
        # Model for theory
        self.widget.SASModelToQModel("cylinder")
        # Call the tested method
        self.widget.calculateQGridForModel()
        time.sleep(1)
        # Test the mock
        self.assertTrue(threads.deferToThread.called)
        self.assertEqual(threads.deferToThread.call_args_list[0][0][0].__name__, "compute")

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
        self.assertEqual(self.widget.lblChi2Value.text(), '---')

        # Force same data into logic
        self.widget.logic.data = test_data
        self.widget.calculateResiduals(test_data)
        # Now, the difference is 0, as data is the same
        self.assertEqual(self.widget.lblChi2Value.text(), '0')

        # Change data
        test_data_2 = Data1D(x=[1,2], y=[2.1,3.49])
        self.widget.logic.data = test_data_2
        self.widget.calculateResiduals(test_data)
        # Now, the difference is non-zero
        self.assertEqual(float(self.widget.lblChi2Value.text()), 1.7151)

    def testSetPolyModel(self):
        """
        Test the polydispersity model setup
        """
        self.widget.show()
        # Change the category index so we have a model with no poly
        category_index = self.widget.cbCategory.findText("Shape Independent")
        self.widget.cbCategory.setCurrentIndex(category_index)
        # Check the poly model
        self.assertEqual(self.widget._poly_model.rowCount(), 0)
        self.assertEqual(self.widget._poly_model.columnCount(), 0)

        # Change the category index so we have a model available
        self.widget.cbCategory.setCurrentIndex(2)

        # Check the poly model
        self.assertEqual(self.widget._poly_model.rowCount(), 4)
        self.assertEqual(self.widget._poly_model.columnCount(), 8)

        # Test the header
        self.assertEqual(self.widget.lstPoly.horizontalHeader().count(), 8)
        self.assertFalse(self.widget.lstPoly.horizontalHeader().stretchLastSection())

        # Test tooltips
        self.assertEqual(len(self.widget._poly_model.header_tooltips), 8)

        header_tooltips = ['Select parameter for fitting',
                             'Enter polydispersity ratio (STD/mean). '
                             'STD: standard deviation from the mean value',
                             'Enter minimum value for parameter',
                             'Enter maximum value for parameter',
                             'Enter number of points for parameter',
                             'Enter number of sigmas parameter',
                             'Select distribution function',
                             'Select filename with user-definable distribution']
        for column, tooltip in enumerate(header_tooltips):
             self.assertEqual(self.widget._poly_model.headerData( column,
                QtCore.Qt.Horizontal, QtCore.Qt.ToolTipRole),
                         header_tooltips[column])

        # Test presence of comboboxes in last column
        for row in xrange(self.widget._poly_model.rowCount()):
            func_index = self.widget._poly_model.index(row, 6)
            self.assertTrue(isinstance(self.widget.lstPoly.indexWidget(func_index), QtGui.QComboBox))
            self.assertIn('Distribution of', self.widget._poly_model.item(row, 0).text())
        #self.widget.close()

    def testPolyModelChange(self):
        """
        Polydispersity model changed - test all possible scenarios
        """
        self.widget.show()
        # Change the category index so we have a model with polydisp
        category_index = self.widget.cbCategory.findText("Cylinder")
        self.widget.cbCategory.setCurrentIndex(category_index)

        # click on a poly parameter checkbox
        index = self.widget._poly_model.index(0,0)
        # Set the checbox
        self.widget._poly_model.item(0,0).setCheckState(2)
        # Assure the parameter is added
        self.assertEqual(self.widget.parameters_to_fit, ['radius_bell.width'])

        # Add another parameter
        self.widget._poly_model.item(2,0).setCheckState(2)
        # Assure the parameters are added
        self.assertEqual(self.widget.parameters_to_fit, ['radius_bell.width', 'length.width'])

        # Change the min/max values
        self.assertEqual(self.widget.kernel_module.details['radius_bell'][1], 0.0)
        self.widget._poly_model.item(0,2).setText("1.0")
        self.assertEqual(self.widget.kernel_module.details['radius_bell'][1], 1.0)

        # Change the number of points
        self.assertEqual(self.widget.kernel_module.getParam('radius_bell.npts'), 35)
        self.widget._poly_model.item(0,4).setText("22")
        self.assertEqual(self.widget.kernel_module.getParam('radius_bell.npts'), 22)
        # try something stupid
        self.widget._poly_model.item(0,4).setText("butt")
        # see that this didn't annoy the control at all
        self.assertEqual(self.widget.kernel_module.getParam('radius_bell.npts'), 22)

        # Change the number of sigmas
        self.assertEqual(self.widget.kernel_module.getParam('radius_bell.nsigmas'), 3)
        self.widget._poly_model.item(0,5).setText("222")
        self.assertEqual(self.widget.kernel_module.getParam('radius_bell.nsigmas'), 222)
        # try something stupid again
        self.widget._poly_model.item(0,4).setText("beer")
        # no efect
        self.assertEqual(self.widget.kernel_module.getParam('radius_bell.nsigmas'), 222)

    def testOnPolyComboIndexChange(self):
        """
        Test the slot method for polydisp. combo box index change
        """
        self.widget.show()
        # Change the category index so we have a model with polydisp
        category_index = self.widget.cbCategory.findText("Cylinder")
        self.widget.cbCategory.setCurrentIndex(category_index)

        # call method with default settings
        self.widget.onPolyComboIndexChange('gaussian', 0)
        # check values
        self.assertEqual(self.widget.kernel_module.getParam('radius_bell.npts'), 35)
        self.assertEqual(self.widget.kernel_module.getParam('radius_bell.nsigmas'), 3)
        # Change the index
        self.widget.onPolyComboIndexChange('rectangle', 0)
        # check values
        self.assertEqual(self.widget.kernel_module.getParam('radius_bell.npts'), 35)
        self.assertEqual(self.widget.kernel_module.getParam('radius_bell.nsigmas'), 1.70325)
        # Change the index
        self.widget.onPolyComboIndexChange('lognormal', 0)
        # check values
        self.assertEqual(self.widget.kernel_module.getParam('radius_bell.npts'), 80)
        self.assertEqual(self.widget.kernel_module.getParam('radius_bell.nsigmas'), 8)
        # Change the index
        self.widget.onPolyComboIndexChange('schulz', 0)
        # check values
        self.assertEqual(self.widget.kernel_module.getParam('radius_bell.npts'), 80)
        self.assertEqual(self.widget.kernel_module.getParam('radius_bell.nsigmas'), 8)

        # mock up file load
        self.widget.loadPolydispArray = MagicMock()
        # Change to 'array'
        self.widget.onPolyComboIndexChange('array', 0)
        # See the mock fire
        self.assertTrue(self.widget.loadPolydispArray.called)

    def testLoadPolydispArray(self):
        """
        Test opening of the load file dialog for 'array' polydisp. function
        """
        filename = os.path.join("UnitTesting", "testdata_noexist.txt")
        QtGui.QFileDialog.getOpenFileName = MagicMock(return_value=filename)
        self.widget.show()
        # Change the category index so we have a model with polydisp
        category_index = self.widget.cbCategory.findText("Cylinder")
        self.widget.cbCategory.setCurrentIndex(category_index)

        self.widget.onPolyComboIndexChange('array', 0)
        # check values - unchanged since the file doesn't exist
        self.assertTrue(self.widget._poly_model.item(0, 1).isEnabled())
        with self.assertRaises(AttributeError):
            self.widget.disp_model()

        # good file
        filename = os.path.join("UnitTesting", "testdata.txt")
        QtGui.QFileDialog.getOpenFileName = MagicMock(return_value=filename)

        self.widget.onPolyComboIndexChange('array', 0)
        # check values - disabled control, present weights
        self.assertFalse(self.widget._poly_model.item(0, 1).isEnabled())
        self.assertEqual(self.widget.disp_model.weights[0], 2.83954)
        self.assertEqual(len(self.widget.disp_model.weights), 19)
        self.assertEqual(len(self.widget.disp_model.values), 19)
        self.assertEqual(self.widget.disp_model.values[0], 0.0)
        self.assertEqual(self.widget.disp_model.values[18], 3.67347)

    def testSetMagneticModel(self):
        """
        Test the magnetic model setup
        """
        self.widget.show()
        # Change the category index so we have a model available
        category_index = self.widget.cbCategory.findText("Sphere")
        self.widget.cbCategory.setCurrentIndex(category_index)

        # Check the magnetic model
        self.assertEqual(self.widget._magnet_model.rowCount(), 9)
        self.assertEqual(self.widget._magnet_model.columnCount(), 5)

        # Test the header
        self.assertEqual(self.widget.lstMagnetic.horizontalHeader().count(), 5)
        self.assertFalse(self.widget.lstMagnetic.horizontalHeader().stretchLastSection())

        #Test tooltips
        self.assertEqual(len(self.widget._magnet_model.header_tooltips), 5)

        header_tooltips = ['Select parameter for fitting',
                             'Enter parameter value',
                             'Enter minimum value for parameter',
                             'Enter maximum value for parameter',
                             'Unit of the parameter']
        for column, tooltip in enumerate(header_tooltips):
             self.assertEqual(self.widget._magnet_model.headerData(column,
                QtCore.Qt.Horizontal, QtCore.Qt.ToolTipRole),
                         header_tooltips[column])

        # Test rows
        for row in xrange(self.widget._magnet_model.rowCount()):
            func_index = self.widget._magnet_model.index(row, 0)
            self.assertIn(':', self.widget._magnet_model.item(row, 0).text())


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
        last_row = self.widget._last_model_row
        func_index = self.widget._model_model.index(last_row-1, 1)
        self.assertIsInstance(self.widget.lstParams.indexWidget(func_index), QtGui.QComboBox)

        # Change the combo box index
        self.widget.lstParams.indexWidget(func_index).setCurrentIndex(3)

        # Check that the number of rows increased
        more_rows = self.widget._model_model.rowCount() - last_row
        self.assertEqual(more_rows, 6) # 6 new rows: 2 params per index

        # Back to 0
        self.widget.lstParams.indexWidget(func_index).setCurrentIndex(0)
        self.assertEqual(self.widget._model_model.rowCount(), last_row)

    def testPlotTheory(self):
        """
        See that theory item can produce a chart
        """
        # By default, the compute/plot button is disabled
        self.assertFalse(self.widget.cmdPlot.isEnabled())
        self.assertEqual(self.widget.cmdPlot.text(), 'Show Plot')

        # Assign a model
        self.widget.show()
        # Change the category index so we have a model available
        category_index = self.widget.cbCategory.findText("Sphere")
        self.widget.cbCategory.setCurrentIndex(category_index)

        # Check the enablement/text
        self.assertTrue(self.widget.cmdPlot.isEnabled())
        self.assertEqual(self.widget.cmdPlot.text(), 'Calculate')

        # Spying on plot update signal
        spy = QtSignalSpy(self.widget, self.widget.communicate.plotRequestedSignal)

        # Press Calculate
        QtTest.QTest.mouseClick(self.widget.cmdPlot, QtCore.Qt.LeftButton)

        # Observe cmdPlot caption change
        self.assertEqual(self.widget.cmdPlot.text(), 'Show Plot')

        # Make sure the signal has NOT been emitted
        self.assertEqual(spy.count(), 0)

        # Click again
        QtTest.QTest.mouseClick(self.widget.cmdPlot, QtCore.Qt.LeftButton)

        # This time, we got the update signal
        self.assertEqual(spy.count(), 0)

    def testPlotData(self):
        """
        See that data item can produce a chart
        """
        # By default, the compute/plot button is disabled
        self.assertFalse(self.widget.cmdPlot.isEnabled())
        self.assertEqual(self.widget.cmdPlot.text(), 'Show Plot')

        self.widget.show()

        # Set data
        test_data = Data1D(x=[1,2], y=[1,2])

        # Force same data into logic
        self.widget.logic.data = test_data
        self.widget.data_is_loaded = True

        # Change the category index so we have a model available
        category_index = self.widget.cbCategory.findText("Sphere")
        self.widget.cbCategory.setCurrentIndex(category_index)

        # Check the enablement/text
        self.assertTrue(self.widget.cmdPlot.isEnabled())
        self.assertEqual(self.widget.cmdPlot.text(), 'Show Plot')

        # Spying on plot update signal
        spy = QtSignalSpy(self.widget, self.widget.communicate.plotRequestedSignal)

        # Press Calculate
        QtTest.QTest.mouseClick(self.widget.cmdPlot, QtCore.Qt.LeftButton)

        # Observe cmdPlot caption did not change
        self.assertEqual(self.widget.cmdPlot.text(), 'Show Plot')

        # Make sure the signal has been emitted == new plot
        self.assertEqual(spy.count(), 1)

    def testOnFit1D(self):
        """
        Test the threaded fitting call
        """
        # Set data
        test_data = Data1D(x=[1,2], y=[1,2])
        item = QtGui.QStandardItem()
        updateModelItem(item, [test_data], "test")
        # Force same data into logic
        self.widget.data = item
        category_index = self.widget.cbCategory.findText("Sphere")
        self.widget.cbCategory.setCurrentIndex(category_index)

        self.widget.show()

        # Test no fitting params
        self.widget.parameters_to_fit = []

        with self.assertRaises(ValueError) as error:
            self.widget.onFit()
        self.assertEqual(str(error.exception), 'no fitting parameters')

        # Assing fitting params
        self.widget.parameters_to_fit = ['scale']

        # Spying on status update signal
        update_spy = QtSignalSpy(self.widget, self.widget.communicate.statusBarUpdateSignal)

        with threads.deferToThread as MagicMock:
            self.widget.onFit()
            # thread called
            self.assertTrue(threads.deferToThread.called)
            # thread method is 'compute'
            self.assertEqual(threads.deferToThread.call_args_list[0][0][0].__name__, 'compute')

            # the fit button changed caption and got disabled
            self.assertEqual(self.widget.cmdFit.text(), 'Running...')
            self.assertFalse(self.widget.cmdFit.isEnabled())

            # Signal pushed up
            self.assertEqual(update_spy.count(), 1)

    def testOnFit2D(self):
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
        updateModelItem(item, [test_data], "test")
        # Force same data into logic
        self.widget.data = item
        category_index = self.widget.cbCategory.findText("Sphere")
        self.widget.cbCategory.setCurrentIndex(category_index)

        self.widget.show()

        # Test no fitting params
        self.widget.parameters_to_fit = []

        with self.assertRaises(ValueError) as error:
            self.widget.onFit()
        self.assertEqual(str(error.exception), 'no fitting parameters')

        # Assing fitting params
        self.widget.parameters_to_fit = ['scale']

        # Spying on status update signal
        update_spy = QtSignalSpy(self.widget, self.widget.communicate.statusBarUpdateSignal)

        with threads.deferToThread as MagicMock:
            self.widget.onFit()
            # thread called
            self.assertTrue(threads.deferToThread.called)
            # thread method is 'compute'
            self.assertEqual(threads.deferToThread.call_args_list[0][0][0].__name__, 'compute')

            # the fit button changed caption and got disabled
            self.assertEqual(self.widget.cmdFit.text(), 'Running...')
            self.assertFalse(self.widget.cmdFit.isEnabled())

            # Signal pushed up
            self.assertEqual(update_spy.count(), 1)

    def testOnHelp(self):
        """
        Test various help pages shown in this widget
        """
        #Mock the QWebView method
        QtWebKit.QWebView.show = MagicMock()
        QtWebKit.QWebView.load = MagicMock()

        # Invoke the action on default tab
        self.widget.onHelp()
        # Check if show() got called
        self.assertTrue(QtWebKit.QWebView.show.called)
        # Assure the filename is correct
        self.assertIn("fitting_help.html", QtWebKit.QWebView.load.call_args[0][0].toString())

        # Change the tab to options
        self.widget.tabFitting.setCurrentIndex(1)
        self.widget.onHelp()
        # Check if show() got called
        self.assertEqual(QtWebKit.QWebView.show.call_count, 2)
        # Assure the filename is correct
        self.assertIn("residuals_help.html", QtWebKit.QWebView.load.call_args[0][0].toString())

        # Change the tab to smearing
        self.widget.tabFitting.setCurrentIndex(2)
        self.widget.onHelp()
        # Check if show() got called
        self.assertEqual(QtWebKit.QWebView.show.call_count, 3)
        # Assure the filename is correct
        self.assertIn("sm_help.html", QtWebKit.QWebView.load.call_args[0][0].toString())

        # Change the tab to poly
        self.widget.tabFitting.setCurrentIndex(3)
        self.widget.onHelp()
        # Check if show() got called
        self.assertEqual(QtWebKit.QWebView.show.call_count, 4)
        # Assure the filename is correct
        self.assertIn("pd_help.html", QtWebKit.QWebView.load.call_args[0][0].toString())

        # Change the tab to magnetism
        self.widget.tabFitting.setCurrentIndex(4)
        self.widget.onHelp()
        # Check if show() got called
        self.assertEqual(QtWebKit.QWebView.show.call_count, 5)
        # Assure the filename is correct
        self.assertIn("mag_help.html", QtWebKit.QWebView.load.call_args[0][0].toString())

    def testReadFitPage(self):
        """
        Read in the fitpage object and restore state
        """
        # Set data
        test_data = Data1D(x=[1,2], y=[1,2])

        # Force same data into logic
        self.widget.logic.data = test_data
        self.widget.data_is_loaded = True
        category_index = self.widget.cbCategory.findText('Sphere')
        self.widget.cbCategory.setCurrentIndex(category_index)
        self.widget.parameters_to_fit = ['scale']
        # Invoke the tested method
        fp = self.widget.currentState()

        # Prepare modified fit page
        fp.current_model = 'onion'
        fp.is_polydisperse = True

        # Read in modified state
        self.widget.readFitPage(fp)

        # Check if the widget got updated accordingly
        self.assertEqual(self.widget.cbModel.currentText(), 'onion')
        self.assertTrue(self.widget.chkPolydispersity.isChecked())
        #Check if polidispersity tab is available
        self.assertTrue(self.widget.tabFitting.isTabEnabled(3))

        #Check if magnetism box and tab are disabled when 1D data is loaded
        self.assertFalse(self.widget.chkMagnetism.isEnabled())
        self.assertFalse(self.widget.tabFitting.isTabEnabled(4))

    def testReadFitPage2D(self):
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
        self.widget.parameters_to_fit = ['scale']

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
        self.assertEqual(self.widget.cbModel.currentText(), 'cylinder')
        self.assertTrue(self.widget.chkPolydispersity.isChecked())
        self.assertTrue(self.widget.chkPolydispersity.isEnabled())
        #Check if polidispersity tab is available
        self.assertTrue(self.widget.tabFitting.isTabEnabled(3))

        #Check if magnetism box and tab are disabled when 1D data is loaded
        self.assertTrue(self.widget.chkMagnetism.isChecked())
        self.assertTrue(self.widget.chkMagnetism.isEnabled())
        self.assertTrue(self.widget.tabFitting.isTabEnabled(4))

    def testCurrentState(self):
        """
        Set up the fitpage with current state
        """
        # Set data
        test_data = Data1D(x=[1,2], y=[1,2])

        # Force same data into logic
        self.widget.logic.data = test_data
        self.widget.data_is_loaded = True
        category_index = self.widget.cbCategory.findText("Sphere")
        self.widget.cbCategory.setCurrentIndex(category_index)
        self.widget.parameters_to_fit = ['scale']

        # Invoke the tested method
        fp = self.widget.currentState()

        # Test some entries. (Full testing of fp is done in FitPageTest)
        self.assertIsInstance(fp.data, Data1D)
        self.assertListEqual(list(fp.data.x), [1,2])
        self.assertTrue(fp.data_is_loaded)
        self.assertEqual(fp.current_category, "Sphere")
        self.assertEqual(fp.current_model, "adsorbed_layer")
        self.assertListEqual(fp.parameters_to_fit, ['scale'])

    def testPushFitPage(self):
        """
        Push current state of fitpage onto stack
        """
        # Set data
        test_data = Data1D(x=[1,2], y=[1,2])

        # Force same data into logic
        self.widget.logic.data = test_data
        self.widget.data_is_loaded = True
        category_index = self.widget.cbCategory.findText("Sphere")

        # Asses the initial state of stack
        self.assertEqual(self.widget.page_stack, [])

        # Set the undo flag
        self.widget.undo_supported = True
        self.widget.cbCategory.setCurrentIndex(category_index)
        self.widget.parameters_to_fit = ['scale']

        # Check that the stack is updated
        self.assertEqual(len(self.widget.page_stack), 1)

        # Change another parameter
        self.widget._model_model.item(2, 1).setText("3.0")
        # Check that the stack is updated
        self.assertEqual(len(self.widget.page_stack), 2)

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
        self.assertEqual(self.widget._model_model.rowCount(), 6)
        self.assertEqual(self.widget._model_model.columnCount(), 5)

        # Test the header
        #self.assertEqual(self.widget.lstParams.horizontalHeader().count(), 5)
        #self.assertFalse(self.widget.lstParams.horizontalHeader().stretchLastSection())

        self.assertEqual(len(self.widget._model_model.header_tooltips), 5)
        header_tooltips = ['Select parameter for fitting',
                             'Enter parameter value',
                             'Enter minimum value for parameter',
                             'Enter maximum value for parameter',
                             'Unit of the parameter']
        for column, tooltip in enumerate(header_tooltips):
             self.assertEqual(self.widget._model_model.headerData(column,
                QtCore.Qt.Horizontal, QtCore.Qt.ToolTipRole),
                         header_tooltips[column])

        # check that the value has been modified in kernel_module
        self.assertEqual(new_value,
                         str(self.widget.kernel_module.params[name_modified_param]))

        # check that range of variation for this parameter has NOT been changed
        print self.widget.kernel_module.details[name_modified_param]
        self.assertNotIn(new_value, self.widget.kernel_module.details[name_modified_param] )


if __name__ == "__main__":
    unittest.main()
