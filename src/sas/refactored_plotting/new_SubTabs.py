from PySide6.QtWidgets import QTabWidget, QMainWindow, QDockWidget, QWidget
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sas.refactored import TrackedPlot


class SubTabs(QTabWidget):
    """
    Class for keeping subtabs and adding figures with subplots to them. It takes a tabitem to process and iterates
    over all the existing children of the given tabitem to plot their contents in the respective order. For example
    for every child item of the TabItem, one subtab will be created and for every child item of the subtab, one plot
    will be generated.
    The application of modifiers onto plots is also managed in this class constructor.
    """

    plot_object: "TrackedPlot"

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
        self.draw()

    def draw(self):
        raise NotImplementedError()
