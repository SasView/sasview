""" Data structures and types for describing particles """

from typing import Protocol, Tuple, Optional
from dataclasses import dataclass

import numpy as np

# 3D vector output as lists of x,y and z components
VectorComponents3 = Tuple[np.ndarray, np.ndarray, np.ndarray]

class SLDFunction(Protocol):
    """ Type of functions that can represent SLD profiles"""
    def __call__(self, a: np.ndarray, b: np.ndarray, c: np.ndarray, **kwargs: float) -> np.ndarray: ...

class MagnetismFunction(Protocol):
    """ Type of functions that can represent magnetism profiles"""

    def __call__(self, a: np.ndarray, b: np.ndarray, c: np.ndarray, **kwargs: float) -> VectorComponents3: ...

class CoordinateSystemTransform(Protocol):
    """ Type of functions that can represent a coordinate transform"""

    def __call__(self, a: np.ndarray, b: np.ndarray, c: np.ndarray) -> VectorComponents3: ...

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
class Particle:
    """ Object containing the functions that define a particle"""
    sld: SLDDefinition
    magnetism: Optional[MagnetismDefinition]
