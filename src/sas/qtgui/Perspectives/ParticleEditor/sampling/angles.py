"""

Different methods for sampling the angular distribution of q vectors

A list of the different methods available can be found at the bottom of the code and needs to be updated if new ones
are added.


"""

import numpy as np

from sas.qtgui.Perspectives.ParticleEditor.datamodel.calculation import AngularDistribution
from sas.qtgui.Perspectives.ParticleEditor.sampling.geodesic import Geodesic, GeodesicDivisions


class ZDelta(AngularDistribution):
    """ Perfectly oriented sample """

    @staticmethod
    def name():
        return "Oriented"

    def sample_points_and_weights(self):
        return np.array([[0.0, 0.0, -1.0]]), np.array([1.0])

    @property
    def n_points(self):
        return 1

    @staticmethod
    def parameters():
        return []

    def __repr__(self):
        return "ZDelta()"


class Uniform(AngularDistribution):
    """ Spherically averaged sample """

    def __init__(self, geodesic_divisions: int):
        self.divisions = geodesic_divisions
        self._n_points = Geodesic.points_for_division_amount(geodesic_divisions)

    @staticmethod
    def name():
        return "Unoriented"

    def sample_points_and_weights(self) -> tuple[np.ndarray, np.ndarray]:
        return Geodesic.by_divisions(self.divisions)

    @property
    def n_points(self) -> int:
        return self._n_points

    @staticmethod
    def parameters() -> list[tuple[str, str, type]]:
        return [("geodesic_divisions", "Angular Samples", GeodesicDivisions)]

    def __repr__(self):
        return f"Uniform({self.divisions})"


angular_sampling_methods = [ZDelta, Uniform]

