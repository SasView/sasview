from sas.qtgui.Plotting2.Plots.PlotCommon import PlotCommon
from sas.qtgui.Plotting2.Plots.NotionalAxis import NotionalAxis
from sas.qtgui.Plotting2.Plots.NotionalPlot import NotionalPlot
from sas.qtgui.Plotting2.PlotManagement import PlotRecord

class NotionalSubplot(PlotCommon[NotionalPlot, NotionalAxis]):
    def __init__(self):
        super().__init__()

    def parent(self) -> NotionalPlot:
        """ Get the parent plot group"""
        return PlotRecord.parentPlot(self.identifier)

    def children(self) -> list[NotionalAxis]:
        """ Get the subplots of this plot"""
        return PlotRecord.childAxes(self.identifier)


