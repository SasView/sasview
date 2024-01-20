from sas.qtgui.Plotting2.Plots.PlotCommon import PlotCommon
from sas.qtgui.Plotting2.PlotManagement import PlotRecord

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sas.qtgui.Plotting2.Plots.NotionalAxis import NotionalAxis
    from sas.qtgui.Plotting2.Plots.NotionalPlot import NotionalPlot


class NotionalSubplot(PlotCommon[NotionalPlot, NotionalAxis]):
    def __init__(self):
        super().__init__()

    def parent(self) -> NotionalPlot:
        """ Get the parent plot group"""
        return PlotRecord.parent_plot(self.identifier)

    def children(self) -> list[NotionalAxis]:
        """ Get the subplots of this plot"""
        return PlotRecord.child_axes(self.identifier)


