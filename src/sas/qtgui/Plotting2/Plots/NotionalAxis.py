from sas.qtgui.Plotting2.Plots.PlotCommon import PlotCommon
from sas.qtgui.Plotting2.PlotManagement import PlotRecord

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sas.qtgui.Plotting2.Plots.PlotSeriesGroup import PlotSeriesGroup
    from sas.qtgui.Plotting2.Plots.NotionalSubplot import NotionalSubplot


class NotionalAxis(PlotCommon[PlotSeriesGroup, NotionalSubplot]):
    def __init__(self):
        super().__init__()

    def children(self) -> list[PlotSeriesGroup]:
        return PlotRecord.child_series_group(self.identifier)

    def parent(self) -> NotionalSubplot:
        return PlotRecord.parent_subplot(self.identifier)