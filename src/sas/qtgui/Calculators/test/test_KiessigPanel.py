from unittest.mock import MagicMock, patch

import pytest
from PySide6 import QtWidgets
from sas.qtgui.Calculators.KiessigPanel import KiessigPanel

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

class TestKiessigPanel:
    """Test class for KiessigPanel"""

    @classmethod
    def setup_class(cls):
        """Set up class-level resources"""
        setup_module()

    @pytest.fixture
    def panel(self):
        """Create the panel for each test"""
        parent = MagicMock()
        
        # Create a more comprehensive patch setup to handle QRegularExpressionValidator properly
        with patch('sas.qtgui.Calculators.KiessigPanel.QtWidgets.QDialog', autospec=True), \
             patch('sas.qtgui.Calculators.KiessigPanel.Ui_KiessigPanel', autospec=True), \
             patch('sas.qtgui.Calculators.KiessigPanel.KiessigThicknessCalculator', autospec=True), \
             patch('sas.qtgui.Calculators.KiessigPanel.QtCore.QRegularExpression', MagicMock()), \
             patch('sas.qtgui.Calculators.KiessigPanel.QtGui.QRegularExpressionValidator', MagicMock()):
            
            # Skip the Qt UI initialization
            with patch('sas.qtgui.Calculators.KiessigPanel.KiessigPanel.__init__') as mock_init:
                mock_init.return_value = None
                
                # Create the panel
                panel = KiessigPanel()
                
                # Set up the panel manually
                panel.manager = parent
                panel.thickness = MagicMock()
                panel.deltaq_in = MagicMock()
                panel.lengthscale_out = MagicMock()
                panel.helpButton = MagicMock()
                panel.closeButton = MagicMock()
                
                # Set default behavior
                panel.deltaq_in.text.return_value = "0.05"
                
                yield panel

    def test_onHelp(self, panel):
        """Test the onHelp method"""
        # Call the method
        panel.onHelp()
        
        # Verify that showHelp was called with the correct location
        location = "/user/qtgui/Calculators/kiessig_calculator_help.html"
        panel.manager.showHelp.assert_called_once_with(location)
    
    def test_onClose(self, panel):
        """Test the onClose method"""
        # Mock the close method
        with patch.object(panel, 'close') as mock_close:
            # Call the onClose method
            panel.onClose()
            
            # Verify that close was called
            mock_close.assert_called_once()
    
    def test_onCompute_valid_input(self, panel):
        """Test the onCompute method with valid input"""
        # Set up the mock to return a valid value
        panel.deltaq_in.text.return_value = "0.05"
        
        # Mock the compute_thickness method to return a known value
        expected_thickness = 62.83  # PI / 0.05
        panel.thickness.compute_thickness.return_value = expected_thickness
        
        # Call the onCompute method
        panel.onCompute()
        
        # Verify that set_deltaq was called with the correct value
        panel.thickness.set_deltaq.assert_called_once_with(dq=0.05)
        
        # Verify that compute_thickness was called
        panel.thickness.compute_thickness.assert_called_once()
        
        # Verify that the output was set correctly
        panel.lengthscale_out.setText.assert_called_once_with("62.830")
    
    def test_onCompute_zero_input(self, panel):
        """Test the onCompute method with zero input (should cause division by zero)"""
        # Set up the mock to return zero
        panel.deltaq_in.text.return_value = "0.0"
        
        # Mock the compute_thickness method to return None (simulating division by zero)
        panel.thickness.compute_thickness.return_value = None
        
        # Call the onCompute method
        panel.onCompute()
        
        # Verify that set_deltaq was called with zero
        panel.thickness.set_deltaq.assert_called_once_with(dq=0.0)
        
        # Verify that compute_thickness was called
        panel.thickness.compute_thickness.assert_called_once()
        
        # Verify that the output was set to empty string
        panel.lengthscale_out.setText.assert_called_once_with("")
    
    def test_onCompute_invalid_input(self, panel):
        """Test the onCompute method with invalid input"""
        # Set up the mock to return an invalid string
        panel.deltaq_in.text.return_value = "invalid"
        
        # Mock the thickness.set_deltaq to raise ValueError
        panel.thickness.set_deltaq.side_effect = ValueError("Invalid input")
        
        # Call the onCompute method
        panel.onCompute()
        
        # Verify that the output was set to empty string due to ValueError
        panel.lengthscale_out.setText.assert_called_once_with("")
    
    def test_onCompute_negative_input(self, panel):
        """Test the onCompute method with negative input"""
        # Set up the mock to return a negative value
        panel.deltaq_in.text.return_value = "-0.05"
        
        # Mock the compute_thickness method to return a negative value
        expected_thickness = -62.83  # We want to test with a negative result
        panel.thickness.compute_thickness.return_value = expected_thickness
        
        # Call the onCompute method
        panel.onCompute()
        
        # Verify that set_deltaq was called with the negative value
        panel.thickness.set_deltaq.assert_called_once_with(dq=-0.05)
        
        # Verify that compute_thickness was called
        panel.thickness.compute_thickness.assert_called_once()
        
        # Verify that the output was set correctly with the negative value result
        panel.lengthscale_out.setText.assert_called_once_with("-62.830")
        panel.thickness.compute_thickness.assert_called_once()
        
        # Verify that the output was set correctly with the negative value result
        panel.lengthscale_out.setText.assert_called_once_with("-62.830")
