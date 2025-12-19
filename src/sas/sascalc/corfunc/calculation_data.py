from dataclasses import dataclass
from enum import Enum
from typing import Generic, TypeVar

from sasdata.dataloader.data_info import Data1D

T = TypeVar("T")

class Fittable(Generic[T]):
    """ Container for parameters that can be fitted by the corfunc perspective"""
    def __init__(self, data: T | None = None, allow_fit: bool = True):
        self.data: T | None = data
        self.allow_fit: bool = allow_fit

    def clear(self):
        self.data = None

    def __repr__(self):
        return f"{self.__class__.__name__}({self.data}, {self.allow_fit})"

@dataclass
class TransformedData:
    """ Container for the data that is returned by the corfunc transform method"""
    gamma_1: Data1D
    gamma_3: Data1D
    idf: Data1D


@dataclass
class SupplementaryParameters:
    """ Parameters used for drawing the diagram """
    tangent_point_z: float
    tangent_point_gamma: float
    tangent_gradient: float
    first_minimum_z: float
    first_minimum_gamma: float
    first_maximum_z: float
    first_maximum_gamma: float
    hard_block_z: float
    hard_block_gamma: float
    interface_z: float
    core_z: float
    z_range: tuple[float, float]
    gamma_range: tuple[float, float]

@dataclass
class LamellarParameters:
    """ Lamellar parameters"""
    long_period: float
    interface_thickness: float
    hard_block_thickness: float
    soft_block_thickness: float
    core_thickness: float
    polydispersity_ryan: float
    polydispersity_stribeck: float
    local_crystallinity: float

@dataclass
class GuinierData:
    """ Parameters for a Guinier model """
    A: float
    B: float

@dataclass
class PorodData:
    """ Parameters for a Porod model """
    K: float
    sigma: float


class EntryListEnum(Enum):
    """ Enum with a helper method that gives a string containing all the options"""
    @classmethod
    def options(cls) -> str:
        return ", ".join([c.value for c in cls])


class TangentMethod(EntryListEnum):
    """ Methods for estimating the tangent """
    INFLECTION = 'inflection'
    HALF_MIN = 'half-min'


class LongPeriodMethod(EntryListEnum):
    """ Methods for estimating the long period """
    MAX = 'max'
    DOUBLE_MIN = 'double-min'
