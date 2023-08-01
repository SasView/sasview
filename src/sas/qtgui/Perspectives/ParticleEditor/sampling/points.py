from typing import Dict

from abc import ABC, abstractmethod
from sas.qtgui.Perspectives.ParticleEditor.datamodel.types import VectorComponents3

import math
import numpy as np

from collections import defaultdict


class PointGenerator(ABC):
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


class GridPointGenerator(PointGenerator):
    """ Generate points on a grid within a cube with side length 2*radius """
    def __init__(self, radius: float, desired_points: int):
        self.desired_points = desired_points
        self.n_points_per_axis = math.ceil(desired_points**(1/3))

        super().__init__(radius, n_points=self.n_points_per_axis**3, n_desired_points=desired_points)

    @property
    def info(self):
        return f"{self.n_points_per_axis}x{self.n_points_per_axis}x{self.n_points_per_axis} = {self.n_points}"


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
    """ Generate random points in a cube with side length 2*radius"""
    def __init__(self, radius: float, desired_points: int, seed=None):

        super().__init__(radius, n_points=desired_points, n_desired_points=desired_points)

        self._seed_rng = np.random.default_rng(seed)

        # Accessing this will generate random seeds if they don't exist and store them to be accessed if they do
        self.seeds = defaultdict(lambda: self._seed_rng.integers(0, 0x7fff_ffff_ffff_ffff))

    def generate(self, start_index: int, end_index: int) -> VectorComponents3:
        # This method of tracking seeds only works if the same start_indices are used each time points
        # in a region are requested - i.e. if they're chunks form a grid

        n_points = end_index - start_index
        seed = self.seeds[start_index]

        rng = np.random.default_rng(seed=seed)

        xyz = rng.random(size=(n_points, 3))

        xyz -= 0.5
        xyz *= 2*self.radius

        return xyz[:, 0], xyz[:, 1], xyz[:, 2]


