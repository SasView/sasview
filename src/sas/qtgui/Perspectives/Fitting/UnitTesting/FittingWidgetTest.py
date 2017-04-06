import sys
import unittest

from PyQt4 import QtGui
from PyQt4 import QtTest
from PyQt4 import QtCore
from mock import MagicMock
from twisted.internet import threads

# set up import paths
import sas.qtgui.path_prepare

# Local
from sas.qtgui.GuiUtils import *
from sas.qtgui.Perspectives.Fitting.FittingWidget import *
from sas.qtgui.UnitTesting.TestUtils import QtSignalSpy

from sas.sasgui.guiframe.dataFitting import Data1D

app = QtGui.QApplication(sys.argv)

class dummy_manager(object):
    def communicate(self):
        return Communicate()

class FittingWidgetTest(unittest.TestCase):
    """Test the fitting widget GUI"""

    def setUp(self):
        """Create the GUI"""
        self.widget = FittingWidget(dummy_manager())

    def tearDown(self):
        """Destroy the GUI"""
        self.widget.close()
        self.widget = None

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

    def testSelectCategory(self):
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

        widget_with_data = FittingWidget(dummy_manager(), data=item, id=3)

        self.assertEqual(widget_with_data.data, data)
        self.assertTrue(widget_with_data.data_is_loaded)
        # self.assertTrue(widget_with_data.cmdFit.isEnabled())
        self.assertFalse(widget_with_data.acceptsData())

    def notestSelectModel(self):
        """
        Test if models have been loaded properly
        :return:
        """
        fittingWindow =  self.widget

        #Test loading from json categories
        model_list = fittingWindow.master_category_dict["Cylinder"]
        self.assertTrue(['cylinder', True] in model_list)
        self.assertTrue(['core_shell_cylinder', True] in model_list)
        self.assertTrue(['barbell', True] in model_list)
        self.assertTrue(['core_shell_bicelle', True] in model_list)
        self.assertTrue(['flexible_cylinder', True] in model_list)
        self.assertTrue(['flexible_cylinder_elliptical', True] in model_list)
        self.assertTrue(['pearl_necklace', True] in model_list)
        self.assertTrue(['capped_cylinder', True] in model_list)
        self.assertTrue(['elliptical_cylinder', True] in model_list)
        self.assertTrue(['pringle', True] in model_list)
        self.assertTrue(['hollow_cylinder', True] in model_list)
        self.assertTrue(['core_shell_bicelle_elliptical', True] in model_list)
        self.assertTrue(['stacked_disks', True] in model_list)

        #Test for existence in combobox
        self.assertNotEqual(fittingWindow.cbModel.findText("cylinder"),-1)
        self.assertNotEqual(fittingWindow.cbModel.findText("core_shell_cylinder"),-1)
        self.assertNotEqual(fittingWindow.cbModel.findText("barbell"),-1)
        self.assertNotEqual(fittingWindow.cbModel.findText("core_shell_bicelle"),-1)
        self.assertNotEqual(fittingWindow.cbModel.findText("flexible_cylinder"),-1)
        self.assertNotEqual(fittingWindow.cbModel.findText("flexible_cylinder_elliptical"),-1)
        self.assertNotEqual(fittingWindow.cbModel.findText("pearl_necklace"),-1)
        self.assertNotEqual(fittingWindow.cbModel.findText("capped_cylinder"),-1)
        self.assertNotEqual(fittingWindow.cbModel.findText("elliptical_cylinder"),-1)
        self.assertNotEqual(fittingWindow.cbModel.findText("pringle"),-1)
        self.assertNotEqual(fittingWindow.cbModel.findText("hollow_cylinder"),-1)
        self.assertNotEqual(fittingWindow.cbModel.findText("core_shell_bicelle_elliptical"),-1)
        self.assertNotEqual(fittingWindow.cbModel.findText("stacked_disks"),-1)


    def testSelectPolydispersity(self):
        """
        Test if models have been loaded properly
        :return:
        """
        fittingWindow =  self.widget

        #Test loading from json categories
        fittingWindow.SASModelToQModel("cylinder")
        pd_index = fittingWindow.lstPoly.model().index(0,0)
        self.assertEqual(str(pd_index.data().toString()), "Distribution of radius")
        pd_index = fittingWindow.lstPoly.model().index(1,0)
        self.assertEqual(str(pd_index.data().toString()), "Distribution of length")

    def testSelectStructureFactor(self):
        """
        Test if structure factors have been loaded properly
        :return:
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

    def  testSelectCategory(self):
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


        # TODO once functionality fixed
        ## Switch category to structure factor
        #structure_index=self.widget.cbCategory.findText(CATEGORY_STRUCTURE)
        #self.widget.cbCategory.setCurrentIndex(structure_index)
        ## Choose the last factor
        #last_index = self.widget.cbStructureFactor.count()
        #self.widget.cbStructureFactor.setCurrentIndex(last_index-1)

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

    def notestCreateTheoryIndex(self):
        """
        Test the data->QIndex conversion
        """
        # set up the model update spy
        spy = QtSignalSpy(self.widget._model_model, self.widget.communicate.updateTheoryFromPerspectiveSignal)

        self.widget.show()
        # Change the category index so we have some models
        self.widget.cbCategory.setCurrentIndex(1)

        # Create the index
        self.widget.createTheoryIndex()

        # Check the signal sent
        print spy

        # Check the index

    def testCalculateQGridForModel(self):
        """
        Check that the fitting 1D data object is ready
        """
        # Mock the thread creation
        threads.deferToThread = MagicMock()
        # Call the tested method
        self.widget.calculateQGridForModel()
        # Test the mock
        self.assertTrue(threads.deferToThread.called)
        self.assertEqual(threads.deferToThread.call_args_list[0][0][0].__name__, "compute")

    def testComplete1D(self):
        """
        Check that a new 1D plot is generated
        """
        # TODO when chisqr method coded
        pass

    def testComplete2D(self):
        """
        Check that a new 2D plot is generated
        """
        # TODO when chisqr method coded
        pass

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
        self.assertEqual(self.widget._poly_model.columnCount(), 7)

        # Test the header
        self.assertEqual(self.widget.lstPoly.horizontalHeader().count(), 7)
        self.assertFalse(self.widget.lstPoly.horizontalHeader().stretchLastSection())

        # Test presence of comboboxes in last column
        for row in xrange(self.widget._poly_model.rowCount()):
            func_index = self.widget._poly_model.index(row, 6)
            self.assertTrue(isinstance(self.widget.lstPoly.indexWidget(func_index), QtGui.QComboBox))
            self.assertIn('Distribution of', self.widget._poly_model.item(row, 0).text())

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


if __name__ == "__main__":
    unittest.main()
