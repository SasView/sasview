from typing import Union, Generic, TypeVar
from abc import ABC, abstractmethod
from sas.qtgui.Plotting2.PlotManagement import PlotRecord, Identifier

from sas.qtgui.Plotting2.Plots.FormattingOptions import FormattingOptions

T = TypeVar("T")
S = TypeVar("S")



class PlotCommon(ABC, Generic[S, T]):
    def __init__(self):
        self._identifier = PlotRecord.new_identifier()
        self._formatting_options = FormattingOptions()

    @property
    def identifier(self) -> Identifier:
        """ Unique ID for this object"""
        return self._identifier

    def parent(self) -> S:
        """ Get the parent object """

    def children(self) -> list[T]:
        """ Get the children of this object """

    def formatting_options(self):
        return self._formatting_options.up

