import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import time

from sas.qtgui.Perspectives.ParticleEditor.sampling_methods import (
    UniformCubeSample, UniformSphereSample,
    RadiallyBiasedCubeSample, RadiallyBiasedSphereSample,
    MixedCubeSample, MixedSphereSample)

test_radius = 5
sample_radius = 10

def octahedron(x,y,z):
    inds = np.abs(x) + np.abs(y) + np.abs(z) <= test_radius
    sld = np.zeros_like(x)
    sld[inds] = 1.0

    return sld


def cube(x,y,z):

    inds = np.logical_and(
            np.abs(x) < test_radius,
            np.logical_and(
                np.abs(y) < test_radius,
                np.abs(z) < test_radius))

    sld = np.zeros_like(x)
    sld[inds] = 1.0

    return sld


def off_centre_cube(x,y,z):

    inds = np.logical_and(
            np.abs(x+test_radius/2) < test_radius,
            np.logical_and(
                np.abs(y+test_radius/2) < test_radius,
                np.abs(z+test_radius/2) < test_radius))

    sld = np.zeros_like(x)
    sld[inds] = 1.0

    return sld


def sphere(x, y, z):

    inds = x**2 + y**2 + z**2 <= test_radius**2
    sld = np.zeros_like(x)
    sld[inds] = 1.0

    return sld

test_functions = [cube, sphere, octahedron, off_centre_cube]
sampler_classes = [UniformCubeSample, UniformSphereSample,
                   RadiallyBiasedCubeSample, RadiallyBiasedSphereSample,
                   MixedCubeSample, MixedSphereSample]

colors = plt.rcParams['axes.prop_cycle'].by_key()['color']


bin_edges = np.linspace(0, np.sqrt(3)*sample_radius, 201)
bin_centre = 0.5*(bin_edges[1:] + bin_edges[:-1])

for test_function in test_functions:

    legends = []

    plt.figure("Test function " + test_function.__name__)

    for sampler_cls, color in zip(sampler_classes, colors):

        print(sampler_cls.__name__)
        for repeat in range(3):
            sampler = sampler_cls(n_points=1_000_000, radius=sample_radius)

            start_time = time.time()

            distro = None
            counts = None

            for (x0, y0, z0), (x1, y1, z1) in sampler(size_hint=1000):

                sld0 = test_function(x0, y0, z0)
                sld1 = test_function(x1, y1, z1)

                rho = sld0 * sld1

                r = np.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2 + (z1 - z0) ** 2)

                if distro is None:
                    distro = np.histogram(r, bins=bin_edges, weights=rho)[0]
                    counts = np.histogram(r, bins=bin_edges)[0]

                else:
                    distro += np.histogram(r, bins=bin_edges, weights=rho)[0]
                    counts += np.histogram(r, bins=bin_edges)[0]


            good_values = counts > 0

            distro = distro[good_values].astype(float)
            counts = counts[good_values]
            bin_centres_good = bin_centre[good_values]

            distro /= counts
            distro *= sampler.sample_volume()

            f = interp1d(bin_centres_good, distro,
                                kind='linear', bounds_error=False, fill_value=0, assume_sorted=True)


            ax = plt.plot(bin_centre, f(bin_centre), color=color)
            if repeat == 0:
                legends.append((ax[0], sampler.__class__.__name__))


            print("Time:", time.time() - start_time)

    handles = [handle for handle, _ in legends]
    titles = [title for _, title in legends]
    plt.legend(handles, titles)

plt.show()