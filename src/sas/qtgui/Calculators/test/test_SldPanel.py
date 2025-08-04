import sys
import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from PySide6 import QtCore, QtWidgets, QtGui

from sas.qtgui.Calculators.SldPanel import SldPanel, MODEL, neutronSldAlgorithm, xraySldAlgorithm

# Global QApplication instance
_app = None

def setup_module():
    """Create QApplication before any tests run"""
    global _app
    if not QtWidgets.QApplication.instance():
        _app = QtWidgets.QApplication([])

def teardown_module():
    """Delete QApplication after all tests complete"""
    global _app
    if _app is not None:
        _app = None

class TestSldPanel:
    """Test class for SldPanel"""

    @classmethod
    def setup_class(cls):
        """Set up class-level resources"""
        setup_module()

    @pytest.fixture
    def panel(self):
        """Create the SLD panel for each test"""
        parent = MagicMock()
        
        # Skip the Qt UI initialization to avoid issues
        with patch('sas.qtgui.Calculators.SldPanel.SldPanel.__init__') as mock_init:
            mock_init.return_value = None
            
            # Create the panel
            panel = SldPanel()
            
            # Set up the panel manually
            panel.manager = parent
            panel.ui = MagicMock()
            panel.model = MagicMock()
            
            # Mock all the UI components that are used
            panel.ui.editMolecularFormula = MagicMock()
            panel.ui.editMassDensity = MagicMock()
            panel.ui.editNeutronWavelength = MagicMock()
            panel.ui.editXrayWavelength = MagicMock()
            panel.ui.editNeutronSldReal = MagicMock()
            panel.ui.editNeutronSldImag = MagicMock()
            panel.ui.editXraySldReal = MagicMock()
            panel.ui.editXraySldImag = MagicMock()
            panel.ui.editNeutronIncXs = MagicMock()
            panel.ui.editNeutronAbsXs = MagicMock()
            panel.ui.editNeutronLength = MagicMock()
            
            # Set default values for the inputs
            panel.ui.editMolecularFormula.text.return_value = "H2O"
            panel.ui.editMassDensity.text.return_value = "1.0"
            panel.ui.editNeutronWavelength.text.return_value = "6.0"
            panel.ui.editXrayWavelength.text.return_value = "1.0"
            
            # Create items in the model
            for i in range(12):
                panel.model.item.return_value = MagicMock()
            
            yield panel

    def test_displayHelp(self, panel):
        """Test the displayHelp method"""
        panel.displayHelp()
        location = "/user/qtgui/Calculators/sld_calculator_help.html"
        panel.manager.showHelp.assert_called_once_with(location)
    
    def test_closePanel(self, panel):
        """Test the closePanel method"""
        with patch.object(panel, 'close') as mock_close:
            panel.closePanel()
            mock_close.assert_called_once()
    
    def test_setupModel(self, panel):
        """Test the setupModel method"""
        # Mock QtGui.QStandardItemModel and QStandardItem
        with patch('sas.qtgui.Calculators.SldPanel.QtGui.QStandardItemModel', return_value=MagicMock()) as mock_model, \
             patch('sas.qtgui.Calculators.SldPanel.QtGui.QStandardItem', return_value=MagicMock()) as mock_item, \
             patch.object(panel, 'modelReset'):
            
            # Call the method
            panel.model = None  # Reset the model
            panel.setupModel()
            
            # Verify that the model was created
            mock_model.assert_called_once()
            
            # Verify that the required number of items were created (11 in MODEL enum)
            # The MODEL enum has 11 items (0 through 10), not 12
            assert mock_item.call_count == 11
            
            # Verify that modelReset was called
            panel.modelReset.assert_called_once()
    
    def test_setupMapper(self, panel):
        """Test the setupMapper method"""
        # Mock QtWidgets.QDataWidgetMapper
        with patch('sas.qtgui.Calculators.SldPanel.QtWidgets.QDataWidgetMapper', return_value=MagicMock()) as mock_mapper:
            
            # Call the method
            panel.mapper = None  # Reset the mapper
            panel.setupMapper()
            
            # Verify that the mapper was created
            mock_mapper.assert_called_once()
            
            # Verify that the mapper was set up correctly
            panel.mapper.setModel.assert_called_once_with(panel.model)
            panel.mapper.setOrientation.assert_called_once()
            
            # Verify that the correct number of mappings were added (11 in total)
            assert panel.mapper.addMapping.call_count == 11
            
            # Verify that toFirst was called
            panel.mapper.toFirst.assert_called_once()
    
    def test_neutronSldAlgorithm(self):
        """Test the neutronSldAlgorithm function"""
        with patch('sas.qtgui.Calculators.SldPanel.neutron_scattering') as mock_ns:
            # Set up the mock to return test values
            ns_return = ((1.0, -0.1, 0), (0, 0.2, 0.3), 0.4)
            mock_ns.return_value = ns_return
            
            # Call the function
            result = neutronSldAlgorithm("H2O", 1.0, 6.0)
            
            # Verify that neutron_scattering was called with the correct parameters
            mock_ns.assert_called_once_with(compound="H2O", density=1.0, wavelength=6.0)
            
            # Verify the result
            assert result.neutron_wavelength == 6.0
            assert result.neutron_sld_real == 1.0e-6
            assert result.neutron_sld_imag == 0.1e-6
            assert result.neutron_inc_xs == 0.3
            assert result.neutron_abs_xs == 0.2
            assert result.neutron_length == 0.4
    
    def test_xraySldAlgorithm(self):
        """Test the xraySldAlgorithm function"""
        with patch('sas.qtgui.Calculators.SldPanel.xray_sld') as mock_xs:
            # Set up the mock to return test values
            mock_xs.return_value = (2.0, 0.2)
            
            # Call the function
            result = xraySldAlgorithm("H2O", 1.0, 1.0)
            
            # Verify that xray_sld was called with the correct parameters
            mock_xs.assert_called_once_with(compound="H2O", density=1.0, wavelength=1.0)
            
            # Verify the result
            assert result.xray_wavelength == 1.0
            assert result.xray_sld_real == 2.0e-6
            assert result.xray_sld_imag == 0.2e-6
    
    def test_recalculateSLD_valid_inputs(self, panel):
        """Test the recalculateSLD method with valid inputs"""
        # Mock the neutronSldAlgorithm and xraySldAlgorithm functions
        with patch('sas.qtgui.Calculators.SldPanel.neutronSldAlgorithm') as mock_neutron, \
             patch('sas.qtgui.Calculators.SldPanel.xraySldAlgorithm') as mock_xray:
            
            # Set up the mocks to return test values
            neutron_result = MagicMock()
            neutron_result.neutron_sld_real = 1.0
            neutron_result.neutron_sld_imag = 0.1
            neutron_result.neutron_inc_xs = 0.3
            neutron_result.neutron_abs_xs = 0.2
            neutron_result.neutron_length = 0.4
            mock_neutron.return_value = neutron_result
            
            xray_result = MagicMock()
            xray_result.xray_sld_real = 2.0
            xray_result.xray_sld_imag = 0.2
            mock_xray.return_value = xray_result
            
            # Create separate mocks for each model item we'll check
            neutron_sld_real_item = MagicMock()
            neutron_sld_imag_item = MagicMock()
            neutron_inc_xs_item = MagicMock()
            neutron_abs_xs_item = MagicMock()
            neutron_length_item = MagicMock()
            xray_sld_real_item = MagicMock()
            xray_sld_imag_item = MagicMock()
            
            # Set up the model.item to return the appropriate mock based on the index
            panel.model.item.side_effect = lambda idx: {
                MODEL.NEUTRON_SLD_REAL: neutron_sld_real_item,
                MODEL.NEUTRON_SLD_IMAG: neutron_sld_imag_item,
                MODEL.NEUTRON_INC_XS: neutron_inc_xs_item,
                MODEL.NEUTRON_ABS_XS: neutron_abs_xs_item,
                MODEL.NEUTRON_LENGTH: neutron_length_item,
                MODEL.XRAY_SLD_REAL: xray_sld_real_item,
                MODEL.XRAY_SLD_IMAG: xray_sld_imag_item
            }.get(idx, MagicMock())
            
            # Call the method
            panel.recalculateSLD()
            
            # Verify that the algorithms were called with the correct parameters
            mock_neutron.assert_called_once_with("H2O", 1.0, 6.0)
            mock_xray.assert_called_once_with("H2O", 1.0, 1.0)
            
            # Verify that the model items were updated with the correct values
            neutron_sld_real_item.setText.assert_called_with("1")
            neutron_sld_imag_item.setText.assert_called_with("0.1")
            neutron_inc_xs_item.setText.assert_called_with("0.3")
            neutron_abs_xs_item.setText.assert_called_with("0.2")
            neutron_length_item.setText.assert_called_with("0.4")
            xray_sld_real_item.setText.assert_called_with("2")
            xray_sld_imag_item.setText.assert_called_with("0.2")
            
            # Verify that the fields were enabled
            panel.ui.editNeutronSldReal.setEnabled.assert_called_with(True)
            panel.ui.editNeutronSldImag.setEnabled.assert_called_with(True)
            panel.ui.editXraySldReal.setEnabled.assert_called_with(True)
            panel.ui.editXraySldImag.setEnabled.assert_called_with(True)
    
    def test_recalculateSLD_empty_formula(self, panel):
        """Test the recalculateSLD method with empty formula"""
        # Set up the mock to return an empty string
        panel.ui.editMolecularFormula.text.return_value = ""
        
        # Call the method
        panel.recalculateSLD()
        
        # Verify that no further processing was done (no calls to neutronSldAlgorithm or xraySldAlgorithm)
        panel.model.item.assert_not_called()
    
    def test_recalculateSLD_no_density(self, panel):
        """Test the recalculateSLD method with no density"""
        # Set up the mock to return empty density
        panel.ui.editMassDensity.text.return_value = ""
        
        # Call the method
        panel.recalculateSLD()
        
        # Verify that the density field was highlighted
        panel.ui.editMassDensity.setStyleSheet.assert_called_with("background-color: yellow")
        
        # Verify that no further processing was done
        panel.model.item.assert_not_called()
    
    def test_recalculateSLD_error_in_calculation(self, panel):
        """Test the recalculateSLD method with error in calculation"""
        # Mock the neutronSldAlgorithm to raise a ValueError
        with patch('sas.qtgui.Calculators.SldPanel.neutronSldAlgorithm', side_effect=ValueError):
            
            # Call the method
            panel.recalculateSLD()
            
            # Verify that the formula field was highlighted
            panel.ui.editMolecularFormula.setStyleSheet.assert_called_with("background-color: yellow")
            
            # Verify that no model items were updated
            panel.model.item.return_value.setText.assert_not_called()
    
    def test_recalculateSLD_zero_wavelength(self, panel):
        """Test the recalculateSLD method with zero wavelength"""
        # Set up the mock to return zero wavelength
        panel.ui.editNeutronWavelength.text.return_value = "0.0"
        panel.ui.editXrayWavelength.text.return_value = "0.0"
        
        # Call the method
        panel.recalculateSLD()
        
        # Verify that the fields were disabled
        panel.ui.editNeutronSldReal.setEnabled.assert_called_with(False)
        panel.ui.editNeutronSldImag.setEnabled.assert_called_with(False)
        panel.ui.editXraySldReal.setEnabled.assert_called_with(False)
        panel.ui.editXraySldImag.setEnabled.assert_called_with(False)
    
    def test_modelReset(self, panel):
        """Test the modelReset method"""
        # Mock the recalculateSLD method and create separate mock items
        with patch.object(panel, 'recalculateSLD'):
            # Create separate mocks for each model item
            mol_formula_item = MagicMock()
            mass_density_item = MagicMock()
            neutron_wavelength_item = MagicMock()
            xray_wavelength_item = MagicMock()
            
            # Set up the model.item to return the appropriate mock based on the index
            panel.model.item.side_effect = lambda idx: {
                MODEL.MOLECULAR_FORMULA: mol_formula_item,
                MODEL.MASS_DENSITY: mass_density_item,
                MODEL.NEUTRON_WAVELENGTH: neutron_wavelength_item,
                MODEL.XRAY_WAVELENGTH: xray_wavelength_item
            }.get(idx, MagicMock())
            
            # Call the method
            panel.modelReset()
            
            # Verify that the model items were reset with default values
            mol_formula_item.setText.assert_called_with("H2O")
            mass_density_item.setText.assert_called_with("1.0")
            neutron_wavelength_item.setText.assert_called_with("6.0")
            xray_wavelength_item.setText.assert_called_with("1.0")
            
            # Verify that recalculateSLD was called
            panel.recalculateSLD.assert_called_once()
