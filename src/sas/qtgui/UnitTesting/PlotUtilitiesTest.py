import sys
import unittest
from collections import OrderedDict

from UnitTesting.TestUtils import WarningTestNotImplemented

# Tested module
import PlotUtilities

class PlotUtilitiesTest(unittest.TestCase):
    '''Test the Plot Utilities functions'''
    def setUp(self):
        '''Empty'''
        pass

    def tearDown(self):
        '''Empty'''
        pass

    def testDefaults(self):
        """ default method variables values """
        self.assertIsInstance(PlotUtilities.SHAPES, OrderedDict)
        self.assertIsInstance(PlotUtilities.COLORS, OrderedDict)

    def testBuildMatrix(self):
        """ build matrix for 2d plot from a vector """
        WarningTestNotImplemented()

    def testGetBins(self):
        """ test 1d arrays of the index with square binning """
        WarningTestNotImplemented()

    def testFillupPixels(self):
        """ test filling z values of the empty cells of 2d image matrix """
        WarningTestNotImplemented()

    def testRescale(sef):
        """ test the helper function for step based zooming """
        WarningTestNotImplemented()

    def testGgetValidColor(self):
        """ test that the method returns a color understood by MPL """
        WarningTestNotImplemented()

if __name__ == "__main__":
    unittest.main()
