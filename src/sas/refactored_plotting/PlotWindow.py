from sas.refactored_plotting.PlotModifiers import PlotModifier
from matplotlib.backends.backend_qt import NavigationToolbar2QT
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from functools import cached_property
from sasdata.data import SasData, SasMeasurement
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from PySide6.QtWidgets import QTabWidget, QMainWindow, QDockWidget, QWidget, QVBoxLayout
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from sas.refactored import TrackedPlot, TrackedFit

type Plottable = "SasMeasurement | TrackedFit"

tab_name_dict = {0: "Data", 1: "Fit"}


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
            print("gray")
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
