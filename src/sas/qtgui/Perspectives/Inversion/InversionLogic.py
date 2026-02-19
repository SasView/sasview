import logging

import numpy as np
from PySide6.QtGui import QStandardItem

from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Utilities.GuiUtils import dataFromItem

PR_FIT_LABEL = r"$P_{fit}(r)$"
PR_LOADED_LABEL = r"$P_{loaded}(r)$"
IQ_DATA_LABEL = r"$I_{obs}(q)$"
IQ_FIT_LABEL = r"$I_{fit}(q)$"
IQ_SMEARED_LABEL = r"$I_{smeared}(q)$"
GROUP_ID_IQ_DATA = r"$I_{obs}(q)$"
GROUP_ID_PR_FIT = r"$P_{fit}(r)$"
PR_PLOT_PTS = 51

logger = logging.getLogger(__name__)


class InversionLogic:
    """All the data-related logic. This class deals exclusively with Data1D/2D. No QStandardModelIndex here."""

    _data_item: QStandardItem | None

    def __init__(self, data_item: QStandardItem | None = None):
        self._data_item = data_item
        self.data_is_loaded: bool = data_item is not None
        self.qmin: float = 0.0
        self.qmax: float = np.inf

    @property
    def data_item(self) -> QStandardItem | None:
        """Return the raw QStandardItem held by this logic instance."""
        return self._data_item

    @property
    def data(self) -> Data1D:
        """Return the Data1D object extracted from the current data item."""
        return dataFromItem(self._data_item)

    @data.setter
    def data(self, value: QStandardItem) -> None:
        """Set the data item and update the loaded flag accordingly."""
        self._data_item = value
        self.data_is_loaded = self._data_item is not None

    def isLoadedData(self) -> bool:
        """Return whether data has been loaded into this logic instance."""
        return self.data_is_loaded

    def new1DPlot(self, tab_id: int = 1, out=None, pr=None, q=None) -> Data1D:
        """Create a new 1D data instance based on fitting results."""
        qtemp = pr.x
        if q is not None:
            qtemp = q

        maxq = max(qtemp)
        minq = min(qtemp)

        # Check for user min/max
        if pr.q_min is not None and maxq >= pr.q_min >= minq:
            minq = pr.q_min
        if pr.q_max is not None and maxq >= pr.q_max >= minq:
            maxq = pr.q_max

        x = np.arange(minq, maxq, maxq / 301.0)

        # Vectorised iq.
        y = pr.iq(out, x)
        err = np.sqrt(np.abs(y))
        index = np.isnan(y)
        if index.any():
            y[index] = err[index] = 1.0
            logger.info("Could not compute I(q) for q =", list(x[index]))

        new_plot = Data1D(x, y)
        new_plot.is_data = False
        new_plot.dy = np.zeros(len(y))
        new_plot.name = "%s [%s]" % (IQ_FIT_LABEL, self.data.name)
        new_plot.xaxis("\\rm{Q}", "A^{-1}")
        new_plot.yaxis("\\rm{Intensity} ", "cm^{-1}")
        title = "I(q)"
        new_plot.title = title

        # If we have a group ID, use it
        if "plot_group_id" in pr.info:
            new_plot.group_id = pr.info["plot_group_id"]
        new_plot.id = str(tab_id) + IQ_FIT_LABEL

        # If we have used slit smearing, plot the smeared I(q) too
        if pr.slit_width > 0 or pr.slit_height > 0:
            x = np.arange(minq, maxq, maxq / 301.0)

            # Vectorised iq_smeared.
            y = pr.get_iq_smeared(out, x)
            err = np.sqrt(np.abs(y))
            index = np.isnan(y)
            if index.any():
                y[index] = err[index] = 1.0
                logger.info("Could not compute smeared I(q) for q =", list(x[index]))

            new_plot = Data1D(x, y)
            new_plot.name = IQ_SMEARED_LABEL
            new_plot.xaxis("\\rm{Q}", "A^{-1}")
            new_plot.yaxis("\\rm{Intensity} ", "cm^{-1}")
            # If we have a group ID, use it
            if "plot_group_id" in pr.info:
                new_plot.group_id = pr.info["plot_group_id"]
            new_plot.id = IQ_SMEARED_LABEL
            new_plot.title = title

        new_plot.symbol = "Line"
        new_plot.hide_error = True

        return new_plot

    def newPRPlot(self, out, pr, cov=None) -> Data1D:
        """Create a new P(r) plot from the inversion results."""
        x = np.arange(0.0, pr.dmax, pr.dmax / PR_PLOT_PTS)

        if cov is None:
            y = pr.pr(out, x)
            new_plot = Data1D(x, y)
        else:
            (y, dy) = pr.pr_err(out, cov, x)
            new_plot = Data1D(x, y, dy=dy)

        new_plot.name = "%s [%s]" % (PR_FIT_LABEL, self.data.name)
        new_plot.xaxis("\\rm{r}", "A")
        new_plot.yaxis("\\rm{P(r)} ", "cm^{-3}")
        new_plot.title = "P(r) fit"
        new_plot.id = PR_FIT_LABEL
        new_plot.xtransform = "x"
        new_plot.ytransform = "y"
        new_plot.group_id = GROUP_ID_PR_FIT

        return new_plot

    def add_errors(self, sigma: float = 0.05) -> np.ndarray:
        """Add errors to the data set if they are not available."""
        if self.data.dy.size == 0.0:
            self.data.dy = np.sqrt(np.fabs(self.data.y)) * sigma

        if self.data.dy is not None:
            self.data.dy = np.where(self.data.dy < 0.0, np.sqrt(np.fabs(self.data.y)) * sigma, self.data.dy)
            self.data.dy = np.where(np.fabs(self.data.dy) < 1e-16, 1e-16, self.data.dy)
        return self.data.dy

    def computeDataRange(self) -> tuple[float | None, float | None]:
        """Compute the data range based on the local dataset."""
        return self.computeRangeFromData(self.data)

    def computeRangeFromData(self, data: Data1D) -> tuple[float | None, float | None]:
        """Compute the minimum and maximum range of the data. Returns the (qmin, qmax) tuple."""
        qmin, qmax = None, None
        if isinstance(data, Data1D):
            try:
                qmax = max(data.x)
                # Set q values where intensity is zero to qmax and exclude from minimum accepted q
                # to avoid dodgy points around beam stop.
                usable_qrange = np.where(data.y <= 0, qmax, data.x)
                qmin = min(usable_qrange)
            except (ValueError, TypeError):
                msg = "Unable to find min/max/length of \n data named %s" % self.data.filename
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
