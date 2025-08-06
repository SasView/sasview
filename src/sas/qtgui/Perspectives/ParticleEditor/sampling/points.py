"""

Instances of the spatial sampler



"""

import math
from collections import defaultdict

import numpy as np

from sas.qtgui.Perspectives.ParticleEditor.datamodel.calculation import SpatialDistribution
from sas.qtgui.Perspectives.ParticleEditor.datamodel.types import VectorComponents3


class BoundedByCube(SpatialDistribution):

    _boundary_base_points = np.array([
        [-1, 0, 0],
        [ 1, 0, 0],
        [ 0,-1, 0],
        [ 0, 1, 0],
        [ 0, 0,-1],
        [ 0, 0, 1],
        [ 1, 1, 1],
        [ 1, 1,-1],
        [ 1,-1, 1],
        [ 1,-1,-1],
        [-1, 1, 1],
        [-1, 1,-1],
        [-1,-1, 1],
        [-1,-1,-1],
    ], dtype=float)
    def _bounding_surface_check_points(self) -> VectorComponents3:
        return BoundedByCube._boundary_base_points * self.radius


class Grid(BoundedByCube):
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



class RandomCube(BoundedByCube):
    """ Generate random points in a cube with side length 2*radius"""
    def __init__(self, radius: float, desired_points: int, seed=None):

        super().__init__(radius, n_points=desired_points, n_desired_points=desired_points)

        self._seed_rng = np.random.default_rng(seed)

        # Accessing this will generate random seeds if they don't exist and store them to be accessed if they do
        self.seeds = defaultdict(lambda: self._seed_rng.integers(0, 0x7fff_ffff_ffff_ffff))

    def allows_bootstrap(self) -> bool:
        return True

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


class PointGeneratorStepper:
    """ Generate batches of step_size points from a PointGenerator instance
    """

    def __init__(self, point_generator: SpatialDistribution, step_size: int, bootstrap_sections: int):
        self.point_generator = point_generator
        self.step_size = step_size

    def _iterator(self):
        n_sections, remainder = divmod(self.point_generator.n_points, self.step_size)

        for i in range(n_sections):
            yield self.point_generator.generate(i*self.step_size, (i+1)*self.step_size)

        if remainder != 0:
            yield self.point_generator.generate(n_sections*self.step_size, self.point_generator.n_points)

    def __iter__(self):
        return self._iterator()

