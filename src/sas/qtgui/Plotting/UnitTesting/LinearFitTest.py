import sys
import unittest
import numpy

from PyQt5 import QtGui, QtWidgets
from unittest.mock import MagicMock

from UnitTesting.TestUtils import QtSignalSpy

# set up import paths
import path_prepare

from sas.qtgui.Plotting.PlotterData import Data1D
import sas.qtgui.Plotting.Plotter as Plotter

# Local
from sas.qtgui.Plotting.LinearFit import LinearFit

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)

class LinearFitTest(unittest.TestCase):
    '''Test the LinearFit'''
    def setUp(self):
        '''Create the LinearFit'''
        self.data = Data1D(x=[1.0, 2.0, 3.0],
                           y=[10.0, 11.0, 12.0],
                           dx=[0.1, 0.2, 0.3],
                           dy=[0.1, 0.2, 0.3])
        plotter = Plotter.Plotter(None, quickplot=True)
        self.widget = LinearFit(parent=plotter, data=self.data, xlabel="log10(x^2)", ylabel="log10(y)")

    def tearDown(self):
        '''Destroy the GUI'''
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        '''Test the GUI in its default state'''
        self.assertIsInstance(self.widget, QtWidgets.QDialog)
        self.assertEqual(self.widget.windowTitle(), "Linear Fit")
        self.assertEqual(self.widget.txtA.text(), "1")
        self.assertEqual(self.widget.txtB.text(), "1")
        self.assertEqual(self.widget.txtAerr.text(), "0")
        self.assertEqual(self.widget.txtBerr.text(), "0")

        self.assertEqual(self.widget.lblRange.text(), "Fit range of log10(x^2)")

    def testFit(self):
        '''Test the fitting wrapper '''
        # Catch the update signal
        #self.widget.updatePlot.emit = MagicMock()
        #self.widget.updatePlot.emit = MagicMock()
        spy_update = QtSignalSpy(self.widget, self.widget.updatePlot)

        # Set some initial values
        self.widget.txtRangeMin.setText("1.0")
        self.widget.txtRangeMax.setText("3.0")
        self.widget.txtFitRangeMin.setText("1.0")
        self.widget.txtFitRangeMax.setText("3.0")
        # Run the fitting
        self.widget.fit(None)

        # Expected one spy instance
        self.assertEqual(spy_update.count(), 1)

        return_values = spy_update.called()[0]['args'][0]
        # Compare
        self.assertCountEqual(return_values[0], [1.0, 3.0])
        self.assertAlmostEqual(return_values[1][0], 10.004054329, 6)
        self.assertAlmostEqual(return_values[1][1], 12.030439848, 6)

        # Set the log scale
        self.widget.x_is_log = True
        self.widget.fit(None)
        self.assertEqual(spy_update.count(), 2)
        return_values = spy_update.called()[1]['args'][0]
        # Compare
        self.assertCountEqual(return_values[0], [1.0, 3.0])
        self.assertAlmostEqual(return_values[1][0], 9.987732937, 6)
        self.assertAlmostEqual(return_values[1][1], 11.84365082, 6)

    def testOrigData(self):
        ''' Assure the un-logged data is returned'''
        # log(x), log(y)
        self.widget.xminFit, self.widget.xmaxFit = self.widget.range()
        orig_x = [ 1.,  2.,  3.]
        orig_y = [1.0, 1.0413926851582251, 1.0791812460476249]
        orig_dy = [0.01, 0.018181818181818184, 0.024999999999999998]
        x, y, dy = self.widget.origData()

        self.assertCountEqual(x, orig_x)
        self.assertEqual(y[0], orig_y[0])
        self.assertAlmostEqual(y[1], orig_y[1], 8)
        self.assertAlmostEqual(y[2], orig_y[2], 8)
        self.assertEqual(dy[0], orig_dy[0])
        self.assertAlmostEqual(dy[1], orig_dy[1], 8)
        self.assertAlmostEqual(dy[2], orig_dy[2], 8)

        # x, y
        self.widget.x_is_log = False
        self.widget.y_is_log = False
        self.widget.xminFit, self.widget.xmaxFit = self.widget.range()
        orig_x = [ 1.,  2.,  3.]
        orig_y = [10., 11., 12.]
        orig_dy = [0.1, 0.2, 0.3]
        x, y, dy = self.widget.origData()

        self.assertCountEqual(x, orig_x)
        self.assertCountEqual(y, orig_y)
        self.assertCountEqual(dy, orig_dy)

        # x, log(y)
        self.widget.x_is_log = False
        self.widget.y_is_log = True
        self.widget.xminFit, self.widget.xmaxFit = self.widget.range()
        orig_x = [ 1.,  2.,  3.]
        orig_y = [1.0, 1.0413926851582251, 1.0791812460476249]
        orig_dy = [0.01, 0.018181818181818184, 0.024999999999999998]
        x, y, dy = self.widget.origData()

        self.assertCountEqual(x, orig_x)
        self.assertEqual(y[0], orig_y[0])
        self.assertAlmostEqual(y[1], orig_y[1], 8)
        self.assertAlmostEqual(y[2], orig_y[2], 8)
        self.assertEqual(dy[0], orig_dy[0])
        self.assertAlmostEqual(dy[1], orig_dy[1], 8)
        self.assertAlmostEqual(dy[2], orig_dy[2], 8)

    def testCheckFitValues(self):
        '''Assure fit values are correct'''
        # Good values
        self.assertTrue(self.widget.checkFitValues(self.widget.txtFitRangeMin))
        # Colors platform dependent
        #self.assertEqual(self.widget.txtFitRangeMin.palette().color(10).name(), "#f0f0f0")
        # Bad values
        self.widget.x_is_log = True
        self.widget.txtFitRangeMin.setText("-1.0")
        self.assertFalse(self.widget.checkFitValues(self.widget.txtFitRangeMin))
       

    def testFloatInvTransform(self):
        '''Test the helper method for providing conversion function'''
        self.widget.xLabel="x"
        self.assertEqual(self.widget.floatInvTransform(5.0), 5.0)
        self.widget.xLabel="x^(2)"
        self.assertEqual(self.widget.floatInvTransform(25.0), 5.0)
        self.widget.xLabel="x^(4)"
        self.assertEqual(self.widget.floatInvTransform(81.0), 3.0)
        self.widget.xLabel="log10(x)"
        self.assertEqual(self.widget.floatInvTransform(2.0), 100.0)
        self.widget.xLabel="ln(x)"
        self.assertEqual(self.widget.floatInvTransform(1.0), numpy.exp(1))
        self.widget.xLabel="log10(x^(4))"
        self.assertEqual(self.widget.floatInvTransform(4.0), 10.0)
      
if __name__ == "__main__":
    unittest.main()
