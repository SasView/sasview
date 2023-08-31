from typing import Optional, Callable, Tuple, Protocol, List
import numpy as np
from enum import Enum
from dataclasses import dataclass

from sas.qtgui.Perspectives.ParticleEditor.datamodel.types import (
    SLDFunction, MagnetismFunction, CoordinateSystemTransform)
from sas.qtgui.Perspectives.ParticleEditor.datamodel.parameters import CalculationParameters


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
    """ Options """
    radial_distribution: bool # Create a radial distribution function from the origin
    sampling_distributions: bool # Return the sampling distributions used in the calculation
    realspace: bool # Return realspace data
    q_space: Optional[QSample] = None
    q_space_2d: Optional[QSample] = None
    sesans: Optional[ZSample] = None


class OrientationalDistribution(Enum):
    """ Types of orientation supported """
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
    parameter_settings: CalculationParameters
    polarisation_vector: Optional[np.ndarray]
    seed: Optional[int]
    bounding_surface_sld_check: bool
    bin_count = 1_000
    sample_chunk_size_hint: int = 100_000


@dataclass
class SamplingDistribution:
    name: str
    bin_edges: np.ndarray
    counts: np.ndarray

@dataclass
class QPlotData:
    abscissa: QSample
    ordinate: np.ndarray

@dataclass
class RealPlotData:
    abscissa: np.ndarray
    ordinate: np.ndarray


@dataclass
class QSpaceCalcDatum:
    q_space_data: QPlotData
    correlation_data: Optional[RealPlotData]

@dataclass
class ScatteringOutput:
    radial_distribution: Optional[Tuple[np.ndarray, np.ndarray]]
    q_space: Optional[QSpaceCalcDatum]
    q_space_2d: Optional[QSpaceCalcDatum]
    sesans: Optional[RealPlotData]
    sampling_distributions: List[SamplingDistribution]
    calculation_time: float
    seed_used: int


