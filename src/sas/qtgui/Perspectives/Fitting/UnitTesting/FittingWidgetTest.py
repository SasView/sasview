import sys
import unittest

from PyQt4 import QtGui
from PyQt4 import QtTest
from PyQt4 import QtCore
from mock import MagicMock

# set up import paths
import sas.qtgui.path_prepare

# Local
from sas.qtgui.GuiUtils import *
from sas.qtgui.Perspectives.Fitting.FittingWidget import *
#from sas.qtgui.Perspectives.Fitting.FittingWidget import FittingWidget
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

        widget_with_data = FittingWidget(dummy_manager(), data=[data], id=3)

        self.assertEqual(widget_with_data.data, data)
        self.assertTrue(widget_with_data.data_is_loaded)
        self.assertTrue(widget_with_data.cmdFit.isEnabled())
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
        fittingWindow.setModelModel("cylinder")
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
        Test the widget exmitted signals
        """
        pass

    def  testSelectCategory(self):
        """
        Assure proper behaviour on changing category
        """
        pass

    def testSelectModel(self):
        """
        Assure proper behaviour on changing model
        """
        pass

    def testSelectFactor(self):
        """
        Assure proper behaviour on changing structure factor
        """
        pass

    def testReadCategoryInfo(self):
        """
        Check the category file reader
        """
        pass

    def testGetIterParams(self):
        """
        Assure the right multishell parameters are returned
        """
        pass

    def testGetMultiplicity(self):
        """
        Assure more multishell parameters are evaluated correctly
        """
        pass

    def testAddCheckedListToModel(self):
        """
        Test for utility function
        """
        pass

    def testUpdateParamsFromModel(self):
        """
        Checks the sasmodel parameter update from QModel items
        """
        pass

    def testComputeDataRange(self):
        """
        Tests the data range calculator on Data1D/Data2D
        """
        pass

    def testAddParametersToModel(self):
        """
        Checks the QModel update from Sasmodel parameters
        """
        pass

    def testAddSimpleParametersToModel(self):
        """
        Checks the QModel update from Sasmodel parameters - no polydisp
        """
        pass

    def testCreateDefault1dData(self):
        """
        Tests the default 1D set
        """
        pass

    def testCreateDefault2dData(self):
        """
        Tests the default 2D set
        """
        pass

    def testCreateTheoryIndex(self):
        """
        Test the data->QIndex conversion
        """
        pass

    def testCalculate1DForModel(self):
        """
        Check that the fitting 1D data object is ready
        """
        pass

    def testCalculate2DForModel(self):
        """
        Check that the fitting 2D data object is ready
        """
        pass

    def testComplete1D(self):
        """
        Check that a new 1D plot is generated
        """
        pass

    def testComplete2D(self):
        """
        Check that a new 2D plot is generated
        """
        pass

    def testReplaceShellName(self):
        """
        Test the utility function for string manipulation
        """
        pass

    def testSetPolyModel(self):
        """
        Test the polydispersity model setup
        """
        pass

    def testSetMagneticModel(self):
        """
        Test the magnetic model setup
        """
        pass

    def testAddExtraShells(self):
        """
        Test how the extra shells are presented
        """
        pass

    def testModifyShellsInList(self):
        """
        Test the additional rows added by modifying the shells combobox
        """
        pass


if __name__ == "__main__":
    unittest.main()
