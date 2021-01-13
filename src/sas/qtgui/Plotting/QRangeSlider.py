"""
Slider for modifying the Q range on a fit
"""
import numpy as np

from sas.qtgui.Plotting.Slicers.BaseInteractor import BaseInteractor


# TODO: This should connected to a widget
class QRangeSlider(BaseInteractor):
    """
    Draw a single vertical line that can be modified
    """
    def __init__(self, base, axes, color='black', zorder=5, x=0.5, y_min=0.0, y_max=1.0):
        """
        """
        BaseInteractor.__init__(self, base, axes, color=color)
        self.markers = []
        self.axes = axes
        self.x = np.fabs(x)
        self.save_x = self.x
        self.y_max = np.fabs(y_max)
        self.y_min = np.fabs(y_min)
        self.save_y = np.average([self.y_min, self.y_max])
        # Inner circle marker
        self.inner_marker = self.axes.plot([self.x], [0], linestyle='',
                                           marker='s', markersize=10,
                                           color=self.color, alpha=0.6,
                                           pickradius=5, label="pick",
                                           zorder=zorder, visible=True)[0]
        self.line = self.axes.plot([self.x, self.x],
                                         [self.y_min, self.y_max],
                                         linestyle='-', marker='',
                                         color=self.color, visible=True)[0]
        self.has_move = False
        self.connect_markers([self.line, self.inner_marker])
        self.update()

    def validate(self, param_name, param_value):
        """
        Validate input from user
        """
        return True

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
        self.inner_marker.remove()
        self.line.remove()

    def update(self, x=None, y=None):
        """
        Draw the new roughness on the graph.

        :param x: x-coordinates to reset current class x
        :param y: y-coordinates to reset current class y

        """
        # Reset x, y -coordinates if given as parameters
        if x is not None:
            self.x = np.sign(self.x) * np.fabs(x)
        if y is not None:
            self.y = np.sign(self.y) * np.fabs(y)
        # Draw lines and markers
        self.inner_marker.set(xdata=[self.x], ydata=[self.save_y])
        self.line.set(xdata=[-self.x, -self.x], ydata=[self.y_min, self.y_max])

    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.save_x = self.x
        self.save_y = self.y

    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self.x = self.save_x
        self.y = self.save_y

    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        self.has_move = True
        self.x = x
        self.base.base.update()

    def clear_markers(self):
        """
        Should be no way to clear the markers
        """
        pass

    def connect_markers(self, markers):
        """
        No connections for now
        """
        pass
