from PySide6 import QtWidgets
from PySide6 import QtCore

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from sas.qtgui.Utilities import GuiUtils

class SubTabs(QtWidgets.QTabWidget):
    """
    This class is for keeping all the subtabs for Plots that are displayed in these. One SubTabs item should
    always be associated with one QStandardItem plot_item
    """
    def __init__(self, parent, plots):
        super().__init__(parent=parent)
        # keep track of the parent to access the index of the fitpage?
        self.parent = parent
        self.counter = 1

        # The idea is: To use the existing infrastructure of the Plotter but not create multiple instances of them
        # just to use the plot() function, that the number of Axes that is needed is already created here and
        self.ax = None

        self.add_subtab(plots)

    def add_subtab(self, plots):
        self.figure = Figure(figsize=(5, 5))


        print("from SubTabs: add_subtab plots", plots)
        print("from SubTabs: add_subtab len(plots)", len(plots))
        # filling the slots for the plots temporary to try out the functionalities of the dock container and the
        # clickable canvas
        subplot_count = len(plots)
        if subplot_count == 1:
            self.ax = self.figure.subplots(subplot_count)
            # putting the axes object in a list so that the access can be generic for both cases with multiple
            # subplots and without
            self.ax = [self.ax]
        else:
            # for multiple subplots: decide on the ratios for the bigger, central plot and the smaller, side plots
            # region for the big central plot in gridspec
            gridspec = self.figure.add_gridspec(ncols=2, width_ratios=[3, 1])
            # region for the small side plots in sub_gridspec
            sub_gridspec = gridspec[1].subgridspec(ncols=1, nrows=subplot_count-1)

            ax = [self.figure.add_subplot(gridspec[0])]
            # add small plots to axes list, so it can be accessed that way
            for idx in range(subplot_count - 1):
                ax.append(self.figure.add_subplot(sub_gridspec[idx]))

        i = 0
        for item, plot in plots.items():
            # [item, plot]
            # data = GuiUtils.dataFromItem(item)
            # ax[i].plot(data.x, data.y)
            print("from SubTabs in the plotting for loop: plotting")


            i += 1

        self.addTab(DockContainer(self.figure), str(self.counter))

        self.counter += 1


class DockContainer(QtWidgets.QMainWindow):
    def __init__(self, figure):
        super().__init__()
        # TODO: identifier needs to be added to the objectname string --
        # otherwise changing the stylesheet could potentially change the stylesheets of all existing dockcontainers
        self.setObjectName("DockContainer")

        # add the dockable widget and set the widget where the canvas will be in and
        # the plots will be painted on afterwards
        dock_widget = QtWidgets.QDockWidget()
        dock_widget.setWidget(CanvasWidget(figure))

        # connect graying out when docked out method
        dock_widget.topLevelChanged.connect(lambda x: self.grayOutOnDock(self, dock_widget))

        self.addDockWidget(QtCore.Qt.DockWidgetArea.TopDockWidgetArea, dock_widget)

    def grayOutOnDock(self, dock_container: QtWidgets.QMainWindow, dock_widget: QtWidgets.QDockWidget):
        """
        Function that is connected to the topLevelChanged slot of the dock widget that lives in one subtab. When the
        dock is floating, the area where the dock widget was before, is grayed out. When it is docked in again,
        the state is reverted.
        """
        name = dock_container.objectName()
        if dock_widget.isFloating():
            dock_container.setStyleSheet("QMainWindow#" + name + " { background-color: gray }")
        else:
            dock_container.setStyleSheet("QMainWindow#" + name + " { background-color: white }")

class CanvasWidget(QtWidgets.QWidget):
    def __init__(self, figure):
        super().__init__()

        layout = QtWidgets.QVBoxLayout()

        canvas = ClickableCanvas(figure)

        layout.addWidget(canvas)

        self.setLayout(layout)

class ClickableCanvas(FigureCanvasQTAgg):
    """
    This class provides an extension of the normal Qt Figure Canvas, so that clicks on subplots of a figure can be
    processed to switch the plot position. Example: if there are 3 plots in a figure 1,2,3 and plot 3 is clicked,
    the clicked plot will always change its position with the plot 1.
    """
    def __init__(self, figure):
        super().__init__(figure)
        self.mpl_connect("button_press_event", self.onclick)
        self.big = 0

    def onclick(self, event):
        big = self.big
        if event.inaxes:
            axs = self.figure.get_axes()
            for index, ax in enumerate(axs):
                if (index != big) and (ax == event.inaxes):
                    temp = axs[big].get_position()
                    axs[big].set_position(axs[index].get_position())
                    axs[index].set_position(temp)
                    self.big = index
                self.draw()