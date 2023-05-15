from typing import Optional
from abc import ABC, abstractmethod
import numpy as np

class Sample(ABC):
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
    def get_sample(self) -> (np.ndarray, np.ndarray, np.ndarray):
        """ Get the sample points """


class RandomSampleSphere(Sample):
    """ Rejection Random Sampler for a sphere with a given radius """
    def __init__(self, n_points_desired: int, radius: float, seed: Optional[int] = None):
        super().__init__(n_points_desired, radius)
        self.seed = seed

    def _calculate_n_actual(self) -> int:
        return self._n_points_desired

    def sampling_details(self) -> str:
        return ""

    def get_sample(self):
        # Sample within a sphere

        # A sphere will occupy pi/6 of a cube, which is 0.5236 ish
        # With rejection sampling we need to oversample by about a factor of 2


        target_n = self._n_points_desired

        output_data = []
        while target_n > 0:
            xyz = np.random.random((int(1.91 * target_n), 3)) - 0.5

            indices = np.sum(xyz**2, axis=1) <= 0.25

            print(indices.shape)

            xyz = xyz[indices, :]

            if xyz.shape[0] > target_n:
                target_n = 0
                output_data.append(xyz[:target_n, :])
            else:
                target_n -= xyz.shape[0]
                output_data.append(xyz)

        xyz = np.concatenate(output_data, axis=0) * (2*self.radius)

        return xyz[:,0], xyz[:,1], xyz[:,2]


class RandomSampleCube(Sample):
    """ Randomly sample points in a 2r x 2r x 2r cube centred at the origin"""
    def __init__(self, n_points_desired: int, radius: float, seed: Optional[int] = None):
        super().__init__(n_points_desired, radius)
        self.seed = seed

    def _calculate_n_actual(self) -> int:
        return self._n_points_desired

    def sampling_details(self) -> str:
        return ""

    def get_sample(self):
        # Sample within a cube

        xyz = np.random.random((self._n_points_desired, 3))*2 - 1.0

        return xyz[:,0], xyz[:,1], xyz[:,2]


class GridSample(Sample):
    def _calculate_n_actual(self) -> int:
        side_length = int(np.ceil(np.cbrt(self._n_points_desired)))
        return side_length**3

    def sampling_details(self) -> str:
        side_length =  int(np.ceil(np.cbrt(self._n_points_desired)))
        return "%ix%ix%i = %i"%(side_length, side_length, side_length, side_length**3)

    def get_sample(self):
        side_length = int(np.ceil(np.cbrt(self._n_points_desired)))
        n = side_length**3

        # We want the sampling to happen in the centre of each voxel
        # get points at edges and centres, then skip ever other one not the edge
        sample_values = np.linspace(-self.radius, self.radius, 2*side_length+1)[1::2]

        x, y, z = np.meshgrid(sample_values, sample_values, sample_values)

        return x.reshape((n, )), y.reshape((n, )), z.reshape((n, ))


if __name__ == "__main__":
    sampler = RandomSampleSphere(n_points_desired=100, radius=1)
    x,y,z = sampler.get_sample()
    print(x**2 + y**2 + z**2)