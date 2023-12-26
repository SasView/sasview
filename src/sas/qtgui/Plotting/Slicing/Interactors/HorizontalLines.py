import numpy as np

from matplotlib.axes import Axes

from sas.qtgui.Plotting.Plotter2D import Plotter2D
from sas.qtgui.Plotting.Slicing.Interactors.MouseDragBaseInteractor import MouseDragBaseInteractor


class HorizontalLines(MouseDragBaseInteractor):
    """
    Draw 2 Horizontal lines centered on (0,0) that can move
    on the x direction. The two lines move symmetrically (in opposite
    directions). It also defines the x and -x position of a box.
    """

    def __init__(self, base: Plotter2D, axes: Axes, color='black', zorder=5, x=0.5, y=0.5):
        """
        """
        super().__init__(self, base, axes, color=color)
        # Class initialization

        # Saving the end points of two lines
        self.x = x
        self.save_x = x

        self.y = y
        self.save_y = y
        # Creating a marker
        # Inner circle marker
        self.inner_marker = self.axes.plot([0], [self.y], linestyle='',
                                           marker='s', markersize=10,
                                           color=self.color, alpha=0.6,
                                           pickradius=5, label="pick",
                                           zorder=zorder,
                                           visible=True)[0]
        # Define 2 horizontal lines
        self.top_line = self.axes.plot([self.x, -self.x], [self.y, self.y],
                                       linestyle='-', marker='',
                                       color=self.color, visible=True)[0]
        self.bottom_line = self.axes.plot([self.x, -self.x], [-self.y, -self.y],
                                          linestyle='-', marker='',
                                          color=self.color, visible=True)[0]
        # Flag to check the motion of the lines
        self.has_move = False
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

    def update(self, x=None, y=None):
        """
        Draw the new roughness on the graph.

        :param x: x-coordinates to reset current class x
        :param y: y-coordinates to reset current class y

        """
        # Reset x, y- coordinates if send as parameters
        if x is not None:
            self.x = np.sign(self.x) * np.fabs(x)
        if y is not None:
            self.y = np.sign(self.y) * np.fabs(y)

        # Draw lines and markers
        self.inner_marker.set(xdata=[0], ydata=[self.y])
        self.top_line.set(xdata=[self.x, -self.x], ydata=[self.y, self.y])
        self.bottom_line.set(xdata=[self.x, -self.x], ydata=[-self.y, -self.y])

    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        self.y = y
        super().move(x,y,ev)