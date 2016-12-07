import sys
import unittest
import webbrowser

from PyQt4 import QtGui
from PyQt4.QtTest import QTest
from PyQt4 import QtCore
from mock import MagicMock

####### TEMP
import path_prepare
#######

# Local
from DensityPanel import DensityPanel
from DensityPanel import toMolarMass
from sas.qtgui.GuiUtils import FormulaValidator

import sas.qtgui.LocalConfig

app = QtGui.QApplication(sys.argv)

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

    def tearDown(self):
        '''Destroy the DensityCalculator'''
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        '''Test the GUI in its default state'''
        self.assertIsInstance(self.widget, QtGui.QWidget)
        self.assertEqual(self.widget.windowTitle(), "Density/Volume Calculator")
        self.assertIsInstance(self.widget.ui.editMolecularFormula.validator(), FormulaValidator)
        self.assertEqual(self.widget.ui.editMolecularFormula.styleSheet(), '')
        self.assertEqual(self.widget.model.columnCount(), 1)
        self.assertEqual(self.widget.model.rowCount(), 4)
        self.assertEqual(self.widget.sizePolicy().Policy(), QtGui.QSizePolicy.Fixed)

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

        # this should not rise
        self.widget.displayHelp()

if __name__ == "__main__":
    unittest.main()
