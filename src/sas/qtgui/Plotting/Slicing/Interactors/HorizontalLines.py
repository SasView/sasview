import numpy as np

from matplotlib.axes import Axes

from sas.qtgui.Plotting.Plotter2D import Plotter2D
from sas.qtgui.Plotting.Slicing.Interactors.SlicerInteractor import SlicerInteractor

from sas.qtgui.Utilities.TypedInputVariables import MutableInputVariableContainer

class HorizontalLines(SlicerInteractor):
    """
    Draw 2 Horizontal lines centered on (0,0) that can move
    on the x direction. The two lines move symmetrically (in opposite
    directions). It also defines the x and -x position of a box.
    """

    def __init__(self,
                 base: Plotter2D, axes: Axes,
                 x: MutableInputVariableContainer[float],
                 y: MutableInputVariableContainer[float],
                 color='black', zorder=5):

        super().__init__(base, axes, color=color)


        # Saving the end points of two lines
        self.x = x
        self.y = y

        # Creating a marker
        # Inner circle marker
        self.inner_marker = self.axes.plot([0], [self.y.value], linestyle='',
                                           marker='s', markersize=10,
                                           color=self.color, alpha=0.6,
                                           pickradius=5, label="pick",
                                           zorder=zorder,
                                           visible=True)[0]
        # Define 2 horizontal lines
        self.top_line = self.axes.plot([self.x.value, -self.x.value], [self.y.value, self.y.value],
                                       linestyle='-', marker='',
                                       color=self.color, visible=True)[0]

        self.bottom_line = self.axes.plot([self.x.value, -self.x.value], [-self.y.value, -self.y.value],
                                          linestyle='-', marker='',
                                          color=self.color, visible=True)[0]


        # Connecting markers to mouse events and draw
        self.connect_markers([self.top_line, self.inner_marker])
        self.update()


    def clear(self):
        """
        Clear this slicer  and its markers
        """
        self.clear_markers()
        self.inner_marker.remove()
        self.top_line.remove()
        self.bottom_line.remove()

    def update(self):
        """
        Draw the new roughness on the graph.

        :param x: x-coordinates to reset current class x
        :param y: y-coordinates to reset current class y

        """
        # Reset x, y- coordinates if send as parameters
        x = self.x.value
        y = self.y.value

        # Draw lines and markers
        self.inner_marker.set(xdata=[0], ydata=[y])
        self.top_line.set(xdata=[x, -x], ydata=[y, y])
        self.bottom_line.set(xdata=[x, -x], ydata=[-y, -y])

    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        super().move(x, y, ev)

        self.y = y
