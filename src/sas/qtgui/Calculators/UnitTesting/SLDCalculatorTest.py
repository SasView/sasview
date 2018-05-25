import sys
import unittest
import webbrowser

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtTest import QTest
from PyQt5 import QtCore
from unittest.mock import MagicMock

####### TEMP
import sas.qtgui.path_prepare
#######

# Local
from sas.qtgui.Calculators.SldPanel import SldResult
from sas.qtgui.Calculators.SldPanel import SldPanel
from sas.qtgui.Calculators.SldPanel import sldAlgorithm
from sas.qtgui.Utilities.GuiUtils import FormulaValidator

import sas.qtgui.Utilities.LocalConfig

#if not QtWidgets.QApplication.instance():
#    app = QtWidgets.QApplication(sys.argv)
app = QtWidgets.QApplication(sys.argv)

class SldResultTest(unittest.TestCase):
    """ Test the simple container class"""
    def testObjectSize(self):
        results = SldResult(0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                            0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        self.assertEqual(sys.getsizeof(results), 56)


class SldAlgorithmTest(unittest.TestCase):
    """ Test the periodictable wrapper """
    def testSldAlgorithm1(self):
        molecular_formula = "H2O"
        mass_density = 1.0
        wavelength = 6.0
        
        results = sldAlgorithm( molecular_formula,
                                mass_density,
                                wavelength)
        self.assertIsInstance(results, SldResult)
        self.assertAlmostEqual(results.neutron_length, 0.175463, 5)
        self.assertAlmostEqual(results.neutron_inc_xs, 5.365857, 5)
        self.assertAlmostEqual(results.neutron_abs_xs, 0.074224, 5)

    def testSldAlgorithm2(self):
        molecular_formula = "C29O[18]5+7NH[2]3"
        mass_density = 3.0
        wavelength = 666.0
        
        results = sldAlgorithm( molecular_formula,
                                mass_density,
                                wavelength)
        self.assertIsInstance(results, SldResult)
        self.assertAlmostEqual(results.neutron_length,   0.059402, 5)
        self.assertAlmostEqual(results.neutron_inc_xs,   0.145427, 5)
        self.assertAlmostEqual(results.neutron_abs_xs,  15.512215, 5)
        self.assertAlmostEqual(results.neutron_sld_real, 1.3352833e-05, 5)
        self.assertAlmostEqual(results.neutron_sld_imag, 1.1645807e-10, 5)


class SLDCalculatorTest(unittest.TestCase):
    '''Test the SLDCalculator'''
    def setUp(self):
        '''Create the SLDCalculator'''
        self.widget = SldPanel(None)

    def tearDown(self):
        '''Destroy the DensityCalculator'''
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        '''Test the GUI in its default state'''
        self.assertIsInstance(self.widget, QtWidgets.QWidget)
        # temporarily commented out until FormulaValidator fixed for Qt5
        # self.assertEqual(self.widget.windowTitle(), "SLD Calculator")
        # self.assertIsInstance(self.widget.ui.editMolecularFormula.validator(), FormulaValidator)
        self.assertEqual(self.widget.ui.editMolecularFormula.styleSheet(), '')
        self.assertEqual(self.widget.model.columnCount(), 1)
        self.assertEqual(self.widget.model.rowCount(), 12)
        self.assertEqual(self.widget.sizePolicy().Policy(), QtWidgets.QSizePolicy.Fixed)

    def testSimpleEntry(self):
        ''' Default compound calculations '''

        self.widget.show()

        self.widget.ui.editMassDensity.clear()
        self.widget.ui.editMassDensity.insert("1.0")
        # Send tab x3
        key = QtCore.Qt.Key_Tab
        QTest.keyEvent(QTest.Press, self.widget, key, QtCore.Qt.NoModifier)
        QTest.keyEvent(QTest.Press, self.widget, key, QtCore.Qt.NoModifier)
        QtWidgets.qApp.processEvents()
        QTest.qWait(100)

        # Assure the output fields are set
        self.assertEqual(self.widget.ui.editNeutronIncXs.text(), '5.62')

        # Change mass density
        self.widget.ui.editWavelength.clear()
        self.widget.ui.editWavelength.setText("666.0")

        # Send shift-tab to update the molar volume field
        QTest.keyEvent(QTest.Press, self.widget, key, QtCore.Qt.NoModifier)
        QTest.keyEvent(QTest.Press, self.widget, key, QtCore.Qt.NoModifier)
        QtWidgets.qApp.processEvents()
        QTest.qWait(100)

        # Assure the molar volume field got updated
        self.assertEqual(self.widget.ui.editNeutronAbsXs.text(), '8.24')

    def testComplexEntryAndReset(self):
        ''' User entered compound calculations and subsequent reset'''

        self.widget.ui.editMolecularFormula.clear()
        self.widget.ui.editMolecularFormula.insert("CaCO[18]3+6H2O")
        self.widget.ui.editMassDensity.insert("5.0")

        self.widget.show()
        # Send tab x2
        key = QtCore.Qt.Key_Tab
        QTest.keyEvent(QTest.Press, self.widget, key, QtCore.Qt.NoModifier)
        QTest.keyEvent(QTest.Press, self.widget, key, QtCore.Qt.NoModifier)
        QTest.qWait(100)
        QTest.keyEvent(QTest.Press, self.widget, key, QtCore.Qt.NoModifier)

        # Assure the mass density field is set
        self.assertEqual(self.widget.ui.editNeutronIncXs.text(), '43.4')

        # Reset the widget
        self.widget.modelReset()

        self.assertEqual(self.widget.ui.editMolecularFormula.text(), "H2O")
        self.assertEqual(self.widget.ui.editMassDensity.text(), "1")
        self.assertEqual(self.widget.ui.editWavelength.text(), "6")

    def testHelp(self):
        """ Assure help file is shown """
        self.widget.manager = QtWidgets.QWidget()
        self.widget.manager.showHelp = MagicMock()
        self.widget.displayHelp()
        self.assertTrue(self.widget.manager.showHelp.called_once())
        args = self.widget.manager.showHelp.call_args
        self.assertIn('sld_calculator_help.html', args[0][0])

if __name__ == "__main__":
    unittest.main()
