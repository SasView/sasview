from unittest.mock import MagicMock, patch

import pytest
from PySide6 import QtGui, QtWidgets
from sas.qtgui.Calculators.DensityPanel import MODES, DensityPanel, toMolarMass

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


class TestDensityPanel:
    """Test class for DensityPanel"""

    @classmethod
    def setup_class(cls):
        """Set up class-level resources"""
        setup_module()

    @pytest.fixture
    def panel(self):
        """Create the panel for each test"""
        parent = MagicMock()
        
        # Create more comprehensive mocks to handle QDialog properly
        with patch('sas.qtgui.Calculators.DensityPanel.QtWidgets.QDialog', MagicMock()), \
             patch('sas.qtgui.Calculators.DensityPanel.Ui_DensityPanel', MagicMock()), \
             patch('sas.qtgui.Calculators.DensityPanel.QtWidgets.QDataWidgetMapper', MagicMock()), \
             patch('sas.qtgui.Calculators.DensityPanel.QtGui.QRegularExpressionValidator', MagicMock()), \
             patch('sas.qtgui.Calculators.DensityPanel.QtCore.QRegularExpression', MagicMock()):
            
            # Need to patch setupUi since it tries to access minimumSizeHint()
            with patch.object(DensityPanel, 'setupUi'), \
                 patch.object(DensityPanel, 'setupModel'), \
                 patch.object(DensityPanel, 'setupMapper'):
                
                panel = DensityPanel(parent=parent)
                
                # Mock the UI components
                panel.ui = MagicMock()
                panel.ui.editMolarVolume = MagicMock()
                panel.ui.editMassDensity = MagicMock()
                panel.ui.editMolecularFormula = MagicMock()
                panel.ui.editMolarMass = MagicMock()
                panel.ui.buttonBox = MagicMock()
                
                # Set up the model manually
                panel.model = QtGui.QStandardItemModel()
                for i in range(4):  # MODEL enum has 4 items
                    panel.model.setItem(i, QtGui.QStandardItem())
                
                # Mock the mapper
                panel.mapper = MagicMock()
                
                yield panel
                
                # Cleanup
                panel.model = None

    def test_init(self, panel):
        """Test the initialization of the panel"""
        assert panel.mode is None
        assert panel.manager is not None
        assert panel.model is not None
        assert panel.mapper is not None

    def test_molecular_formula_conversion(self):
        """Test the conversion of molecular formula to molar mass"""
        # Test valid formulas
        assert float(toMolarMass("H2O")) > 0
        assert float(toMolarMass("NaCl")) > 0
        assert float(toMolarMass("C6H12O6")) > 0
        
        # Test invalid formula returns empty string
        assert toMolarMass("InvalidFormula") == ""

    def test_volume_to_density_calculation(self, panel):
        """Test the calculation of density from volume"""
        # Set a valid formula
        panel.model.item(0).setText("H2O")
        
        # Set the mode to volume to density
        panel.setMode(MODES.VOLUME_TO_DENSITY)
        
        # Set a volume value
        volume = "18.0"  # Approximate molar volume of water
        panel.model.item(2).setText(volume)
        
        # Trigger the calculation
        panel._updateDensity()
        
        # Get the calculated density
        density = panel.model.item(3).text()
        
        # Verify that a density value was calculated
        assert density != ""
        assert float(density) > 0

    def test_density_to_volume_calculation(self, panel):
        """Test the calculation of volume from density"""
        # Set a valid formula
        panel.model.item(0).setText("H2O")
        
        # Set the mode to density to volume
        panel.setMode(MODES.DENSITY_TO_VOLUME)
        
        # Set a density value
        density = "1.0"  # Approximate density of water
        panel.model.item(3).setText(density)
        
        # Trigger the calculation
        panel._updateVolume()
        
        # Get the calculated volume
        volume = panel.model.item(2).text()
        
        # Verify that a volume value was calculated
        assert volume != ""
        assert float(volume) > 0

    def test_volume_changed(self, panel):
        """Test the volumeChanged method"""
        # Set a valid formula
        panel.model.item(0).setText("H2O")
        
        # Call the volumeChanged method with a volume value
        panel.volumeChanged("18.0")
        
        # Verify that mode is set correctly
        assert panel.mode == MODES.VOLUME_TO_DENSITY
        
        # Verify that density is calculated
        density = panel.model.item(3).text()
        assert density != ""
        assert float(density) > 0

    def test_mass_changed(self, panel):
        """Test the massChanged method"""
        # Set a valid formula
        panel.model.item(0).setText("H2O")
        
        # Call the massChanged method with a density value
        panel.massChanged("1.0")
        
        # Verify that mode is set correctly
        assert panel.mode == MODES.DENSITY_TO_VOLUME
        
        # Verify that volume is calculated
        volume = panel.model.item(2).text()
        assert volume != ""
        assert float(volume) > 0

    def test_formula_changed(self, panel):
        """Test the formulaChanged method"""
        # Call the formulaChanged method with a valid formula
        panel.formulaChanged("NaCl")
        
        # Verify that the formula is updated in the model
        assert panel.model.item(0).text() == "NaCl"
        
        # Call the formulaChanged method with an invalid formula
        with patch('sas.qtgui.Calculators.DensityPanel.toMolarMass', side_effect=ValueError):
            panel.formulaChanged("InvalidFormula")
            
        # Molar volume should be empty after an invalid formula
        assert panel.model.item(2).text() == ""

    def test_model_reset(self, panel):
        """Test the modelReset method"""
        # Set some values
        panel.model.item(0).setText("NaCl")
        panel.model.item(2).setText("25.0")
        panel.model.item(3).setText("2.16")
        panel.setMode(MODES.VOLUME_TO_DENSITY)
        
        # Reset the model
        panel.modelReset()
        
        # Verify that values are reset
        assert panel.mode is None
        assert panel.model.item(0).text() == "H2O"
        assert panel.model.item(2).text() == ""
        assert panel.model.item(3).text() == ""

    def test_display_help(self, panel):
        """Test the displayHelp method"""
        panel.displayHelp()
        panel.manager.showHelp.assert_called_once_with("/user/qtgui/Calculators/density_calculator_help.html")
