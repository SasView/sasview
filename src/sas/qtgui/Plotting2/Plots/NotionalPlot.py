from PySide6.QtWidgets import QWidget

from PySide6.QtWidgets import QVBoxLayout, QLabel

from sas.qtgui.Plotting2.PlotManagement import PlotRecord
from sas.qtgui.Plotting2.Plots.PlotCommon import PlotCommon

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sas.qtgui.Plotting2.Plots.NotionalSubplot import NotionalSubplot
    from sas.qtgui.Plotting2.Plots.PlotRoot import PlotRoot

# Prototyping stuff
def fnumber():
    val = [0]
    def fun():
        val[0] += 1
        return val
    return fun
number = fnumber()

class TempPlotWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("Placeholder"))


### End prototyping stuff





class NotionalPlot(PlotCommon[PlotRoot, NotionalSubplot]):
    def __init__(self):
        super().__init__()

        self.plot_name = f"Plot {number()}"

    def parent(self) -> PlotRoot:
        """ Get the parent plot group"""
        return PlotRecord.root()

    def children(self) -> list[NotionalSubplot]:
        """ Get the subplots of this plot"""
        return PlotRecord.child_subplots(self.identifier)

    def plot_widget(self):
        return TempPlotWidget()
