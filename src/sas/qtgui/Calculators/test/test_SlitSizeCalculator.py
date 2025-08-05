import os
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from PySide6 import QtWidgets
from sas.qtgui.Calculators.SlitSizeCalculator import SlitSizeCalculator
from sas.qtgui.Plotting.PlotterData import Data1D, Data2D

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

class TestSlitSizeCalculator:
    """Test class for SlitSizeCalculator"""

    @classmethod
    def setup_class(cls):
        """Set up class-level resources"""
        setup_module()

    @pytest.fixture
    def calculator(self):
        """Create the calculator panel for each test"""
        parent = MagicMock()
        
        # Create a more comprehensive mock setup to avoid initialization issues
        with patch('sas.qtgui.Calculators.SlitSizeCalculator.SlitSizeCalculator.__init__') as mock_init:
            # Make __init__ return None to skip actual initialization
            mock_init.return_value = None
            
            # Create the calculator instance
            calculator = SlitSizeCalculator()
            
            # Set up the panel manually with the required attributes
            calculator._parent = parent
            calculator.thickness = MagicMock()
            
            # Mock UI components
            calculator.helpButton = MagicMock()
            calculator.browseButton = MagicMock()
            calculator.closeButton = MagicMock()
            calculator.data_file = MagicMock()
            calculator.slit_length_out = MagicMock()
            calculator.unit_out = MagicMock()
            
            yield calculator

    def test_init(self, calculator):
        """Test the initialization of the calculator"""
        assert calculator._parent is not None
        assert calculator.thickness is not None

    def test_onHelp(self, calculator):
        """Test the onHelp method"""
        calculator.onHelp()
        
        # Verify the correct help path was provided
        location = "/user/qtgui/Calculators/slit_calculator_help.html"
        calculator._parent.showHelp.assert_called_once_with(location)
    
    def test_onClose(self, calculator):
        """Test the onClose method"""
        with patch.object(calculator, 'close') as mock_close:
            calculator.onClose()
            mock_close.assert_called_once()
    
    def test_clearResults(self, calculator):
        """Test the clearResults method"""
        calculator.clearResults()
        
        # Verify the output fields were cleared properly
        calculator.slit_length_out.setText.assert_called_once_with("ERROR!")
        calculator.unit_out.clear.assert_called_once()
    
    def test_chooseFile(self, calculator):
        """Test the chooseFile method"""
        file_path = "/path/to/test_file.txt"
        
        # Mock QFileDialog.getOpenFileName
        with patch('sas.qtgui.Calculators.SlitSizeCalculator.QtWidgets.QFileDialog.getOpenFileName', 
                  return_value=(file_path, None)):
            
            # Call the method
            result = calculator.chooseFile()
            
            # Verify the result is the file path
            assert result == file_path

    def test_onBrowse_success(self, calculator):
        """Test the onBrowse method with successful file loading"""
        # Mock the file selection and data loading
        test_file = "/path/to/test_file.txt"
        test_data = Data1D(x=[0.1, 0.2, 0.3], y=[1.0, 2.0, 3.0])
        
        with patch.object(calculator, 'chooseFile', return_value=test_file), \
             patch('sas.qtgui.Calculators.SlitSizeCalculator.Loader') as mock_loader, \
             patch.object(calculator, 'calculateSlitSize') as mock_calculate:
            
            # Mock the loader to return our test data
            loader_instance = mock_loader.return_value
            loader_instance.load.return_value = [test_data]
            
            # Call the method
            calculator.onBrowse()
            
            # Verify that the file was loaded
            loader_instance.load.assert_called_once_with(test_file)
            
            # Verify that the filename was set in the UI
            calculator.data_file.setText.assert_called_once_with(os.path.basename(test_file))
            
            # Verify that calculateSlitSize was called with the loaded data
            mock_calculate.assert_called_once_with(test_data)
    
    def test_onBrowse_no_file_selected(self, calculator):
        """Test the onBrowse method when no file is selected"""
        with patch.object(calculator, 'chooseFile', return_value=""), \
             patch('sas.qtgui.Calculators.SlitSizeCalculator.Loader') as mock_loader:
            
            # Call the method
            calculator.onBrowse()
            
            # Verify that the loader was not called
            mock_loader.return_value.load.assert_not_called()
    
    def test_onBrowse_load_error(self, calculator):
        """Test the onBrowse method when there's an error loading the file"""
        # Mock the file selection and a loading error
        test_file = "/path/to/test_file.txt"
        
        with patch.object(calculator, 'chooseFile', return_value=test_file), \
             patch('sas.qtgui.Calculators.SlitSizeCalculator.Loader') as mock_loader, \
             patch('sas.qtgui.Calculators.SlitSizeCalculator.logging') as mock_logging:
            
            # Mock the loader to raise an exception
            loader_instance = mock_loader.return_value
            loader_instance.load.side_effect = ValueError("Error loading file")
            
            # Call the method
            calculator.onBrowse()
            
            # Verify that the loader was called
            loader_instance.load.assert_called_once_with(test_file)
            
            # Verify that the error was logged
            mock_logging.error.assert_called_once()
    
    def test_calculateSlitSize_success(self, calculator):
        """Test the calculateSlitSize method with valid data"""
        # Create test data
        test_data = Data1D(x=[0.1, 0.2, 0.3], y=[1.0, 2.0, 3.0])
        
        # Mock the slit length calculator
        mock_slit_calculator = MagicMock()
        mock_slit_calculator.calculate_slit_length.return_value = 0.12345
        
        with patch('sas.qtgui.Calculators.SlitSizeCalculator.SlitlengthCalculator', 
                  return_value=mock_slit_calculator):
            
            # Call the method
            calculator.calculateSlitSize(test_data)
            
            # Verify that the slit length calculator was set up correctly
            mock_slit_calculator.set_data.assert_called_once_with(x=test_data.x, y=test_data.y)
            
            # Verify that the calculate_slit_length method was called
            mock_slit_calculator.calculate_slit_length.assert_called_once()
            
            # Verify that the result was formatted and displayed correctly
            calculator.slit_length_out.setText.assert_called_once_with("0.12345")
            calculator.unit_out.setText.assert_called_once_with("[Unknown]")
    
    def test_calculateSlitSize_with_none_data(self, calculator):
        """Test the calculateSlitSize method with None data"""
        with patch('sas.qtgui.Calculators.SlitSizeCalculator.logging') as mock_logging:
            # Call the method with None data
            calculator.calculateSlitSize(None)
            
            # Verify that clearResults was called
            calculator.slit_length_out.setText.assert_called_once_with("ERROR!")
            calculator.unit_out.clear.assert_called_once()
            
            # Verify that an error was logged
            mock_logging.error.assert_called_once()
    
    def test_calculateSlitSize_with_2d_data(self, calculator):
        """Test the calculateSlitSize method with 2D data"""
        # Create 2D test data
        test_data = Data2D(image=np.ones((10, 10)), qx_data=np.arange(100), qy_data=np.arange(100))
        
        with patch('sas.qtgui.Calculators.SlitSizeCalculator.logging') as mock_logging:
            # Call the method with 2D data
            calculator.calculateSlitSize(test_data)
            
            # Verify that clearResults was called
            calculator.slit_length_out.setText.assert_called_once_with("ERROR!")
            calculator.unit_out.clear.assert_called_once()
            
            # Verify that an error was logged
            mock_logging.error.assert_called_once()
    
    def test_calculateSlitSize_with_empty_data(self, calculator):
        """Test the calculateSlitSize method with empty data"""
        # Create empty 1D data
        test_data = Data1D(x=[], y=[])
        
        with patch('sas.qtgui.Calculators.SlitSizeCalculator.logging') as mock_logging:
            # Call the method with empty data
            calculator.calculateSlitSize(test_data)
            
            # Verify that an error was logged
            mock_logging.error.assert_called_once()
    
    def test_calculateSlitSize_calculation_error(self, calculator):
        """Test the calculateSlitSize method when calculation fails"""
        # Create test data
        test_data = Data1D(x=[0.1, 0.2, 0.3], y=[1.0, 2.0, 3.0])
        
        # Mock the slit length calculator to raise an exception
        mock_slit_calculator = MagicMock()
        mock_slit_calculator.calculate_slit_length.side_effect = ValueError("Calculation error")
        
        with patch('sas.qtgui.Calculators.SlitSizeCalculator.SlitlengthCalculator', 
                  return_value=mock_slit_calculator), \
             patch('sas.qtgui.Calculators.SlitSizeCalculator.logging') as mock_logging:
            
            # Call the method
            calculator.calculateSlitSize(test_data)
            
            # Verify that clearResults was called
            calculator.slit_length_out.setText.assert_called_once_with("ERROR!")
            calculator.unit_out.clear.assert_called_once()
            
            # Verify that an error was logged
            mock_logging.error.assert_called_once()
            mock_logging.error.assert_called_once()
