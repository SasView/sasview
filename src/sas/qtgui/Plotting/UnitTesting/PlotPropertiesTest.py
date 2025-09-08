
import pytest
from PySide6 import QtGui, QtWidgets

# Local
from sas.qtgui.Plotting.PlotProperties import PlotProperties


class PlotPropertiesTest:
    '''Test the PlotProperties'''

    @pytest.fixture(autouse=True)
    def widget(self, qapp):
        '''Create/Destroy the PlotProperties'''
        w = PlotProperties(None,
                         color=1,
                         marker=3,
                         marker_size=10,
                         legend="LL")

        yield w

        '''Destroy the GUI'''
        w.close()

    def testDefaults(self, widget):
        '''Test the GUI in its default state'''
        assert isinstance(widget, QtWidgets.QDialog)
        assert widget.windowTitle() == "Modify Plot Properties"

        # Check the combo boxes
        assert widget.cbColor.currentText() == "Green"
        assert widget.cbColor.count() == 7
        assert widget.cbShape.currentText() == "Triangle Down"
        assert widget.txtLegend.text() == "LL"
        assert widget.sbSize.value() == 10

    def testDefaultsWithCustomColor(self, widget):
        '''Test the GUI when called with custom color'''
        widget = PlotProperties(None,
                         color="#FF00FF",
                         marker=7,
                         marker_size=10,
                         legend="LL")

        assert widget.cbColor.currentText() == "Custom"
        assert widget.cbColor.count() == 8

    def testOnColorChange(self, widget, mocker):
        '''Test the response to color change event'''
        # Accept the new color
        mocker.patch.object(QtWidgets.QColorDialog, 'getColor', return_value=QtGui.QColor(255, 0, 255))

        widget.onColorChange()

        assert widget.color() == "#ff00ff"
        assert widget.custom_color
        assert widget.cbColor.currentIndex() == 7
        assert widget.cbColor.currentText() == "Custom"

        # Reset the color - this will remove "Custom" from the combobox
        # and set its index to "Green"
        widget.cbColor.setCurrentIndex(1)
        assert widget.cbColor.currentText() == "Green"

        # Cancel the dialog now
        bad_color = QtGui.QColor() # constructs an invalid color
        mocker.patch.object(QtWidgets.QColorDialog, 'getColor', return_value=bad_color)
        widget.onColorChange()

        assert widget.color() == 1
        assert not widget.custom_color
        assert widget.cbColor.currentIndex() == 1
        assert widget.cbColor.currentText() == "Green"


    def testOnColorIndexChange(self, widget):
        '''Test the response to color index change event'''
        # Intitial population of the color combo box
        widget.onColorIndexChange()
        assert widget.cbColor.count() == 7
        # Block the callback so we can update the cb
        widget.cbColor.blockSignals(True)
        # Add the Custom entry
        widget.cbColor.addItems(["Custom"])
        # Unblock the callback
        widget.cbColor.blockSignals(False)
        # Assert the new CB
        assert widget.cbColor.count() == 8
        # Call the method
        widget.onColorIndexChange()
        # see that the Custom entry disappeared
        assert widget.cbColor.count() == 7
        assert widget.cbColor.findText("Custom") == -1
