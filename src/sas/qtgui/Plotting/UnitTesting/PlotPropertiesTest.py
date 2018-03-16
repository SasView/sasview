import sys
import unittest
from unittest.mock import MagicMock

from PyQt5 import QtGui, QtWidgets

# set up import paths
import path_prepare

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
        self.assertIsInstance(self.widget, QtWidgets.QDialog)
        self.assertEqual(self.widget.windowTitle(), "Modify Plot Properties")

        # Check the combo boxes
        self.assertEqual(self.widget.cbColor.currentText(), "Green")
        self.assertEqual(self.widget.cbColor.count(), 7)
        self.assertEqual(self.widget.cbShape.currentText(), "Triangle Down")
        self.assertEqual(self.widget.txtLegend.text(), "LL")
        self.assertEqual(self.widget.sbSize.value(), 10)

    def testDefaultsWithCustomColor(self):
        '''Test the GUI when called with custom color'''
        widget = PlotProperties(None,
                         color="#FF00FF",
                         marker=7,
                         marker_size=10,
                         legend="LL")

        self.assertEqual(widget.cbColor.currentText(), "Custom")
        self.assertEqual(widget.cbColor.count(), 8)
        
    def testOnColorChange(self):
        '''Test the response to color change event'''
        # Accept the new color
        QtWidgets.QColorDialog.getColor = MagicMock(return_value=QtGui.QColor(255, 0, 255))

        self.widget.onColorChange()

        self.assertEqual(self.widget.color(), "#ff00ff")
        self.assertTrue(self.widget.custom_color)
        self.assertEqual(self.widget.cbColor.currentIndex(), 7)
        self.assertEqual(self.widget.cbColor.currentText(), "Custom")

        # Reset the color - this will remove "Custom" from the combobox
        # and set its index to "Green"
        self.widget.cbColor.setCurrentIndex(1)
        self.assertEqual(self.widget.cbColor.currentText(), "Green")

        # Cancel the dialog now
        bad_color = QtGui.QColor() # constructs an invalid color
        QtWidgets.QColorDialog.getColor = MagicMock(return_value=bad_color)
        self.widget.onColorChange()

        self.assertEqual(self.widget.color(), 1)
        self.assertFalse(self.widget.custom_color)
        self.assertEqual(self.widget.cbColor.currentIndex(), 1)
        self.assertEqual(self.widget.cbColor.currentText(), "Green")


    def testOnColorIndexChange(self):
        '''Test the response to color index change event'''
        # Intitial population of the color combo box
        self.widget.onColorIndexChange()
        self.assertEqual(self.widget.cbColor.count(), 7)
        # Block the callback so we can update the cb
        self.widget.cbColor.blockSignals(True)
        # Add the Custom entry
        self.widget.cbColor.addItems(["Custom"])
        # Unblock the callback
        self.widget.cbColor.blockSignals(False)
        # Assert the new CB
        self.assertEqual(self.widget.cbColor.count(), 8)
        # Call the method
        self.widget.onColorIndexChange()
        # see that the Custom entry disappeared
        self.assertEqual(self.widget.cbColor.count(), 7)
        self.assertEqual(self.widget.cbColor.findText("Custom"), -1)

if __name__ == "__main__":
    unittest.main()
