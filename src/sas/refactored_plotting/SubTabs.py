
import matplotlib.figure
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from PlotModifiers import ModifierColormap, ModifierLinecolor, ModifierLinestyle, PlotModifier
from PlotTreeItems import PlottableItem
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget, QMainWindow, QTabWidget, QVBoxLayout, QWidget


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

class SubTabs(QTabWidget):
    """
    Class for keeping subtabs and adding figures with subplots to them. It takes a tabitem to process and iterates
    over all the existing children of the given tabitem to plot their contents in the respective order. For example
    for every child item of the TabItem, one subtab will be created and for every child item of the subtab, one plot
    will be generated.
    The application of modifiers onto plots is also managed in this class constructor.
    """
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

    def __init__(self, datacollector, tabitem):
        super().__init__()

        self.datacollector = datacollector
        self.figures: list[matplotlib.figure] = []
        # iterate through subtabs
        for i in range(tabitem.childCount()):
            # add subplots
            layout = QVBoxLayout()
            figure = matplotlib.figure.Figure(figsize=(5, 5))
            canvas = ClickableCanvas(figure)
            layout.addWidget(canvas)
            layout.addWidget(NavigationToolbar2QT(canvas))

            # decide whether there is only one plot needs to be plotted. then, only one central plot is needed
            subplot_count = tabitem.child(i).childCount()
            if subplot_count == 1:
                ax = figure.subplots(subplot_count)
                # putting the axes object in a list so that the access can be generic for both cases with multiple
                # subplots and without
                ax = [ax]
            else:
                # for multiple subplots: decide on the ratios for the bigger, central plot and the smaller, side plots
                # region for the big central plot in gridspec
                gridspec = figure.add_gridspec(ncols=2, width_ratios=[3, 1])
                # region for the small side plots in sub_gridspec
                sub_gridspec = gridspec[1].subgridspec(ncols=1, nrows=subplot_count - 1)

                ax = [figure.add_subplot(gridspec[0])]
                # add small plots to axes list, so it can be accessed that way
                for idx in range(subplot_count-1):
                    ax.append(figure.add_subplot(sub_gridspec[idx]))

            # after the subplots are created, the axes objects need to be filled with actual lines/2d plots
            # iterate through subplots
            for j in range(tabitem.child(i).childCount()):
                # set the title of the plot with the subplot name of the PlotTreeWidget item
                ax[j].set_title(str(tabitem.child(i).child(j).text(0)))

                # iterate through plottables and plot modifiers (PlotTreeWidget items)
                for k in range(tabitem.child(i).child(j).childCount()):

                    plottable_or_modifier_item = tabitem.child(i).child(j).child(k).data(0, 1)
                    # check if the plottable or modifier item is a PlottableItem (actual data to be displayed)
                    if isinstance(plottable_or_modifier_item, PlottableItem):
                        plottable = plottable_or_modifier_item
                        dataset = self.datacollector.get_data_by_id(plottable.data_id)

                        # if the dataset is 2d, plotting will be done with a heatmap plot
                        if dataset.is_data_2d:

                            # collect a possible existing colormap plot modifier (child item)
                            # and save it, so that it can be used during plot creation
                            colormap_modifier = ""
                            for ii in range(plottable.childCount()):
                                if isinstance(plottable.child(ii), ModifierColormap):
                                    colormap_modifier = plottable.child(ii).text(0).split('=')[1]
                            if colormap_modifier == "":
                                colormap_modifier = "jet"

                            # get the data from the dataset for the plot
                            x = dataset.x_data
                            y = dataset.y_data
                            y_fit = dataset.y_fit

                            # check if the plot is a data plot (4), fit plot (5) or residual plot (6)
                            if plottable.type_num == 4:
                                ax[j].pcolor(x[0], x[1], y,
                                             norm=matplotlib.colors.LogNorm(vmin=np.min(y),
                                                                            vmax=np.max(y)),
                                             cmap=colormap_modifier)
                            elif plottable.type_num == 5:
                                ax[j].pcolor(x[0], x[1], y_fit,
                                             norm=matplotlib.colors.LogNorm(vmin=np.min(y_fit),
                                                                            vmax=np.max(y_fit)),
                                             cmap=colormap_modifier)
                            elif plottable.type_num == 6:
                                y_res = np.absolute(np.subtract(y_fit, y))
                                ax[j].pcolor(x[0], x[1], y_res,
                                             norm=matplotlib.colors.LogNorm(vmin=np.min(y_res),
                                                                            vmax=np.max(y_res)),
                                             cmap=colormap_modifier)

                        # if it is not a 2d plot, it must be a 1d plot (line plot)
                        else:
                            # select again for data plot (1), fit plot (2) and residual plot (3)
                            if plottable.type_num == 1:  # data plot: log-log plot, show only data
                                ax[j].plot(dataset.x_data, dataset.y_data)
                                ax[j].set_yscale('log')
                            elif plottable.type_num == 2:  # fit plot: log-log plot, show fit and data curve
                                ax[j].plot(dataset.x_data, dataset.y_fit)
                                ax[j].set_yscale('log')
                            elif plottable.type_num == 3:  # residual plot lin-log plot, show calc and show res only
                                ax[j].plot(dataset.x_data, np.subtract(dataset.y_fit, dataset.y_data))

                            # iterate through plottable modifier, e.g. linecolor, linestyle
                            for l in range(plottable.childCount()):
                                plottable_modifier = plottable.child(l)
                                if isinstance(plottable_modifier.data(0, 1), ModifierLinecolor):
                                    ax[j].get_lines()[-1].set_color(plottable_modifier.text(0).split('=')[1])
                                elif isinstance(plottable_modifier.data(0, 1), ModifierLinestyle):
                                    ax[j].get_lines()[-1].set_linestyle(plottable_modifier.text(0).split('=')[1])

                    # applying a colormap to a set of lines and setting the respective color to lines that are
                    # returned by the axes object
                    elif isinstance(plottable_or_modifier_item, PlotModifier):
                        plot_modifier = plottable_or_modifier_item
                        if isinstance(plot_modifier, ModifierColormap):
                            cmap = matplotlib.colormaps[plot_modifier.text(0).split('=')[1]]
                            n = len(ax[j].get_lines())
                            for m in range(n):
                                ax[j].get_lines()[m].set_color(cmap(m/(n-1)))

            # create the widget that will be inside the dock widget
            figure.tight_layout()
            canvas_widget = QWidget()
            canvas_widget.setLayout(layout)

            # create the main window, which is the container for the dock widget, so that it can be dragged out and
            # put in again
            dock_container = QMainWindow()
            # set the object name for later, so that the style sheet changes for graying out only affects the dock
            # container itself and not the child widgets of the dock container. fitpage_index is used as an identifier
            # here
            dock_container.setObjectName("DockContainer" + str(tabitem.data(0, 1).fitpage_index))
            dock_widget = QDockWidget()

            dock_widget.topLevelChanged.connect(lambda x: self.grayOutOnDock(dock_container, dock_widget))

            dock_widget.setWidget(canvas_widget)
            dock_container.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, dock_widget)

            self.addTab(dock_container, tabitem.child(i).text(0))
            self.figures.append(figure)


