from collections import OrderedDict

# Tested module
import sas.qtgui.Plotting.PlotUtilities as PlotUtilities
from sas.qtgui.UnitTesting.TestUtils import WarningTestNotImplemented


class PlotUtilitiesTest:

    def testDefaults(self):
        """ default method variables values """
        assert isinstance(PlotUtilities.SHAPES, OrderedDict)
        assert isinstance(PlotUtilities.COLORS, OrderedDict)

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
