from functools import cached_property
from sasdata.data import SasData, SasMeasurement
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from PySide6.QtWidgets import QTabWidget, QMainWindow, QDockWidget, QWidget
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sas.refactored import TrackedPlot, TrackedFit

type Plottable = "SasMeasurement | TrackedFit"


class SubTabs(QTabWidget):
    """
    Class for keeping subtabs and adding figures with subplots to them. It takes a tabitem to process and iterates
    over all the existing children of the given tabitem to plot their contents in the respective order. For example
    for every child item of the TabItem, one subtab will be created and for every child item of the subtab, one plot
    will be generated.
    The application of modifiers onto plots is also managed in this class constructor.
    """

    plot_object: "TrackedPlot"
    tabs: list[FigureCanvasQTAgg]

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
            tabs = self.tabsForPlottable(i)
            raise NotImplementedError()

    def drawTab(self, cansas: FigureCanvasQTAgg, plottables: list[Plottable]):
        raise NotImplementedError()
