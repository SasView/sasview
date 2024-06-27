from PySide6.QtWidgets import QWidget, QTabWidget, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
from typing import List
import matplotlib.figure
from PlotTreeItems import PlottableItem
from PlotModifiers import PlotModifier, ModifierLinecolor, ModifierLinestyle, ModifierColormap

import numpy as np

class SubTabs(QTabWidget):
    def __init__(self, datacollector, tabitem):
        super().__init__()

        self.datacollector = datacollector
        self.figures: List[matplotlib.figure] = []

        # iterate through subtabs
        for i in range(tabitem.childCount()):
            #add subtabs
            subtab_widget = QWidget()
            subtab = self.addTab(QWidget(), tabitem.child(i).text(0))

            #add subplots
            layout = QVBoxLayout()
            figure = matplotlib.figure.Figure(figsize=(5, 5))
            canvas = FigureCanvasQTAgg(figure)
            layout.addWidget(canvas)
            layout.addWidget(NavigationToolbar2QT(canvas))

            subplot_count = tabitem.child(i).childCount()
            ax = figure.subplots(subplot_count)
            if subplot_count <= 1:
                ax = [ax]
            # iterate through subplots
            for j in range(subplot_count):
                ax[j].set_title(str(tabitem.child(i).child(j).text(0)))
                ax[j].set_xscale('log')
                # iterate through plottables and plot modifiers
                for k in range(tabitem.child(i).child(j).childCount()):
                    plottable_or_modifier_item = tabitem.child(i).child(j).child(k).data(0, 1)
                    if isinstance(plottable_or_modifier_item, PlottableItem):
                        plottable = plottable_or_modifier_item
                        dataset = self.datacollector.get_data_id(plottable_or_modifier_item.get_data_id())
                        if dataset.is_2d():
                            #plot 2d data. and modifier for linestyles or linecolors make no sense for 2d objects
                            pass
                        else:
                            if plottable.type_num == 1: #data plot: log-log plot, show only data
                                ax[j].plot(dataset.get_x_data(), dataset.get_y_data())
                                ax[j].set_yscale('log')
                            elif plottable.type_num == 2: #fit plot: log-log plot, show fit and data curve
                                ax[j].plot(dataset.get_x_data(), dataset.get_y_data())
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
            self.widget(i).setLayout(layout)
            self.figures.append(figure)

    def get_fitpage_index(self):
        return self.fitpage_index
