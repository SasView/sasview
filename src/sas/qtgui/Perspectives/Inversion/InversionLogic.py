import numpy as np

from sas.qtgui.Plotting.PlotterData import Data1D


class InversionLogic(object):
    """
    All the data-related logic. This class deals exclusively with Data1D/2D
    No QStandardModelIndex here.
    """

    def __init__(self, data=None):
        self._data = data
        self.data_is_loaded = False
        if data is not None:
            self.data_is_loaded = True

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        """ data setter """
        self._data = value
        self.data_is_loaded = True

    def isLoadedData(self):
        """ accessor """
        return self.data_is_loaded

    def new1DPlot(self, return_data):
        """
        Create a new 1D data instance based on fitting results
        """
        # Unpack return data from Calc1D
        x, y, page_id, state, weight,\
        fid, toggle_mode_on, \
        elapsed, index, model,\
        data, update_chisqr, source = return_data

        # Create the new plot
        new_plot = Data1D(x=x, y=y)
        new_plot.is_data = False
        new_plot.dy = np.zeros(len(y))
        _yaxis, _yunit = data.get_yaxis()
        _xaxis, _xunit = data.get_xaxis()

        new_plot.group_id = data.group_id
        new_plot.id = data.name
        new_plot.name = model.name + " [" + data.name + "]"
        new_plot.title = new_plot.name
        new_plot.xaxis(_xaxis, _xunit)
        new_plot.yaxis(_yaxis, _yunit)

        return new_plot

    def computeDataRange(self):
        """
        Wrapper for calculating the data range based on local dataset
        """
        return self.computeRangeFromData(self.data)

    def computeRangeFromData(self, data):
        """
        Compute the minimum and the maximum range of the data
        return the npts contains in data
        """
        qmin, qmax, npts = None, None, None
        if isinstance(data, Data1D):
            try:
                qmin = min(data.x)
                qmax = max(data.x)
                npts = len(data.x)
            except (ValueError, TypeError):
                msg = "Unable to find min/max/length of \n data named %s" % \
                            self.data.filename
                raise ValueError, msg

        else:
            qmin = 0
            try:
                x = max(np.fabs(data.xmin), np.fabs(data.xmax))
                y = max(np.fabs(data.ymin), np.fabs(data.ymax))
            except (ValueError, TypeError):
                msg = "Unable to find min/max of \n data named %s" % \
                            self.data.filename
                raise ValueError, msg
            qmax = np.sqrt(x * x + y * y)
            npts = len(data.data)
        return qmin, qmax, npts
