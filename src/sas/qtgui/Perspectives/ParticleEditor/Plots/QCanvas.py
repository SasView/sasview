from __future__ import annotations

from typing import Optional

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from sas.qtgui.Perspectives.ParticleEditor.scattering import ScatteringOutput

import numpy as np
def spherical_form_factor(q, r):
    rq = r * q
    f = (np.sin(rq) - rq * np.cos(rq)) / (rq ** 3)
    return f * f

class QCanvas(FigureCanvas):
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

        self.axes.cla()

        if scattering_output.q_sampling_method.is_log:
            self.axes.loglog(q_values, i_values)

            self.axes.axvline(0.07)
            self.axes.axvline(0.13)
            self.axes.axvline(0.19)
            self.axes.axvline(0.25)
            self.axes.axvline(0.30)

            # For comparisons: TODO: REMOVE
            # self.axes.loglog(q_values, spherical_form_factor(q_values, 50))
        else:
            self.axes.semilogy(q_values, i_values)



        self.draw()