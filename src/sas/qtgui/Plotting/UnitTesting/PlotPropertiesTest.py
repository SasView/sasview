import sys
import unittest
from unittest.mock import MagicMock

from PyQt5 import QtGui, QtWidgets

# set up import paths
import sas.qtgui.path_prepare

# Local
from sas.qtgui.Plotting.PlotProperties import PlotProperties

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)

class PlotPropertiesTest(unittest.TestCase):
    '''Test the PlotProperties'''
    def setUp(self):
        '''Create the PlotProperties'''

        self.widget = PlotProperties(None,
                         color=1,
                         marker=3,
                         marker_size=10,
                         legend="LL")

    def tearDown(self):
        '''Destroy the GUI'''
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        '''Test the GUI in its default state'''
        assert isinstance(self.widget, QtWidgets.QDialog)
        assert self.widget.windowTitle() == "Modify Plot Properties"

        # Check the combo boxes
        assert self.widget.cbColor.currentText() == "Green"
        assert self.widget.cbColor.count() == 7
        assert self.widget.cbShape.currentText() == "Triangle Down"
        assert self.widget.txtLegend.text() == "LL"
        assert self.widget.sbSize.value() == 10

    def testDefaultsWithCustomColor(self):
        '''Test the GUI when called with custom color'''
        widget = PlotProperties(None,
                         color="#FF00FF",
                         marker=7,
                         marker_size=10,
                         legend="LL")

        assert widget.cbColor.currentText() == "Custom"
        assert widget.cbColor.count() == 8
        
    def testOnColorChange(self):
        '''Test the response to color change event'''
        # Accept the new color
        QtWidgets.QColorDialog.getColor = MagicMock(return_value=QtGui.QColor(255, 0, 255))

        self.widget.onColorChange()

        assert self.widget.color() == "#ff00ff"
        assert self.widget.custom_color
        assert self.widget.cbColor.currentIndex() == 7
        assert self.widget.cbColor.currentText() == "Custom"

        # Reset the color - this will remove "Custom" from the combobox
        # and set its index to "Green"
        self.widget.cbColor.setCurrentIndex(1)
        assert self.widget.cbColor.currentText() == "Green"

        # Cancel the dialog now
        bad_color = QtGui.QColor() # constructs an invalid color
        QtWidgets.QColorDialog.getColor = MagicMock(return_value=bad_color)
        self.widget.onColorChange()

        assert self.widget.color() == 1
        assert not self.widget.custom_color
        assert self.widget.cbColor.currentIndex() == 1
        assert self.widget.cbColor.currentText() == "Green"


    def testOnColorIndexChange(self):
        '''Test the response to color index change event'''
        # Intitial population of the color combo box
        self.widget.onColorIndexChange()
        assert self.widget.cbColor.count() == 7
        # Block the callback so we can update the cb
        self.widget.cbColor.blockSignals(True)
        # Add the Custom entry
        self.widget.cbColor.addItems(["Custom"])
        # Unblock the callback
        self.widget.cbColor.blockSignals(False)
        # Assert the new CB
        assert self.widget.cbColor.count() == 8
        # Call the method
        self.widget.onColorIndexChange()
        # see that the Custom entry disappeared
        assert self.widget.cbColor.count() == 7
        assert self.widget.cbColor.findText("Custom") == -1

if __name__ == "__main__":
    unittest.main()
