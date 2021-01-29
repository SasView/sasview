"""
Double slider interactor for setting the Q range for a fit or function
"""
import numpy as np

from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.Slicers.BaseInteractor import BaseInteractor


class QRangeSlider(BaseInteractor):
    """
    Draw a pair of draggable vertical lines. Each line can be linked to a GUI input.
    The GUI input should update the lines and vice-versa.
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
        self.x_min = np.fabs(min(self.data.x))
        self.y_marker_min = self.data.y[np.where(self.data.x == self.x_min)[0][0]]
        self.x_max = np.fabs(max(self.data.x))
        self.y_marker_max = self.data.y[np.where(self.data.x == self.x_max)[0][-1]]
        self.updateOnMove = data.slider_update_on_move
        self.line_min = LineInteractor(self, axes, zorder=zorder, x=self.x_min, y=self.y_marker_min,
                                       input=self.data.slider_low_q_input, setter=self.data.slider_low_q_setter,
                                       getter=self.data.slider_low_q_getter)
        self.line_max = LineInteractor(self, axes, zorder=zorder, x=self.x_max, y=self.y_marker_max,
                                       input=self.data.slider_high_q_input, setter=self.data.slider_high_q_setter,
                                       getter=self.data.slider_high_q_getter)
        self.has_move = True
        ######################################################
        # Reset all slider values in data so save/load does not choke on them
        # Remove once slider definition moved out of PlotterData
        self.data.slider_low_q_setter = None
        self.data.slider_high_q_setter = None
        self.data.slider_low_q_input = None
        self.data.slider_high_q_input = None
        self.data.slider_update_on_move = False
        self.data.slider_low_q_getter = None
        self.data.slider_high_q_getter = None
        ######################################################
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

    def update(self, x=None, y=None):
        """
        Draw the new roughness on the graph.
        """
        self.line_min.update(x, y)
        self.line_max.update(x, y)
        self.base.update()

    def save(self, ev):
        """
        Remember the roughness for this layer and the next so that we
        can restore on Esc.
        """
        self.line_min.save(ev)
        self.line_max.save(ev)

    def restore(self, ev):
        """
        Restore the roughness for this layer.
        """
        self.line_max.restore(ev)
        self.line_min.restore(ev)

    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        pass

    def clear_markers(self):
        """
        Clear each of the lines individually
        """
        self.line_min.clear()
        self.line_max.clear()

    def draw(self):
        """
        """
        self.base.draw()


class LineInteractor(BaseInteractor):
    """
    Draw a single vertical line that can be dragged on a plot
    """
    def __init__(self, base, axes, color='black', zorder=5, x=0.5, y=0.5, input=None, setter=None, getter=None):
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
        # Map GUI input to x value so slider and input update each other
        self.input = input
        if self.input:
            self.input.textChanged.connect(self.inputChanged)
        self.setter = setter if callable(setter) else None
        self.getter = getter if callable(getter) else None
        self.connect_markers([self.line, self.inner_marker])
        self.update()

    def validate(self, param_name, param_value):
        """
        Validate input from user - Should never fail
        """
        return True

    def clear(self):
        self.clear_markers()
        self.remove()

    def remove(self):
        """
        Clear this slicer and its markers
        """
        self.inner_marker.remove()
        self.line.remove()

    def _set_q(self, value):
        """
        Call the q setter callback method if it exists
        """
        self.setter(value)

    def _get_q(self):
        """
        Get the q value, inferring the method to get the value
        """
        if self.getter:
            # Separate callback method to get Q value
            self.x = float(self.getter())
        elif hasattr(self.input, 'text'):
            # Line edit box
            self.x = float(self.input.text())
        elif hasattr(self.input, 'getText'):
            # Text box
            self.x = float(self.input.getText())

    def inputChanged(self):
        """ Track the input linked to the x value for this slider and update as needed """
        self._get_q()
        self.y_marker = self.base.data.y[(np.abs(self.base.data.x - self.x)).argmin()]
        self.update()

    def update(self, x=None, y=None):
        """
        Update the line position on the graph.
        """
        # Reset x, y -coordinates if given as parameters
        if x is not None:
            self.x = np.sign(self.x) * np.fabs(x)
        if y is not None:
            self.y_marker = y
        # Draw lines and markers
        self.inner_marker.set_xdata([self.x])
        self.inner_marker.set_ydata([self.y_marker])
        self.line.set_xdata([self.x])

    def save(self, ev):
        """
        Remember the position for this line so that we can restore on Esc.
        """
        self.save_x = self.x
        self.save_y = self.y_marker

    def restore(self, ev):
        """
        Restore the position for this line
        """
        self.x = self.save_x
        self.y_marker = self.save_y

    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        self.has_move = True
        self.x = x
        if self.base.updateOnMove:
            if self.setter:
                self._set_q(self.x)
            else:
                self.input.setText(f"{self.x:.3}")
        self.y_marker = self.base.data.y[(np.abs(self.base.data.x - self.x)).argmin()]
        self.update()

    def onRelease(self, ev):
        """
        Update the line position when the mouse button is released
        """
        if self.setter:
            self._set_q(self.x)
        else:
            self.input.setText(f"{self.x:.3}")
        self.update()
        self.moveend(ev)
        return True

    def clear_markers(self):
        """
        Disconnect the input and clear the callbacks
        """
        if self.input:
            self.input.textChanged.disconnect(self.inputChanged)
        self.setter = None
        self.getter = None
        self.input = None
