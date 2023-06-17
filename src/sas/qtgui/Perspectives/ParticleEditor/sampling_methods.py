from typing import Optional, Tuple
from abc import ABC, abstractmethod
import numpy as np

from sas.qtgui.Perspectives.ParticleEditor.datamodel.sampling import SpatialSample
from sas.qtgui.Perspectives.ParticleEditor.datamodel.types import VectorComponents3

class RandomSpatialSample(SpatialSample):
    """ Base class for random sampling methods """
    def __init__(self, n_points: int, radius: float, seed: Optional[int] = None):
        super().__init__(n_points, radius)
        self._seed = seed
        self.rng = np.random.default_rng(seed=seed)

    @property
    def seed(self):
        return self._seed

    @seed.setter
    def seed(self, s):
        self._seed = s
        self.rng = np.random.default_rng(seed=s)

    def __repr__(self):
        return "%s(n=%i,r=%g,seed=%s)" % (self.__class__.__name__, self.n_points, self.radius, str(self.seed))

    @abstractmethod
    def generate_pairs(self, size_hint: int) -> Tuple[int, Tuple[VectorComponents3, VectorComponents3]]:
        """ Generate pairs of points, each uniformly distrubted over the sample space, with
        their distance distributed uniformly

        :returns: number of points generated, and the pairs of points"""

    def __call__(self, size_hint: int):
        """ __call__ is a generator that goes through the points in chunks that aim to be a certain size
        for efficiency, we do not require that the chunks are exactly the size requested"""

        n_remaining = self.n_points

        while n_remaining > 0:

            n, pairs = self.generate_pairs(min((n_remaining, size_hint)))

            if n <= n_remaining:
                # Still plenty to go, return regardless of size

                yield pairs
                n_remaining -= n

            else:
                # We've made more points than we needed, just return enough to complete the requested amount
                (x0, y0, z0), (x1, y1, z1) = pairs
                yield (x0[:n_remaining], y0[:n_remaining], z0[:n_remaining]), \
                      (x1[:n_remaining], y1[:n_remaining], z1[:n_remaining])

                n_remaining = 0


class UniformCubeSample(RandomSpatialSample):
    """ Uniformly sample pairs of points from a cube """
    def generate_pairs(self, size_hint: int) -> Tuple[int, Tuple[VectorComponents3, VectorComponents3]]:
        """ Generate pairs of points, each within a cube"""

        pts = (2*self.radius) * (self.rng.random(size=(size_hint, 6)) - 0.5)

        return size_hint, ((pts[:, 0], pts[:, 1], pts[:, 2]), (pts[:, 3], pts[:, 4], pts[:, 5]))


    def max_xyz(self):
        """ Maximum distance between points in 3D - along the main diagonal"""
        return 2 * self.radius * np.sqrt(3)

    def max_xy(self):
        """ Maximum distance between points in 2D projection in an axis - along
        the diagonal of a face (or equivalent)"""
        return 2 * self.radius * np.sqrt(2)

    def max_principal_axis(self):
        """ Maximum distance between points along one axis - along one of the axes """
        return 2 * self.radius

    def sample_volume(self):
        """ Volume of sampling region - a cube """
        return 8*(self.radius**3)

    def bounding_surface_check_points(self) -> VectorComponents3:
        """Bounding box check points

        8 corners
        12 edge centres
        6 face centres
        """

        corners = [
            [ self.radius,  self.radius,  self.radius],
            [ self.radius,  self.radius, -self.radius],
            [ self.radius, -self.radius,  self.radius],
            [ self.radius, -self.radius, -self.radius],
            [-self.radius,  self.radius,  self.radius],
            [-self.radius,  self.radius, -self.radius],
            [-self.radius, -self.radius,  self.radius],
            [-self.radius, -self.radius, -self.radius]]

        edge_centres = [
            [ self.radius,  self.radius, 0 ],
            [ self.radius, -self.radius, 0 ],
            [-self.radius,  self.radius, 0 ],
            [-self.radius, -self.radius, 0 ],
            [ self.radius, 0,  self.radius],
            [ self.radius, 0, -self.radius],
            [-self.radius, 0,  self.radius],
            [-self.radius, 0, -self.radius],
            [ 0,  self.radius,  self.radius],
            [ 0,  self.radius, -self.radius],
            [ 0, -self.radius,  self.radius],
            [ 0, -self.radius, -self.radius]]

        face_centres = [
            [  self.radius, 0, 0 ],
            [ -self.radius, 0, 0 ],
            [ 0,  self.radius, 0 ],
            [ 0, -self.radius, 0 ],
            [ 0, 0,  self.radius ],
            [ 0, 0, -self.radius ]]

        check_points = np.concatenate((corners, edge_centres, face_centres), axis=0)

        return check_points[:, 0], check_points[:, 1], check_points[:, 2]


