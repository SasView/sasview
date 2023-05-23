from typing import Optional, Tuple
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

    @abstractmethod
    def pairs(self, int) -> Tuple[Tuple[np.ndarray, np.ndarray, np.ndarray],Tuple[np.ndarray, np.ndarray, np.ndarray]]:
        """ Pairs of points """

    # TODO: Implement this to allow better sampling of distances
    #
    # @abstractmethod
    # def deltas(self):
    #     """ Changes in point position """

    def __repr__(self):
        return "%s(n=%i,r=%g)" % (self.__class__.__name__, self._n_points_desired, self.radius)

    @abstractmethod
    def start_location(self, size_hint: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """ Get the sample points """

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

    def generate(self, n):
        # Sample within a cube

        xyz = (np.random.random((n, 3)) - 0.5)*(2*self.radius)

        return xyz[:,0], xyz[:,1], xyz[:,2]

#
# class GridSample(SpatialSample):
#     def _calculate_n_actual(self) -> int:
#         side_length = int(np.ceil(np.cbrt(self._n_points_desired)))
#         return side_length**3
#
#     def sampling_details(self) -> str:
#         side_length =  int(np.ceil(np.cbrt(self._n_points_desired)))
#         return "%ix%ix%i = %i"%(side_length, side_length, side_length, side_length**3)
#
#     def pairs(self, size_hint: int):
#         raise NotImplementedError("Pair function not implemented for grid function")
#
#     def start_location(self, size_hint: int):
#
#         side_length = int(np.ceil(np.cbrt(self._n_points_desired)))
#         n = side_length ** 3
#
#         # We want the sampling to happen in the centre of each voxel
#         # get points at edges and centres, then skip ever other one not the edge
#         sample_values = np.linspace(-self.radius, self.radius, 2*side_length+1)[1::2]
#
#         # Calculate the number of slices per chunk, minimum of one slice
#         n_chunks = n / size_hint
#         n_slices_per_chunk = int(np.ceil(side_length/n_chunks))
#
#         print(n_slices_per_chunk)
#
#         for i in range(0, side_length, n_slices_per_chunk):
#
#             x, y, z = np.meshgrid(sample_values, sample_values, sample_values[i:i+n_slices_per_chunk])
#
#             yield x.reshape((-1, )), y.reshape((-1, )), z.reshape((-1, ))


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

