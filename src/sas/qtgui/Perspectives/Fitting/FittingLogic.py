import numpy as np

from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.PlotterData import Data2D

from sas.sascalc.dataloader.data_info import Detector
from sas.sascalc.dataloader.data_info import Source


class FittingLogic(object):
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

    def createDefault1dData(self, interval, tab_id=0):
        """
        Create default data for fitting perspective
        Only when the page is on theory mode.
        """
        self._data = Data1D(x=interval)
        self._data.xaxis('\\rm{Q}', "A^{-1}")
        self._data.yaxis('\\rm{Intensity}', "cm^{-1}")
        self._data.is_data = False
        self._data.id = str(tab_id) + " data"
        self._data.group_id = str(tab_id) + " Model1D"

    def createDefault2dData(self, qmax, qstep, tab_id=0):
        """
        Create 2D data by default
        Only when the page is on theory mode.
        """
        self._data = Data2D()
        self._data.xaxis('\\rm{Q_{x}}', 'A^{-1}')
        self._data.yaxis('\\rm{Q_{y}}', 'A^{-1}')
        self._data.is_data = False
        self._data.id = str(tab_id) + " data"
        self._data.group_id = str(tab_id) + " Model2D"

        # Default detector
        self._data.detector.append(Detector())
        index = len(self._data.detector) - 1
        self._data.detector[index].distance = 8000   # mm
        self._data.source.wavelength = 6             # A
        self._data.detector[index].pixel_size.x = 5  # mm
        self._data.detector[index].pixel_size.y = 5  # mm
        self._data.detector[index].beam_center.x = qmax
        self._data.detector[index].beam_center.y = qmax
        # theory default: assume the beam
        #center is located at the center of sqr detector
        xmax = qmax
        xmin = -qmax
        ymax = qmax
        ymin = -qmax

        x = np.linspace(start=xmin, stop=xmax, num=qstep, endpoint=True)
        y = np.linspace(start=ymin, stop=ymax, num=qstep, endpoint=True)
        # Use data info instead
        new_x = np.tile(x, (len(y), 1))
        new_y = np.tile(y, (len(x), 1))
        new_y = new_y.swapaxes(0, 1)

        # all data required in 1d array
        qx_data = new_x.flatten()
        qy_data = new_y.flatten()
        q_data = np.sqrt(qx_data * qx_data + qy_data * qy_data)

        # set all True (standing for unmasked) as default
        mask = np.ones(len(qx_data), dtype=bool)
        # calculate the range of qx and qy: this way,
        # it is a little more independent
        # store x and y bin centers in q space
        x_bins = x
        y_bins = y

        self._data.source = Source()
        self._data.data = np.ones(len(mask))
        self._data.err_data = np.ones(len(mask))
        self._data.qx_data = qx_data
        self._data.qy_data = qy_data
        self._data.q_data = q_data
        self._data.mask = mask
        self._data.x_bins = x_bins
        self._data.y_bins = y_bins
        # max and min taking account of the bin sizes
        self._data.xmin = xmin
        self._data.xmax = xmax
        self._data.ymin = ymin
        self._data.ymax = ymax

    def new1DPlot(self, return_data, tab_id):
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
        new_plot.id = str(tab_id) + " " + data.name
        new_plot.name = model.name + " [" + data.name + "]"
        new_plot.title = new_plot.name
        new_plot.xaxis(_xaxis, _xunit)
        new_plot.yaxis(_yaxis, _yunit)

        return new_plot

    def new2DPlot(self, return_data):
        """
        Create a new 2D data instance based on fitting results
        """
        image, data, page_id, model, state, toggle_mode_on,\
        elapsed, index, fid, qmin, qmax, weight, \
        update_chisqr, source = return_data

        np.nan_to_num(image)
        new_plot = Data2D(image=image, err_image=data.err_data)
        new_plot.name = model.name + '2d'
        new_plot.title = "Analytical model 2D "
        new_plot.id = str(page_id) + " " + data.name
        new_plot.group_id = str(page_id) + " Model2D"
        new_plot.detector = data.detector
        new_plot.source = data.source
        new_plot.is_data = False
        new_plot.qx_data = data.qx_data
        new_plot.qy_data = data.qy_data
        new_plot.q_data = data.q_data
        new_plot.mask = data.mask
        ## plot boundaries
        new_plot.ymin = data.ymin
        new_plot.ymax = data.ymax
        new_plot.xmin = data.xmin
        new_plot.xmax = data.xmax

        title = data.title

        new_plot.is_data = False
        if data.is_data:
            data_name = str(data.name)
        else:
            data_name = str(model.__class__.__name__) + '2d'

        if len(title) > 1:
            new_plot.title = "Model2D for %s " % model.name + data_name
        new_plot.name = model.name + " [" + \
                                    data_name + "]"

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
                raise ValueError(msg)

        else:
            qmin = 0
            try:
                x = max(np.fabs(data.xmin), np.fabs(data.xmax))
                y = max(np.fabs(data.ymin), np.fabs(data.ymax))
            except (ValueError, TypeError):
                msg = "Unable to find min/max of \n data named %s" % \
                            self.data.filename
                raise ValueError(msg)
            qmax = np.sqrt(x * x + y * y)
            npts = len(data.data)
        return qmin, qmax, npts
