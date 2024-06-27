from PySide6.QtWidgets import QTabWidget, QWidget, QVBoxLayout
from SubTabs import SubTabs

class PlotWidget(QTabWidget):
    def __init__(self, datacollector):
        super().__init__()
        self.setWindowTitle("Plot Widget")
        self.setMinimumSize(600, 600)

        self.datacollector = datacollector

    def widget(self, index) -> SubTabs:
        return super().widget(index)

    def redrawTab(self, tabitem):
        # check if the tab is already existing.
        # if it is not existing: create it. otherwise: recalculate the tab
        fitpage_index = tabitem.get_fitpage_index()
        plot_index = self.datacollector.get_data_fp(fitpage_index).get_plotpage_index()
        if plot_index == -1:
            self.datacollector.set_plot_index(fitpage_index, self.count())
            self.addTab(SubTabs(self.datacollector, tabitem), "Plot for FitPage " + str(fitpage_index))
        else:
            self.removeTab(plot_index)
            self.insertTab(plot_index, SubTabs(self.datacollector, tabitem),
                           "Plot for FitPage " + str(fitpage_index))



    def get_subtabs(self, fitpage_index):
        for i in range(self.count()):
            if fitpage_index == self.widget(i).fitpage_index:
                return self.widget(i)

    def get_figures(self, fitpage_index):
        for i in range(self.count()):
            if fitpage_index == self.widget(i).fitpage_index:
                return self.widget(i).figures





