import numpy as np

from matplotlib.axes import Axes

from sas.qtgui.Plotting.Plotter2D import Plotter2D
from sas.qtgui.Plotting.Slicing.Interactors.SlicerInteractor import SlicerInteractor

class VerticalLinePair(SlicerInteractor):
    """
    Draw 2 vertical lines centered on (0,0) that can move
    on the y direction. The two lines move symmetrically (in opposite
    directions). It also defines the y and -y position of a box.
    """

    def __init__(self, base: Plotter2D, axes: Axes, color='black', zorder=5, x=0.5, y=0.5):
        """
        """
        super().__init__(self, base, axes, color=color)

        self.x = np.fabs(x)
        self.save_x = self.x
        self.y = np.fabs(y)
        self.save_y = y

        # Inner circle marker
        self.inner_marker = self.axes.plot([self.x], [0], linestyle='',
                                           marker='s', markersize=10,
                                           color=self.color, alpha=0.6,
                                           pickradius=5, label="pick",
                                           zorder=zorder, visible=True)[0]

        self.right_line = self.axes.plot([self.x, self.x],
                                         [self.y, -self.y],
                                         linestyle='-', marker='',
                                         color=self.color, visible=True)[0]

        self.left_line = self.axes.plot([-self.x, -self.x],
                                        [self.y, -self.y],
                                        linestyle='-', marker='',
                                        color=self.color, visible=True)[0]

        self.connect_markers([self.right_line, self.inner_marker])
        self.update()



    def clear(self):
        """
        Clear this slicer  and its markers
        """
        self.clear_markers()
        self.inner_marker.remove()
        self.left_line.remove()
        self.right_line.remove()

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
        self.inner_marker.set(xdata=[self.x], ydata=[0])
        self.left_line.set(xdata=[-self.x, -self.x], ydata=[self.y, -self.y])
        self.right_line.set(xdata=[self.x, self.x], ydata=[self.y, -self.y])

    def move(self, x, y, ev):
        """
        Process move to a new position, making sure that the move is allowed.
        """

        self.x = x
        super().move(x, y, ev)