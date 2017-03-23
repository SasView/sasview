import sys
import unittest
from PyQt4 import QtGui

from UnitTesting.TestUtils import WarningTestNotImplemented
#from sasmodels.sasview_model import load_standard_models
from sasmodels import generate
from sasmodels import modelinfo

# Tested module
from sas.qtgui.Perspectives.Fitting import FittingUtilities

class FittingUtilitiesTest(unittest.TestCase):
    '''Test the Fitting Utilities functions'''
    def setUp(self):
        '''Empty'''
        pass

    def tearDown(self):
        '''Empty'''
        pass

    def testReplaceShellName(self):
        """
        Test the utility function for string manipulation
        """
        param_name = "test [123]"
        value = "replaced"
        result = FittingUtilities.replaceShellName(param_name, value)
        
        self.assertEqual(result, "test replaced")

        # Assert!
        param_name = "no brackets"
        with self.assertRaises(AssertionError):
            result = FittingUtilities.replaceShellName(param_name, value)

        
    def testGetIterParams(self):
        """
        Assure the right multishell parameters are returned
        """
        # Use a single-shell parameter
        model_name = "barbell"
        kernel_module = generate.load_kernel_module(model_name)
        barbell_parameters = modelinfo.make_parameter_table(getattr(kernel_module, 'parameters', []))

        params = FittingUtilities.getIterParams(barbell_parameters)
        # returns empty list
        self.assertEqual(params, [])

        # Use a multi-shell parameter
        model_name = "core_multi_shell"
        kernel_module = generate.load_kernel_module(model_name)
        multishell_parameters = modelinfo.make_parameter_table(getattr(kernel_module, 'parameters', []))

        params = FittingUtilities.getIterParams(multishell_parameters)
        # returns a non-empty list
        self.assertNotEqual(params, [])
        self.assertIn('sld', str(params))
        self.assertIn('thickness', str(params))

    def testGetMultiplicity(self):
        """
        Assure more multishell parameters are evaluated correctly
        """
        # Use a single-shell parameter
        model_name = "barbell"
        kernel_module = generate.load_kernel_module(model_name)
        barbell_parameters = modelinfo.make_parameter_table(getattr(kernel_module, 'parameters', []))

        param_name, param_length = FittingUtilities.getMultiplicity(barbell_parameters)
        # returns nothing
        self.assertEqual(param_name, "")
        self.assertEqual(param_length, 0)

        # Use a multi-shell parameter
        model_name = "core_multi_shell"
        kernel_module = generate.load_kernel_module(model_name)
        multishell_parameters = modelinfo.make_parameter_table(getattr(kernel_module, 'parameters', []))

        param_name, param_length = FittingUtilities.getMultiplicity(multishell_parameters)

        self.assertEqual(param_name, "n")
        self.assertEqual(param_length, 10)

    def testAddParametersToModel(self):
        """
        Checks the QModel update from Sasmodel parameters
        """
        # Use a single-shell parameter
        model_name = "barbell"
        kernel_module = generate.load_kernel_module(model_name)
        barbell_parameters = modelinfo.make_parameter_table(getattr(kernel_module, 'parameters', []))

        model = QtGui.QStandardItemModel()

        FittingUtilities.addParametersToModel(barbell_parameters, model)

        # Test the resulting model
        self.assertEqual(model.rowCount(), 5)
        self.assertTrue(model.item(0).isCheckable())
        self.assertEqual(model.item(0).text(), "sld")
        self.assertEqual(model.item(1).text(), "sld_solvent")

        # Use a multi-shell parameter to see that the method includes shell params
        model_name = "core_multi_shell"
        kernel_module = generate.load_kernel_module(model_name)
        multi_parameters = modelinfo.make_parameter_table(getattr(kernel_module, 'parameters', []))

        model = QtGui.QStandardItemModel()

        FittingUtilities.addParametersToModel(multi_parameters, model)

        # Test the resulting model
        self.assertEqual(model.rowCount(), 3)
        self.assertTrue(model.item(0).isCheckable())
        self.assertEqual(model.item(0).text(), "sld_core")
        self.assertEqual(model.item(1).text(), "radius")
        self.assertEqual(model.item(2).text(), "sld_solvent")

    def testAddSimpleParametersToModel(self):
        """
        Checks the QModel update from Sasmodel parameters - no polydisp
        """
        # Use a multi-shell parameter to see that the method doesn't include shells
        model_name = "core_multi_shell"
        kernel_module = generate.load_kernel_module(model_name)
        multi_parameters = modelinfo.make_parameter_table(getattr(kernel_module, 'parameters', []))

        model = QtGui.QStandardItemModel()

        FittingUtilities.addParametersToModel(multi_parameters, model)

        # Test the resulting model
        self.assertEqual(model.rowCount(), 3)
        self.assertTrue(model.item(0).isCheckable())
        self.assertEqual(model.item(0).text(), "sld_core")
        self.assertEqual(model.item(1).text(), "radius")

    def testAddCheckedListToModel(self):
        """
        Test for inserting a checkboxed item into a QModel
        """
        model = QtGui.QStandardItemModel()
        params = ["row1", "row2", "row3"]

        FittingUtilities.addCheckedListToModel(model, params)

        # Check the model
        self.assertEqual(model.rowCount(), 1)
        self.assertTrue(model.item(0).isCheckable())
        self.assertEqual(model.item(0, 0).text(), params[0])
        self.assertEqual(model.item(0, 1).text(), params[1])
        self.assertEqual(model.item(0, 2).text(), params[2])

    def testAddShellsToModel(self):
        """
        Test for inserting a list of QItems into a model
        """
        # Use a multi-shell parameter to see that the method doesn't include shells
        model_name = "core_multi_shell"
        kernel_module = generate.load_kernel_module(model_name)
        multi_parameters = modelinfo.make_parameter_table(getattr(kernel_module, 'parameters', []))

        model = QtGui.QStandardItemModel()

        index = 2
        FittingUtilities.addShellsToModel(multi_parameters, model, index)
        # There should be index*len(multi_parameters) new rows
        self.assertEqual(model.rowCount(), 4)

        model = QtGui.QStandardItemModel()
        index = 5
        FittingUtilities.addShellsToModel(multi_parameters, model, index)
        self.assertEqual(model.rowCount(), 10)
        
        self.assertEqual(model.item(1).child(0).text(), "Polydispersity")
        self.assertEqual(model.item(1).child(0).child(0).text(), "Distribution")
        self.assertEqual(model.item(1).child(0).child(0,1).text(), "40.0")

if __name__ == "__main__":
    unittest.main()
