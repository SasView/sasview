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
from sas.qtgui.Calculators.DensityPanel import DensityPanel
from sas.qtgui.Calculators.DensityPanel import toMolarMass
from sas.qtgui.Utilities.GuiUtils import FormulaValidator

import sas.qtgui.Utilities.LocalConfig

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)

class ToMolarMassTest(unittest.TestCase):
    """ Test the auxiliary conversion method"""
    def testGoodEasy(self):
        self.assertEqual(toMolarMass("H2"), "2.01588")

    def testGoodComplex(self):
        self.assertEqual(toMolarMass("H24O12C4C6N2Pu"), "608.304")

    def testGoodComplex2(self):
        self.assertEqual(toMolarMass("(H2O)0.5(D2O)0.5"), "19.0214")

    def testBadInputInt(self):
        self.assertEqual(toMolarMass(1), "")

    def testBadInputStr(self):
        self.assertEqual(toMolarMass("Im a bad string"), "")

class DensityCalculatorTest(unittest.TestCase):
    '''Test the DensityCalculator'''
    def setUp(self):
        '''Create the DensityCalculator'''
        self.widget = DensityPanel(None)

        # temporarily set the text here
        self.widget.ui.editMolecularFormula.setText("H2O")

    def tearDown(self):
        '''Destroy the DensityCalculator'''
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        '''Test the GUI in its default state'''
        self.assertIsInstance(self.widget, QtWidgets.QWidget)
        self.assertEqual(self.widget.windowTitle(), "Density/Volume Calculator")
        # temporarily commented out until FormulaValidator fixed for Qt5
        #self.assertIsInstance(self.widget.ui.editMolecularFormula.validator(), FormulaValidator)
        self.assertEqual(self.widget.ui.editMolecularFormula.styleSheet(), '')
        self.assertEqual(self.widget.model.columnCount(), 1)
        self.assertEqual(self.widget.model.rowCount(), 4)
        self.assertEqual(self.widget.sizePolicy().Policy(), QtWidgets.QSizePolicy.Fixed)

    def testSimpleEntry(self):
        ''' Default compound calculations '''
        self.widget.ui.editMolarVolume.insert("1.0")

        self.widget.show()
        # Send tab x3
        key = QtCore.Qt.Key_Tab
        QTest.keyEvent(QTest.Press, self.widget, key, QtCore.Qt.NoModifier)
        QTest.keyEvent(QTest.Press, self.widget, key, QtCore.Qt.NoModifier)
        QTest.keyEvent(QTest.Press, self.widget, key, QtCore.Qt.NoModifier)
        QTest.qWait(100)
        QTest.keyEvent(QTest.Press, self.widget, key, QtCore.Qt.NoModifier)

        # Assure the mass density field is set
        self.assertEqual(self.widget.ui.editMassDensity.text(), '18.0153')

        # Change mass density
        self.widget.ui.editMassDensity.insert("16.0")
        # Send shift-tab to update the molar volume field
        key =  QtCore.Qt.Key_Tab
        QTest.keyEvent(QTest.Press, self.widget, key, QtCore.Qt.ShiftModifier)
        QTest.qWait(100)

        # Assure the molar volume field got updated
        self.assertEqual(self.widget.ui.editMolarVolume.text(), '1.12595625')

    def testComplexEntryAndReset(self):
        ''' User entered compound calculations and subsequent reset'''

        self.widget.ui.editMolecularFormula.clear()
        self.widget.ui.editMolecularFormula.insert("KMnO4")
        self.widget.ui.editMolarVolume.insert("2.0")

        self.widget.show()
        # Send tab x3
        key = QtCore.Qt.Key_Tab
        QTest.keyEvent(QTest.Press, self.widget, key, QtCore.Qt.NoModifier)
        QTest.keyEvent(QTest.Press, self.widget, key, QtCore.Qt.NoModifier)
        QTest.keyEvent(QTest.Press, self.widget, key, QtCore.Qt.NoModifier)
        QTest.qWait(100)
        QTest.keyEvent(QTest.Press, self.widget, key, QtCore.Qt.NoModifier)

        # Assure the mass density field is set
        self.assertEqual(self.widget.ui.editMassDensity.text(), '79.017')

        # Reset the widget
        self.widget.modelReset()

        self.assertEqual(self.widget.ui.editMolecularFormula.text(), "H2O")
        self.assertEqual(self.widget.ui.editMolarMass.text(), "18.0153")
        self.assertEqual(self.widget.ui.editMolarVolume.text(), "")
        self.assertEqual(self.widget.ui.editMassDensity.text(), "")

        #self.widget.exec_()

    def testHelp(self):
        """ Assure help file is shown """
        self.widget.manager = QtWidgets.QWidget()
        self.widget.manager.showHelp = MagicMock()
        self.widget.displayHelp()
        self.assertTrue(self.widget.manager.showHelp.called_once())
        args = self.widget.manager.showHelp.call_args
        self.assertIn('density_calculator_help.html', args[0][0])

if __name__ == "__main__":
    unittest.main()
