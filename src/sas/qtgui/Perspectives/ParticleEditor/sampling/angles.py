
"""

Different methods for sampling the angular distribution of q vectors

A list of the different methods available can be found at the bottom of the code and needs to be updated if new ones
are added.


"""


from typing import List, Tuple
from abc import ABC, abstractmethod
import numpy as np

from sas.qtgui.Perspectives.ParticleEditor.sampling.geodesic import Geodesic, GeodesicDivisions


class AngularDistribution(ABC):
    """ Base class for angular distributions """

    @staticmethod
    @abstractmethod
    def name() -> str:
        """ Name of this distribution """


    @staticmethod
    @abstractmethod
    def parameters() -> List[Tuple[str, str, type]]:
        """ List of keyword arguments to constructor, names for GUI, and the type of value"""

    @abstractmethod
    def sample_points_and_weights(self) -> Tuple[np.ndarray, np.ndarray]:
        """ Get sample q vector directions and associated weights"""


class ZDelta(AngularDistribution):
    """ Perfectly oriented sample """

    @staticmethod
    def name():
        return "Oriented"

    def sample_points_and_weights(self):
        return np.array([[0.0, 0.0, -1.0]]), np.array([1.0])

    @staticmethod
    def parameters():
        return []

    def __repr__(self):
        return f"ZDelta()"


class Uniform(AngularDistribution):
    """ Spherically averaged sample """

    def __init__(self, geodesic_divisions: int):
        self.divisions = geodesic_divisions

    @staticmethod
    def name():
        return "Unoriented"

    def sample_points_and_weights(self) -> Tuple[np.ndarray, np.ndarray]:
        return Geodesic.by_divisions(self.divisions)

    @staticmethod
    def parameters() -> List[Tuple[str, str, type]]:
        return [("geodesic_divisions", "Angular Samples", GeodesicDivisions)]

    def __repr__(self):
        return f"Uniform({self.divisions})"


angular_sampling_methods = [ZDelta, Uniform]

