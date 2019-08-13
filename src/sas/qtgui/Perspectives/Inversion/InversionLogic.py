import math
import logging
import numpy as np

from sas.qtgui.Plotting.PlotterData import Data1D

PR_FIT_LABEL = r"$P_{fit}(r)$"
PR_LOADED_LABEL = r"$P_{loaded}(r)$"
IQ_DATA_LABEL = r"$I_{obs}(q)$"
IQ_FIT_LABEL = r"$I_{fit}(q)$"
IQ_SMEARED_LABEL = r"$I_{smeared}(q)$"
GROUP_ID_IQ_DATA = r"$I_{obs}(q)$"
GROUP_ID_PR_FIT = r"$P_{fit}(r)$"
PR_PLOT_PTS = 51

logger = logging.getLogger(__name__)


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
        self.data_is_loaded = (self._data is not None)

    def isLoadedData(self):
        """ accessor """
        return self.data_is_loaded

    def new1DPlot(self, out, pr, q=None):
        """
        Create a new 1D data instance based on fitting results
        """
        qtemp = pr.x
        if q is not None:
            qtemp = q

        # Make a plot
        maxq = max(qtemp)

        minq = min(qtemp)

        # Check for user min/max
        if pr.q_min is not None and maxq >= pr.q_min >= minq:
            minq = pr.q_min
        if pr.q_max is not None and maxq >= pr.q_max >= minq:
            maxq = pr.q_max

        x = np.arange(minq, maxq, maxq / 301.0)
        y = np.zeros(len(x))
        err = np.zeros(len(x))
        #vectorised iq
        y = pr.iq(out, x)
        with np.errstate(invalid='ignore'):
            err = np.sqrt(np.abs(y))
        index = np.isnan(err)
        if index.any():
            err[index] = 1.0
            logger.log("Could not compute error for (q, I(q)) = ", list(zip(x[index], value[index])))

        new_plot = Data1D(x, y)
        new_plot.name = IQ_FIT_LABEL
        new_plot.xaxis("\\rm{Q}", 'A^{-1}')
        new_plot.yaxis("\\rm{Intensity} ", "cm^{-1}")
        title = "I(q)"
        new_plot.title = title

        # If we have a group ID, use it
        if 'plot_group_id' in pr.info:
            new_plot.group_id = pr.info["plot_group_id"]
        new_plot.id = IQ_FIT_LABEL


        # If we have used slit smearing, plot the smeared I(q) too
        if pr.slit_width > 0 or pr.slit_height > 0:
            x = np.arange(minq, maxq, maxq / 301.0)
            y = np.zeros(len(x))
            err = np.zeros(len(x))

            #vectorised iq_smeared

            y = pr.iq_smeared(out, x)
            with np.errstate(invalid='ignore'):
                err = np.sqrt(np.abs(y))
            index = np.isnan(err)
            if index.any():
                err[index] = 1.0
                logger.log("Could not compute error for (q, I(q)) = ", list(zip(x[index], value[index])))

            new_plot = Data1D(x, y)
            new_plot.name = IQ_SMEARED_LABEL
            new_plot.xaxis("\\rm{Q}", 'A^{-1}')
            new_plot.yaxis("\\rm{Intensity} ", "cm^{-1}")
            # If we have a group ID, use it
            if 'plot_group_id' in pr.info:
                new_plot.group_id = pr.info["plot_group_id"]
            new_plot.id = IQ_SMEARED_LABEL
            new_plot.title = title

        new_plot.symbol = 'Line'
        new_plot.hide_error = True

        return new_plot

    def newPRPlot(self, out, pr, cov=None):
        """
        """
        # Show P(r)
        x = np.arange(0.0, pr.d_max, pr.d_max / PR_PLOT_PTS)

        if cov is None:
            y = pr.pr(out, x)
            new_plot = Data1D(x, y)
        else:
            (y, dy) = pr.pr_err(out, cov, x)
            new_plot = Data1D(x, y, dy=dy)

        new_plot.name = PR_FIT_LABEL
        new_plot.xaxis("\\rm{r}", 'A')
        new_plot.yaxis("\\rm{P(r)} ", "cm^{-3}")
        new_plot.title = "P(r) fit"
        new_plot.id = PR_FIT_LABEL
        new_plot.scale = "linear"
        new_plot.group_id = GROUP_ID_PR_FIT

        return new_plot

    def add_errors(self, sigma=0.05):
        """
        Adds errors to data set is they are not available.
        Uses  $\Delta y = \sigma | y |$.
        """
        self._data.dy = sigma * np.fabs(self._data.y)

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
        qmin, qmax = None, None
        if isinstance(data, Data1D):
            try:
                qmin = min(data.x)
                qmax = max(data.x)
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
        return qmin, qmax
