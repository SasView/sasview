import pytest
from PySide6 import QtCore, QtWidgets
from PySide6.QtTest import QTest

# Local
from sas.qtgui.Calculators.DensityPanel import MODEL, DensityPanel, toMolarMass


class ToMolarMassTest:
    """ Test the auxiliary conversion method"""
    def testGoodEasy(self):
        assert toMolarMass("H2") == "2.01588"

    def testGoodComplex(self):
        assert toMolarMass("H24O12C4C6N2Pu") == "608.304"

    def testGoodComplex2(self):
        assert toMolarMass("(H2O)0.5(D2O)0.5") == "19.0214"

    def testBadInputInt(self):
        assert toMolarMass(1) == ""

    def testBadInputStr(self):
        assert toMolarMass("Im a bad string") == ""


class DensityCalculatorTest:
    '''Test the DensityCalculator'''

    @pytest.fixture(autouse=True)
    def widget(self, qapp):
        """Create/Destroy the DensityPanel"""
        w = DensityPanel(None)
        w.ui.editMolecularFormula.setText("H2O")

        yield w

        w.close()
        w = None

    def testDefaults(self, widget):
        '''Test the GUI in its default state'''
        assert isinstance(widget, QtWidgets.QWidget)
        assert widget.windowTitle() == "Density/Volume Calculator"
        # temporarily commented out until FormulaValidator fixed for Qt5
        #assert isinstance(widget.ui.editMolecularFormula.validator(), FormulaValidator)
        assert widget.ui.editMolecularFormula.styleSheet() == ''
        assert widget.model.columnCount() == 1
        assert widget.model.rowCount() == 4
        assert widget.sizePolicy().Policy() == QtWidgets.QSizePolicy.Fixed


    def testModelMolecularFormula(self, widget, qtbot):
        ''' Default compound calculations '''
        qtbot.addWidget(widget)
        widget.show()

        widget.ui.editMolecularFormula.clear()
        qtbot.keyClicks(widget.ui.editMolecularFormula, "C6H12")

        assert widget.ui.editMolecularFormula.text() == "C6H12"
        assert widget.model.item(MODEL.MOLECULAR_FORMULA).text() == "C6H12"


    def testModelVolume(self, widget, qtbot):
        ''' Default compound calculations '''
        qtbot.addWidget(widget)
        widget.show()

        widget.ui.editMolarVolume.clear()
        qtbot.keyClicks(widget.ui.editMolarVolume, "42.0")

        assert widget.ui.editMolarVolume.text() == "42.0"
        assert widget.model.item(MODEL.MOLAR_VOLUME).text() == "42.0"


    def testModelMassDensity(self, widget, qtbot):
        ''' Default compound calculations '''
        qtbot.addWidget(widget)
        widget.show()

        qtbot.keyClicks(widget.ui.editMassDensity, "19.9")

        assert widget.ui.editMassDensity.text() == "19.9"
        assert widget.model.item(MODEL.MASS_DENSITY).text() == "19.9"


    def testSimpleEntry(self, widget, qtbot):
        ''' Default compound calculations '''
        qtbot.addWidget(widget)

        widget.show()

        qtbot.keyClicks(widget.ui.editMolarVolume, "1.0")

        # Send tab x3
        key = QtCore.Qt.Key_Tab
        qtbot.keyEvent(QTest.Press, widget, key, QtCore.Qt.NoModifier)
        qtbot.keyEvent(QTest.Press, widget, key, QtCore.Qt.NoModifier)
        qtbot.keyEvent(QTest.Press, widget, key, QtCore.Qt.NoModifier)
        qtbot.wait(100)
        qtbot.keyEvent(QTest.Press, widget, key, QtCore.Qt.NoModifier)

        # Assure the mass density field is set
        assert widget.ui.editMassDensity.text() == '18.015'

        # Change mass density
        widget.ui.editMassDensity.clear()
        qtbot.keyClicks(widget.ui.editMassDensity, "16.0")
        # Send shift-tab to update the molar volume field
        key =  QtCore.Qt.Key_Tab
        QTest.keyEvent(QTest.Press, widget, key, QtCore.Qt.ShiftModifier)
        QTest.qWait(100)

        # Assure the molar volume field got updated
        assert widget.ui.editMolarVolume.text() == '1.126'

    def testComplexEntryAndReset(self, widget, qtbot):
        ''' User entered compound calculations and subsequent reset'''
        qtbot.addWidget(widget)

        widget.show()

        widget.ui.editMolecularFormula.clear()
        qtbot.keyClicks(widget.ui.editMolecularFormula, "KMnO4")
        qtbot.keyClicks(widget.ui.editMolarVolume, "2.0")

        qtbot.wait(100)

        # Send tab x3
        key = QtCore.Qt.Key_Tab
        qtbot.keyEvent(QTest.Press, widget, key, QtCore.Qt.NoModifier)
        qtbot.keyEvent(QTest.Press, widget, key, QtCore.Qt.NoModifier)
        qtbot.keyEvent(QTest.Press, widget, key, QtCore.Qt.NoModifier)
        qtbot.wait(100)
        qtbot.keyEvent(QTest.Press, widget, key, QtCore.Qt.NoModifier)

        # Assure the mass density field is set
        assert widget.ui.editMassDensity.text() == '79.017'

        # Reset the widget
        qtbot.mouseClick(widget.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Reset), QtCore.Qt.LeftButton)

        qtbot.wait(100)

        assert widget.ui.editMolecularFormula.text() == "H2O"
        assert widget.ui.editMolarMass.text() == "18.015"
        assert widget.ui.editMolarVolume.text() == ""
        assert widget.ui.editMassDensity.text() == ""

    def testHelp(self, widget, mocker):
        """ Assure help file is shown """
        widget.manager = QtWidgets.QWidget()
        mocker.patch.object(widget.manager, 'showHelp', create=True)
        widget.displayHelp()
        assert widget.manager.showHelp.called_once()
        args = widget.manager.showHelp.call_args
        assert 'density_calculator_help.html' in args[0][0]
