import numpy as np

from sas.qtgui.Plotting.PlotterData import Data1D, DataRole

DATA_PLOT_LABEL = "Background"
GROUP_ID_SIZE_DISTR_DATA = "SizeDistrData"
SIZE_DISTR_LABEL = "SizeDistrFit"
GROUP_ID_SIZE_DISTR_FIT = "SizeDistrFit"


class SizeDistributionLogic:
    """
    All the data-related logic. This class deals exclusively with Data1D/2D
    No QStandardModelIndex here.
    """

    def __init__(self, data=None):
        self._data = data
        self.data_is_loaded = False
        # di data presence in the dataset
        self.di_flag = False
        if data is not None:
            self.data_is_loaded = True
            self.setDataProperties()

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        """data setter"""
        self._data = value
        self.data_is_loaded = self._data is not None
        if self._data is not None:
            self.setDataProperties()

    def isLoadedData(self):
        """accessor"""
        return self.data_is_loaded

    def setDataProperties(self):
        """
        Analyze data and set up some properties important for
        the Presentation layer
        """
        if self._data.__class__.__name__ == "Data2D":
            if self._data.err_data is not None and np.any(self._data.err_data):
                self.di_flag = True
        else:
            if self._data.dy is not None and np.any(self._data.dy):
                self.di_flag = True

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
        if isinstance(data, Data1D):
            try:
                qmin = min(data.x)
                qmax = max(data.x)
            except (ValueError, TypeError):
                msg = (
                    "Unable to find min/max/length of \n data named %s"
                    % self.data.filename
                )
                raise ValueError(msg)

        else:
            qmin = 0
            try:
                x = max(np.fabs(data.xmin), np.fabs(data.xmax))
                y = max(np.fabs(data.ymin), np.fabs(data.ymax))
            except (ValueError, TypeError):
                msg = "Unable to find min/max of \n data named %s" % self.data.filename
                raise ValueError(msg)
            qmax = np.sqrt(x * x + y * y)
        return qmin, qmax

    def new_data_plot(self, data):
        """
        Create a new 1D data instance
        """
        # Create the new plot
        new_plot = Data1D(data[0], data[1])
        new_plot.is_data = False
        new_plot.plot_role = DataRole.ROLE_DATA

        new_plot.id = DATA_PLOT_LABEL
        new_plot.group_id = GROUP_ID_SIZE_DISTR_DATA
        new_plot.name = DATA_PLOT_LABEL + f"[{self._data.name}]"

        new_plot.title = new_plot.name
        new_plot.xaxis("\\rm{Q}", "A^{-1}")
        new_plot.yaxis("\\rm{Intensity} ", "cm^{-1}")

        return new_plot

    def new_size_distr_plot(self, data):
        """
        Create a new 1D data instance based on fitting results
        """
        # Create the new plot
        x = data["x"]
        y = data["y"]
        new_plot = Data1D(x=x, y=y)
        new_plot.is_data = False
        new_plot.plot_role = DataRole.ROLE_STAND_ALONE
        new_plot.dy = np.zeros(len(y))

        new_plot.id = SIZE_DISTR_LABEL
        new_plot.group_id = GROUP_ID_SIZE_DISTR_FIT
        new_plot.name = SIZE_DISTR_LABEL + f"[{self._data.name}]"

        new_plot.title = new_plot.name
        new_plot.xaxis("\\rm{Diameter}", "A")
        new_plot.yaxis("\\rm{VolumeDistribution} ", "")

        return new_plot
