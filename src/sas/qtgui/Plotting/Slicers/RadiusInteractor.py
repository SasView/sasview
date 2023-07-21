import numpy as np

from sas.qtgui.Plotting.Slicers.BaseInteractor import BaseInteractor


class RadiusInteractor(BaseInteractor):
    """
     Draw a radial line (centered at [0,0]) at an angle theta from the x-axis
     on a data2D plot from r1 to r2 defined by two arcs (arc1 and arc2). Used
     for example to define a wedge area on the plot.

     param theta: angle of the radial line from the x-axis
     param arc1: inner arc of radius r1 used to define the starting point of
                the radial line
     param arc2: outer arc of radius r2 used to define the ending point of
                the radial line
    """
    def __init__(self, base, axes, color='black', zorder=5, arc1=None,
                 arc2=None, theta2=np.pi / 8, phi=np.pi / 4):
        """
        """
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
                                       zorder=zorder, visable=True)[0]
        self.r_marker = self.axes.plot([(r_x1+r_x2)/2], [(r_y1+r_y2)/2],
                                       linestyle='', marker='s', markersize=10,
                                       color=self.color, alpha=0.6,
                                       pickradius=5, label='pick',
                                       zorder=zorder, visable=True)[0]
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
        """
        self.layernum = n
        self.update()

    def clear(self):
        """
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

    # def get_angle(self):
    #     """
    #     """
    #     return self.theta

    def update(self, theta2=None, phi=None):
        """
        Draw the new roughness on the graph.
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
        # May also need a save_theta2 variable

    def moveend(self, ev):
        """
        """
        self.has_move = False
        self.base.moveend(ev)

    def restore(self, ev):
        """
        Restore the roughness for this layer.
        """
        self.phi = self.save_phi
        # May also need a save_theta2 variable

    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        theta = np.arctan2(y, x)
        self.phi = np.fabs(theta - self.theta2)
        self.has_move = True
        self.base.update()
        self.base.draw()

    def set_cursor(self, x, y):
        """
        """
        self.move(x, y, None)
        self.update()

    # def get_params(self):
    #     """
    #     Store a copy of values of parameters of the slicer into a dictionary.
    #     :return params: the dictionary created
    #     """
    #     params = {}
    #     params["radius1"] = self.r1
    #     params["radius2"] = self.r2
    #     params["theta"] = self.theta2
    #     params["phi"] = self.phi
    #     return params

    # def set_params(self, params):
    #     """
    #     Receive a dictionary and reset the slicer with values contained
    #     in the values of the dictionary.
    #
    #     :param params: a dictionary containing name of slicer parameters and
    #         values the user assigned to the slicer.
    #     """
    #     r1 = params["radius1"]
    #     r2 = params["radius2"]
    #     theta = params["theta"]
    #     phi = params["phi"]
    #     self.set_cursor(x1, x2, theta)

