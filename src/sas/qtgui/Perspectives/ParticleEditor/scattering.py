from typing import Dict, DefaultDict, Callable, Optional, Any, Tuple, Union
from enum import Enum
from dataclasses import dataclass

import time

import numpy as np
from scipy.special import jv as besselJ

from sas.qtgui.Perspectives.ParticleEditor.datamodel.calculation import (
    QSample, ZSample, OutputType, OrientationalDistribution, ScatteringCalculation)

from sas.qtgui.Perspectives.ParticleEditor.datamodel.sampling import SpatialSample

@dataclass
class ScatteringOutput:
    output_type: OutputType
    q_sampling_method: QSample
    spatial_sampling_method: SpatialSample
    intensity_data: np.ndarray
    r_values: Optional[np.ndarray]
    realspace_intensity: Optional[np.ndarray]
    calculation_time: float

def calculate_scattering(calculation: ScatteringCalculation) -> ScatteringOutput:
    """ Main function for calculating scattering"""

    start_time = time.time() # Track how long it takes

    # Calculate contribution of SLD
    if calculation.orientation == OrientationalDistribution.UNORIENTED:

        print("Unoriented")

        if calculation.output_type == OutputType.SLD_2D:
            raise NotImplementedError("2D scattering not implemented yet")

        # Try a different method, estimate the radial distribution
        n_r = 1000
        n_r_upscale = 10000
        bin_edges = np.linspace(0, calculation.spatial_sampling_method.radius, n_r+1)
        bin_size = calculation.spatial_sampling_method.radius / n_r

        sld = None
        counts = None
        sld_total = 0

        for x0, y0, z0 in calculation.spatial_sampling_method.singles(calculation.sample_chunk_size_hint):

            # evaluate sld
            input_coordinates1 = calculation.sld_function_from_cartesian(x0, y0, z0)
            # input_coordinates2 = calculation.sld_function_from_cartesian(x1, y1, z1)

            sld1 = calculation.sld_function(*input_coordinates1, **calculation.sld_function_parameters)
            sld1 -= calculation.solvent_sld
            #
            # sld2 = calculation.sld_function(*input_coordinates2, **calculation.sld_function_parameters)
            # sld2 -= calculation.solvent_sld
            #
            # rho = sld1*sld2
            rho = sld1

            # Do the integration
            # sample_rs = np.sqrt((x1 - x0)**2 + (y1 - y0)**2 + (z1 - z0)**2)
            sample_rs = np.sqrt(x0**2 + y0**2 + z0**2)
            # sample_rs = np.abs(np.sqrt(x0**2 + y0**2 + z0**2) - np.sqrt(x1**2 + y1**2 + z1**2))

            if sld is None:
                sld = np.histogram(sample_rs, bins=bin_edges, weights=rho)[0]
                counts = np.histogram(sample_rs, bins=bin_edges)[0]
            else:
                sld += np.histogram(sample_rs, bins=bin_edges, weights=rho)[0]
                counts += np.histogram(sample_rs, bins=bin_edges)[0]

            sld_total += np.sum(sld1) #+ np.sum(sld2)

        if counts is None or sld is None:
            raise ValueError("No sample points")


        # Remove all zero count bins
        non_empty_bins = counts > 0

        # print(np.count_nonzero(non_empty_bins))

        # Calculate the mean sld at each radius
        r_small = (bin_edges[:-1] + 0.5 * bin_size)[non_empty_bins]
        sld_average = sld[non_empty_bins] / counts[non_empty_bins]
        

        # Upscale
        r_upscaled = np.arange(0, n_r_upscale+1) * (calculation.spatial_sampling_method.radius / n_r_upscale)
        # bin_centres = 0.5*(r_upscaled[1:] + r_upscaled[:-1])
        upscaled_sld_average = np.interp(r_upscaled, r_small, sld_average)


        #
        # Do transform
        #

        q = calculation.q_sampling_method()
        qr = np.outer(q, r_upscaled[1:])
        #
        # # Power of q must be -1 for correct slope at low q
        # f = np.sum((new_averages * (r_large * r_large)) * np.sinc(qr/np.pi), axis=1) # Correct for sphere with COM sampling

        # Change in sld for each bin
        deltas = np.diff(upscaled_sld_average)

        # r_large is the right hand bin entry

        factors = (np.sin(qr) - qr * np.cos(qr)) / (qr ** 3)
        #
        # import matplotlib.pyplot as plt
        # start_count = 10
        # for i, delta in enumerate(deltas):
        #     if i%10 == 0:
        #         if delta != 0:
        #             f = np.sum(deltas[:i] * (r_upscaled[1:i+1]**2) * factors[:, :i], axis=1)
        #             f /= f[0]
        #             if start_count > 0:
        #                 plt.loglog(q, f*f, color='r')
        #             else:
        #                 plt.loglog(q, f*f, color='k')
        #             start_count -= 1
        # plt.show()

        f = np.sum(deltas * factors, axis=1)
        # f = np.sum((deltas * (r_upscaled[1:]**2)) * factors, axis=1)

        # Value at qr=0
        # mean_density = sld_total / (2*calculation.spatial_sampling_method.n_actual) # 2 because we sampled two points above
        # f0 = mean_density * calculation.spatial_sampling_method.sample_volume()


        intensity = f**2 # Correct for sphere with COM sampling

        intensity /= calculation.spatial_sampling_method.n_actual

        # intensity += 1e-12

        # Calculate magnet contribution
        # TODO: implement magnetic scattering

        # Wrap up

        calculation_time = time.time() - start_time

        return ScatteringOutput(
            output_type=calculation.output_type,
            q_sampling_method=calculation.q_sampling_method,
            spatial_sampling_method=calculation.spatial_sampling_method,
            intensity_data=intensity,
            calculation_time=calculation_time,
            r_values=r_upscaled,
            realspace_intensity=upscaled_sld_average)


    elif calculation.orientation == OrientationalDistribution.FIXED:

        print("Oriented")

        if calculation.output_type == OutputType.SLD_2D:
            raise NotImplementedError("2D scattering not implemented yet")

        # Try a different method, estimate the radial distribution


        sld = None
        counts = None
        sld_total = 0
        q = calculation.q_sampling_method()

        n_r = 1000
        n_r_upscale = 10000
        bin_edges = np.linspace(0, calculation.spatial_sampling_method.radius, n_r + 1)
        bin_size = calculation.spatial_sampling_method.radius / n_r

        for (x0, y0, z0), (x1, y1, z1) in calculation.spatial_sampling_method.pairs(calculation.sample_chunk_size_hint):

            # evaluate sld
            input_coordinates1 = calculation.sld_function_from_cartesian(x0, y0, z0)
            input_coordinates2 = calculation.sld_function_from_cartesian(x1, y1, z1)

            sld1 = calculation.sld_function(*input_coordinates1, **calculation.sld_function_parameters)
            sld1 -= calculation.solvent_sld

            sld2 = calculation.sld_function(*input_coordinates2, **calculation.sld_function_parameters)
            sld2 -= calculation.solvent_sld

            rho = sld1*sld2

            r_xy = np.sqrt((x1-x0)**2 + (y1-y0)**2)

            if sld is None:
                sld = np.histogram(r_xy, bins=bin_edges, weights=rho)[0]
                counts = np.histogram(r_xy, bins=bin_edges)[0]
            else:
                sld += np.histogram(r_xy, bins=bin_edges, weights=rho)[0]
                counts += np.histogram(r_xy, bins=bin_edges)[0]

            sld_total += np.sum(sld1) + np.sum(sld2)

        if counts is None or sld is None:
            raise ValueError("No sample points")


        # Value at qr=zero
        f /= calculation.spatial_sampling_method.n_actual

        mean_density = sld_total / calculation.spatial_sampling_method.n_actual
        f0 = mean_density / calculation.spatial_sampling_method.sample_volume()


        # intensity = f*f # Correct for sphere with COM sampling
        # intensity = np.real(f)
        intensity = f + f0

        # intensity = np.real(fft)

        # intensity = (f + f0)**2


        # Calculate magnet contribution
        # TODO: implement magnetic scattering

        # Wrap up

        calculation_time = time.time() - start_time

        return ScatteringOutput(
            output_type=calculation.output_type,
            q_sampling_method=calculation.q_sampling_method,
            spatial_sampling_method=calculation.spatial_sampling_method,
            intensity_data=intensity,
            calculation_time=calculation_time,
            r_values=None,
            realspace_intensity=None)
