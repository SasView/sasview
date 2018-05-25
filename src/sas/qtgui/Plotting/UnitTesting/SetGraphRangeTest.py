import sys
import unittest

from PyQt5 import QtGui, QtWidgets

# set up import paths
import sas.qtgui.path_prepare

# Local
from sas.qtgui.Plotting.SetGraphRange import SetGraphRange

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)

class SetGraphRangeTest(unittest.TestCase):
    '''Test the SetGraphRange'''
    def setUp(self):
        '''Create the SetGraphRange'''

        self.widget = SetGraphRange(None)

    def tearDown(self):
        '''Destroy the GUI'''
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        '''Test the GUI in its default state'''
        self.assertIsInstance(self.widget, QtWidgets.QDialog)
        self.assertEqual(self.widget.windowTitle(), "Set Graph Range")
        self.assertIsInstance(self.widget.txtXmin, QtWidgets.QLineEdit)
        self.assertIsInstance(self.widget.txtXmin.validator(), QtGui.QDoubleValidator)
        
    def testGoodRanges(self):
        '''Test the X range values set by caller''' 
        self.assertEqual(self.widget.xrange(), (0.0, 0.0))
        self.assertEqual(self.widget.yrange(), (0.0, 0.0))

        new_widget = SetGraphRange(None, ("1.0", 2.0), (8.0, "-2"))
        self.assertEqual(new_widget.xrange(), (1.0, 2.0))
        self.assertEqual(new_widget.yrange(), (8.0, -2.0))


    def testBadRanges(self):
        '''Test the incorrect X range values set by caller'''
        with self.assertRaises(ValueError):
            new_widget = SetGraphRange(None, ("1.0", "aa"), (None, "@"))
            self.assertEqual(new_widget.xrange(), (1.0, 0.0))
            self.assertEqual(new_widget.yrange(), (0.0, 0.0))

        with self.assertRaises(AssertionError):
            new_widget = SetGraphRange(None, "I'm a tuple", None)
            self.assertEqual(new_widget.xrange(), (1.0, 0.0))
            self.assertEqual(new_widget.yrange(), (0.0, 0.0))

if __name__ == "__main__":
    unittest.main()
