from typing import NamedTuple, List

from sas.qtgui.Plotting.PlotterBase import PlotterBase

class ReportData(NamedTuple):
    html: str
    text: str
    images: List[PlotterBase]