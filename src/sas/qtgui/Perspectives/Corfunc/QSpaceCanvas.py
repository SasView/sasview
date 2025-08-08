from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from matplotlib.lines import Line2D

if TYPE_CHECKING:
    from sas.qtgui.Perspectives.Corfunc.CorfuncPerspective import CorfuncWindow

from sas.qtgui.Perspectives.Corfunc.CorfuncCanvas import CorfuncCanvas
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.sascalc.corfunc.calculation_data import ExtrapolationInteractionState


class QSpaceCanvas(CorfuncCanvas):
    """ Canvas for displaying input data and extrapolation parameters"""

    def __init__(self, corfunc_window: CorfuncWindow, width=5, height=4, dpi=100):
        super().__init__(corfunc_window, width, height, dpi)


        self.extrap: Data1D | None = None

        # Vertical lines
        self.line1: Line2D | None = None
        self.line2: Line2D | None = None
        self.line3: Line2D | None = None
        self.ghost_line: Line2D | None = None # Ghostly line for showing during interactions

    @property
    def interactive_lines(self):
        return self.line1, self.line2, self.line3

    def update_lines(self, parameters: ExtrapolationInteractionState):
        """ Update the plots vertical lines based on the position of the slider and/or text box values"""
        lines = self.interactive_lines


        # Set all lines black, then if there is an interactive one, make it grey
        for line, position in zip(lines, [
                                  parameters.extrapolation_parameters.point_1,
                                  parameters.extrapolation_parameters.point_2,
                                  parameters.extrapolation_parameters.point_3,
                                  parameters.extrapolation_parameters.data_q_max]):

            line.set_xdata(np.array([position]))
            line.set_color('k')

        if parameters.working_line_id is not None:
            lines[parameters.working_line_id].set_color([0.4]*3) # grey

        if parameters.dragging_line_position is None:
            self.ghost_line.set_alpha(0)
        else:
            self.ghost_line.set_alpha(0.5)
            self.ghost_line.set_xdata(np.array([parameters.dragging_line_position]))

        self.draw()



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
        self.axes.set_xlabel(r"Q [$\AA^{-1}$]")
        self.axes.set_ylabel("I(Q) [cm$^{-1}$]")
        self.axes.set_title("Scattering data")
        self.fig.tight_layout()

        if self.data is not None:

            extrapolation_params = self.corfunc_windows.extrapolation_paramameters

            self.axes.errorbar(self.data[0].x,
                               self.data[0].y,
                               yerr=self.data[0].dy,
                               label="Experimental Data",
                               marker='o',
                               linestyle='',
                               markersize=3,
                               capsize=2)

            self.line1 = self.axes.axvline(extrapolation_params.point_1, color='k')
            self.line2 = self.axes.axvline(extrapolation_params.point_2, color='k')
            self.line3 = self.axes.axvline(extrapolation_params.point_3, color='k')
            self.ghost_line = self.axes.axvline(0.1, color='k', alpha=0)
            self.axes.set_xlim(extrapolation_params.data_q_min / 2,
                               extrapolation_params.data_q_max* 1.5 - 0.5 * extrapolation_params.data_q_min)
            self.axes.set_ylim(min(self.data[0].y) / 2,
                               max(self.data[0].y) * 1.5 - 0.5 * min(self.data[0].y))

        if self.extrap is not None:
            self.axes.plot(self.extrap.x, self.extrap.y, label="Extrapolation")

        if self.data is not None or self.extrap is not None:
            self.legend = self.axes.legend()

        self.draw()

