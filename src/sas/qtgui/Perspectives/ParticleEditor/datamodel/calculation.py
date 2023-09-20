from typing import Optional, Callable, Protocol
import numpy as np
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod

from sas.qtgui.Perspectives.ParticleEditor.datamodel.types import (
    SLDFunction, MagnetismFunction, CoordinateSystemTransform)
from sas.qtgui.Perspectives.ParticleEditor.datamodel.parameters import CalculationParameters

from sas.qtgui.Perspectives.ParticleEditor.datamodel.types import VectorComponents3


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


class SpatialDistribution(ABC):
    """ Base class for point generators """

    def __init__(self, radius: float, n_points: int, n_desired_points):
        self.radius = radius
        self.n_desired_points = n_desired_points
        self.n_points = n_points

    @property
    def info(self):
        """ Information to be displayed in the settings window next to the point number input """
        return ""

    @abstractmethod
    def generate(self, start_index: int, end_index: int) -> VectorComponents3:
        """ Generate points from start_index up to end_index """

    @abstractmethod
    def _bounding_surface_check_points(self) -> np.ndarray:
        """ Points used to check that the SLD/magnetism vector are zero outside the sample space"""

    def bounding_surface_check_points(self) -> VectorComponents3:
        pts = self._bounding_surface_check_points()
        return pts[:, 0], pts[:, 1], pts[:, 2]

class AngularDistribution(ABC):
    """ Base class for angular distributions """

    @property
    @abstractmethod
    def n_points(self) -> int:
        """ Number of sample points """

    @staticmethod
    @abstractmethod
    def name() -> str:
        """ Name of this distribution """


    @staticmethod
    @abstractmethod
    def parameters() -> list[tuple[str, str, type]]:
        """ List of keyword arguments to constructor, names for GUI, and the type of value"""

    @abstractmethod
    def sample_points_and_weights(self) -> tuple[np.ndarray, np.ndarray]:
        """ Get sample q vector directions and associated weights"""


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
    q_sampling: QSample
    angular_sampling: AngularDistribution
    spatial_sampling_method: SpatialDistribution
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
class QSpaceScattering:
    abscissa: QSample
    ordinate: np.ndarray

@dataclass
class RealSpaceScattering:
    abscissa: np.ndarray
    ordinate: np.ndarray


@dataclass
class ScatteringOutput:
    q_space: Optional[QSpaceScattering]
    calculation_time: float
    seed_used: Optional[int]


