import numpy as np

from sas.qtgui.Plotting.Slicers.BaseInteractor import BaseInteractor


class ArcInteractor(BaseInteractor):
    """
    Draw an arc on a data2D plot with a variable radius (centered at [0,0]).
    User interaction adjusts the parameter r

    param r: radius from (0,0) of the arc on a data2D plot
    param theta: angle from x-axis of the central point on the arc
    param phi: angle from the centre point on the arc to each of its edges
    """
    def __init__(self, base, axes, color='black', zorder=5, r=1.0,
                 theta=np.pi / 3, phi=np.pi / 8):
        BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        self.color = color
        # Variables for the current mouse position
        self._mouse_x = r
        self._mouse_y = 0
        # Last known mouse position, for when the cursor moves off the plot
        self._save_x = r
        self._save_y = 0
        self.scale = 10.0
        # Key variables for drawing the interactor element
        self.theta = theta
        self.phi = phi
        self.radius = r
        # Calculate the marker coordinates and define the marker
        self.marker = self.axes.plot([], [], linestyle='',
                                     marker='s', markersize=10,
                                     color=self.color, alpha=0.6, pickradius=5,
                                     label='pick', zorder=zorder,
                                     visible=True)[0]
        # Define the arc
        self.arc = self.axes.plot([], [], linestyle='-', marker='', color=self.color)[0]
        # The number of points that make the arc line
        self.npts = 40
        # Flag to keep track of motion
        self.has_move = False
        self.connect_markers([self.marker, self.arc])
        self.update()

    def set_layer(self, n):
        """
        Allow adding plot to the same panel
        :param n: the number of layer
        """
        self.layernum = n
        self.update()

    def clear(self):
        """
        Clear this slicer and its markers
        """
        self.clear_markers()
        self.marker.remove()
        self.arc.remove()

    def update(self, theta=None, phi=None, r=None):
        """
        Draw the new roughness on the graph.
        :param theta: angle from x-axis of the central point on the arc
        :param phi: angle from the centre point on the arc to each of its edges
        :param r: radius from (0,0) of the arc on a data2D plot
        """
        if theta is not None:
            self.theta = theta
        if phi is not None:
            self.phi = phi
        if r is not None:
            self.radius = r
        # Calculate the points on the arc, and draw them
        angle_offset = self.theta - self.phi
        angle_factor = np.asarray([2 * self.phi / (self.npts - 1) * i + angle_offset for i in range(self.npts)])
        x = self.radius * np.cos(angle_factor)
        y = self.radius * np.sin(angle_factor)
        self.arc.set_data(x.tolist(), y.tolist())

        # Calculate the new marker location, and draw that too
        marker_x = self.radius * np.cos(self.theta - 0.5 * self.phi)
        marker_y = self.radius * np.sin(self.theta - 0.5 * self.phi)
        self.marker.set(xdata=[marker_x], ydata=[marker_y])

    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self._save_x = self._mouse_x
        self._save_y = self._mouse_y

    def moveend(self, ev):
        """
        After a dragging motion reset the flag self.has_move to False
        :param ev: event
        """
        self.has_move = False
        self.base.moveend(ev)

    def restore(self, ev):
        """
        Restore the roughness for this layer.
        """
        self._mouse_x = self._save_x
        self._mouse_y = self._save_y

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
