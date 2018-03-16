import math
import pylab
import numpy as np

from sas.qtgui.Plotting.PlotterData import Data1D

PR_FIT_LABEL = r"$P_{fit}(r)$"
PR_LOADED_LABEL = r"$P_{loaded}(r)$"
IQ_DATA_LABEL = r"$I_{obs}(q)$"
IQ_FIT_LABEL = r"$I_{fit}(q)$"
IQ_SMEARED_LABEL = r"$I_{smeared}(q)$"
GROUP_ID_IQ_DATA = r"$I_{obs}(q)$"
GROUP_ID_PR_FIT = r"$P_{fit}(r)$"


class InversionLogic(object):
    """
    All the data-related logic. This class deals exclusively with Data1D/2D
    No QStandardModelIndex here.
    """

    # TODO: Add way to change this value
    _pr_n_pts = 51

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

        x = pylab.arange(minq, maxq, maxq / 301.0)
        y = np.zeros(len(x))
        err = np.zeros(len(x))
        for i in range(len(x)):
            value = pr.iq(out, x[i])
            y[i] = value
            try:
                err[i] = math.sqrt(math.fabs(value))
            except:
                err[i] = 1.0
                print(("Error getting error", value, x[i]))

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
            x = pylab.arange(minq, maxq, maxq / 301.0)
            y = np.zeros(len(x))
            err = np.zeros(len(x))
            for i in range(len(x)):
                value = pr.iq_smeared(pr.out, x[i])
                y[i] = value
                try:
                    err[i] = math.sqrt(math.fabs(value))
                except:
                    err[i] = 1.0
                    print(("Error getting error", value, x[i]))

            new_plot = Data1D(x, y)
            new_plot.name = IQ_SMEARED_LABEL
            new_plot.xaxis("\\rm{Q}", 'A^{-1}')
            new_plot.yaxis("\\rm{Intensity} ", "cm^{-1}")
            # If we have a group ID, use it
            if 'plot_group_id' in pr.info:
                new_plot.group_id = pr.info["plot_group_id"]
            new_plot.id = IQ_SMEARED_LABEL
            new_plot.title = title

        return new_plot

    def update1DPlot(self, plot, out, pr, q=None):
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

        x = pylab.arange(minq, maxq, maxq / 301.0)
        y = np.zeros(len(x))
        err = np.zeros(len(x))
        for i in range(len(x)):
            value = pr.iq(out, x[i])
            y[i] = value
            try:
                err[i] = math.sqrt(math.fabs(value))
            except:
                err[i] = 1.0
                print(("Error getting error", value, x[i]))

        plot.x = x
        plot.y = y

        # If we have used slit smearing, plot the smeared I(q) too
        if pr.slit_width > 0 or pr.slit_height > 0:
            x = pylab.arange(minq, maxq, maxq / 301.0)
            y = np.zeros(len(x))
            err = np.zeros(len(x))
            for i in range(len(x)):
                value = pr.iq_smeared(pr.out, x[i])
                y[i] = value
                try:
                    err[i] = math.sqrt(math.fabs(value))
                except:
                    err[i] = 1.0
                    print(("Error getting error", value, x[i]))

            plot.x = x
            plot.y = y

        return plot

    def newPRPlot(self, out, pr, cov=None):
        """
        """
        # Show P(r)
        x = pylab.arange(0.0, pr.d_max, pr.d_max / self._pr_n_pts)

        y = np.zeros(len(x))
        dy = np.zeros(len(x))

        total = 0.0
        pmax = 0.0
        cov2 = np.ascontiguousarray(cov)

        for i in range(len(x)):
            if cov2 is None:
                value = pr.pr(out, x[i])
            else:
                (value, dy[i]) = pr.pr_err(out, cov2, x[i])
            total += value * pr.d_max / len(x)

            # keep track of the maximum P(r) value
            if value > pmax:
                pmax = value

            y[i] = value

        # if self._normalize_output == True:
        #     y = y / total
        #     dy = dy / total
        # elif self._scale_output_unity == True:
        #     y = y / pmax
        #     dy = dy / pmax

        if cov2 is None:
            new_plot = Data1D(x, y)
        else:
            new_plot = Data1D(x, y, dy=dy)
        new_plot.name = PR_FIT_LABEL
        new_plot.xaxis("\\rm{r}", 'A')
        new_plot.yaxis("\\rm{P(r)} ", "cm^{-3}")
        new_plot.title = "P(r) fit"
        new_plot.id = PR_FIT_LABEL
        # Make sure that the plot is linear
        new_plot.xtransform = "x"
        new_plot.ytransform = "y"
        new_plot.group_id = GROUP_ID_PR_FIT

        return new_plot

    def updatePRPlot(self, plot, out, pr, cov=None):
        x = pylab.arange(0.0, pr.d_max, pr.d_max / self._pr_n_pts)

        y = np.zeros(len(x))
        dy = np.zeros(len(x))

        total = 0.0
        pmax = 0.0
        cov2 = np.ascontiguousarray(cov)

        for i in range(len(x)):
            if cov2 is None:
                value = pr.pr(out, x[i])
            else:
                (value, dy[i]) = pr.pr_err(out, cov2, x[i])
            total += value * pr.d_max / len(x)

            # keep track of the maximum P(r) value
            if value > pmax:
                pmax = value

            y[i] = value

        # if self._normalize_output == True:
        #     y = y / total
        #     dy = dy / total
        # elif self._scale_output_unity == True:
        #     y = y / pmax
        #     dy = dy / pmax
        plot.x = x
        plot.y = y

        if cov2 is not None:
            plot.dy = dy

        return plot

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
