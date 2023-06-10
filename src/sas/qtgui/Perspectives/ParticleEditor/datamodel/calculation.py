from typing import Optional, Callable, Tuple, Protocol
import numpy as np
from enum import Enum
from dataclasses import dataclass

from sas.qtgui.Perspectives.ParticleEditor.datamodel.sampling import SpatialSample
from sas.qtgui.Perspectives.ParticleEditor.datamodel.types import (
    SLDFunction, MagnetismFunction, CoordinateSystemTransform)


class QSample:
    """ Representation of Q Space sampling """
    def __init__(self, start, end, n_points, is_log):
        self.start = start
        self.end = end
        self.n_points = n_points
        self.is_log = is_log

    def __repr__(self):
        return f"QSampling({self.start}, {self.end}, n={self.n_points}, is_log={self.is_log})"

    def __call__(self):
        if self.is_log:
            start_log = np.log(self.start)
            end_log = np.log(self.end)
            return np.exp(np.linspace(start_log, end_log, self.n_points))
        else:
            return np.linspace(self.start, self.end, self.n_points)


class ZSample:
    """ Sample of correlation space """

    def __init__(self, start, end, n_points):
        self.start = start
        self.end = end
        self.n_points = n_points

    def __repr__(self):
        return f"QSampling({self.start}, {self.end}, n={self.n_points})"

    def __call__(self):
        return np.linspace(self.start, self.end, self.n_points)


@dataclass
class OutputOptions:
    radial_distribution: Optional = None
    radial_correlation: Optional = None
    p_of_r: Optional = None
    q_space: Optional[QSample] = None
    q_space_2d: Optional[QSample] = None
    sesans: Optional[ZSample] = None
    sesans_2d: Optional[ZSample] = None


class OrientationalDistribution(Enum):
    FIXED = "Fixed"
    UNORIENTED = "Unoriented"


@dataclass
class SLDDefinition:
    """ Definition of the SLD scalar field"""
    sld_function: SLDFunction
    to_cartesian_conversion: CoordinateSystemTransform


@dataclass
class MagnetismDefinition:
    """ Definition of the magnetism vector fields"""
    magnetism_function: MagnetismFunction
    to_cartesian_conversion: CoordinateSystemTransform


@dataclass
class ParticleDefinition:
    """ Object containing the functions that define a particle"""
    sld: SLDDefinition
    magnetism: Optional[MagnetismDefinition]


@dataclass
class ScatteringCalculation:
    """ Specification for a scattering calculation """
    output_options: OutputOptions
    orientation: OrientationalDistribution
    spatial_sampling_method: SpatialSample
    particle_definition: ParticleDefinition
    magnetism_vector: Optional[np.ndarray]
    seed: Optional[int]
    bounding_surface_sld_check: bool
    sample_chunk_size_hint: int = 100_000


@dataclass
class ScatteringOutput:
    output_type: OutputOptions
    q_sampling_method: QSample
    spatial_sampling_method: SpatialSample
    intensity_data: np.ndarray
    r_values: Optional[np.ndarray]
    realspace_intensity: Optional[np.ndarray]
    calculation_time: float
    seed_used: int


