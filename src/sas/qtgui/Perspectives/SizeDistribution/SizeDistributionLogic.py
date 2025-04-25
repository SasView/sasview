import numpy as np

from sas.qtgui.Perspectives.SizeDistribution.SizeDistributionUtils import MaxEntResult
from sas.qtgui.Plotting.PlotterData import Data1D, DataRole
from sasdata.dataloader.data_info import Data1D as LoadData1D

BACKGD_PLOT_LABEL = "Background"
BACKGD_SUBTR_PLOT_LABEL = "Intensity-Background"
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
        self.background = None
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
        if self._data.dy is not None and np.any(self._data.dy):
            self.di_flag = True

    def computeDataRange(self):
        """
        Compute the minimum and the maximum range of the data
        """
        try:
            qmin = min(self.data.x)
            qmax = max(self.data.x)
        except (ValueError, TypeError):
            msg = (
                "Unable to find min/max/length of \n data named %s" % self.data.filename
            )
            raise ValueError(msg)
        return qmin, qmax

    def computeBackground(self, constant: float, scale: float, power: float):
        x = self.data.x
        # calculate a*x^m + b
        y_back = scale * x**power + constant
        # TODO: the dy is the same as in TestSizeDistribution.py, but is it needed?
        self.background = LoadData1D(
            x, y_back, dy=0.0001 * y_back, lam=None, dlam=None, isSesans=False
        )

    def newDataPlot(self):
        """
        Create a new 1D data instance
        """
        # Background plot
        backgd_plot = Data1D(self.background.x, self.background.y)
        backgd_plot.is_data = False
        backgd_plot.plot_role = DataRole.ROLE_DATA

        backgd_plot.id = BACKGD_PLOT_LABEL
        backgd_plot.group_id = GROUP_ID_SIZE_DISTR_DATA
        backgd_plot.name = BACKGD_PLOT_LABEL + f"[{self._data.name}]"

        backgd_plot.title = backgd_plot.name
        backgd_plot.xaxis("\\rm{Q}", "A^{-1}")
        backgd_plot.yaxis("\\rm{Intensity} ", "cm^{-1}")

        backgd_plot.symbol = "Line"
        backgd_plot.show_errors = False

        # Background subtracted plot
        y_sub = self.data.y - self.background.y
        backgd_subtr_plot = Data1D(self.data.x, y_sub, dy=self._data.dy)
        backgd_subtr_plot.is_data = False
        backgd_subtr_plot.plot_role = DataRole.ROLE_DATA

        backgd_subtr_plot.id = BACKGD_SUBTR_PLOT_LABEL
        backgd_subtr_plot.group_id = GROUP_ID_SIZE_DISTR_DATA
        backgd_subtr_plot.name = BACKGD_SUBTR_PLOT_LABEL + f"[{self._data.name}]"

        backgd_subtr_plot.title = backgd_subtr_plot.name
        backgd_subtr_plot.xaxis("\\rm{Q}", "A^{-1}")
        backgd_subtr_plot.yaxis("\\rm{Intensity} ", "cm^{-1}")

        backgd_subtr_plot.symbol = "Circle"
        backgd_subtr_plot.show_errors = True
        backgd_subtr_plot.show_q_range_sliders = True
        # Suppress the GUI update until the move is finished to limit model calculations
        backgd_subtr_plot.slider_update_on_move = False
        backgd_subtr_plot.slider_perspective_name = "SizeDistribution"
        backgd_subtr_plot.slider_low_q_input = ["txtMinRange"]
        backgd_subtr_plot.slider_high_q_input = ["txtMaxRange"]

        return backgd_plot, backgd_subtr_plot

    def newSizeDistrPlot(self, result: MaxEntResult):
        """
        Create a new 1D data instance based on fitting results
        """
        # Create the new plot
        #bins are radius but plot is in diameter
        x = 2 * result.bins
        y = result.bin_mag
        dy = result.bin_err
        new_plot = Data1D(x=x, y=y, dy=dy)
        new_plot.is_data = False
        new_plot.plot_role = DataRole.ROLE_STAND_ALONE
        new_plot.symbol = "Line"

        new_plot.id = SIZE_DISTR_LABEL
        new_plot.group_id = GROUP_ID_SIZE_DISTR_FIT
        new_plot.name = SIZE_DISTR_LABEL + f"[{self._data.name}]"

        new_plot.title = new_plot.name
        new_plot.xaxis("\\rm{Diameter}", "A")
        new_plot.yaxis("\\rm{VolumeDistribution} ", "")

        return new_plot
