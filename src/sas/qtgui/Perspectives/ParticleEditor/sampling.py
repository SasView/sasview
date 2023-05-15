from typing import Optional
from abc import ABC, abstractmethod
import numpy as np


class SpatialSample(ABC):
    """ Base class for spatial sampling methods"""
    def __init__(self, n_points_desired, radius):
        self._n_points_desired = n_points_desired
        self.radius = radius

    @abstractmethod
    def _calculate_n_actual(self) -> int:
        """ Calculate the actual number of sample points, based on the desired number of points"""

    @abstractmethod
    def sampling_details(self) -> str:
        """ A string describing the details of the sample points """

    def __repr__(self):
        return "%s(n=%i,r=%g)" % (self.__class__.__name__, self._n_points_desired, self.radius)

    @abstractmethod
    def __call__(self) -> (np.ndarray, np.ndarray, np.ndarray):
        """ Get the sample points """


class RandomSample(SpatialSample):
    def __init__(self, n_points_desired: int, radius: float, seed: Optional[int] = None):
        super().__init__(n_points_desired, radius)
        self.seed = seed

    def __repr__(self):
        return "%s(n=%i,r=%g,seed=%s)" % (self.__class__.__name__, self._n_points_desired, self.radius, str(self.seed))


class RandomSampleSphere(RandomSample):
    """ Rejection Random Sampler for a sphere with a given radius """

    def _calculate_n_actual(self) -> int:
        return self._n_points_desired

    def sampling_details(self) -> str:
        return ""

    def __call__(self):
        # Sample within a sphere

        # A sphere will occupy pi/6 of a cube, which is 0.5236 ish
        # With rejection sampling we need to oversample by about a factor of 2


        target_n = self._n_points_desired

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

    def __call__(self):
        # Sample within a cube

        xyz = np.random.random((self._n_points_desired, 3))*2 - 1.0

        return xyz[:,0], xyz[:,1], xyz[:,2]


class GridSample(SpatialSample):
    def _calculate_n_actual(self) -> int:
        side_length = int(np.ceil(np.cbrt(self._n_points_desired)))
        return side_length**3

    def sampling_details(self) -> str:
        side_length =  int(np.ceil(np.cbrt(self._n_points_desired)))
        return "%ix%ix%i = %i"%(side_length, side_length, side_length, side_length**3)

    def __call__(self):
        side_length = int(np.ceil(np.cbrt(self._n_points_desired)))
        n = side_length**3

        # We want the sampling to happen in the centre of each voxel
        # get points at edges and centres, then skip ever other one not the edge
        sample_values = np.linspace(-self.radius, self.radius, 2*side_length+1)[1::2]

        x, y, z = np.meshgrid(sample_values, sample_values, sample_values)

        return x.reshape((n, )), y.reshape((n, )), z.reshape((n, ))


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


if __name__ == "__main__":
    sampler = RandomSampleSphere(n_points_desired=100, radius=1)
    for i in range(5):
        x,y,z = sampler()
        # print(x**2 + y**2 + z**2)
        print(len(x))