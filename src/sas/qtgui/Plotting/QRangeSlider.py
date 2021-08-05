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
        assert isinstance(data, Data1D)
        BaseInteractor.__init__(self, base, axes, color=color)
        self.base = base
        self.markers = []
        self.axes = axes
        self.data = data
        self.is_visible = False
        self.connect = self.base.connect
        self.x_min = np.fabs(min(self.data.x))
        self.y_marker_min = self.data.y[np.where(self.data.x == self.x_min)[0][0]]
        self.x_max = np.fabs(max(self.data.x))
        self.y_marker_max = self.data.y[np.where(self.data.x == self.x_max)[0][-1]]
        self.updateOnMove = data.slider_update_on_move
        self.line_min = LineInteractor(self, axes, zorder=zorder, x=self.x_min, y=self.y_marker_min,
                                       input=data.slider_low_q_input, setter=data.slider_low_q_setter,
                                       getter=data.slider_low_q_getter, perspective=data.slider_perspective_name,
                                       tab=data.slider_tab_name)
        self.line_max = LineInteractor(self, axes, zorder=zorder, x=self.x_max, y=self.y_marker_max,
                                       input=data.slider_high_q_input, setter=data.slider_high_q_setter,
                                       getter=data.slider_high_q_getter, perspective=data.slider_perspective_name,
                                       tab=data.slider_tab_name)
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

    def show(self):
        self.line_max.draw()
        self.line_min.draw()
        self.update()

    def remove(self):
        self.line_max.remove()
        self.line_min.remove()
        self.is_visible = False

    def update(self, x=None, y=None):
        """
        Draw the new roughness on the graph.
        """
        self.line_min.update(x, y, draw=True)
        self.line_max.update(x, y, draw=True)
        self.base.update()
        self.is_visible = True

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

    def toggle(self):
        if self.is_visible:
            self.remove()
        else:
            self.show()

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
    def __init__(self, base, axes, color='black', zorder=5, x=0.5, y=0.5,
                 input=None, setter=None, getter=None, perspective=None, tab=None):
        """
        """
        BaseInteractor.__init__(self, base, axes, color=color)
        self.base = base
        self._input = None
        self._setter = None
        self._getter = None
        self.markers = []
        self.axes = axes
        self.x = x
        self.save_x = self.x
        self.y_marker = y
        self.save_y = self.y_marker
        self.draw(zorder)
        self.has_move = True
        if not perspective:
            self.perspective = None
            return
        # Map GUI input to x value so slider and input update each other
        self.perspective = base.base.parent.manager.parent.loadedPerspectives.get(perspective, None)
        if tab and hasattr(self.perspective, 'getTabByName'):
            self.perspective = self.perspective.getTabByName(tab)
        if self.perspective:
            self.input = self._get_input_or_callback(input)
            self.setter = self._get_input_or_callback(setter)
            self.getter = self._get_input_or_callback(getter)
        self.connect_markers([self.line, self.inner_marker])
        self.update(draw=True)

    @property
    def input(self):
        return self._input

    @input.setter
    def input(self, input):
        self._input = input
        if self._input:
            self._input.textChanged.connect(self.inputChanged)

    @property
    def setter(self):
        return self._setter

    @setter.setter
    def setter(self, setter):
        self._setter = setter if callable(setter) else None

    @property
    def getter(self):
        return self._getter

    @getter.setter
    def getter(self, getter):
        self._getter = getter if callable(getter) else None

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
        if self.inner_marker:
            self.inner_marker.remove()
        if self.line:
            self.line.remove()

    def draw(self, zorder=5):
        # Inner circle marker
        self.inner_marker = self.axes.plot([self.x], [self.y_marker], linestyle='', marker='o', markersize=4,
                                           color=self.color, alpha=0.6, pickradius=5, label=None, zorder=zorder,
                                           visible=True)[0]
        self.line = self.axes.axvline(self.x, linestyle='-', color=self.color, marker='', pickradius=5,
                                      label=None, zorder=zorder, visible=True)

    def _get_input_or_callback(self, connection_list=None):
        """Returns an input or callback method based on a list of inputs/commands"""
        connection = None
        if isinstance(connection_list, list):
            connection = self.perspective
            for item in connection_list:
                try:
                    connection = getattr(connection, item)
                except Exception:
                    return None
        return connection

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
        self.update(draw=True)

    def update(self, x=None, y=None, draw=False):
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
        if draw:
            self.base.draw()

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
        # type: ([float], [float], event) -> ()
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
        self.update(draw=self.base.updateOnMove)

    def onRelease(self, ev):
        """
        Update the line position when the mouse button is released
        """
        if self.setter:
            self._set_q(self.x)
        else:
            self.input.setText(f"{self.x:.3}")
        self.update(draw=True)
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