class DistanceBiasedSample(RandomSpatialSample):
    """ Base class for samplers with a bias towards shorter distances"""
    def cube_sample(self, n: int) -> np.ndarray:
        """ Sample uniformly from a 2r side length cube, centred on the origin """

        return (2*self.radius) * (self.rng.random(size=(n, 3)) - 0.5)

    def uniform_radial_sample(self, n: int) -> VectorComponents3:
        """ Sample within the maximum possible radius, uniformly over the distance from the
        origin (not a uniform distribution in space)"""

        xyz = self.rng.standard_normal(size=(n, 3))

        scaling = self.max_xyz() * self.rng.random(size=n) / np.sqrt(np.sum(xyz**2, axis=1))

        return xyz * scaling[:, np.newaxis]

class BiasedSampleSphere(DistanceBiasedSample):
    """ Sample over a sphere with a specified radius """

    def generate_pairs(self, n):
        """ Rejection sample pairs in a sphere

        The cube_sample method will generate valid start points with a probability (sphere
          volume/cube volume) of 0.5235
        The uniform_radial_sample will generate deltas landing within the sample volume with
          a probability (r radius sphere / 2r radius sphere) of 0.125

        Overall then, the probability of not being rejected is 0.0654498
        so we need to sample 15.278874 times as many points than requested if we want to
        get an expected number of points equal to the requested number

        We also add an extra couple of points to the required number, so that for small
        requests numbers, the chance of fulfilling the request is much bigger than 0.5.
        For example, if n=1, we'll have slightly less the 50% probability, if we use n+1,
        well have 75%, if we use n+2 we'll have 83%.

        It seems like quite a lot to reject, but it should be less costly than undersampling the radius

        """

        n_start = int((n+2)*15.278)

        xyz0 = self.cube_sample(n_start)

        in_sphere = np.sum(xyz0**2, axis=1) <= self.radius**2

        xyz0 = xyz0[in_sphere,:]

        dxyz = self.uniform_radial_sample(xyz0.shape[0])
        xyz1 = xyz0 + dxyz

        in_sphere = np.sum(xyz1**2, axis=1) <= self.radius**2

        xyz0 = xyz0[in_sphere, :]
        xyz1 = xyz1[in_sphere, :]

        return xyz0.shape[0], ((xyz0[:, 0], xyz0[:, 1], xyz0[:, 2]), (xyz1[:, 0], xyz1[:, 1], xyz1[:, 2]))

    def bounding_surface_check_points(self) -> VectorComponents3:
        """ Points to check:

        6 principal directions
        50 random points over the sphere
        """

        principal_directions = [
            [  self.radius, 0, 0 ],
            [ -self.radius, 0, 0 ],
            [ 0,  self.radius, 0 ],
            [ 0, -self.radius, 0 ],
            [ 0, 0,  self.radius ],
            [ 0, 0, -self.radius ]]

        random_points = self.rng.standard_normal(size=(50, 3))

        random_points /= self.radius / np.sqrt(np.sum(random_points**2, axis=1))

        check_points = np.concatenate((principal_directions, random_points), axis=0)

        return check_points[:, 0], check_points[:, 1], check_points[:, 2]
    def max_xyz(self):
        """ Maximum distance between points in 3D - opposite sides of sphere """
        return 2*self.radius

    def max_xy(self):
        """ Maximum distance between points in 2D projection - also opposite sides of sphere """
        return 2*self.radius

    def max_principal_axis(self):
        """ Maximum distance between points in an axis - again, opposite sides of sphere """
        return 2*self.radius

    def sample_volume(self):
        return (4*np.pi/3)*(self.radius**3)


