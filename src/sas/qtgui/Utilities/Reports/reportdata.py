from typing import NamedTuple, List

from sas.qtgui.Plotting.PlotterBase import PlotterBase

class ReportData(NamedTuple):
    html: str = "<html><body>No Data</body></html>"
    text: str = "No data"
    images: List[PlotterBase] = []