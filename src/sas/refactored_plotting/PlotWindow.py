from functools import cached_property
from typing import TYPE_CHECKING, cast

from matplotlib.axes import Axes
from matplotlib.backends.backend_qt import NavigationToolbar2QT
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.mathtext import MathTextParser
from PySide6.QtWidgets import QDockWidget, QMainWindow, QTabWidget, QVBoxLayout, QWidget

from sasdata.data import SasMeasurement
from sasdata.quantities.quantity import Quantity

if TYPE_CHECKING:
    from sas.refactored import TrackedFit, TrackedPlot

type Plottable = "SasMeasurement | TrackedFit"

tab_name_dict = {0: "Data", 1: "Fit"}


# Axis names, as written in the axis labels by the data loaders of the current (non-refactored) SasView.
_axis_names = {
    "I": "Intensity",
    "Qx": "Q_{x}",
    "Qy": "Q_{y}",
}
_mathtext_parser = MathTextParser("path")


def unit_label(symbol: str) -> str:
    """Format a unit symbol from sasdata (e.g. 'Ang^-1') as in the current SasView plots (e.g. 'A^{-1}')."""
    if symbol in ("", "none"):
        return ""
    parts = []
    for part in symbol.split():
        base, _, exponent = part.partition("^")
        if base == "Ang":
            base = "A"
        parts.append(f"{base}^{{{exponent}}}" if exponent else base)
    return r"\ ".join(parts)


def axis_label(quantity: Quantity) -> str:
    """Axis label from the name and unit of a quantity, written as in the current SasView plots but with a space
    before the unit, e.g. '$\\rm{Q}\\ (A^{-1})$'.

    Names stored as paths (e.g. '/sasentry01/sasdata01/I' from HDF5 files) are shortened to their last part.
    If the label can't be written as a matplotlib math expression, it is returned as plain text, e.g. 'Q (A^-1)'.
    """
    name = getattr(quantity, "name", "") or ""
    name = name.rstrip("/").split("/")[-1]
    units = getattr(quantity, "units", None)
    symbol = units.ascii_symbol if units is not None else ""
    unit = unit_label(symbol)
    if not name and not unit:
        return ""

    label = rf"\rm{{{_axis_names.get(name, name)}}}" if name else ""
    if unit:
        # A plain space is ignored in a math expression, so use an explicit one
        label += rf"\ ({unit})" if label else f"({unit})"
    label = f"${label}$"
    try:
        _mathtext_parser.parse(label)
    except ValueError:
        return f"{name} ({symbol})" if name and unit else name or symbol
    return label


def tab_name(i: int) -> str:
    return tab_name_dict.get(i, "Unknown")


class PlotWindow(QTabWidget):
    """
    Class for keeping subtabs and adding figures with subplots to them. It takes a tabitem to process and iterates
    over all the existing children of the given tabitem to plot their contents in the respective order. For example
    for every child item of the TabItem, one subtab will be created and for every child item of the subtab, one plot
    will be generated.
    The application of modifiers onto plots is also managed in this class constructor.
    """

    plot_object: "TrackedPlot"
    tabs: list[FigureCanvasQTAgg]
    figures: list[Figure]

    def grayOutOnDock(self, dock_container: QMainWindow, dock_widget: QDockWidget):
        """
        Function that is connected to the topLevelChanged slot of the dock widget for the plot widget. When the
        dock is floating, the area where the dock widget was before, is grayed out. When it is docked in again,
        the state is reverted.
        """
        name = dock_container.objectName()
        if dock_widget.isFloating():
            dock_container.setStyleSheet("QMainWindow#" + name + " { background-color: gray }")
        else:
            print("white")
            dock_container.setStyleSheet("QMainWindow#" + name + " { background-color: white }")

    def __init__(self, plot_object: "TrackedPlot", parent: QWidget | None = None):
        super().__init__(parent)
        self.plot_object = plot_object
        self.tabs = []
        self.figures = []
        self.draw()

    @cached_property
    def tabCount(self) -> int:
        if self.plot_object.to_plot and self.plot_object.fit:
            # This may become 3 later if residuals are involved.
            return 2
        elif self.plot_object.to_plot:
            return 1
        else:
            raise ValueError("There is nothing to plot!")

    def tabsForPlottable(self, tab: int) -> list[Plottable]:
        assert self.plot_object.to_plot is not None
        match tab:
            case 0:
                return [self.plot_object.to_plot]
            case 1:
                assert self.plot_object.fit is not None
                return [self.plot_object.to_plot, self.plot_object.fit]
            case _:
                raise ValueError(f"The objects to be drawn in tab {tab} are not defined.")

    def draw(self):
        for i in range(self.tabCount):
            plottables = self.tabsForPlottable(i)
            layout = QVBoxLayout()
            figure = Figure(figsize=(5, 5))
            tab_canvas = FigureCanvasQTAgg(figure)
            layout.addWidget(tab_canvas)
            layout.addWidget(NavigationToolbar2QT(tab_canvas))
            self.drawTab(plottables, figure)
            figure.tight_layout()
            canvas_widget = QWidget()
            canvas_widget.setLayout(layout)
            self.addTab(canvas_widget, tab_name(i))
            self.figures.append(figure)

    def plot1d(self, data: SasMeasurement, axis: Axes, fit: "TrackedFit | None" = None):
        axis.set_title(data.name)
        axis.plot(data.abscissae.axes[0].value, data.ordinate.value, marker="o", linestyle="")
        axis.set_xlabel(axis_label(data.abscissae.axes[0]))
        axis.set_ylabel(axis_label(data.ordinate))
        axis.set_yscale("log")
        axis.set_xscale("log")
        if fit:
            axis.plot(fit.fit.abscissae.axes[0].value, fit.fit.ordinate.value)
        for modifier in self.plot_object.modifiers:
            modifier.modify_axes(axis)

    def drawTab(self, plottables: list[Plottable], figure: Figure):
        if len(plottables) <= 2:
            axis = figure.subplots()
            # putting the axes object in a list so that the access can be
            # generic for both cases with multiple subplots and without
            axes = [axis]
        else:
            # for multiple subplots: decide on the ratios for the bigger, central plot and the smaller, side plots
            # region for the big central plot in gridspec
            gridspec = figure.add_gridspec(ncols=2, width_rations=[3, 1])
            # region for the small side plots in sub_gridspec
            sub_gridspec = gridspec[1].subgridspec(ncols=1, nrows=len(plottables) - 1)

            axes = [figure.add_subplot(gridspec[0])]
            # add small plots to axes list, so it can be accessed that way
            for axis_no in range(len(plottables) - 1):
                axes.append(figure.add_subplot(sub_gridspec[axis_no]))
        for i, axis in enumerate(axes):
            match i:
                case 0:
                    data = cast(SasMeasurement, plottables[0])
                    fit = cast("TrackedFit", plottables[1]) if len(plottables) > 1 else None
                    self.plot1d(data, axis, fit)
                case 1:
                    raise NotImplementedError("Residuals plot is not implemented yet.")
                case _:
                    raise ValueError("There are more axes than what the plotter knows what to do with.")
