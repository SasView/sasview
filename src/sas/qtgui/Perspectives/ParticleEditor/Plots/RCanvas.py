from __future__ import annotations

from typing import Optional

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from sas.qtgui.Perspectives.ParticleEditor.scattering import ScatteringOutput


class RCanvas(FigureCanvas):
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

        self.axes.cla()


        self.axes.plot(scattering_output.r_values, scattering_output.realspace_intensity)

        self.draw()