class BiasedSampleCube(DistanceBiasedSample):
    """ Randomly sample points in a 2r x 2r x 2r cube centred at the origin"""

    def generate_pairs(self, n):
        """ Rejection sample pairs in a sphere

        The cube_sample method will generate valid start points with 100% probability
        The uniform_radial_sample will generate deltas landing within the sample volume with
          a probability ( side length 2 cube / 2 sqrt(3) radius sphere) of

        Overall then, the probability of not being rejected is 0.04594
        so we need to sample 21.766 times as many points than requested if we want to
        get an expected number of points equal to the requested number

        We also add an extra couple of points to the required number, so that for small
        requests numbers, the chance of fulfilling the request is much bigger than 0.5.
        For example, if n=1, we'll have slightly less the 50% probability, if we use n+1,
        well have 75%, if we use n+2 we'll have 83%.

        This rejects more points than the sphere sampling, but the pruning is faster.

        """

        n_start = int((n + 2) * 21.766)

        xyz0 = self.cube_sample(n_start)

        dxyz = self.uniform_radial_sample(n_start)

        xyz1 = xyz0 + dxyz

        in_cube = np.all(np.abs(xyz1) <= self.radius, axis=1)

        xyz0 = xyz0[in_cube, :]
        xyz1 = xyz1[in_cube, :]

        return xyz0.shape[0], ((xyz0[:, 0], xyz0[:, 1], xyz0[:, 2]), (xyz1[:, 0], xyz1[:, 1], xyz1[:, 2]))

    def max_xyz(self):
        """ Maximum distance between points in 3D - along the main diagonal"""
        return 2 * self.radius * np.sqrt(3)

    def max_xy(self):
        """ Maximum distance between points in 2D projection in an axis - along
        the diagonal of a face (or equivalent)"""
        return 2 * self.radius * np.sqrt(2)

    def max_principal_axis(self):
        """ Maximum distance between points along one axis - along one of the axes """
        return 2 * self.radius

    def sample_volume(self):
        """ Volume of sampling region - a cube """
        return 8*(self.radius**3)

    def bounding_surface_check_points(self) -> VectorComponents3:
        """Bounding box check points

        8 corners
        12 edge centres
        6 face centres
        """

        corners = [
            [ self.radius,  self.radius,  self.radius],
            [ self.radius,  self.radius, -self.radius],
            [ self.radius, -self.radius,  self.radius],
            [ self.radius, -self.radius, -self.radius],
            [-self.radius,  self.radius,  self.radius],
            [-self.radius,  self.radius, -self.radius],
            [-self.radius, -self.radius,  self.radius],
            [-self.radius, -self.radius, -self.radius]]

        edge_centres = [
            [ self.radius,  self.radius, 0 ],
            [ self.radius, -self.radius, 0 ],
            [-self.radius,  self.radius, 0 ],
            [-self.radius, -self.radius, 0 ],
            [ self.radius, 0,  self.radius],
            [ self.radius, 0, -self.radius],
            [-self.radius, 0,  self.radius],
            [-self.radius, 0, -self.radius],
            [ 0,  self.radius,  self.radius],
            [ 0,  self.radius, -self.radius],
            [ 0, -self.radius,  self.radius],
            [ 0, -self.radius, -self.radius]]

        face_centres = [
            [  self.radius, 0, 0 ],
            [ -self.radius, 0, 0 ],
            [ 0,  self.radius, 0 ],
            [ 0, -self.radius, 0 ],
            [ 0, 0,  self.radius ],
            [ 0, 0, -self.radius ]]

        check_points = np.concatenate((corners, edge_centres, face_centres), axis=0)

        return check_points[:, 0], check_points[:, 1], check_points[:, 2]

