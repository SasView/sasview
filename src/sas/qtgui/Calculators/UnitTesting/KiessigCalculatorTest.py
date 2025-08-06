
import pytest
from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from sas.qtgui.Calculators.KiessigPanel import KiessigPanel


class KiessigCalculatorTest:
    """Test the KiessigCalculator"""

    @pytest.fixture(autouse=True)
    def widget(self, qapp):
        """Create/Destroy the KiessigPanel"""
        w = KiessigPanel(None)

        yield w

        w.close()
        w = None


    def testDefaults(self, widget, mocker):
        """Test the GUI in its default state"""
        assert isinstance(widget, QtWidgets.QWidget)
        assert widget.windowTitle() == "Kiessig Thickness Calculator"
        assert widget.sizePolicy().Policy() == QtWidgets.QSizePolicy.Fixed

    def testHelp(self, widget, mocker):
        """ Assure help file is shown """
        widget.manager = QtWidgets.QWidget()
        mocker.patch.object(widget.manager, 'showHelp', create=True)
        widget.onHelp()
        assert widget.manager.showHelp.called_once()
        args = widget.manager.showHelp.call_args
        assert 'kiessig_calculator_help.html' in args[0][0]

    def testComplexEntryNumbers(self, widget):
        """ User entered compound calculations and subsequent reset"""

        widget.deltaq_in.clear()
        widget.deltaq_in.insert('0.05')
        #
        # Push Compute with the left mouse button
        computeButton = widget.computeButton
        QTest.mouseClick(computeButton, Qt.LeftButton)
        assert widget.lengthscale_out.text() == '125.664'

    def testComplexEntryNumbers2(self, widget):
        """ User entered compound calculations and subsequent reset"""

        widget.deltaq_in.clear()
        widget.deltaq_in.insert('1.0')
        #
        # Push Compute with the left mouse button
        computeButton = widget.computeButton
        QTest.mouseClick(computeButton, Qt.LeftButton)
        assert widget.lengthscale_out.text() == '6.283'

    def testComplexEntryNumbers3(self, widget):
        """ User entered compound calculations and subsequent reset"""

        widget.deltaq_in.clear()
        widget.deltaq_in.insert('2.0')
        #
        # Push Compute with the left mouse button
        computeButton = widget.computeButton
        QTest.mouseClick(computeButton, Qt.LeftButton)
        assert widget.lengthscale_out.text() == '3.142'

    def testComplexEntryLetters(self, widget):
        """ User entered compound calculations and subsequent reset"""
        widget.deltaq_in.clear()
        widget.deltaq_in.insert("xyz")

        # Push Compute with the left mouse button
        computeButton = widget.computeButton
        QTest.mouseClick(computeButton, Qt.LeftButton)
        assert widget.deltaq_in.text() == ''
        assert widget.lengthscale_out.text() == ''
