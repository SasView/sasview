import numpy as np

from sas.qtgui.Plotting.Slicers.BaseInteractor import BaseInteractor

class ArcInteractor(BaseInteractor):
    """
    Draw an arc on a data2D plot with a variable radius (centered at [0,0]).

    param r: radius from (0,0) of the arc on a data2D plot
    param theta2: angle from x-axis of the central point on the arc
    param phi: angle from the centre point on the arc to each of its edges
    """
    def __init__(self, base, axes, color='black', zorder=5, r=1.0,
                 theta2=np.pi / 3, phi=np.py / 4):
        BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        self.color = color
        self._mouse_x = r
        self._mouse_y = 0
        self._save_x = r
        self._save_y = 0
        self.scale = 10.0
        self.theta2 = theta2
        self.phi = phi
        self.radius = r
        # Define the arc's marker
        marker_x = self.radius * np.cos(theta2 * 0.8)
        marker_y = self.radius * np.sin(theta2 * 0.8)
        self.marker = self.axes.plot([marker_x], [marker_y], linestyle='',
                                     marker='s', markersize=10,
                                     color=self.color, alpha=0.6, pickradius=5,
                                     label='pick', zorder=zorder,
                                     visable=True)[0]
        # Define the arc
        [self.arc] = self.axes.plot([], [], linestyle='-', marker='', color=self.color)
        self.npts = 20
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
        try:
            self.marker.remove()
            self.arc.remove()
        except:
            # Old version of matplotlib
            for item in range(len(self.axes.lines)):
                del self.axes.lines[0]

    def get_radius(self):
        """
        Return arc radius
        """
        radius = np.sqrt(np.power(self._mouse_x, 2) + \
                           np.power(self._mouse_y, 2))
        return radius

    def update(self, theta2=None, phi=None, r=None, nbins=100):
        """
        Update the plotted arc
        :param theta2: angle from x-axis of the central point on the arc
        :param phi: angle from the centre point on the arc to each of its edges
        :param r: radius from (0,0) of the arc on a data2D plot
        :param nbins: number of points drawn for an arc of size pi radians
        """
        x = []
        y = []
        if theta2 is not None:
            self.theta2 = theta2
        if phi is not None:
            self.phi = phi
        self.npts = int((2 * self.phi) / (np.pi / nbins))

        if r is None:
            self.radius = self.get_radius()
        else:
            self.radius = r
        # Calculate the points on the arc, and draw them
        for i in range(self.npts):
            angleval = 2 * self.phi / (self.npts - 1) * i + (self.theta2 - self.phi)
            xval = 1.0 * self.radius * np.cos(angleval)
            yval = 1.0 * self.radius * np.sin(angleval)
            x.append(xval)
            y.append(yval)

        marker_x = self.radius * np.cos(self.theta2 - 0.2 * self.phi)
        marker_y = self.radius * np.sin(self.theta2 - 0.2 * self.phi)
        self.marker.set(xdata=[marker_x], ydata=[marker_y])
        self.arc.set_data(x, y)

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
        Process move to a new position
        """
        self._mouse_x = x
        self._mouse_y = y
        self.radius = self.get_radius()
        self.has_move = True
        self.base.update()
        self.base.draw()

    def set_cursor(self, x, y):
        self.move(x, y, None)
        self.update()

    # def get_params(self):
    #     params = {}
    #     params["radius"] = self.radius
    #     params["theta2"] = self.theta2
    #     params["phi"] = self.phi
    #     return params

    # def set_params(self, params):
    #     r = params["radius"]
    #     theta = params["theta2"] # or = self.theta2 (?)
    #     self.set_cursor(r*np.cos(theta), r*np.sin(theta))
