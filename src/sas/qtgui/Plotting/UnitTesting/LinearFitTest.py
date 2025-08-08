import matplotlib as mpl
import numpy
import pytest

mpl.use("Qt5Agg")

from PySide6 import QtWidgets

import sas.qtgui.Plotting.Plotter as Plotter

# Local
from sas.qtgui.Plotting.LinearFit import LinearFit
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.UnitTesting.TestUtils import QtSignalSpy


class LinearFitTest:
    '''Test the LinearFit'''

    @pytest.fixture(autouse=True)
    def widget(self, qapp):
        '''Create/Destroy the LinearFit'''
        data = Data1D(x=[1.0, 2.0, 3.0],
                           y=[10.0, 11.0, 12.0],
                           dx=[0.1, 0.2, 0.3],
                           dy=[0.1, 0.2, 0.3])
        plotter = Plotter.Plotter(None, quickplot=True)
        plotter.plot(data)
        w = LinearFit(parent=plotter, data=data, xlabel="log10(x^2)", ylabel="log10(y)")

        yield w

        '''Destroy the GUI'''
        w.close()

    def testDefaults(self, widget):
        '''Test the GUI in its default state'''
        assert isinstance(widget, QtWidgets.QDialog)
        assert widget.windowTitle() == "Linear Fit"
        assert widget.txtA.text() == "1"
        assert widget.txtB.text() == "1"
        assert widget.txtAerr.text() == "0"
        assert widget.txtBerr.text() == "0"

        assert widget.lblRange.text() == "Fit range of log10(x^2)"

    @pytest.mark.skip("2022-09 already broken - generates runtime error")
    # Plotting/LinearFit.py:230: RuntimeWarning: invalid value encountered in sqrt rg = numpy.sqrt(-3 * float(cstA))
    def testFit(self, widget):
        '''Test the fitting wrapper '''
        # Catch the update signal
        #widget.updatePlot.emit = MagicMock()
        #widget.updatePlot.emit = MagicMock()
        spy_update = QtSignalSpy(widget, widget.updatePlot)

        # Set some initial values
        widget.txtRangeMin.setText("1.0")
        widget.txtRangeMax.setText("3.0")
        widget.txtFitRangeMin.setText("1.0")
        widget.txtFitRangeMax.setText("3.0")
        # Run the fitting
        widget.fit(None)

        # Expected one spy instance
        assert spy_update.count() == 1

        return_values = spy_update.called()[0]['args'][0]
        # Compare
        assert sorted(return_values[0]) == [1.0, 3.0]
        assert return_values[1] == pytest.approx([10.004054329, 12.030439848], abs=1e-6)

        # Set the log scale
        widget.x_is_log = True
        widget.fit(None)
        assert spy_update.count() == 2
        return_values = spy_update.called()[1]['args'][0]
        # Compare
        assert sorted(return_values[0]) == [1.0, 3.0]
        assert return_values[1] == pytest.approx([9.987732937, 11.84365082], abs=1e-6)

    #@pytest.mark.skip("2022-09 already broken - generates runtime error")
    # LinearFit.py:255: RuntimeWarning: divide by zero encountered in log10 xmin_check = numpy.log10(self.xminFit)
    def testOrigData(self, widget):
        ''' Assure the un-logged data is returned'''
        # log(x), log(y)
        widget.xminFit, widget.xmaxFit = widget.range()
        orig_x = [ 1.,  2.,  3.]
        orig_y = [1.0, 1.0413926851582251, 1.0791812460476249]
        orig_dy = [0.01, 0.018181818181818184, 0.024999999999999998]
        x, y, dy = widget.origData()

        assert sorted(x) == sorted(orig_x)
        assert y[0] == orig_y[0]
        assert y[1:3] == pytest.approx(orig_y[1:3], abs=1e-8)
        assert dy[0] == orig_dy[0]
        assert dy[1:3] == pytest.approx(orig_dy[1:3], abs=1e-8)

        # x, y
        widget.x_is_log = False
        widget.y_is_log = False
        widget.xminFit, widget.xmaxFit = widget.range()
        orig_x = [ 1.,  2.,  3.]
        orig_y = [10., 11., 12.]
        orig_dy = [0.1, 0.2, 0.3]
        x, y, dy = widget.origData()

        assert sorted(x) == sorted(orig_x)
        assert sorted(y) == sorted(orig_y)
        assert sorted(dy) == sorted(orig_dy)

        # x, log(y)
        widget.x_is_log = False
        widget.y_is_log = True
        widget.xminFit, widget.xmaxFit = widget.range()
        orig_x = [ 1.,  2.,  3.]
        orig_y = [1.0, 1.0413926851582251, 1.0791812460476249]
        orig_dy = [0.01, 0.018181818181818184, 0.024999999999999998]
        x, y, dy = widget.origData()

        assert sorted(x) == sorted(orig_x)
        assert y[0] == orig_y[0]
        assert y[1:3] == pytest.approx(orig_y[1:3], abs=1e-8)
        assert dy[0] == orig_dy[0]
        assert dy[1:3] == pytest.approx(orig_dy[1:3], abs=1e-8)

    def testCheckFitValues(self, widget):
        '''Assure fit values are correct'''
        # Good values
        assert widget.checkFitValues(widget.txtFitRangeMin)
        # Colors platform dependent
        #assert widget.txtFitRangeMin.palette().color(10).name() == "#f0f0f0"
        # Bad values
        widget.x_is_log = True
        widget.txtFitRangeMin.setText("-1.0")
        assert not widget.checkFitValues(widget.txtFitRangeMin)


    def testFloatInvTransform(self, widget):
        '''Test the helper method for providing conversion function'''
        widget.xLabel="x"
        assert widget.floatInvTransform(5.0) == 5.0
        widget.xLabel="x^(2)"
        assert widget.floatInvTransform(25.0) == 5.0
        widget.xLabel="x^(4)"
        assert widget.floatInvTransform(81.0) == 3.0
        widget.xLabel="log10(x)"
        assert widget.floatInvTransform(2.0) == 100.0
        widget.xLabel="ln(x)"
        assert widget.floatInvTransform(1.0) == numpy.exp(1)
        widget.xLabel="log10(x^(4))"
        assert widget.floatInvTransform(4.0) == 10.0
