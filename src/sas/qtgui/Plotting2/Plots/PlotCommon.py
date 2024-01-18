from typing import Union, Generic, TypeVar
from abc import ABC, abstractmethod
from sas.qtgui.Plotting2.PlotManagement import PlotRecord, Identifier


T = TypeVar("T")
S = TypeVar("S")

class PlotCommon(ABC, Generic[S, T]):
    def __init__(self):
        self._identifier = PlotRecord.new_identifier()
        self._base_color = None

    @property
    def identifier(self) -> Identifier:
        """ Unique ID for this object"""
        return self._identifier

    def parent(self) -> S:
        """ Get the parent object """

    def children(self) -> list[T]:
        """ Get the children of this object """

    def set_color(self, color: Union[str, tuple[float, float, float]]):
        """ Set the colour of plot lines within this object """
        pass

    def set_marker(self, marker: str):
        """ Set the marker type for plot lines within this object"""
        pass

