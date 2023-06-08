from typing import Optional, Tuple
from abc import ABC, abstractmethod
import numpy as np

from sas.qtgui.Perspectives.ParticleEditor.datamodel.sampling import SpatialSample


class RandomSample(SpatialSample):
    def __init__(self, n_points_desired: int, radius: float, seed: Optional[int] = None):
        super().__init__(n_points_desired, radius)
        self.seed = seed

    def start_location(self, size_hint: int):
        n_full = self._n_points_desired // size_hint
        n_rest = self._n_points_desired % size_hint

        for i in range(n_full):
            yield self.generate(size_hint)

        if n_rest > 0:
            yield self.generate(n_rest)

    def pairs(self, size_hint):
        n_full = self._n_points_desired // size_hint
        n_rest = self._n_points_desired % size_hint

        for i in range(n_full):
            yield self.generate(size_hint), self.generate(size_hint)

        if n_rest > 0:
            yield self.generate(n_rest), self.generate(n_rest)

    def singles(self, size_hint: int):
        n_full = self._n_points_desired // size_hint
        n_rest = self._n_points_desired % size_hint

        for i in range(n_full):
            yield self.generate(size_hint)

        if n_rest > 0:
            yield self.generate(n_rest)


    @abstractmethod
    def generate(self, n):
        """ Generate n random points"""


    def __repr__(self):
        return "%s(n=%i,r=%g,seed=%s)" % (self.__class__.__name__, self._n_points_desired, self.radius, str(self.seed))


class RandomSampleSphere(RandomSample):
    """ Rejection Random Sampler for a sphere with a given radius """

    def _calculate_n_actual(self) -> int:
        return self._n_points_desired

    def sampling_details(self) -> str:
        return ""

    def sample_volume(self) -> float:
        return (4*np.pi/3)*(self.radius**3)

    def generate(self, n):
        # Sample within a sphere

        # A sphere will occupy pi/6 of a cube, which is 0.5236 ish
        # With rejection sampling we need to oversample by about a factor of 2


        target_n = n

        output_data = []
        while target_n > 0:
            xyz = np.random.random((int(1.91 * target_n)+1, 3)) - 0.5

            indices = np.sum(xyz**2, axis=1) <= 0.25

            xyz = xyz[indices, :]

            if xyz.shape[0] > target_n:
                output_data.append(xyz[:target_n, :])
                target_n = 0
            else:
                output_data.append(xyz)
                target_n -= xyz.shape[0]

        xyz = np.concatenate(output_data, axis=0) * (2*self.radius)

        return xyz[:,0], xyz[:,1], xyz[:,2]


class RandomSampleCube(RandomSample):
    """ Randomly sample points in a 2r x 2r x 2r cube centred at the origin"""

    def _calculate_n_actual(self) -> int:
        return self._n_points_desired

    def sampling_details(self) -> str:
        return ""

    def sample_volume(self) -> float:
        return 8*(self.radius**3)

    def generate(self, n):
        # Sample within a cube

        xyz = (np.random.random((n, 3)) - 0.5)*(2*self.radius)

        return xyz[:,0], xyz[:,1], xyz[:,2]
