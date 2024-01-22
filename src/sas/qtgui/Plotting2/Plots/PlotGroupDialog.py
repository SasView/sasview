
from PySide6.QtWidgets import QWidget, QTabWidget, QVBoxLayout, QLayout, QDialog, QLabel

from sas.qtgui.Plotting2.Plots.NotionalPlot import NotionalPlot
from sas.qtgui.Plotting2.Plots.PlotGroup import PlotGroup

from sas.qtgui.Plotting2.PlotManagement import GroupIdentifier, Identifier, PlotRecord

class PlotGroupDialog(QWidget):
    """ Window that groups plots together"""

    def __init__(self, model_identifier: GroupIdentifier):

        super().__init__()

        self.modelIdentifier = model_identifier

        self.updateContents()


    def _createLayout(self) -> QLayout:
        """ Create the layout, if it's got more than one thing in it, use tabs, otherwise don't"""
        print("_create_layout")
        layout = QVBoxLayout()
        plot_group = PlotRecord.plot_group(self.modelIdentifier)

        if plot_group.size() == 0:
            layout.addWidget(QLabel("Empty"))

        elif plot_group.size() == 1:
            layout.addWidget(plot_group.plots()[0].plot_widget())

        else:
            tabs = QTabWidget()
            layout.addWidget(tabs)

            for plot in plot_group.plots():
                tabs.addTab(plot.plot_widget(), plot.plot_name)

        return layout

    def updateContents(self):

        new_layout = self._createLayout()
        self.setLayout(new_layout)