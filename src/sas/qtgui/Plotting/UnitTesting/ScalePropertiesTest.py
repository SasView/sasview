
import pytest
from PySide6 import QtWidgets

# Local
from sas.qtgui.Plotting.ScaleProperties import ScaleProperties


class ScalePropertiesTest:
    '''Test the ScaleProperties'''
    @pytest.fixture(autouse=True)
    def widget(self, qapp):
        '''Create/Destroy the ScaleProperties'''
        w = ScaleProperties(None)
        yield w
        w.close()

    def testDefaults(self, widget):
        '''Test the GUI in its default state'''
        assert isinstance(widget, QtWidgets.QDialog)
        assert widget.windowTitle() == "Scale Properties"
        assert widget.cbX.count() == 6
        assert widget.cbY.count() == 12
        assert widget.cbView.count() == 7

    def testGetValues(self, widget):
        '''Test the values returned'''
        assert widget.getValues() == ("x", "y")
        widget.cbX.setCurrentIndex(2)
        widget.cbY.setCurrentIndex(4)
        assert widget.getValues() == ("x^(4)", "y*x^(2)")

    def testSettingView(self, widget):
        '''Test various settings of view'''
        widget.cbView.setCurrentIndex(1)
        assert widget.getValues() == ("x", "y")
        widget.cbView.setCurrentIndex(6)
        assert widget.getValues() == ("x", "y*x^(2)")

        # Assure the View combobox resets on the x index changes
        assert widget.cbView.currentIndex() != 0
        widget.cbX.setCurrentIndex(2)
        assert widget.cbView.currentIndex() == 0

        # Same for Y
        widget.cbView.setCurrentIndex(6)
        assert widget.cbView.currentIndex() != 0
        widget.cbY.setCurrentIndex(2)
        assert widget.cbView.currentIndex() == 0
