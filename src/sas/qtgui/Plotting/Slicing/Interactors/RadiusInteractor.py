import numpy as np

from PySide6.QtCore import QEvent

from matplotlib.axes import Axes

from sas.qtgui.Plotting.BaseInteractor import BaseInteractor
from sas.qtgui.Plotting.Plotter2D import Plotter2D

from sas.qtgui.Utilities.TypedInputVariables import MutableInputVariableContainer

class RadiusInteractor(BaseInteractor[Plotter2D]):
    """
    Draw a pair of lines radiating from a center at [0,0], between radius
    values r1 and r2 with and average angle from the x-axis of theta, and an
    angular diaplacement of phi either side of this average. Used for example
    to define the left and right edges of the wedge area on a plot, see
    WedgeInteractor. User interaction adjusts the parameter phi.

    :param r1: radius of the inner end of the radial lines
    :param r2: radius of the outer end of the radial lines
    :param theta: average angle of the lines from the x-axis
    :param phi: angular displacement of the lines either side of theta
    """
    def __init__(self, base: Plotter2D, axes: Axes,
                 r1: MutableInputVariableContainer[float],
                 r2: MutableInputVariableContainer[float],
                 theta: MutableInputVariableContainer[float],
                 phi: MutableInputVariableContainer[float],
                 color='black', zorder=5):


        # Old defaults: r1 = 1.0, r2 = 2.0, theta = np.pi / 3, phi = np.pi / 8,

        super().__init__(base, axes, color=color)

        # Key variables used when drawing the interactor element
        self.r1 = r1
        self.r2 = r2
        self.theta = theta
        self.phi = phi

        # Last known phi value for when the cursor moves off the plot
        self.save_phi = phi.value


        # Variables for the left and right radial lines
        l_x1 = self.r1.value * np.cos(self.theta.value + self.phi.value)
        l_y1 = self.r1.value * np.sin(self.theta.value + self.phi.value)
        l_x2 = self.r2.value * np.cos(self.theta.value + self.phi.value)
        l_y2 = self.r2.value * np.sin(self.theta.value + self.phi.value)
        r_x1 = self.r1.value * np.cos(self.theta.value - self.phi.value)
        r_y1 = self.r1.value * np.sin(self.theta.value - self.phi.value)
        r_x2 = self.r2.value * np.cos(self.theta.value - self.phi.value)
        r_y2 = self.r2.value * np.sin(self.theta.value - self.phi.value)

        # Define the left and right markers
        self.l_marker = self.axes.plot([(l_x1+l_x2)/2], [(l_y1+l_y2)/2],
                                       linestyle='', marker='s', markersize=10,
                                       color=self.color, alpha=0.6,
                                       pickradius=5, label='pick',
                                       zorder=zorder, visible=True)[0]

        self.r_marker = self.axes.plot([(r_x1+r_x2)/2], [(r_y1+r_y2)/2],
                                       linestyle='', marker='s', markersize=10,
                                       color=self.color, alpha=0.6,
                                       pickradius=5, label='pick',
                                       zorder=zorder, visible=True)[0]

        # Define the left and right lines
        self.l_line = self.axes.plot([l_x1, l_x2], [l_y1, l_y2],
                                     linestyle='-', marker='',
                                     color=self.color, visible=True)[0]
        self.r_line = self.axes.plot([r_x1, r_x2], [r_y1, r_y2],
                                     linestyle='-', marker='',
                                     color=self.color, visible=True)[0]

        # Flag to keep track of motion

        self.connect_markers([self.l_marker, self.l_line,
                              self.r_marker, self.r_line])
        self.update()

    def clear(self):
        """
        Clear this slicer and its markers
        """
        self.clear_markers()
        self.l_marker.remove()
        self.l_line.remove()
        self.r_marker.remove()
        self.r_line.remove()

    def update(self):
        """
        Draw the new roughness on the graph.
        :param r1: radius of the inner end of the radial lines
        :param r2: radius of the outer end of the radial lines
        :param theta: average angle of the lines from the x-axis
        :param phi: angular displacement of the lines either side of theta
        """

        # Variables for the left and right radial lines
        l_x1 = self.r1.value * np.cos(self.theta.value + self.phi.value)
        l_y1 = self.r1.value * np.sin(self.theta.value + self.phi.value)
        l_x2 = self.r2.value * np.cos(self.theta.value + self.phi.value)
        l_y2 = self.r2.value * np.sin(self.theta.value + self.phi.value)
        r_x1 = self.r1.value * np.cos(self.theta.value - self.phi.value)
        r_y1 = self.r1.value * np.sin(self.theta.value - self.phi.value)
        r_x2 = self.r2.value * np.cos(self.theta.value - self.phi.value)
        r_y2 = self.r2.value * np.sin(self.theta.value - self.phi.value)

        # Draw the updated markers and lines
        self.l_marker.set(xdata=[(l_x1+l_x2)/2], ydata=[(l_y1+l_y2)/2])
        self.l_line.set(xdata=[l_x1, l_x2], ydata=[l_y1, l_y2])
        self.r_marker.set(xdata=[(r_x1+r_x2)/2], ydata=[(r_y1+r_y2)/2])
        self.r_line.set(xdata=[r_x1, r_x2], ydata=[r_y1, r_y2])

    def save(self, ev: QEvent):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """

        super().save(ev)

        self.save_phi = self.phi

    def restore(self, ev: QEvent):
        """
        Restore the roughness for this layer.
        """
        super().restore(ev)

        self.phi = self.save_phi

    def move(self, x, y, ev):
        """
        Process move to a new position.
        """
        angle = np.arctan2(y, x)
        phi = np.fabs(angle - self.theta)
        if phi > np.pi:
            phi = 2 * np.pi - phi
        self.phi = phi
        self.has_move = True
        self.base.update()
        self.base.draw()

    def set_cursor(self, x, y):
        self.move(x, y, None)
        self.update()

