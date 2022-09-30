import sys
import unittest

import pytest

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
        assert isinstance(self.widget, QtWidgets.QDialog)
        assert self.widget.windowTitle() == "Set Graph Range"
        assert isinstance(self.widget.txtXmin, QtWidgets.QLineEdit)
        assert isinstance(self.widget.txtXmin.validator(), QtGui.QDoubleValidator)
        
    def testGoodRanges(self):
        '''Test the X range values set by caller''' 
        assert self.widget.xrange() == (0.0, 0.0)
        assert self.widget.yrange() == (0.0, 0.0)

        new_widget = SetGraphRange(None, ("1.0", 2.0), (8.0, "-2"))
        assert new_widget.xrange() == (1.0, 2.0)
        assert new_widget.yrange() == (8.0, -2.0)


    def testBadRanges(self):
        '''Test the incorrect X range values set by caller'''
        with pytest.raises(ValueError):
            new_widget = SetGraphRange(None, ("1.0", "aa"), (None, "@"))
            assert new_widget.xrange() == (1.0, 0.0)
            assert new_widget.yrange() == (0.0, 0.0)

        with pytest.raises(AssertionError):
            new_widget = SetGraphRange(None, "I'm a tuple", None)
            assert new_widget.xrange() == (1.0, 0.0)
            assert new_widget.yrange() == (0.0, 0.0)

if __name__ == "__main__":
    unittest.main()
