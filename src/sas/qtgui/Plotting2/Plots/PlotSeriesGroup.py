from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sas.qtgui.Plotting2.Plots.NotionalAxis import NotionalAxis
    from sas.qtgui.Plotting2.Plots.PlotSeries import PlotSeries

from sas.qtgui.Plotting2.PlotManagement import PlotRecord, PlotCommon


class PlotSeriesGroup(PlotCommon):
    def __init__(self):
        super().__init__()

    def parent(self) -> NotionalAxis:
        return PlotRecord.parent_axis(self.identifier)

    def children(self) -> list[PlotSeries]:
        return PlotRecord.child_series(self.identifier)