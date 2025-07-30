"""Double slider interactor for setting the Q range for a fit or function"""
import numpy as np

import sas.qtgui.Utilities.ObjectLibrary as ol
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.Slicers.BaseInteractor import BaseInteractor


class QRangeSlider(BaseInteractor):
    """  Draw a pair of draggable vertical lines. Each line can be linked to a GUI input.
    The GUI input should update the lines and vice-versa.
    """
    def __init__(self, base, axes, color='black', zorder=5, data=None):
        # type: (Plotter, Plotter.ax, str, int, Data1D) -> None
        """ Initialize the slideable lines and associated markers """
        # Assert the data object is a plottable
        assert isinstance(data, Data1D)
        # Plotter object
        BaseInteractor.__init__(self, base, axes, color=color)
        self.base = base
        self.markers = []
        self.axes = axes
        self.data = data
        # Track the visibility for toggling the slider on/off
        self.is_visible = False
        self.connect = self.base.connect
        # Min and max x values
        self.x_min = np.fabs(min(self.data.x))
        self.y_marker_min = self.data.y[np.where(self.data.x == self.x_min)[0][0]]
        self.x_max = np.fabs(max(self.data.x))
        self.y_marker_max = self.data.y[np.where(self.data.x == self.x_max)[0][-1]]
        # Should the inputs update while the bar is actively being dragged?
        self.updateOnMove = data.slider_update_on_move
        # Draw the lines
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

    def clear(self):
        # type: () -> None
        """ Clear this slicer and its markers """
        self.clear_markers()

    def show(self):
        # type: () -> None
        """ Show this slicer and its markers """
        self.line_max.draw()
        self.line_min.draw()
        self.update()

    def remove(self):
        # type: () -> None
        """ Remove this slicer and its markers """
        self.line_max.remove()
        self.line_min.remove()
        self.draw()
        self.is_visible = False

    def update(self, x=None, y=None):
        # type: (float, float) -> None
        """Draw the new lines on the graph."""
        self.line_min.update(x, y, draw=self.updateOnMove)
        self.line_max.update(x, y, draw=self.updateOnMove)
        self.base.update()
        self.is_visible = True

    def save(self, ev):
        # type: (QEvent) -> None
        """ Remember the position of the lines so that we can restore on Esc. """
        self.line_min.save(ev)
        self.line_max.save(ev)

    def restore(self, ev):
        # type: (QEvent) -> None
        """ Restore the lines. """
        self.line_max.restore(ev)
        self.line_min.restore(ev)

    def toggle(self):
        # type: () -> None
        """ Toggle the slider visibility. """
        if self.is_visible:
            self.remove()
        else:
            self.show()

    def move(self, x, y, ev):
        # type: (float, float, QEvent) -> None
        """ Process move to a new position, making sure that the move is allowed. """
        pass

    def clear_markers(self):
        # type: () -> None
        """ Clear each of the lines individually """
        self.line_min.clear()
        self.line_max.clear()

    def draw(self):
        # type: () -> None
        """ Update the plot """
        self.base.draw()


