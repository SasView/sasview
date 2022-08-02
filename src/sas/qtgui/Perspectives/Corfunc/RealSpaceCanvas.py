from typing import Optional, Tuple

import numpy as np

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from .corefuncutil import WIDGETS


class RealSpaceCanvas(FigureCanvas):
    """ Canvas for displaying real space representation"""

    def __init__(self, model, width=5, height=4, dpi=100):
        self.model = model
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)

        FigureCanvas.__init__(self, self.fig)

        self.data: Optional[Tuple[np.ndarray, np.ndarray, np.ndarray]] = None


    def draw_real_space(self):
        """
        This function draws the real space data onto the plot

        The 1d correlation function in self.data, the 3d correlation function
        in self.data3, and the interface distribution function in self.data_idf
        are all draw in on the plot in linear cooredinates."""

        self.draggable = False

        self.fig.clf()

        self.axes = self.fig.add_subplot(111)
        self.axes.set_xscale("linear")
        self.axes.set_yscale("linear")
        self.axes.set_xlabel("Z [$\AA$]")
        self.axes.set_ylabel("Correlation")
        self.axes.set_title("Real Space Correlations")
        self.fig.tight_layout()

        if self.data:
            data1, data3, data_idf = self.data
            self.axes.plot(data1.x, data1.y, label="1D Correlation")
            self.axes.plot(data3.x, data3.y, label="3D Correlation")
            self.axes.set_xlim(0, max(data1.x) / 4)
            self.legend = self.axes.legend()

        self.draw()

