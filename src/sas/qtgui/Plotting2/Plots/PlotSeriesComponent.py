from sas.qtgui.Plotting2.Plots.PlotCommon import PlotCommon
from sas.qtgui.Plotting2.Plots.PlotSeries import PlotSeries
from sas.qtgui.Plotting2.PlotManagement import PlotRecord

class PlotSeriesComponent(PlotCommon[PlotSeries, None]):
    """ Components of a plot object: a plot might have errors or other things associated, one of these for each of those"""


    def __init__(self):
        super().__init__()

    def parent(self) -> PlotSeries:
        return PlotRecord.parent_series(self.identifier)

    def children(self) -> list[None]:
        return []





