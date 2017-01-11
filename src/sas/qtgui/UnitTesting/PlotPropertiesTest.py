import sys
import unittest

from PyQt4 import QtGui

# set up import paths
import path_prepare

from UnitTesting.TestUtils import WarningNotImplemented

# Local
from PlotProperties import PlotProperties

app = QtGui.QApplication(sys.argv)

class PlotPropertiesTest(unittest.TestCase):
    '''Test the PlotProperties'''
    def setUp(self):
        '''Create the PlotProperties'''

        self.widget = PlotProperties(None)

    def tearDown(self):
        '''Destroy the GUI'''
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        '''Test the GUI in its default state'''
        self.assertIsInstance(self.widget, QtGui.QDialog)
        self.assertEqual(self.widget.windowTitle(), "Modify Plot Properties")
        
    def testOnColorChange(self):
        '''Test the response to color change event'''
        WarningNotImplemented(sys._getframe().f_code.co_name)

    def testOnColorIndexChange(self):
        '''Test the response to color index change event'''
        WarningNotImplemented(sys._getframe().f_code.co_name)
    

if __name__ == "__main__":
    unittest.main()
