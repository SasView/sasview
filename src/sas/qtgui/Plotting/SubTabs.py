from PySide6 import QtWidgets
from PySide6 import QtCore

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from sas.qtgui.Utilities import GuiUtils

from sas.qtgui.Plotting import TabbedPlotWidget

class SubTabs(QtWidgets.QTabWidget):
    """
    This class is for keeping all the subtabs for Plots that are displayed in these. One SubTabs item should
    always be associated with one QStandardItem plot_item
    """
    def __init__(self, parent: TabbedPlotWidget, plots: list):
        super().__init__(parent=parent)
        # keep track of the parent to access the index of the fitpage?
        self.parent = parent
        self.counter = 1

        # Set the object parameters after creating this subtab in the tabbedplotwidget. Then this subtab knows
        # the tab_id of the parent and the tab index of itself in the parent tab widget.
        self.parent_tab_index = -1
        self.tab_id = -1

        # The idea is: I want to use the Axes that are created by the Plotter.plot function and copy them over to the
        # TabbedPlotWidget. But since matplotlib does not allow copying of Axes between figures straight away, the Axes
        # in the TabbedPlotWidget need to be created straight away and then given to the Plotter so that it can
        # populate these Axes with the same Data, Labels, Titles that the QWidgets for every single plot were
        # populated with.
        self.ax = None

        self.add_subtab(plots)

    def set_parent_tab_index(self):
        self.parent_tab_index = self.parent.indexOf(self)
        self.tab_id = self.parent.inv_tab_fitpage_dict[self.parent_tab_index]
        print(self.parent_tab_index)
        print(self.tab_id)

    def add_subtab(self, plots):
        """
        Function to add a sub tab with the desired functionality to instances of this class (which are: docking,
            multiple subplots, interactive subplots for clicking)
        The widget that the QTabWidget that is extended by this class looks like this:
        QTabWidget stores a Widget in one of its tabs.
        This Widget is a QMainWindow (the DockContainer) that can function as a container for the docking function,
            so that the window that will have the plot can be docked out, moved around and docked in again.
        The QMainWindow (DockContainer) is filled with a DockWidget, which will be able to dock in and out itself.
        The content of this DockWidget is a CanvasWidget(QWidget) with a stored layout, where the further widgets can
            be added into.
        The layout of the CanvasWidget is populated with the canvas that the matplotlib figure with the final number
            of subplots will be in. The matplotlib navigation toolbar can also be added to this layout later.
        The canvas added to the layout of the CanvasWidget is the ClickableCanvas and extends the FigureCanvasQtAgg
            in a way that subplots from the figure of this FigureCanvas can be clicked and will change their position
            with the first (big) subplot

        As a flowchart (?): QTabWidget->QMainWindow->QDockWidget->QWidget->QLayout of former QWidget->FigureCanvasQtAgg
        """

        # The idea behind creating the figure here already is to feed it to the creation of the canvas right away,
        # because otherwise it can be quite tricky to navigate through all the layers in between to add the figure
        # or manipulate all the axes for example
        self.figure = Figure(figsize=(5, 5))

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

        print("axes created in SubTabs:", self.ax[0])

        self.addTab(DockContainer(self.figure), str(self.counter))
        self.counter += 1


class DockContainer(QtWidgets.QMainWindow):
    """
    Container for docking purposes. Carries a
    """
    def __init__(self, figure):
        super().__init__()
        # TODO: identifier needs to be added to the objectname string --
        # otherwise changing the stylesheet could potentially change the stylesheets of all existing dockcontainers
        # a combination of the tab_id from the TabbedPlotWidget and the subtab index of the DockContainer would be a
        # sensible approach
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
    """
    QWidget that can be added into the DockWidget in the MainWindow. The layout of this carries the
    """
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