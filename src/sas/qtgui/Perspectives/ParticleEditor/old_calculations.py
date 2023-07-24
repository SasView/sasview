from typing import Optional, Tuple
import time

import numpy as np
from scipy.interpolate import interp1d

from scipy.special import jv as bessel

from sas.qtgui.Perspectives.ParticleEditor.datamodel.calculation import (
    ScatteringCalculation, ScatteringOutput, OrientationalDistribution, SamplingDistribution,
    QPlotData, QSpaceCalcDatum, RealPlotData)

def calculate_average(input_data, counts, original_bin_edges, new_bin_edges, two_times_sld_squared_sum):
    """ Get averaged data, taking into account under sampling

    :returns: mean correlation, associated bin sizes"""

    total_counts = np.sum(counts)
    mean_rho = 0.5 * two_times_sld_squared_sum / total_counts

    original_bin_centres = 0.5 * (original_bin_edges[1:] + original_bin_edges[:-1])
    new_bin_centres = 0.5 * (new_bin_edges[1:] + new_bin_edges[:-1])

    non_empty = counts > 0
    means = input_data[non_empty] / counts[non_empty]
    mean_function = interp1d(original_bin_centres[non_empty], means,
                             bounds_error=False, fill_value=(mean_rho, 0), assume_sorted=True)

    delta_rs = 0.5 * (new_bin_edges[1:] - new_bin_edges[:-1])

    return mean_function(new_bin_centres), delta_rs




