from __future__ import annotations

import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from sas.qtgui.Perspectives.ParticleEditor.datamodel.calculation import ScatteringOutput


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

        self._data: ScatteringOutput | None = None

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, scattering_output: ScatteringOutput):

        # print("Setting QPlot Data")

        self._data = scattering_output
        self.axes.cla()

        if self._data.q_space is not None:
            # print(self._data.q_space)
            plot_data = self._data.q_space

            q_sample = plot_data.abscissa
            q_values = q_sample()
            i_values = plot_data.ordinate

            if q_sample.is_log:
                self.axes.loglog(q_values, i_values)
                #
                # self.axes.axvline(0.07)
                # self.axes.axvline(0.13)
                # self.axes.axvline(0.19)
                # self.axes.axvline(0.25)
                # self.axes.axvline(0.30)

                # For comparisons: TODO: REMOVE
                # thing = spherical_form_factor(q_values, 50)
                # self.axes.loglog(q_values, thing*np.max(i_values)/np.max(thing))
                # It works, NICE!
            else:
                self.axes.semilogy(q_values, i_values)



        self.draw()
