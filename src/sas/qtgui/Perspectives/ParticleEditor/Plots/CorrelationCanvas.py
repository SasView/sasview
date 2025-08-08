from __future__ import annotations

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from sas.qtgui.Perspectives.ParticleEditor.old_calculations import ScatteringOutput


class CorrelationCanvas(FigureCanvas):
    """ Plot window for output from scattering calculations"""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.parent = parent
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)

        FigureCanvas.__init__(self, self.fig)

        self._data: ScatteringOutput | None = None

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, scattering_output: ScatteringOutput):

        self._data = scattering_output

        self.axes.cla()

        if self._data.q_space is not None:
            if self._data.q_space.correlation_data is not None:

                plot_data = scattering_output.q_space.correlation_data

                r = plot_data.abscissa
                rho = plot_data.ordinate

                self.axes.plot(r, rho)

                import numpy as np

                R = 50

                f1 = lambda r: 1 - (3 / 4) * (r / R) + (1 / 16) * (r / R) ** 3
                def f(x):
                    out = np.zeros_like(x)
                    x_in = x[x <= 2 * R]
                    out[x <= 2 * R] = f1(x_in)
                    return out

                self.axes.plot(r, f(r)/6)


        self.draw()
