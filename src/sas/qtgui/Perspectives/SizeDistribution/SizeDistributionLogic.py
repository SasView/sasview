import logging

import numpy as np

from sasdata.dataloader.data_info import Data1D as LoadData1D

from sas.qtgui.Perspectives.SizeDistribution.SizeDistributionUtils import MaxEntResult
from sas.qtgui.Plotting.PlotterData import Data1D, DataRole
from sas.sascalc.size_distribution.SizeDistribution import background_fit

BACKGD_PLOT_LABEL = "Background"
BACKGD_SUBTR_PLOT_LABEL = "Intensity-Background"
FIT_PLOT_LABEL = "Fit"
GROUP_ID_SIZE_DISTR_DATA = "SizeDistrData"
SIZE_DISTR_LABEL = "SizeDistrFit"
GROUP_ID_SIZE_DISTR_FIT = "SizeDistrFit"
TRUST_RANGE_LABEL = "SizeDistrTrustRange"


logger = logging.getLogger(__name__)


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
        self.data_fit = None
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
        else:
            self.di_flag = False

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

    def computeTrustRange(self, qmin: float, qmax: float):
        """
        Compute the trusted range (green area in Irena)
        """
        d_trust_min = 1.8 * np.pi / qmax
        d_trust_max = 0.95 * np.pi / qmin
        return [d_trust_min, d_trust_max]

    def fitBackground(
        self, power: float | None, qmin: float, qmax: float
    ) -> list[float]:
        """
        Estimate the background power law, scale * q^(power)
        :param power: if a float is given, the power is fixed; if None, the power is fitted
        :return: fit parameters; [scale] if power is fixed, or [scale, power] if power is fitted
        """
        try:
            background, _ = background_fit(self.data, power, qmin, qmax)
        except ValueError:
            logger.exception("Fitting failed")
            return None
        return background

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

        # Fit plot
        fit_plot = None
        if self.data_fit is not None:
            fit_plot = Data1D(self.data_fit.x, self.data_fit.y, dy=self.data_fit.dy)
            fit_plot.is_data = False
            fit_plot.plot_role = DataRole.ROLE_DATA

            fit_plot.id = FIT_PLOT_LABEL
            fit_plot.group_id = GROUP_ID_SIZE_DISTR_DATA
            fit_plot.name = FIT_PLOT_LABEL + f"[{self._data.name}]"

            fit_plot.title = fit_plot.name
            fit_plot.xaxis("\\rm{Q}", "A^{-1}")
            fit_plot.yaxis("\\rm{Intensity} ", "cm^{-1}")

            fit_plot.symbol = "Line"
            fit_plot.show_errors = True

        return backgd_plot, backgd_subtr_plot, fit_plot

    def newSizeDistrPlot(self, result: MaxEntResult, qmin: float, qmax: float):
        """
        Create a new 1D data instance based on fitting results
        """
        # Create the new plot
        # bins are radius but plot is in diameter
        x = 2 * result.bins
        y = result.bin_mag
        dy = result.bin_err
        new_plot = Data1D(x=x, y=y, dy=dy)
        new_plot.is_data = False
        new_plot.plot_role = DataRole.ROLE_SIZE_DISTRIBUTION
        new_plot.symbol = "Circle"

        new_plot.id = SIZE_DISTR_LABEL
        new_plot.group_id = GROUP_ID_SIZE_DISTR_FIT
        new_plot.name = SIZE_DISTR_LABEL + f"[{self._data.name}]"

        new_plot.hide_error = False
        new_plot.title = new_plot.name
        new_plot.xaxis("\\rm{Diameter}", "A")
        new_plot.yaxis("\\rm{VolumeDistribution}", "")

        # Create vertical lines for trusted range
        x_trust = self.computeTrustRange(qmin, qmax)
        y_max_trust = np.full_like(x_trust, max(y))  # lines start at 0.0 and end at y
        trust_plot = Data1D(x=x_trust, y=y_max_trust)
        trust_plot.is_data = False
        trust_plot.symbol = "Vline"
        trust_plot.custom_color = "Red"
        trust_plot.xaxis("\\rm{Diameter}", "A")
        trust_plot.yaxis("\\rm{VolumeDistribution}", "")
        trust_plot.plot_role = DataRole.ROLE_SIZE_DISTRIBUTION

        trust_plot.id = TRUST_RANGE_LABEL
        trust_plot.group_id = GROUP_ID_SIZE_DISTR_FIT
        trust_plot.name = TRUST_RANGE_LABEL + f"[{self._data.name}]"

        return new_plot, trust_plot
