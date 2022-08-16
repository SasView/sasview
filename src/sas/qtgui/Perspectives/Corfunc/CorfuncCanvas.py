from __future__ import annotations

from abc import ABCMeta, abstractmethod

from typing import Optional, Union, List, Iterable, TYPE_CHECKING

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# TODO: Make not crazy
from sas.qtgui.Plotting.PlotterData import Data1D as Data1DVersion1
from sas.sascalc.dataloader.data_info import Data1D as Data1DVersion2
from sasmodels.data import Data1D as Data1DVersion3
Data1D = (Data1DVersion1, Data1DVersion2, Data1DVersion3)
Data1DType = Union[Data1DVersion1, Data1DVersion2, Data1DVersion3]

if TYPE_CHECKING:
    from sas.qtgui.Perspectives.Corfunc.CorfuncPerspective import CorfuncWindow


class CorfuncCanvasMeta(type(FigureCanvas), ABCMeta):
    """ Metaclass for both ABC and matplotlib figure

    This is needed to enable the mixin of CorfuncCanvas
    """


class CorfuncCanvas(FigureCanvas, metaclass=CorfuncCanvasMeta):
    """ Base class for the canvases in corfunc"""

    def __init__(self, parent: CorfuncWindow, width=5, height=4, dpi=100):
        self.parent = parent
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)

        FigureCanvas.__init__(self, self.fig)

        self._data: Optional[List[Data1D]] = None

    def clear(self):
        """ Remove data from plots"""
        self._data = None

    @abstractmethod
    def draw_data(self):
        pass

    @property
    def data(self) -> Optional[List[Data1D]]:
        """ The data currently shown by the plots """
        return self._data

    @data.setter
    def data(self, target_data: Optional[Union[Data1DType, Iterable[Data1DType]]]):
        # I'm not 100% sure this is good practice, but it will make things cleaner in the short term
        if target_data is None:
            self._data = None
        elif isinstance(target_data, Data1D):
            self._data = [target_data]
        else:
            self._data = list(target_data)

        self.draw_data()