"""
Slider for modifying the Q range on a fit
"""
import logging
import numpy as np

from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.Slicers.BaseInteractor import BaseInteractor

logger = logging.getLogger(__name__)


class QRangeSlider(BaseInteractor):
    """
    Draw a single vertical line that can be modified
    """
    def __init__(self, base, axes, color='black', zorder=5, data=None):
        """
        """
        BaseInteractor.__init__(self, base, axes, color=color)
        assert isinstance(data, Data1D)
        self.base = base
        self.markers = []
        self.axes = axes
        self.data = data
        self.connect = self.base.connect
        self.connect = self.base.connect
        self.x_min = np.fabs(min(self.data.x))
        self.y_marker_min = self.data.y[np.where(self.data.x == self.x_min)[0][0]]
        self.x_max = np.fabs(max(self.data.x))
        self.y_marker_max = self.data.y[np.where(self.data.x == self.x_max)[0][-1]]
        self.line_min = LineInteractor(self, axes, zorder=zorder, x=self.x_min, y=self.y_marker_min,
                                       validator=self.data.q_range_slider_low_validator)
        self.line_max = LineInteractor(self, axes, zorder=zorder, x=self.x_max, y=self.y_marker_max,
                                       validator=self.data.q_range_slider_high_validator)
        self.has_move = True
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

    def update(self):
        """
        Draw the new roughness on the graph.

        :param x: x-coordinates to reset current class x
        :param y: y-coordinates to reset current class y

        """
        self.line_min.update()
        self.line_max.update()
        self.base.update()

    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.save_x = self.x
        self.save_y = self.y_marker

    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self.x = self.save_x
        self.y_marker = self.save_y

    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        self.has_move = True
        self.x = x
        self.update()

    def clear_markers(self):
        """
        Should be no way to clear the markers
        """
        pass

    def draw(self):
        """
        """
        self.base.draw()


class LineInteractor(BaseInteractor):
    """
    Draw a single vertical line that can be modified
    """
    def __init__(self, base, axes, color='black', zorder=5, x=0.5, y=0.5, validator=None):
        """
        """
        BaseInteractor.__init__(self, base, axes, color=color)
        self.base = base
        self.markers = []
        self.axes = axes
        self.x = x
        self.save_x = self.x
        self.y_marker = y
        self.save_y = self.y_marker
        # Inner circle marker
        self.inner_marker = self.axes.plot([self.x], [self.y_marker], linestyle='', marker='o', markersize=4,
                                           color=self.color, alpha=0.6, pickradius=5, label=None, zorder=zorder,
                                           visible=True)[0]
        self.line = self.axes.axvline(self.x, linestyle='-', color=self.color, marker='', pickradius=5,
                                      label=None, zorder=zorder, visible=True)
        self.has_move = True
        self.validator = validator
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
            self.y_marker = y
        # Draw lines and markers
        if self.validator(self.x):
            self.inner_marker.set_xdata([self.x])
            self.inner_marker.set_ydata([self.y_marker])
            self.line.set_xdata([self.x])

    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.save_x = self.x
        self.save_y = self.y_marker

    def restore(self):
        """
        Restore the roughness for this layer.
        """
        self.x = self.save_x
        self.y_marker = self.save_y

    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        self.has_move = True
        self.x = x
        self.y_marker = self.base.data.y[(np.abs(self.base.data.x - self.x)).argmin()]
        self.update()

    def clear_markers(self):
        """
        Should be no way to clear the markers
        """
        pass