class LineInteractor(BaseInteractor):
    """
    Draw a single vertical line that can be dragged on a plot
    """
    def __init__(self, base, axes, color='black', zorder=5, x=0.5, y=0.5,
                 input=None, setter=None, getter=None, perspective=None, tab=None):
        # type: (Plotter, Plotter.ax, str, int, float, float, [str], [str], [str], str, str) -> None
        """ Initialize the line interactor object"""
        BaseInteractor.__init__(self, base, axes, color=color)
        # Plotter object
        self.base = base
        # Inputs and methods linking this slider to a GUI element so, as one changes, the other also updates
        self._input = None
        self._setter = None
        self._getter = None
        # The marker(s) for this line - typically only one
        self.markers = []
        # The Plotter.ax object
        self.axes = axes
        # X and Y values used for the line and markers
        self.x = x
        self.save_x = self.x
        self.y_marker = y
        self.save_y = self.y_marker
        self.draw(zorder)
        # Is the slider able to move
        self.has_move = True
        try:
            data_explorer = ol.getObject('DataExplorer')
            self.perspective = data_explorer.parent.loadedPerspectives.get(perspective, None)
        except AttributeError:
            # QRangeSlider is disconnected from GuiManager for testing
            self.perspective = None
        if self.perspective is None:
            return
        if tab and hasattr(self.perspective, 'getTabByName'):
            # If the perspective is tabbed, set the perspective to the tab this slider in associated with
            self.perspective = self.perspective.getTabByName(tab)
        if self.perspective:
            # Connect the inputs and methods
            self.input = self._get_input_or_callback(input)
            self.setter = self._get_input_or_callback(setter)
            self.getter = self._get_input_or_callback(getter)
        self.connect_markers([self.line, self.inner_marker])
        # Get the linked input and draw
        self.inputChanged()

    @property
    def input(self):
        # type: () -> Union[QLineEdit, QTextEdit, None]
        """ Get the text input that should be linked to the position of this slider """
        return self._input

    @input.setter
    def input(self, input):
        # type: (Union[QLineEdit, QTextEdit, None]) -> None
        """ Set the text input that should be linked to the position of this slider """
        self._input = input
        if self._input:
            self._input.editingFinished.connect(self.inputChanged)

    @property
    def setter(self):
        # type: () -> Union[callable, None]
        """ Get the x-value setter method associated with this slider """
        return self._setter

    @setter.setter
    def setter(self, setter):
        # type: (Union[callable, None]) -> None
        """ Set the x-value setter method associated with this slider """
        self._setter = setter if callable(setter) else None

    @property
    def getter(self):
        # type: () -> Union[callable, None]
        """ Get the x-value getter method associated with this slider """
        return self._getter

    @getter.setter
    def getter(self, getter):
        # type: (Union[callable, None]) -> None
        """ Set the x-value getter associated with this slider """
        self._getter = getter if callable(getter) else None

    def clear(self):
        # type: () -> None
        """ Disconnect any inputs and callbacks and the clear the line and marker """
        self.clear_markers()
        self.remove()

    def remove(self):
        # type: () -> None
        """ Clear this slicer and its markers """
        if self.inner_marker:
            self.inner_marker.remove()
        if self.line:
            self.line.remove()

    def draw(self, zorder=5):
        # type: (int) -> None
        """ Draw the line and marker on the linked plot using the latest x and y values """
        # Inner circle marker
        self.inner_marker = self.axes.plot([self.x], [self.y_marker], linestyle='', marker='o', markersize=4,
                                           color=self.color, alpha=0.6, pickradius=5, label=None, zorder=zorder,
                                           visible=True)[0]
        self.line = self.axes.axvline(self.x, linestyle='-', color=self.color, marker='', pickradius=5,
                                      label=None, zorder=zorder, visible=True)

    def _get_input_or_callback(self, connection_list=None):
        # type: ([str]) -> Union[QLineEdit, QTextEdit, None]
        """ Returns an input or callback method based on a list of inputs/commands """
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
        # type: (float) -> None
        """ Call the q setter callback method if it exists """
        self.x = value
        if self.setter and callable(self.setter):
            self.setter(value)
        elif hasattr(self.input, 'setText'):
            self.input.setText(f"{value:.3}")

    def _get_q(self):
        # type: () -> None
        """ Get the q value, inferring the method to get the value """
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
        # type: () -> None
        """ Track the input linked to the x value for this slider and update as needed """
        self._get_q()
        self.y_marker = self.base.data.y[(np.abs(self.base.data.x - self.x)).argmin()]
        self.update(draw=True)

    def update(self, x=None, y=None, draw=False):
        # type: (float, float, bool) -> None
        """ Update the line position on the graph. """
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
        # type: (QEvent) -> None
        """ Remember the position for this line so that we can restore on Esc. """
        self.save_x = self.x
        self.save_y = self.y_marker

    def restore(self, ev):
        # type: (QEvent) -> None
        """ Restore the position for this line """
        self.x = self.save_x
        self.y_marker = self.save_y

    def move(self, x, y, ev):
        # type: (float, float, QEvent) -> None
        """ Process move to a new position, making sure that the move is allowed. """
        self.has_move = True
        self.x = x
        if self.base.updateOnMove:
            self._set_q(x)
        self.y_marker = self.base.data.y[(np.abs(self.base.data.x - self.x)).argmin()]
        self.update(draw=self.base.updateOnMove)

    def onRelease(self, ev):
        # type: (QEvent) -> bool
        """ Update the line position when the mouse button is released """
        # Set the Q value if a callable setter exists otherwise update the attached input
        self._set_q(self.x)
        self.update(draw=True)
        self.moveend(ev)
        return True

    def clear_markers(self):
        # type: () -> None
        """ Disconnect the input and clear the callbacks """
        if self.input:
            self.input.editingFinished.disconnect(self.inputChanged)
        self.setter = None
        self.getter = None
        self.input = None
