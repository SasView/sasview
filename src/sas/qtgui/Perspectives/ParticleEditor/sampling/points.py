from abc import ABC, abstractmethod
from sas.qtgui.Perspectives.ParticleEditor.datamodel.types import VectorComponents3

import math
import numpy as np

class PointGenerator(ABC):
    """ Base class for point generators """

    def __init__(self, radius: float, n_points: int):
        self.radius = radius
        self.n_points = n_points

    @abstractmethod
    def generate(self, start_index: int, end_index: int) -> VectorComponents3:
        """ Generate points from start_index up to end_index """


class GridPointGenerator(PointGenerator):
    def __init__(self, radius: float, desired_points: int):
        self.desired_points = desired_points
        self.n_points_per_axis = math.ceil(desired_points**(1/3))

        super().__init__(radius, n_points=self.n_points_per_axis**3)


    def generate(self, start_index: int, end_index: int) -> VectorComponents3:
        point_indices = np.arange(start_index, end_index)

        z_inds = point_indices % self.n_points_per_axis
        y_inds = (point_indices // self.n_points_per_axis) % self.n_points_per_axis
        x_inds = (point_indices // (self.n_points_per_axis**2)) % self.n_points_per_axis

        return (
            (((x_inds + 0.5) / self.n_points_per_axis) - 0.5) * self.radius,
            (((y_inds + 0.5) / self.n_points_per_axis) - 0.5) * self.radius,
            (((z_inds + 0.5) / self.n_points_per_axis) - 0.5) * self.radius)

class RandomPointGenerator(PointGenerator):
    pass


