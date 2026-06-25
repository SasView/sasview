"""Trust bar for displaying trust information above the results plot for Size Distribution perspective."""


import numpy as np
from matplotlib.axes import Axes
from matplotlib.backend_bases import FigureCanvasBase
from matplotlib.colors import LinearSegmentedColormap

from sas.qtgui.Plotting.PlotterData import Data1D

ColourStop = tuple[float, str]


class TrustBar:

    def __init__(self, ax: Axes, canvas: FigureCanvasBase) -> None:
        self.ax = ax
        self.canvas = canvas
        self.data: Data1D | None = None
        self.bar_ax: Axes | None = None
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

        d_low = self._normalize_x(trust_range["d_low"], xmin, xmax)
        d_high = self._normalize_x(trust_range["d_high"], xmin, xmax)

        stops = self._make_colour_stops(d_low, d_high)

        # Create a custom colormap from the colour stops.
        cmap = LinearSegmentedColormap.from_list("trust_bar_gradient", stops)

        # Create a gradient image for the trust bar.
        gradient = np.linspace(0, 1, 256).reshape(1, -1)

        # Create a thin inset axis above the main plot.
        bar_ax = self.ax.inset_axes((0.0, 1.02, 1.0, 0.02), transform=self.ax.transAxes)

        bar_ax.imshow(gradient, aspect="auto", cmap=cmap, extent=(xmin, xmax, 0, 1), origin="lower")

        # Match main plot x scaling and range.
        bar_ax.set_xscale(self.ax.get_xscale())
        bar_ax.set_xlim(self.ax.get_xlim())

        # Remove ticks and spines for a clean look.
        bar_ax.set_yticks([])
        bar_ax.set_xticks([])
        bar_ax.minorticks_off()
        for spine in bar_ax.spines.values():
            spine.set_visible(False)

        # Store the bar axis for later removal and connect the xlim_changed callback
        # to update the trust bar when the main plot is updated.
        self.xlim_cid = self.ax.callbacks.connect("xlim_changed", self.update)

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

    def _normalize_x(self, x: float, xmin: float, xmax: float) -> float:
        """Returns the normalized x value in the range [0, 1] based on the current x limits."""
        return (x - xmin) / (xmax - xmin)

    def _make_colour_stops(self, low: float, high: float, transition_width: float = 0.05) -> list[ColourStop]:
        """Returns a list of colour stops for the trust bar gradient based on the low and high thresholds.

            red ---- yellow ---- green ---- yellow ---- red
                     (low)                  (high)

        This function also handles cases where the low and high thresholds are outside the [0, 1] range.

        :param low: The lower threshold for the trust bar (normalized to [0, 1]).
        :param high: The upper threshold for the trust bar (normalized to [0, 1]).
        :param transition_width: The width of the transition zone between colours. Default is 0.05.
        :return: A list of tuples representing the colour stops for the gradient.
        """

        stops: list[ColourStop] = []

        # Lower boundary: red to yellow to green
        if low - transition_width >= 1.0:
            return [(0.0, "red"), (1.0, "red")]
        elif low + transition_width <= 0.0:
            stops.append((0.0, "green"))
        elif low <= 0.0:
            stops.extend(
                [
                    (0.0, "yellow"),
                    (low + transition_width, "green"),
                ]
            )
        else:
            stops.extend(
                [
                    (0.0, "red"),
                    (low - transition_width, "red") if low - transition_width > 0.0 else (0.0, "red"),
                    (low, "yellow"),
                    (low + transition_width, "green"),
                ]
            )

        # Upper boundary: green to yellow to red
        if high + transition_width <= 0.0:
            return [(0.0, "red"), (1.0, "red")]
        elif high + transition_width >= 1.0:
            stops.append((1.0, "green"))
        elif high >= 1.0:
            stops.extend(
                [
                    (high - transition_width, "green"),
                    (1.0, "yellow"),
                ]
            )
        else:
            stops.extend(
                [
                    (high - transition_width, "green"),
                    (high, "yellow"),
                    (high + transition_width, "red") if high + transition_width < 1.0 else (1.0, "red"),
                    (1.0, "red"),
                ]
            )

        # Sort the stops by position to ensure they are in the correct order for the colormap.
        stops = sorted(stops, key=lambda x: x[0])

        # Remove duplicate and close stops to avoid issues with the colormap.
        clean_stops: list[ColourStop] = []
        for position, colour in stops:
            if clean_stops and abs(clean_stops[-1][0] - position) < 1e-12:
                clean_stops[-1] = (position, colour)
            else:
                clean_stops.append((position, colour))

        # Handle the case where there is only one stop, which can cause issues with the colormap.
        if len(clean_stops) == 1:
            clean_stops = [
                (0.0, clean_stops[0][1]),
                (1.0, clean_stops[0][1]),
            ]

        return clean_stops
