from sas.qtgui.Plotting2.Plots.PlotCommon import PlotCommon
from sas.qtgui.Plotting2.Plots.NotionalAxis import NotionalAxis
from sas.qtgui.Plotting2.Plots.PlotSeries import PlotSeries
from sas.qtgui.Plotting2.PlotManagement import PlotRecord

class PlotSeriesGroup(PlotCommon[NotionalAxis, PlotSeries]):
    def __init__(self):
        super().__init__()

    def parent(self) -> NotionalAxis:
        return PlotRecord.parent_axis(self.identifier)

    def children(self) -> list[PlotSeries]:
        return PlotRecord.child_series(self.identifier)