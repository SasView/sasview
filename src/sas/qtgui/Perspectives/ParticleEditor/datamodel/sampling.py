from abc import ABC, abstractmethod
from typing import Tuple

from sas.qtgui.Perspectives.ParticleEditor.datamodel.types import VectorComponents3


class SpatialSample(ABC):
    """ Base class for spatial sampling methods"""
    def __init__(self, n_points, radius):
        self.n_points = n_points
        self.radius = radius

    @abstractmethod
    def __call__(self, size_hint: int) -> (VectorComponents3, VectorComponents3):
        """ Get pairs of points """

    @abstractmethod
    def bounding_surface_check_points(self) -> VectorComponents3:
        """ Points that are used to check that the SLD is consistent
        with the solvent SLD at the edge of the sampling space"""

    @abstractmethod
    def max_xyz(self):
        """ maximum distance between in points in X, Y and Z

        For non-oriented scattering
        """

    @abstractmethod
    def max_xy(self):
        """ Maximum distance between points in X,Y projection

        For Oriented 1D SANS
        """

    @abstractmethod
    def max_principal_axis(self):
        """ Maximum distance between points in any principal axis"""


    def max_x(self):
        """ Maximum distance between points in X projection

        For Oriented 2D SANS
        """
        return self.max_principal_axis()

    def max_y(self):
        """ Maximum distance between points in Y projection

        For Oriented 2D SANS
        """
        return self.max_principal_axis()

    def max_z(self):
        """ Maximum distance between points in Z projection

        For completeness
        """
        return self.max_principal_axis()

    def __repr__(self):
        return "%s(n=%i,r=%g)" % (self.__class__.__name__, self.n_points, self.radius)

    @abstractmethod
    def sample_volume(self) -> float:
        """ Volume of sample area """

