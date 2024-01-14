from typing import Optional

import numpy as np


from matplotlib.axes import Axes

from sas.qtgui.Utilities.TypedInputVariables import FloatVariable, MutableInputVariableContainer

from sas.qtgui.Plotting.Plotter2D import Plotter2D
from sas.qtgui.Plotting.Slicing.Interactors.SlicerInteractor import SlicerInteractor



class ArcInteractor(SlicerInteractor):
    """
    Draw an arc on a data2D plot with a variable radius (centered at [0,0]).
    User interaction adjusts the parameter r

    param r: radius from (0,0) of the arc on a data2D plot
    param theta: angle from x-axis of the central point on the arc
    param phi: angle from the centre point on the arc to each of its edges
    """
    def __init__(self, base: Plotter2D, axes: Axes,
                 radius: MutableInputVariableContainer[float],
                 theta: MutableInputVariableContainer[float],
                 phi: MutableInputVariableContainer[float],
                 color='black', zorder: int=5):

        # Old default parameters: radius=1.0, theta=np.pi / 3, phi=np.pi / 8):

        super().__init__(base, axes, color=color)

        # Variables for the current mouse position
        self._mouse_x = 0
        self._mouse_y = 0

        self.scale = 10.0

        # Key variables for drawing the interactor element
        self.theta = theta
        self.phi = phi
        self.radius = radius

        # Calculate the marker coordinates and define the marker
        self.marker = self.axes.plot([], [], linestyle='',
                                     marker='s', markersize=10,
                                     color=self.color, alpha=0.6, pickradius=5,
                                     label='pick', zorder=zorder,
                                     visible=True)[0]
        # Define the arc
        self.arc = self.axes.plot([], [], linestyle='-', marker='', color=self.color)[0]

        # The number of points that make the arc line
        self.n_draw_points = 40


        self.connect_markers([self.marker, self.arc])
        self.update()

    def clear(self):
        """
        Clear this slicer and its markers
        """
        self.arc.remove()

    def update(self):
        """
        Draw the new arc on the graph.
        """

        theta = self.theta.value
        phi = self.phi.value
        radius = self.radius.value

        # Calculate the points on the arc, and draw them
        angle_offset = theta - phi
        angle_factor = np.asarray([2 * phi / (self.n_draw_points - 1) * i + angle_offset for i in range(self.n_draw_points)])

        x = radius * np.cos(angle_factor)
        y = radius * np.sin(angle_factor)

        self.arc.set_data(x.tolist(), y.tolist())

        # Calculate the new marker location, and draw that too
        marker_x = radius * np.cos(theta - 0.5 * phi)
        marker_y = radius * np.sin(theta - 0.5 * phi)
        self.marker.set(xdata=[marker_x], ydata=[marker_y])



    def move(self, x, y, ev):
        """
        Process move to a new position.
        """
        self._mouse_x = x
        self._mouse_y = y
        self.radius = np.sqrt(np.power(self._mouse_x, 2) + \
                              np.power(self._mouse_y, 2))
        self.has_move = True
        self.base.update()
        self.base.draw()

    def set_cursor(self, x, y):
        self.move(x, y, None)
        self.update()
