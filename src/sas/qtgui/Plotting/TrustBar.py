"""Trust bar for displaying trust information above the results plot for Size Distribution perspective."""


import numpy as np
from matplotlib.axes import Axes
from matplotlib.backend_bases import FigureCanvasBase
from matplotlib.collections import LineCollection
from matplotlib.colors import to_rgba

from sas.qtgui.Plotting.PlotterData import Data1D


class TrustBar:

    def __init__(self, ax: Axes, canvas: FigureCanvasBase) -> None:
        self.ax = ax
        self.canvas = canvas
        self.data: Data1D | None = None
        self.bar_ax: Axes | None = None
        self.bar: LineCollection | None = None
        self.xlim_cid: int | None = None  # To store the callback ID for disconnecting later

    def draw(self, data: Data1D) -> None:
        """
        Draw a simple green-yellow-red gradient bar above the main 1D plot.

        :param data: The Data1D object containing the trust range information.
        """

        # Clear any existing trust bar before drawing a new one.
        self.clear()

        self.data = data

        trust_range = getattr(data, "trust_range", None)
        if trust_range is None:
            return

        # Get the current x limits of the main plot.
        xmin, xmax = self.ax.get_xlim()

        d_low = trust_range.get("d_low", xmin)
        d_high = trust_range.get("d_high", xmax)
        
        # Create a set of x values for the trust bar. Use a logarithmic scale if the main plot is logarithmic.
        N = 1000

        if self.ax.get_xscale() == "log":
            x = np.geomspace(xmin, xmax, N)
        else:
            x = np.linspace(xmin, xmax, N)
            
        # Create segments for the LineCollection.
        segments = [
            [(x[i], 0.5), (x[i + 1], 0.5)]
            for i in range(N - 1)
        ]

        # Get the color based on the midpoint of each segment
        colours = [
            self.colour_at(0.5 * (x[i] + x[i + 1]), d_low, d_high)
            for i in range(len(x) - 1)
        ]
        
        # Create an inset axis above the main plot for the trust bar.
        self.bar_ax = self.ax.inset_axes(
            (0.0, 1.02, 1.0, 0.02),
            transform=self.ax.transAxes,
        )

        self.bar = LineCollection(
            segments,
            colors=colours,
            linewidths=8,
            capstyle="butt"
        )

        self.bar_ax.add_collection(self.bar)
        
        # Match main plot x scaling and range.
        self.bar_ax.set_xscale(self.ax.get_xscale())
        self.bar_ax.set_xlim(self.ax.get_xlim())

        self.bar_ax.set_ylim(0, 1)

        # Remove ticks and spines for a clean look.
        self.bar_ax.set_yticks([])
        self.bar_ax.set_xticks([])
        self.bar_ax.minorticks_off()
        for spine in self.bar_ax.spines.values():
            spine.set_visible(False)

        # Store the bar axis for later removal and connect the xlim_changed callback
        # to update the trust bar when the main plot is updated.
        self.xlim_cid = self.ax.callbacks.connect("xlim_changed", self.update)

    def colour_at(self, x: float, d_low: float, d_high: float) -> tuple[float, float, float, float]:
        """
        Determine the color of the trust bar at a given x position based on the trust range.
        
        """
        if x < d_low:
            return to_rgba("red")
        elif x <= d_high:
            return to_rgba("green")
        else:
            return to_rgba("red")

    def clear(self) -> None:
        """
        Clear the trust bar from the plot. This method disconnects the xlim_changed callback
        and removes the bar axis if it exists.
        """
        if self.xlim_cid is not None:
            try:
                self.ax.callbacks.disconnect(self.xlim_cid)
            except Exception:
                pass
            self.xlim_cid = None

        if self.bar_ax is not None:
            try:
                self.bar_ax.remove()
            except ValueError:
                pass
            self.bar_ax = None

        self.data = None

    def update(self, main_ax) -> None:
        """
        Update the trust bar when the main plot is updated.
        """
        if self.data is not None:
            self.draw(self.data)
            self.canvas.draw_idle()
