from __future__ import annotations
from typing import Optional, Tuple, TYPE_CHECKING

import numpy as np

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

if TYPE_CHECKING:
    from sas.qtgui.Perspectives.Corfunc.CorfuncPerspective import CorfuncWindow


class QSpaceCanvas(FigureCanvas):
    """ Canvas for displaying input data and extrapolation parameters"""

    def __init__(self, parent: CorfuncWindow, width=5, height=4, dpi=100):
        self.parent = parent
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)

        FigureCanvas.__init__(self, self.fig)

        self.data: Optional[Tuple[np.ndarray, np.ndarray, np.ndarray]] = None
        self.extrap = None

    def draw_lines(self):
        pass

    def draw_data(self):
        """Draw the Q space data in the plot window

        This draws the q space data in self.data, as well
        as the bounds set by self.qmin, self.qmax1, and self.qmax2.
        It will also plot the extrpolation in self.extrap, if it exists."""

        self.draggable = True

        self.fig.clf()

        self.axes = self.fig.add_subplot(111)
        self.axes.set_xscale("log")
        self.axes.set_yscale("log")
        self.axes.set_xlabel("Q [$\AA^{-1}$]")
        self.axes.set_ylabel("I(Q) [cm$^{-1}$]")
        self.axes.set_title("Scattering data")
        self.fig.tight_layout()

        if self.data:

            extrapolation_params = self.parent.extrapolation_parmameters

            # self.axes.plot(self.data.x, self.data.y, label="Experimental Data")
            self.axes.errorbar(self.data.x, self.data.y, yerr=self.data.dy, label="Experimental Data")
            self.axes.axvline(extrapolation_params.point_1, color='k')
            self.axes.axvline(extrapolation_params.point_2, color='k')
            self.axes.axvline(extrapolation_params.point_3, color='k')
            self.axes.set_xlim(extrapolation_params.data_q_min / 2,
                               extrapolation_params.data_q_max* 1.5 - 0.5 * extrapolation_params.data_q_min)
            self.axes.set_ylim(min(self.data.y) / 2,
                               max(self.data.y) * 1.5 - 0.5 * min(self.data.y))

        if self.extrap:
            self.axes.plot(self.extrap.x, self.extrap.y, label="Extrapolation")

        if self.data or self.extrap:
            self.legend = self.axes.legend()

        self.draw()

