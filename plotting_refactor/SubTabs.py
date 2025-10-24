from PySide6.QtWidgets import QWidget, QTabWidget, QVBoxLayout, QMainWindow, QDockWidget
from PySide6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from typing import List
import matplotlib.figure
import matplotlib.colors as colors
import matplotlib.gridspec as gridspec
from PlotTreeItems import PlottableItem
from PlotModifiers import PlotModifier, ModifierLinecolor, ModifierLinestyle, ModifierColormap

import numpy as np

class ClickableCanvas(FigureCanvasQTAgg):
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
    def __init__(self, datacollector, tabitem):
        super().__init__()

        self.datacollector = datacollector
        self.figures: List[matplotlib.figure] = []
        # iterate through subtabs
        for i in range(tabitem.childCount()):
            #add subplots
            layout = QVBoxLayout()
            figure = matplotlib.figure.Figure(figsize=(5, 5))
            canvas = ClickableCanvas(figure)
            layout.addWidget(canvas)
            layout.addWidget(NavigationToolbar2QT(canvas))

            subplot_count = tabitem.child(i).childCount()
            if subplot_count == 1:
                ax = figure.subplots(subplot_count)
                ax = [ax]
            else:
                # region for the big central plot in gridspec
                gridspec = figure.add_gridspec(ncols=2, width_ratios=[3, 1])
                # region for the small side plots in sub_gridspec
                sub_gridspec = gridspec[1].subgridspec(ncols=1, nrows=subplot_count - 1)

                ax = [figure.add_subplot(gridspec[0])]
                # add small plots to axes list, so it can be accessed that way
                for idx in range(subplot_count-1):
                    ax.append(figure.add_subplot(sub_gridspec[idx]))

            # iterate through subplots
            for j in range(tabitem.child(i).childCount()):
                ax[j].set_title(str(tabitem.child(i).child(j).text(0)))
                # iterate through plottables and plot modifiers
                for k in range(tabitem.child(i).child(j).childCount()):
                    plottable_or_modifier_item = tabitem.child(i).child(j).child(k).data(0, 1)
                    if isinstance(plottable_or_modifier_item, PlottableItem):
                        plottable = plottable_or_modifier_item
                        dataset = self.datacollector.get_data_by_id(plottable.get_data_id())
                        if dataset.is_2d():

                            #collect a possible existing colormap plot modifier
                            colormap_modifier = ""
                            for ii in range(plottable.childCount()):
                                if isinstance(plottable.child(ii), ModifierColormap):
                                    colormap_modifier = plottable.child(ii).text(0).split('=')[1]
                            print("cm: ", colormap_modifier)
                            if colormap_modifier == "":
                                colormap_modifier = "jet"

                            x = dataset.get_x_data()
                            y = dataset.get_y_data()
                            y_fit = dataset.get_y_fit()
                            if plottable.type_num == 4:
                                cm = ax[j].pcolor(x[0], x[1], y,
                                                  norm=matplotlib.colors.LogNorm(vmin=np.min(y), vmax=np.max(y)),
                                                  cmap=colormap_modifier)
                            elif plottable.type_num == 5:
                                cm = ax[j].pcolor(x[0], x[1], y_fit,
                                                  norm=matplotlib.colors.LogNorm(vmin=np.min(y_fit), vmax=np.max(y_fit)),
                                                  cmap=colormap_modifier)
                            elif plottable.type_num == 6:
                                y_res = np.absolute(np.subtract(y_fit,y))
                                cm = ax[j].pcolor(x[0], x[1], y_res,
                                                  norm=matplotlib.colors.LogNorm(vmin=np.min(y_res), vmax=np.max(y_res)),
                                                  cmap=colormap_modifier)
                        else:
                            if plottable.type_num == 1: #data plot: log-log plot, show only data
                                ax[j].plot(dataset.get_x_data(), dataset.get_y_data())
                                ax[j].set_yscale('log')
                            elif plottable.type_num == 2: #fit plot: log-log plot, show fit and data curve
                                #ax[j].plot(dataset.get_x_data(), dataset.get_y_data())
                                ax[j].plot(dataset.get_x_data(), dataset.get_y_fit())
                                ax[j].set_yscale('log')
                            elif plottable.type_num == 3: #residual plot lin-log plot, show calc and show res only
                                ax[j].plot(dataset.get_x_data(), np.subtract(dataset.get_y_fit(), dataset.get_y_data()))

                            # iterate through plottable modifier, e.g. linecolor, linestyle
                            for l in range(plottable.childCount()):
                                plottable_modifier = plottable.child(l)
                                if isinstance(plottable_modifier.data(0, 1), ModifierLinecolor):
                                    ax[j].get_lines()[-1].set_color(plottable_modifier.text(0).split('=')[1])
                                elif isinstance(plottable_modifier.data(0, 1), ModifierLinestyle):
                                    ax[j].get_lines()[-1].set_linestyle(plottable_modifier.text(0).split('=')[1])

                    elif isinstance(plottable_or_modifier_item, PlotModifier):
                        plot_modifier = plottable_or_modifier_item
                        if isinstance(plot_modifier, ModifierColormap):
                            cmap = matplotlib.colormaps[plot_modifier.text(0).split('=')[1]]
                            n = len(ax[j].get_lines())
                            for m in range(n):
                                ax[j].get_lines()[m].set_color(cmap(m/(n-1)))

            figure.tight_layout()
            canvas_widget = QWidget()
            canvas_widget.setLayout(layout)

            dock_container = QMainWindow()
            dock_widget = QDockWidget()
            dock_widget.setWidget(canvas_widget)
            dock_container.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, dock_widget)

            self.addTab(dock_container, tabitem.child(i).text(0))
            self.figures.append(figure)

    def get_fitpage_index(self):
        return self.fitpage_index
