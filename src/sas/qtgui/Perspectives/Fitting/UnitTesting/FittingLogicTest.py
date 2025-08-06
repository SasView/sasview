
import numpy
import pytest

# Local
from sas.qtgui.Perspectives.Fitting.FittingWidget import FittingLogic
from sas.qtgui.Plotting.PlotterData import Data1D, Data2D


class FittingLogicTest:
    """Test the fitting logic class"""

    @pytest.fixture(autouse=True)
    def logic(self, qapp):
        '''Create/Destroy the component'''
        data = Data1D(x=[1,2,3],y=[3,4,5])
        logic = FittingLogic(data=data)
        yield logic

    def testDefaults(self, logic):
        """Test the component in its default state"""
        assert isinstance(logic.data, Data1D)
        assert logic.data_is_loaded
        assert logic.data == logic._data

    def testComputeDataRange(self, logic):
        """
        Tests the data range calculator on Data1D/Data2D
        """
        # Using the default data
        qmin, qmax, npts = logic.computeDataRange()

        assert qmin == 1
        assert qmax == 3
        assert npts == 3

        # data with more points
        data = Data1D(x=[-10, 2, 10, 20],y=[-3, 4, 10, 50])
        logic.data=data
        qmin, qmax, npts = logic.computeDataRange()

        assert qmin == -10
        assert qmax == 20
        assert npts == 4

    def testCreateDefault1dData(self, logic):
        """
        Tests the default 1D set
        """
        interval = numpy.linspace(start=1, stop=10, num=10, endpoint=True)
        logic.createDefault1dData(interval=interval)

        assert logic.data.id == ('0 data')
        assert logic.data.group_id == ('0 Model1D')
        assert not logic.data.is_data
        assert logic.data._xaxis == ('\\rm{Q}')
        assert logic.data._xunit == ('A^{-1}')
        assert logic.data._yaxis == ('\\rm{Intensity}')
        assert logic.data._yunit == ('cm^{-1}')

    def testCreateDefault2dData(self, logic):
        """
        Tests the default 2D set
        """
        logic.createDefault2dData(qmax=0.35, qstep=50, tab_id=8)

        assert logic.data.id == ('8 data')
        assert logic.data.group_id == ('8 Model2D')
        assert not logic.data.is_data
        assert logic.data._xaxis == ('\\rm{Q_{x}}')
        assert logic.data._xunit == ('A^{-1}')
        assert logic.data._yaxis == ('\\rm{Q_{y}}')
        assert logic.data._yunit == ('A^{-1}')

        assert logic.data.xmin == -0.35
        assert logic.data.xmax == 0.35

        assert logic.data.ymin == -0.35
        assert logic.data.ymax == 0.35

        assert logic.data.data.sum() == 2500.0 # 50x50 array of 1's
        assert logic.data.err_data.sum(axis=0) == 2500.0
        assert logic.data.qx_data.sum(axis=0) == pytest.approx(0.0, abs=1e-7)
        assert logic.data.qy_data.sum() == pytest.approx(0.0, abs=1e-7)
        assert logic.data.q_data.sum() == pytest.approx(683.106490, abs=1e-6)
        assert numpy.all(logic.data.mask)
        assert logic.data.x_bins.sum() == pytest.approx(0.0, abs=1e-7)
        assert logic.data.y_bins.sum() == pytest.approx(0.0, abs=1e-7)

    def testNew1DPlot(self, logic):
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

        new_plot = logic.new1DPlot(return_data=return_data, tab_id=0)

        assert isinstance(new_plot, Data1D)
        assert not new_plot.is_data
        assert new_plot.dy.size == 3
        assert new_plot.title == "boop [boop]"
        assert new_plot.name == "boop [boop]"

    def testNew2DPlot(self, logic):
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
        logic.data = data

        qmin, qmax, npts = logic.computeDataRange()

        # Condensed return data (new2DPlot only uses these fields)
        return_data = dict(image = x_0,
                           data = data,
                           page_id = 7,
                           model = data)
        # return_data = (x_0, data, 7, data, None,
        #                 True, 0.0, 1, 0, qmin, qmax,
        #                 0.1, False, None)

        new_plot = logic.new2DPlot(return_data=return_data)

        assert isinstance(new_plot, Data2D)
        assert not new_plot.is_data
        assert new_plot.title == "Analytical model 2D "
        assert new_plot.name == "boop [boop]"
