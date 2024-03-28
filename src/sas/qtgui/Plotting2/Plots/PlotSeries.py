from __future__ import annotations

from sas.qtgui.Plotting2.Plots.PlotSeriesGroup import PlotSeriesGroup
from sas.qtgui.Plotting2.Plots.PlotSeriesComponent import PlotSeriesComponent
from sas.qtgui.Plotting2.PlotManagement import PlotRecord, PlotCommon

class PlotSeries(PlotCommon):
    def children(self) -> list[PlotSeriesComponent]:
        return PlotRecord.child_series_component(self.identifier)

    def parent(self) -> PlotSeriesGroup:
        return PlotRecord.parent_series_group(self.identifier)