def visual_distribution_check(sampler: SpatialSample, axis_curve, r_curve, size_hint=500):

    n_bins = 200

    print("Size hint:", size_hint)
    n_total = 0

    x0_hist = None
    x1_hist = None
    y0_hist = None
    y1_hist = None
    z0_hist = None
    z1_hist = None
    r_hist = None

    bin_edges = np.linspace(-sampler.max_xyz(), sampler.max_xyz(), n_bins+1)
    bin_centres = 0.5*(bin_edges[1:] + bin_edges[:-1])

    r_bin_edges = np.linspace(0, sampler.max_xyz())
    r_bin_centres = 0.5 * (r_bin_edges[1:] + r_bin_edges[:-1])

    for (x0, y0, z0), (x1, y1, z1) in sampler(size_hint):

        n = len(x0)
        n_total += n

        print("Size",n,"chunk,", n_total, "so far")

        r = np.sqrt((x1 - x0)**2 + (y1 - y0)**2 + (z1 - z0)**2)

        if x0_hist is None:
            x0_hist = np.histogram(x0, bins=bin_edges)[0].astype("float")
            y0_hist = np.histogram(y0, bins=bin_edges)[0].astype("float")
            z0_hist = np.histogram(z0, bins=bin_edges)[0].astype("float")
            x1_hist = np.histogram(x1, bins=bin_edges)[0].astype("float")
            y1_hist = np.histogram(y1, bins=bin_edges)[0].astype("float")
            z1_hist = np.histogram(z1, bins=bin_edges)[0].astype("float")
            r_hist = np.histogram(r, bins=r_bin_edges)[0].astype("float")

        else:
            x0_hist += np.histogram(x0, bins=bin_edges)[0]
            y0_hist += np.histogram(y0, bins=bin_edges)[0]
            z0_hist += np.histogram(z0, bins=bin_edges)[0]
            x1_hist += np.histogram(x1, bins=bin_edges)[0]
            y1_hist += np.histogram(y1, bins=bin_edges)[0]
            z1_hist += np.histogram(z1, bins=bin_edges)[0]
            r_hist += np.histogram(r, bins=r_bin_edges)[0]


    x0_hist /= sampler.n_points / n_bins
    y0_hist /= sampler.n_points / n_bins
    z0_hist /= sampler.n_points / n_bins
    x1_hist /= sampler.n_points / n_bins
    y1_hist /= sampler.n_points / n_bins
    z1_hist /= sampler.n_points / n_bins
    r_hist /= sampler.n_points / n_bins

    import matplotlib.pyplot as plt

    plt.subplot(3, 3, 1)
    plt.plot(bin_centres, x0_hist)
    plt.plot(bin_edges, axis_curve(bin_edges))

    plt.subplot(3, 3, 2)
    plt.plot(bin_centres, y0_hist)
    plt.plot(bin_edges, axis_curve(bin_edges))

    plt.subplot(3, 3, 3)
    plt.plot(bin_centres, z0_hist)
    plt.plot(bin_edges, axis_curve(bin_edges))

    plt.subplot(3, 3, 4)
    plt.plot(bin_centres, x1_hist)
    plt.plot(bin_edges, axis_curve(bin_edges))

    plt.subplot(3, 3, 5)
    plt.plot(bin_centres, y1_hist)
    plt.plot(bin_edges, axis_curve(bin_edges))

    plt.subplot(3, 3, 6)
    plt.plot(bin_centres, z1_hist)
    plt.plot(bin_edges, axis_curve(bin_edges))

    plt.subplot(3, 3, 8)
    plt.plot(r_bin_centres, r_hist)
    plt.plot(r_bin_edges, r_curve(r_bin_edges))


if __name__ == "__main__":

    import matplotlib.pyplot as plt

    plt.figure("Sphere")

    sphere_sampler = BiasedSampleSphere(10_000, radius=10)
    def sphere_proj_density(x):
        return np.ones_like(x)

    def sphere_r_curve(x):
        return np.ones_like(x)

    visual_distribution_check(sphere_sampler, axis_curve=sphere_proj_density, r_curve=sphere_r_curve)


    plt.figure("Cube")

    cube_sampler = BiasedSampleCube(10_000, radius=10)
    def cube_proj_density(x):
        return np.ones_like(x)

    def cube_r_curve(x):
        return np.ones_like(x)

    visual_distribution_check(cube_sampler, axis_curve=cube_proj_density, r_curve=cube_r_curve)

    plt.figure("Cube - unform")

    cube_sampler = UniformCubeSample(10_000, radius=10)
    def cube_proj_density(x):
        return np.ones_like(x)

    def cube_r_curve(x):
        return np.ones_like(x)

    visual_distribution_check(cube_sampler, axis_curve=cube_proj_density, r_curve=cube_r_curve)

    plt.show()


