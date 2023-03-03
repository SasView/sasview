from typing import Tuple, NamedTuple

from sasdata.dataloader.data_info import Data1D

from enum import Enum
from dataclasses import dataclass


class TransformedData(NamedTuple):
    """ Container for the data that is returned by the corfunc transform method"""
    gamma_1: Data1D
    gamma_3: Data1D
    idf: Data1D
    q_range: Tuple[float, float]


@dataclass
class SupplementaryParameters:
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
    z_range: Tuple[float, float]
    gamma_range: Tuple[float, float]

@dataclass
class ExtractedParameters:
    long_period: float
    interface_thickness: float
    hard_block_thickness: float
    soft_block_thickness: float
    core_thickness: float
    polydispersity_ryan: float
    polydispersity_stribeck: float
    local_crystallinity: float


class EntryListEnum(Enum):

    @classmethod
    def options(cls) -> str:
        return ", ".join([c.value for c in cls])


class TangentMethod(EntryListEnum):
    INFLECTION = 'inflection'
    HALF_MIN = 'half-min'


class LongPeriodMethod(EntryListEnum):
    MAX = 'max'
    DOUBLE_MIN = 'double-min'