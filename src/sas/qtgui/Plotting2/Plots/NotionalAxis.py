from sas.qtgui.Plotting2.Plots.PlotCommon import PlotCommon
from sas.qtgui.Plotting2.PlotManagement import PlotRecord

from sas.qtgui.Plotting2.Plots.PlotSeriesGroup import PlotSeriesGroup
from sas.qtgui.Plotting2.Plots.NotionalSubplot import NotionalSubplot


class NotionalAxis(PlotCommon[PlotSeriesGroup, NotionalSubplot]):
    def __init__(self):
        super().__init__()

    def children(self) -> PlotSeriesGroup:
        PlotRecord.getChildSeriesGroup(self._identifier)

    def parent(self) -> NotionalSubplot:
        pass