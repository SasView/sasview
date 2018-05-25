import sys
import unittest

import numpy
from unittest.mock import MagicMock

# set up import paths
import sas.qtgui.path_prepare

# Local
from sas.qtgui.Utilities.GuiUtils import *
from sas.qtgui.Perspectives.Fitting.FittingWidget import *
from sas.qtgui.Plotting.PlotterData import Data1D


class FittingLogicTest(unittest.TestCase):
    """Test the fitting logic class"""

    def setUp(self):
        """Create the component"""
        data = Data1D(x=[1,2,3],y=[3,4,5])
        self.logic = FittingLogic(data=data)

    def testDefaults(self):
        """Test the component in its default state"""
        self.assertIsInstance(self.logic.data, Data1D)
        self.assertTrue(self.logic.data_is_loaded)
        self.assertEqual(self.logic.data, self.logic._data)

    def testComputeDataRange(self):
        """
        Tests the data range calculator on Data1D/Data2D
        """
        # Using the default data
        qmin, qmax, npts = self.logic.computeDataRange()

        self.assertEqual(qmin, 1)
        self.assertEqual(qmax, 3)
        self.assertEqual(npts, 3)

        # data with more points
        data = Data1D(x=[-10, 2, 10, 20],y=[-3, 4, 10, 50])
        self.logic.data=data
        qmin, qmax, npts = self.logic.computeDataRange()

        self.assertEqual(qmin, -10)
        self.assertEqual(qmax, 20)
        self.assertEqual(npts, 4)

    def testCreateDefault1dData(self):
        """
        Tests the default 1D set
        """
        interval = numpy.linspace(start=1, stop=10, num=10, endpoint=True)
        self.logic.createDefault1dData(interval=interval)

        self.assertEqual(self.logic.data.id, ('0 data'))
        self.assertEqual(self.logic.data.group_id, ('0 Model1D'))
        self.assertFalse(self.logic.data.is_data)
        self.assertEqual(self.logic.data._xaxis, ('\\rm{Q}'))
        self.assertEqual(self.logic.data._xunit, ('A^{-1}'))
        self.assertEqual(self.logic.data._yaxis, ('\\rm{Intensity}'))
        self.assertEqual(self.logic.data._yunit, ('cm^{-1}'))

    def testCreateDefault2dData(self):
        """
        Tests the default 2D set
        """
        self.logic.createDefault2dData(qmax=0.35, qstep=50, tab_id=8)

        self.assertEqual(self.logic.data.id, ('8 data'))
        self.assertEqual(self.logic.data.group_id, ('8 Model2D'))
        self.assertFalse(self.logic.data.is_data)
        self.assertEqual(self.logic.data._xaxis, ('\\rm{Q_{x}}'))
        self.assertEqual(self.logic.data._xunit, ('A^{-1}'))
        self.assertEqual(self.logic.data._yaxis, ('\\rm{Q_{y}}'))
        self.assertEqual(self.logic.data._yunit, ('A^{-1}'))

        self.assertEqual(self.logic.data.xmin, -0.35)
        self.assertEqual(self.logic.data.xmax, 0.35)

        self.assertEqual(self.logic.data.ymin, -0.35)
        self.assertEqual(self.logic.data.ymax, 0.35)

        self.assertEqual(self.logic.data.data.sum(), 2500.0) # 50x50 array of 1's
        self.assertEqual(self.logic.data.err_data.sum(axis=0), 2500.0)
        self.assertAlmostEqual(self.logic.data.qx_data.sum(axis=0), 0.0)
        self.assertAlmostEqual(self.logic.data.qy_data.sum(), 0.0)
        self.assertAlmostEqual(self.logic.data.q_data.sum(), 683.106490, 6)
        self.assertTrue(numpy.all(self.logic.data.mask))
        self.assertAlmostEqual(self.logic.data.x_bins.sum(), 0.0)
        self.assertAlmostEqual(self.logic.data.y_bins.sum(), 0.0)

    def testNew1DPlot(self):
        """
        Test how the extra shells are presented
        """
        data = Data1D(x=[1,2,3],y=[3,4,5])
        data.name = "boop"
        data.id = "poop"
        return_data = (data.x,data.y, 7, None, None,
                        0, True, 0.0, 1, data,
                        data, False, None)

        new_plot = self.logic.new1DPlot(return_data=return_data, tab_id=0)

        self.assertIsInstance(new_plot, Data1D)
        self.assertFalse(new_plot.is_data)
        self.assertEqual(new_plot.dy.size, 3)
        self.assertEqual(new_plot.title, "boop [poop]")
        self.assertEqual(new_plot.name, "boop [poop]")

    def testNew2DPlot(self):
        """
        Test the additional rows added by modifying the shells combobox
        """
        x_0 = 2.0*numpy.ones(25)
        dx_0 = 0.5*numpy.ones(25)
        qx_0 = numpy.arange(25)
        qy_0 = numpy.arange(25)
        mask_0 = numpy.zeros(25)
        dqx_0 = numpy.arange(25)/100
        dqy_0 = numpy.arange(25)/100
        q_0 = numpy.sqrt(qx_0 * qx_0 + qy_0 * qy_0)

        data = Data2D(image=x_0, err_image=dx_0, qx_data=qx_0,
                      qy_data=qy_0, q_data=q_0, mask=mask_0,
                      dqx_data=dqx_0, dqy_data=dqy_0)

        data.name = "boop"
        data.ymin = numpy.amin(q_0)
        data.ymax = numpy.amax(q_0)
        data.xmin = numpy.amin(x_0)
        data.xmax = numpy.amax(x_0)
        self.logic.data = data

        qmin, qmax, npts = self.logic.computeDataRange()

        return_data = (x_0, data, 7, data, None,
                        True, 0.0, 1, 0, qmin, qmax,
                        0.1, False, None)

        new_plot = self.logic.new2DPlot(return_data=return_data)

        self.assertIsInstance(new_plot, Data2D)
        self.assertFalse(new_plot.is_data)
        self.assertEqual(new_plot.title, "Analytical model 2D ")
        self.assertEqual(new_plot.name, "boop [boop]")



if __name__ == "__main__":
    unittest.main()
