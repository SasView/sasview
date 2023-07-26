import numpy as np

from sas.qtgui.Plotting.Slicers.BaseInteractor import BaseInteractor

class RadiusInteractor(BaseInteractor):
    """
    Draw a pair of lines radiating from a center at [0,0], between radius
    values r1 and r2 with and average angle from the x-axis of theta2, and an
    angular diaplacement of phi either side of this average. Used for example
    to to define the left and right edges of the a wedge area on a plot, see
    WedgeInteractor.

    :param r1: radius of the inner end of the radial lines
    :param r2: radius of the outer end of the radial lines
    :param theta2: average angle of the lines from the x-axis
    :param phi: angular displacement of the lines either side of theta2
    """
    def __init__(self, base, axes, color='black', zorder=5, arc1=None,
                 arc2=None, theta2=np.pi / 3, phi=np.pi / 8):
        BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        self.color = color
        self.r1 = arc1.get_radius()
        self.r2 = arc2.get_radius()
        self.theta2 = theta2
        # self.save_theta2 = theta2
        self.phi = phi
        self.save_phi = phi
        self.arc1 = arc1
        self.arc2 = arc2
        # Variables for the left and right radial lines
        l_x1 = self.r1 * np.cos(self.theta2 + self.phi)
        l_y1 = self.r1 * np.sin(self.theta2 + self.phi)
        l_x2 = self.r2 * np.cos(self.theta2 + self.phi)
        l_y2 = self.r2 * np.sin(self.theta2 + self.phi)
        r_x1 = self.r1 * np.cos(self.theta2 - self.phi)
        r_y1 = self.r1 * np.sin(self.theta2 - self.phi)
        r_x2 = self.r2 * np.cos(self.theta2 - self.phi)
        r_y2 = self.r2 * np.sin(self.theta2 - self.phi)
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
        # # Flag to differentiate the left side's motion from the right's
        # self.left_moving = False
        # Flag to keep track of motion
        self.has_move = False
        self.connect_markers([self.l_marker, self.l_line,
                              self.r_marker, self.r_line])
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
            self.l_marker.remove()
            self.l_line.remove()
            self.r_marker.remove()
            self.r_line.remove()
        except:
            # Old version of matplotlib
            for item in range(len(self.axes.lines)):
                del self.axes.lines[0]

    def update(self, theta2=None, phi=None):
        """
        Draw the new roughness on the graph.
        :param r1: radius of the inner end of the radial lines
        :param r2: radius of the outer end of the radial lines
        :param theta2: average angle of the lines from the x-axis
        :param phi: angular displacement of the lines either side of theta2
        """
        # TODO - try out an 'if self.arc1.has_move:' etc
        self.r1 = self.arc1.get_radius()
        self.r2 = self.arc2.get_radius()
        if theta2 is not None:
            self.theta2 = theta2
        if phi is not None:
            self.phi = phi
        l_x1 = self.r1 * np.cos(self.theta2 + self.phi)
        l_y1 = self.r1 * np.sin(self.theta2 + self.phi)
        l_x2 = self.r2 * np.cos(self.theta2 + self.phi)
        l_y2 = self.r2 * np.sin(self.theta2 + self.phi)
        r_x1 = self.r1 * np.cos(self.theta2 - self.phi)
        r_y1 = self.r1 * np.sin(self.theta2 - self.phi)
        r_x2 = self.r2 * np.cos(self.theta2 - self.phi)
        r_y2 = self.r2 * np.sin(self.theta2 - self.phi)
        self.l_marker.set(xdata=[(l_x1+l_x2)/2], ydata=[(l_y1+l_y2)/2])
        self.l_line.set(xdata=[l_x1, l_x2], ydata=[l_y1, l_y2])
        self.r_marker.set(xdata=[(r_x1+r_x2)/2], ydata=[(r_y1+r_y2)/2])
        self.r_line.set(xdata=[r_x1, r_x2], ydata=[r_y1, r_y2])

    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.save_phi = self.phi
        # self.save_theta2 = self.theta2

    def moveend(self, ev):
        """
        Called when any dragging motion ends.
        Redraw the plot with new parameters and set self.has_move to False.
        """
        self.has_move = False
        self.base.moveend(ev)

    def restore(self, ev):
        """
        Restore the roughness for this layer.
        """
        self.phi = self.save_phi
        # self.theta2 = self.save_theta2

    def move(self, x, y, ev):
        """
        Process move to a new position.
        """
        theta = np.arctan2(y, x)
        self.phi = np.fabs(theta - self.theta2)
        self.has_move = True
        self.base.update()
        self.base.draw()

    def set_cursor(self, x, y):
        self.move(x, y, None)
        self.update()

