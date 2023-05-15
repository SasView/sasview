from __future__ import annotations

from typing import Optional

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from scattering import ScatteringOutput

class OutputCanvas(FigureCanvas):
    """ Plot window for output from scattering calculations"""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.parent = parent
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)

        FigureCanvas.__init__(self, self.fig)

        self._data: Optional[ScatteringOutput] = None

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, scattering_output: ScatteringOutput):

        self._data = scattering_output

        q_values = scattering_output.q_sampling_method()
        i_values = scattering_output.intensity_data

        print(len(q_values))

        self.axes.cla()

        if scattering_output.q_sampling_method.is_log:
            self.axes.loglog(q_values, i_values)
        else:
            self.axes.semilogy(q_values, i_values)

        self.draw()