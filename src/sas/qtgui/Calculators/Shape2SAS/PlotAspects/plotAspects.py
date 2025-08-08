from dataclasses import dataclass

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtWidgets import QSizePolicy


class Canvas(FigureCanvasQTAgg):
    def __init__(self, parent=None):
        self.fig = Figure()
        FigureCanvasQTAgg.__init__(self, self.fig)
        self.setParent(parent)
        Canvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        Canvas.updateGeometry(self)

@dataclass
class ViewerPlotDesign:
    """Values affecting the illustrative aspect of Viewer"""
    colour: list[str] | None


