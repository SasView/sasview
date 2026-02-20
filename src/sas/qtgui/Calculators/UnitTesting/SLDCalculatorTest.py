
import pytest
from PySide6 import QtWidgets
from PySide6.QtTest import QTest

# Local
#from sas.qtgui.Calculators.SldPanel import SldResult
from sas.qtgui.Calculators.SldPanel import SldPanel, neutronSldAlgorithm


class SldAlgorithmTest:
    """ Test the periodictable wrapper """

    def testSldAlgorithm1(self):
        molecular_formula = "H2O"
        mass_density = 1.0
        wavelength = 6.0

        results = neutronSldAlgorithm( molecular_formula,
                                mass_density,
                                wavelength)
        #assert isinstance(results, SldResult)
        assert results.neutron_length == pytest.approx(0.175463, abs=1e-5)
        assert results.neutron_inc_xs == pytest.approx(5.621134, abs=1e-5)
        assert results.neutron_abs_xs == pytest.approx(0.074224, abs=1e-5)

    def testSldAlgorithm2(self):
        molecular_formula = "C29O[18]5+7NH[2]3"
        mass_density = 3.0
        wavelength = 666.0

        results = neutronSldAlgorithm( molecular_formula,
                                mass_density,
                                wavelength)
        #assert isinstance(results, SldResult)
        assert results.neutron_length == pytest.approx(0.059402, abs=1e-5)
        assert results.neutron_inc_xs == pytest.approx(0.16086, abs=1e-5)
        assert results.neutron_abs_xs == pytest.approx(15.511923, abs=1e-5)
        assert results.neutron_sld_real == pytest.approx(1.3352833e-05, abs=1e-5)
        assert results.neutron_sld_imag == pytest.approx(1.1645807e-10, abs=1e-5)

class SLDCalculatorTest:
    '''Test the SLDCalculator'''
    @pytest.fixture(autouse=True)
    def widget(self, qapp):
        """Create/Destroy the SLDCalculator"""
        w = SldPanel(None)

        yield w

        w.close()
        w = None

    def testDefaults(self, widget):
        '''Test the GUI in its default state'''
        assert isinstance(widget, QtWidgets.QWidget)
        # temporarily commented out until FormulaValidator fixed for Qt5
        # assert widget.windowTitle() == "SLD Calculator"
        # assert isinstance(widget.ui.editMolecularFormula.validator(), FormulaValidator)
        assert widget.ui.editMolecularFormula.styleSheet() == ''
        assert widget.model.columnCount() == 1
        assert widget.model.rowCount() == 11
        sp = widget.sizePolicy()
        assert sp.horizontalPolicy() == QtWidgets.QSizePolicy.Policy.Minimum
        assert sp.verticalPolicy() == QtWidgets.QSizePolicy.Policy.Minimum


    def testSimpleEntry(self, widget):
        ''' Default compound calculations '''

        widget.ui.editMassDensity.clear()
        widget.ui.editMassDensity.insert("1.0")
        # Send tab x3
        widget.ui.calculateButton.click()
        QtWidgets.QApplication.processEvents()
        QTest.qWait(100)

        # Assure the output fields are set
        assert widget.ui.editNeutronIncXs.text() == '5.62'

        # Change mass density
        widget.ui.editNeutronWavelength.clear()
        widget.ui.editNeutronWavelength.setText("666.0")

        # Send shift-tab to update the molar volume field
        widget.ui.calculateButton.click()
        QtWidgets.QApplication.processEvents()
        QTest.qWait(100)

        # Assure the molar volume field got updated
        assert widget.ui.editNeutronAbsXs.text() == '8.24'

    def testComplexEntryAndReset(self, widget):
        ''' User entered compound calculations and subsequent reset'''

        widget.ui.editMolecularFormula.clear()
        widget.ui.editMolecularFormula.insert("CaCO[18]3+6H2O")
        widget.ui.editMassDensity.insert("5.0")

        widget.show()
        # Send tab x2
        widget.ui.calculateButton.click()
        QtWidgets.QApplication.processEvents()
        QTest.qWait(100)

        # Assure the mass density field is set
        assert widget.ui.editNeutronIncXs.text() == '2.89'

    def testHelp(self, widget, mocker):
        """ Assure help file is shown """
        widget.manager = QtWidgets.QWidget()
        mocker.patch.object(widget.manager, 'showHelp', create=True)
        widget.displayHelp()
        widget.manager.showHelp.assert_called_once()
        args = widget.manager.showHelp.call_args
        assert 'sld_calculator_help.html' in args[0][0]
