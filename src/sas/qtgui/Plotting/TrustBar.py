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
            xm = [np.sqrt(x[i] * x[i + 1]) for i in range(N - 1)]  # Geometric mean for color calculation in log scale
        else:
            x = np.linspace(xmin, xmax, N)
            xm = [0.5 * (x[i] + x[i + 1]) for i in range(N - 1)]  # Arithmetic mean for color calculation in linear scale

        # Create segments for the LineCollection.
        segments = [
            [(x[i], 0.5), (x[i + 1], 0.5)]
            for i in range(N - 1)
        ]

        # Get the color based on the midpoint of each segment
        colours = [
            self.colour_at(xm[i], d_low, d_high)
            for i in range(len(xm))
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

    def colour_at(self, x: float, d_low: float, d_high: float, tw: float = 0.5) -> tuple[float, float, float, float]:
        """
        Determine the color at a given x position based on the trust range.
        
        Gradient is defined as follows:
        
        red ---- yellow ---- green ---- yellow ---- red
        -------- (low) ---------------- (high) --------
        
        :param x: The x position to evaluate.
        :param d_low: The lower bound of the trust range.
        :param d_high: The upper bound of the trust range.
        :param tw: The transition width for color blending.
        :return: A tuple representing the RGBA color at the given x position.
        """
        
        # Handle logarithmic scale by transforming x, d_low, and d_high to log10 space.
        if self.ax.get_xscale() == "log":
            # Avoid taking log of non-positive values.
            if x <= 0 or d_low <= 0 or d_high <= 0:
                return to_rgba("red")
            x = np.log10(x)
            d_low = np.log10(d_low)
            d_high = np.log10(d_high)

        if x < d_low - tw or x > d_high + tw:
            return to_rgba("red")
        # Transition from red to yellow
        if d_low - tw <= x < d_low:
            a = (x - (d_low - tw)) / tw
            return tuple((1 - a) * r + a * y for r, y in zip(to_rgba("red"), to_rgba("yellow")))
        # Transition from yellow to green
        if d_low <= x < d_low + tw:
            a = (x - d_low) / tw
            return tuple((1 - a) * y + a * g for y, g in zip(to_rgba("yellow"), to_rgba("green")))
        if d_low + tw <= x <= d_high - tw:
            return to_rgba("green")
        # Transition from green to yellow
        if d_high - tw < x <= d_high:
            a = (x - (d_high - tw)) / tw
            return tuple((1 - a) * g + a * y for g, y in zip(to_rgba("green"), to_rgba("yellow")))
        # Transition from yellow to red
        if d_high < x <= d_high + tw:
            a = (x - d_high) / tw
            return tuple((1 - a) * y + a * r for y, r in zip(to_rgba("yellow"), to_rgba("red")))
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
