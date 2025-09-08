
import pytest
from PySide6 import QtCore, QtGui

from sasmodels import generate, modelinfo
from sasmodels.sasview_model import load_standard_models

# Tested module
from sas.qtgui.Perspectives.Fitting import FittingUtilities
from sas.qtgui.Perspectives.Fitting.FittingUtilities import checkConstraints
from sas.qtgui.Plotting.PlotterData import Data1D, Data2D


class FittingUtilitiesTest:
    '''Test the Fitting Utilities functions'''

    def testReplaceShellName(self):
        """
        Test the utility function for string manipulation
        """
        param_name = "test [123]"
        value = "replaced"
        result = FittingUtilities.replaceShellName(param_name, value)

        assert result == "test replaced"

        # Assert!
        param_name = "no brackets"
        with pytest.raises(AssertionError):
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
        assert params == []

        # Use a multi-shell parameter
        model_name = "core_multi_shell"
        kernel_module = generate.load_kernel_module(model_name)
        multishell_parameters = modelinfo.make_parameter_table(getattr(kernel_module, 'parameters', []))

        params = FittingUtilities.getIterParams(multishell_parameters)
        # returns a non-empty list
        assert params != []
        assert 'sld' in str(params)
        assert 'thickness' in str(params)

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
        assert param_name == ""
        assert param_length == 0

        # Use a multi-shell parameter
        model_name = "core_multi_shell"
        kernel_module = generate.load_kernel_module(model_name)
        multishell_parameters = modelinfo.make_parameter_table(getattr(kernel_module, 'parameters', []))

        param_name, param_length = FittingUtilities.getMultiplicity(multishell_parameters)

        assert param_name == "n"
        assert param_length == 10

    def testAddParametersToModel(self):
        """
        Checks the QModel update from Sasmodel parameters
        """
        # Use a single-shell parameter
        model_name = "barbell"
        models = load_standard_models()

        kernel_module = generate.load_kernel_module(model_name)
        kernel_module_o = None
        for model in models:
            if model.name == model_name:
                kernel_module_o = model()
        assert kernel_module_o is not None
        barbell_parameters = modelinfo.make_parameter_table(getattr(kernel_module, 'parameters', []))

        params = FittingUtilities.addParametersToModel(barbell_parameters, kernel_module_o, True)

        # Test the resulting model
        assert len(params) == 7
        assert len(params[0]) == 5
        assert params[0][0].isCheckable()
        assert params[0][0].text() == "sld"
        assert params[1][0].text() == "sld_solvent"

        # Use a multi-shell parameter to see that the method includes shell params
        model_name = "core_multi_shell"
        kernel_module = generate.load_kernel_module(model_name)
        kernel_module_o = None
        for model in models:
            if model.name == model_name:
                kernel_module_o = model()
        assert kernel_module_o is not None
        multi_parameters = modelinfo.make_parameter_table(getattr(kernel_module, 'parameters', []))

        params = FittingUtilities.addParametersToModel(multi_parameters, kernel_module_o, False)

        # Test the resulting model
        assert len(params) == 3
        assert len(params[0]) == 5
        assert params[0][0].isCheckable()
        assert params[0][0].text() == "sld_core"
        assert params[1][0].text() == "radius"

    def testAddSimpleParametersToModel(self):
        """
        Checks the QModel update from Sasmodel parameters - no polydisp
        """
        # Use a multi-shell parameter to see that the method doesn't include shells
        model_name = "core_multi_shell"
        kernel_module = generate.load_kernel_module(model_name)
        models = load_standard_models()
        kernel_module_o = None
        for model in models:
            if model.name == model_name:
                kernel_module_o = model()
        assert kernel_module_o is not None
        multi_parameters = modelinfo.make_parameter_table(getattr(kernel_module, 'parameters', []))

        params = FittingUtilities.addParametersToModel(multi_parameters, kernel_module_o, True)

        # Test the resulting model
        assert len(params) == 3
        assert len(params[0]) == 5
        assert params[0][0].isCheckable()
        assert params[0][0].text() == "sld_core"
        assert params[1][0].text() == "radius"

    def testAddCheckedListToModel(self):
        """
        Test for inserting a checkboxed item into a QModel
        """
        model = QtGui.QStandardItemModel()
        params = ["row1", "row2", "row3"]

        FittingUtilities.addCheckedListToModel(model, params)

        # Check the model
        assert model.rowCount() == 1
        assert model.item(0).isCheckable()
        assert model.item(0, 0).text() == params[0]
        assert model.item(0, 1).text() == params[1]
        assert model.item(0, 2).text() == params[2]

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
        assert model.rowCount() == 4

        model = QtGui.QStandardItemModel()
        index = 5
        FittingUtilities.addShellsToModel(multi_parameters, model, index)
        assert model.rowCount() == 10

        assert model.item(1).child(0).text() == "Polydispersity"
        assert model.item(1).child(0).child(0).text() == "Distribution"
        assert model.item(1).child(0).child(0,1).text() == "40.0"

    def testCalculate1DChi2(self):
        """
        Test the chi2 calculator for Data1D
        """
        reference_data = Data1D(x=[0.1, 0.2], y=[0.0, 0.0])

        # 1. identical data
        current_data = Data1D(x=[0.1, 0.2], y=[0.0, 0.0])
        weights = None
        chi = FittingUtilities.calculateChi2(reference_data, current_data, weights)

        # Should be zero
        assert chi == pytest.approx(0.0, abs=1e-8)

        # 2. far data
        current_data = Data1D(x=[0.1, 0.2], y=[200.0, 150.0])

        chi = FittingUtilities.calculateChi2(reference_data, current_data, weights)

        # Should not be zero
        assert chi == pytest.approx(31250.0, rel=1e-8)

        # 3. Wrong data
        current_data = Data1D(x=[0.1, 0.2], y=[200.0, 150.0, 200.0])
        chi = FittingUtilities.calculateChi2(reference_data, current_data, weights)
        # Should remain unchanged
        assert chi == pytest.approx(31250.0, rel=1e-8)

    def testCalculate2DChi2(self):
        """
        Test the chi2 calculator for Data2D
        """
        reference_data = Data2D(image=[1.0, 2.0, 3.0],
                      err_image=[0.01, 0.02, 0.03],
                      qx_data=[0.1, 0.2, 0.3],
                      qy_data=[0.1, 0.2, 0.3])

        # 1. identical data
        current_data = Data2D(image=[1.0, 2.0, 3.0],
                      err_image=[0.01, 0.02, 0.03],
                      qx_data=[0.1, 0.2, 0.3],
                      qy_data=[0.1, 0.2, 0.3])

        weights = None
        chi = FittingUtilities.calculateChi2(reference_data, current_data, weights)

        # Should be zero
        assert chi == pytest.approx(0.0, abs=1e-8)

        # 2. far data
        current_data = Data2D(image=[100.0, 200.0, 300.0],
                      err_image=[1.01, 2.02, 3.03],
                      qx_data=[0.1, 0.2, 0.3],
                      qy_data=[100.0, 200., 300.])

        chi = FittingUtilities.calculateChi2(reference_data, current_data, weights)

        # Should not be zero
        assert chi == pytest.approx(9607.88, abs=1e-2)

        # 3. Wrong data
        current_data = Data2D(image=[1.0, 2.0, 3.0],
                      err_image=[0.01, 0.02],
                      qx_data=[0.1, 0.2],
                      qy_data=[0.1, 0.2, 0.3])
        # Should throw
        with pytest.raises(ValueError):
            chi = FittingUtilities.calculateChi2(reference_data, current_data, weights)

    def notestAddHeadersToModel(self):
        '''Check to see if headers are correctly applied'''
        #test model
        model = QtGui.QStandardItemModel()
        FittingUtilities.addHeadersToModel(model)

        # Assure we have properly named columns
        names = FittingUtilities.model_header_captions
        names_from_model = [model.headerData(i, QtCore.Qt.Horizontal) for i in range(len(names))]
        assert names == names_from_model

        # Add another model
        model2 = QtGui.QStandardItemModel()
        # Add headers again
        FittingUtilities.addHeadersToModel(model2)
        # We still should have only the original names
        names_from_model2 = [model2.headerData(i, QtCore.Qt.Horizontal) for i in range(len(names))]
        assert names == names_from_model2

    def testCheckConstraints(self):
        ''' Test the constraints checks'''
        # Send a valid constraint
        symtab = {"M1.scale": 1, "M1.background": 1}
        constraints = [("M1.scale", "M1.background")]
        errors = checkConstraints(symtab, constraints)
        assert errors == []

        # Send a constraint with an error
        constraints = [("M1.foo", "M1.background")]
        errors = checkConstraints(symtab, constraints)
        assert isinstance(errors, str)
