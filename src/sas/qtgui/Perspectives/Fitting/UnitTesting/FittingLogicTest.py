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
        assert isinstance(self.logic.data, Data1D)
        assert self.logic.data_is_loaded
        assert self.logic.data == self.logic._data

    def testComputeDataRange(self):
        """
        Tests the data range calculator on Data1D/Data2D
        """
        # Using the default data
        qmin, qmax, npts = self.logic.computeDataRange()

        assert qmin == 1
        assert qmax == 3
        assert npts == 3

        # data with more points
        data = Data1D(x=[-10, 2, 10, 20],y=[-3, 4, 10, 50])
        self.logic.data=data
        qmin, qmax, npts = self.logic.computeDataRange()

        assert qmin == -10
        assert qmax == 20
        assert npts == 4

    def testCreateDefault1dData(self):
        """
        Tests the default 1D set
        """
        interval = numpy.linspace(start=1, stop=10, num=10, endpoint=True)
        self.logic.createDefault1dData(interval=interval)

        assert self.logic.data.id == ('0 data')
        assert self.logic.data.group_id == ('0 Model1D')
        assert not self.logic.data.is_data
        assert self.logic.data._xaxis == ('\\rm{Q}')
        assert self.logic.data._xunit == ('A^{-1}')
        assert self.logic.data._yaxis == ('\\rm{Intensity}')
        assert self.logic.data._yunit == ('cm^{-1}')

    def testCreateDefault2dData(self):
        """
        Tests the default 2D set
        """
        self.logic.createDefault2dData(qmax=0.35, qstep=50, tab_id=8)

        assert self.logic.data.id == ('8 data')
        assert self.logic.data.group_id == ('8 Model2D')
        assert not self.logic.data.is_data
        assert self.logic.data._xaxis == ('\\rm{Q_{x}}')
        assert self.logic.data._xunit == ('A^{-1}')
        assert self.logic.data._yaxis == ('\\rm{Q_{y}}')
        assert self.logic.data._yunit == ('A^{-1}')

        assert self.logic.data.xmin == -0.35
        assert self.logic.data.xmax == 0.35

        assert self.logic.data.ymin == -0.35
        assert self.logic.data.ymax == 0.35

        assert self.logic.data.data.sum() == 2500.0 # 50x50 array of 1's
        assert self.logic.data.err_data.sum(axis=0) == 2500.0
        assert round(abs(self.logic.data.qx_data.sum(axis=0)-0.0), 7) == 0
        assert round(abs(self.logic.data.qy_data.sum()-0.0), 7) == 0
        assert round(abs(self.logic.data.q_data.sum()-683.106490), 6) == 0
        assert numpy.all(self.logic.data.mask)
        assert round(abs(self.logic.data.x_bins.sum()-0.0), 7) == 0
        assert round(abs(self.logic.data.y_bins.sum()-0.0), 7) == 0

    def testNew1DPlot(self):
        """
        Test how the extra shells are presented
        """
        data = Data1D(x=[1,2,3],y=[3,4,5])
        data.name = "boop"
        data.id = "poop"
        # Condensed return data (new1DPlot only uses these fields)
        return_data = dict(x = data.x,
                           y = data.y,
                           model = data,
                           data = data)
        # return_data = (data.x,data.y, 7, None, None,
        #                0, True, 0.0, 1, data,
        #                data, False, None,
        #                None, None, None,
        #                None, None)

        new_plot = self.logic.new1DPlot(return_data=return_data, tab_id=0)

        assert isinstance(new_plot, Data1D)
        assert not new_plot.is_data
        assert new_plot.dy.size == 3
        assert new_plot.title == "boop [boop]"
        assert new_plot.name == "boop [boop]"

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

        # Condensed return data (new2DPlot only uses these fields)
        return_data = dict(image = x_0,
                           data = data,
                           page_id = 7,
                           model = data)
        # return_data = (x_0, data, 7, data, None,
        #                 True, 0.0, 1, 0, qmin, qmax,
        #                 0.1, False, None)

        new_plot = self.logic.new2DPlot(return_data=return_data)

        assert isinstance(new_plot, Data2D)
        assert not new_plot.is_data
        assert new_plot.title == "Analytical model 2D "
        assert new_plot.name == "boop [boop]"



if __name__ == "__main__":
    unittest.main()