def calculate_scattering(calculation: ScatteringCalculation):
    """ Main scattering calculation """

    start_time = time.time() # Track how long it takes

    # Some dereferencing
    sampling = calculation.spatial_sampling_method
    parameters = calculation.parameter_settings

    # What things do we need to calculate
    options = calculation.output_options
    fixed_orientation = calculation.orientation == OrientationalDistribution.FIXED
    no_orientation = calculation.orientation == OrientationalDistribution.UNORIENTED

    # Radial SLD distribution - a special plot - doesn't relate to the other things
    do_radial_distribution = options.radial_distribution

    # Radial correlation based on distance in x, y and z - this is the quantity that matters for
    # unoriented particles
    do_r_xyz_correlation = no_orientation and (options.q_space is not None or options.q_space_2d is not None or options.sesans is not None)

    # Radial correlation based on distance in x, y - this is the quantity that matters for 2D
    do_r_xy_correlation = fixed_orientation and options.q_space is not None

    # XY correlation - this is what we need for standard 2D SANS
    do_xy_correlation = fixed_orientation and options.q_space_2d is not None

    # Z correlation - this is what we need for SESANS when the particles are oriented
    do_z_correlation = fixed_orientation and options.sesans is not None

    #
    # Set up output variables
    #

    n_bins = calculation.bin_count



    radial_bin_edges = np.linspace(0, sampling.radius, n_bins+1) if do_radial_distribution else None
    r_xyz_bin_edges = np.linspace(0, sampling.max_xyz(), n_bins+1) if do_r_xyz_correlation else None
    r_xy_bin_edges = np.linspace(0, sampling.max_xy(), n_bins+1) if do_r_xy_correlation else None
    xy_bin_edges = (np.linspace(0, sampling.max_x(), n_bins+1),
                    np.linspace(0, sampling.max_y(), n_bins+1)) if do_xy_correlation else None

    radial_distribution = None
    radial_counts = None
    r_xyz_correlation = None
    r_xyz_counts = None
    r_xy_correlation = None
    r_xy_counts = None
    xy_correlation = None
    xy_counts = None

    #
    # Seed
    #

    # TODO: This needs to be done properly
    if calculation.seed is None:
        seed = 0
    else:
        seed = calculation.seed

    #
    # Setup for calculation
    #

    sld = calculation.particle_definition.sld
    sld_parameters = calculation.parameter_settings.sld_parameters

    magnetism = calculation.particle_definition.magnetism
    magnetism_parameters = calculation.parameter_settings.magnetism_parameters

    total_square_sld_times_two = 0.0


    for (x0, y0, z0), (x1, y1, z1) in calculation.spatial_sampling_method(calculation.sample_chunk_size_hint):

        #
        # Sample the SLD
        #

        # TODO: Make sure global variables are accessible to the function calls
        sld0 = sld.sld_function(*sld.to_cartesian_conversion(x0, y0, z0), **sld_parameters)
        sld1 = sld.sld_function(*sld.to_cartesian_conversion(x1, y1, z1), **sld_parameters)

        rho = sld0 * sld1

        #
        # Build the appropriate histograms
        #

        if do_radial_distribution:

            r = np.sqrt(x0**2 + y0**2 + z0**2)

            if radial_distribution is None:
                radial_distribution = np.histogram(r, bins=radial_bin_edges, weights=sld0)[0]
                radial_counts = np.histogram(r, bins=radial_bin_edges)[0]

            else:
                radial_distribution += np.histogram(r, bins=radial_bin_edges, weights=sld0)[0]
                radial_counts += np.histogram(r, bins=radial_bin_edges)[0]

        if do_r_xyz_correlation:

            # r_xyz = np.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2 )#+ (z1 - z0) ** 2)
            r_xyz = np.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2 + (z1 - z0) ** 2)

            if r_xyz_correlation is None:
                r_xyz_correlation = np.histogram(r_xyz, bins=r_xyz_bin_edges, weights=rho)[0]
                r_xyz_counts = np.histogram(r_xyz, bins=r_xyz_bin_edges)[0]

            else:
                r_xyz_correlation += np.histogram(r_xyz, bins=r_xyz_bin_edges, weights=rho)[0]
                r_xyz_counts += np.histogram(r_xyz, bins=r_xyz_bin_edges)[0]

        if do_r_xy_correlation:

            r_xy = np.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)

            if r_xy_correlation is None:
                r_xy_correlation = np.histogram(r_xy, bins=r_xy_bin_edges, weights=rho)[0]
                r_xy_counts = np.histogram(r_xy, bins=r_xy_bin_edges)[0]

            else:
                r_xy_correlation += np.histogram(r_xy, bins=r_xy_bin_edges, weights=rho)[0]
                r_xy_counts += np.histogram(r_xy, bins=r_xy_bin_edges)[0]

        if do_xy_correlation:

            x = x1 - x0
            y = y1 - y0

            if xy_correlation is None:
                xy_correlation = np.histogram2d(x, y, bins=xy_bin_edges, weights=rho)[0]
                xy_counts = np.histogram2d(x, y, bins=xy_bin_edges)[0]

            else:
                xy_correlation += np.histogram2d(x, y, bins=xy_bin_edges, weights=rho)[0]
                xy_counts += np.histogram2d(x, y, bins=xy_bin_edges)[0]

        if do_z_correlation:
            raise NotImplementedError("Z correlation not implemented yet")

        #
        # Mean SLD squared, note we have two samples here, so don't forget to divide later
        #

        total_square_sld_times_two += np.sum(sld0**2 + sld1**2)

    #
    # Calculate scattering from the histograms
    #

    q_space = None

    if do_radial_distribution:
        bin_centres = 0.5*(radial_bin_edges[1:] + radial_bin_edges[:-1])

        good_bins = radial_counts > 0

        averages = radial_distribution[good_bins] / radial_counts[good_bins]

        radial_distribution_output = (bin_centres[good_bins], averages)
    else:
        radial_distribution_output = None

    sampling_distributions = []

    if no_orientation:
        if options.q_space is not None:
            q = calculation.output_options.q_space()

            qr = np.outer(q, r_xyz_bin_edges)

            # intensity = parameters.background + parameters.scale * np.sum(np.sinc(qr), axis=1)
            # intensity = np.sum((r_xyz_correlation_patched * delta_rs * r_xyz_bin_edges**2) * np.sinc(qr), axis=1) + total_square_sld_times_two
            # intensity = np.sum((r_xyz_correlation_patched * delta_rs * r_xyz_bin_edges**2) * np.sinc(qr), axis=1)

            # Integral of r^2 sinc(qr)
            sections = ((np.sin(qr) - qr * np.cos(qr)).T / q**3).T
            sections[:, 0] = 0
            sections = sections[:, 1:] - sections[:, :-1]

            bin_centres = 0.5 * (r_xyz_bin_edges[1:] + r_xyz_bin_edges[:-1])

            r_xyz_correlation_interp, delta_r = calculate_average(
                r_xyz_correlation, r_xyz_counts,
                r_xyz_bin_edges, r_xyz_bin_edges,
                total_square_sld_times_two)

            R = 50

            f1 = lambda r: 1 - (3 / 4) * (r / R) + (1 / 16) * (r / R) ** 3

            def f(x):
                out = np.zeros_like(x)
                x_in = x[x <= 2 * R]
                out[x <= 2 * R] = f1(x_in)
                return out

            def poissony(data, scale=100_000):
                return np.random.poisson(lam=scale*data)/scale


            # intensity = np.sum(poissony(f(bin_centres))*delta_r*sections, axis=1)
            intensity = np.sum(f(bin_centres)*delta_r*sections, axis=1)
            # intensity = np.sum(r_xyz_correlation*delta_r*sections, axis=1)


            # intensity = np.abs(np.sum(r_xyz_correlation_patched*diffs, axis=1) + mean_rho*sampling.sample_volume())


            q_space_part = QPlotData(calculation.output_options.q_space, intensity)

            if calculation.output_options.realspace:
                r_space_part = RealPlotData(bin_centres, poissony(f(bin_centres)))
                # r_space_part = RealPlotData(bin_centres, r_xyz_correlation/np.max(r_xyz_correlation))
            else:
                r_space_part = None

            q_space = QSpaceCalcDatum(q_space_part, r_space_part)

            if options.sampling_distributions:
                sampling_distribution = SamplingDistribution(
                    "r_xyz",
                    bin_centres,
                    r_xyz_counts)

                sampling_distributions.append(sampling_distribution)

        if options.q_space_2d is not None:
            pass

        if options.sesans:
            # TODO: SESANS support
            sesans_output = None

    else:

        if options.q_space:
            q = calculation.output_options.q_space()

            qr = np.outer(q, r_xy_bin_edges)

            # intensity = parameters.background + parameters.scale * np.sum(np.sinc(qr), axis=1)
            # intensity = np.sum((r_xyz_correlation_patched * delta_rs * r_xyz_bin_edges**2) * np.sinc(qr), axis=1) + total_square_sld_times_two
            # intensity = np.sum((r_xyz_correlation_patched * delta_rs * r_xyz_bin_edges**2) * np.sinc(qr), axis=1)

            # Integral of r^2 sinc(qr)
            sections = bessel(0, qr)
            sections[:, 0] = 0

            r_xy_correlation_interp, delta_r = calculate_average(
                r_xy_correlation, r_xy_counts,
                r_xy_bin_edges, r_xy_bin_edges,
                total_square_sld_times_two)

            intensity = np.sum(r_xy_correlation_interp * delta_r * sections, axis=1)
            # intensity = np.abs(np.sum(r_xyz_correlation_patched*diffs, axis=1) + mean_rho*sampling.sample_volume())

            q_space_part = QPlotData(calculation.output_options.q_space, intensity)
            if calculation.output_options.realspace:
                r_space_part = RealPlotData(r_xy_bin_edges, r_xy_correlation_interp)
            else:
                r_space_part = None

            q_space = QSpaceCalcDatum(q_space_part, r_space_part)

            if options.sampling_distributions:
                sampling_distribution = SamplingDistribution(
                    "r_xy",
                    0.5*(r_xy_bin_edges[1:] + r_xy_bin_edges[:-1]),
                    r_xy_counts)

                sampling_distributions.append(sampling_distribution)

        if options.q_space_2d:
            # USE: scipy.interpolate.CloughTocher2DInterpolator to do this

            pass

        # TODO: implement
        # TODO: Check that the sampling method is appropriate - it probably isn't
        pass

    return ScatteringOutput(
        radial_distribution=radial_distribution_output,
        q_space=q_space,
        q_space_2d=None,
        sesans=None,
        sampling_distributions=sampling_distributions,
        calculation_time=time.time() - start_time,
        seed_used=seed)
