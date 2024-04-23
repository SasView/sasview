from __future__ import annotations


from sas.qtgui.Plotting2.PlotManagement import PlotRecord, PlotCommon

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sas.qtgui.Plotting2.Plots.PlotSeriesGroup import PlotSeriesGroup
    from sas.qtgui.Plotting2.Plots.NotionalSubplot import NotionalSubplot


class NotionalAxis(PlotCommon):
    def __init__(self):
        super().__init__()

    def children(self) -> list[PlotSeriesGroup]:
        return PlotRecord.child_series_group(self.identifier)

    def parent(self) -> NotionalSubplot:
        return PlotRecord.parent_subplot(self.identifier)