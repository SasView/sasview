from sas.qtgui.Plotting2.PlotManagement import PlotRecord

from sas.qtgui.Plotting2.Plots.PlotCommon import PlotCommon
from sas.qtgui.Plotting2.Plots.NotionalSubplot import NotionalSubplot
from sas.qtgui.Plotting2.Plots.PlotGroup import PlotGroup


class NotionalPlot(PlotCommon[PlotGroup, NotionalSubplot]):
    def __init__(self):
        super().__init__()

    def parent(self) -> PlotGroup:
        """ Get the parent plot group"""
        return PlotRecord.parentPlotGroup(self.identifier)

    def children(self) -> list[NotionalSubplot]:
        """ Get the subplots of this plot"""
        return PlotRecord.childSubplots(self.identifier)


    