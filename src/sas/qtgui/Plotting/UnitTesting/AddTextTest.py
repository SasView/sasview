import sys
import unittest
from unittest.mock import MagicMock

from PyQt5 import QtGui, QtWidgets

# set up import paths
import path_prepare

# Local
from sas.qtgui.Plotting.AddText import AddText

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)

class AddTextTest(unittest.TestCase):
    '''Test the AddText'''
    def setUp(self):
        '''Create the AddText'''
        self.widget = AddText(None)

    def tearDown(self):
        '''Destroy the GUI'''
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        '''Test the GUI in its default state'''
        self.assertIsInstance(self.widget, QtWidgets.QDialog)
        self.assertIsInstance(self.widget._font, QtGui.QFont)
        self.assertEqual(self.widget._color, "black")
        
    def testOnFontChange(self):
        '''Test the QFontDialog output'''
        font_1 = QtGui.QFont("Helvetica", 15)
        QtWidgets.QFontDialog.getFont = MagicMock(return_value=(font_1, True))
        # Call the method
        self.widget.onFontChange(None)
        # Check that the text field got the new font info
        self.assertEqual(self.widget.textEdit.currentFont(), font_1)

        # See that rejecting the dialog doesn't modify the font
        font_2 = QtGui.QFont("Arial", 9)
        QtWidgets.QFontDialog.getFont = MagicMock(return_value=(font_2, False))
        # Call the method
        self.widget.onFontChange(None)
        # Check that the text field retained the previous font info
        self.assertEqual(self.widget.textEdit.currentFont(), font_1)

    def testOnColorChange(self):
        ''' Test the QColorDialog output'''
        new_color = QtGui.QColor("red")
        QtWidgets.QColorDialog.getColor = MagicMock(return_value=new_color)
        # Call the method
        self.widget.onColorChange(None)
        # Check that the text field got the new color info for text
        self.assertEqual(self.widget.textEdit.palette().color(QtGui.QPalette.Text), new_color)
        # ... and the hex value of this color is correct
        self.assertEqual(self.widget.color(), "#ff0000")
        
if __name__ == "__main__":
    unittest.main()
