from typing import Protocol

import numpy as np

# 3D vector output as numpy arrays
VectorComponents3 = tuple[np.ndarray, np.ndarray, np.ndarray]


class SLDFunction(Protocol):
    """ Type of functions that can represent SLD profiles"""
    def __call__(self, a: np.ndarray, b: np.ndarray, c: np.ndarray, **kwargs: float) -> np.ndarray: ...


class MagnetismFunction(Protocol):
    """ Type of functions that can represent magnetism profiles"""

    def __call__(self, a: np.ndarray, b: np.ndarray, c: np.ndarray, **kwargs: float) -> VectorComponents3: ...


class CoordinateSystemTransform(Protocol):
    """ Type of functions that can represent a coordinate transform"""

    def __call__(self, x: np.ndarray, y: np.ndarray, z: np.ndarray) -> VectorComponents3: ...
