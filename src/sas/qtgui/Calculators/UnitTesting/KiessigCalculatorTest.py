
import pytest
from PySide6 import QtWidgets

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
        sp = widget.sizePolicy()
        assert sp.horizontalPolicy() == QtWidgets.QSizePolicy.Policy.Preferred
        assert sp.verticalPolicy() == QtWidgets.QSizePolicy.Policy.Preferred

    def testHelp(self, widget, mocker):
        """ Assure help file is shown """
        widget.manager = QtWidgets.QWidget()
        mocker.patch.object(widget.manager, 'showHelp', create=True)
        widget.onHelp()
        widget.manager.showHelp.assert_called_once()
        args = widget.manager.showHelp.call_args
        assert 'kiessig_calculator_help.html' in args[0][0]

    def testComplexEntryNumbers(self, widget):
        """ User entered compound calculations and subsequent reset"""

        widget.deltaq_in.clear()
        widget.deltaq_in.insert('0.05')
        QtWidgets.QApplication.processEvents()
        assert widget.lengthscale_out.text() == '125.664'

    def testComplexEntryNumbers2(self, widget):
        """ User entered compound calculations and subsequent reset"""

        widget.deltaq_in.clear()
        widget.deltaq_in.insert('1.0')
        QtWidgets.QApplication.processEvents()
        assert widget.lengthscale_out.text() == '6.283'

    def testComplexEntryNumbers3(self, widget):
        """ User entered compound calculations and subsequent reset"""

        widget.deltaq_in.clear()
        widget.deltaq_in.insert('2.0')
        QtWidgets.QApplication.processEvents()
        assert widget.lengthscale_out.text() == '3.142'

    def testComplexEntryLetters(self, widget):
        """ User entered compound calculations and subsequent reset"""
        widget.deltaq_in.clear()
        widget.deltaq_in.insert("xyz")
        QtWidgets.QApplication.processEvents()
        assert widget.deltaq_in.text() == ''
        assert widget.lengthscale_out.text() == ''
