
from PySide6.QtWidgets import QWidget, QTabWidget, QVBoxLayout, QLayout

from sas.qtgui.Plotting2.Plots.NotionalPlot import NotionalPlot
from sas.qtgui.Plotting2.Plots.PlotGroup import PlotGroup

from sas.qtgui.Plotting2.PlotManagement import GroupIdentifier, Identifier, PlotRecord

class PlotGroupDialog(QWidget):
    """ Window that groups plots together"""

    def __init__(self, modelIdentifier: GroupIdentifier):

        super().__init__()

        self.modelIdentifier = modelIdentifier
        self.tabWidget = QTabWidget()

        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.tabWidget)
        self.setLayout(self.main_layout)

    def _createLayout(self) -> QLayout:
        """ Create the layout, if it's got more than one thing in it, use tabs, otherwise don't"""
        layout = QVBoxLayout()
        plot_group = PlotRecord.plot_group(self.modelIdentifier)

        if plot_group.size() > 1:
            layout.addWidget(plot_group.plots()[0].plot_widget())
        else:
            tabs = QTabWidget()
            layout.addWidget(tabs)

            for plot in plot_group.plots():
                tabs.addTab(plot, plot.plot_name)

        return layout

    def updateContents(self):

        new_layout = self._createLayout()
        self.setLayout(new_layout)