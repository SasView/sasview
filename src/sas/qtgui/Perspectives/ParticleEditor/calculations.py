from typing import Optional, Tuple
import numpy as np
import time

from sas.qtgui.Perspectives.ParticleEditor.datamodel.calculation import (
    ScatteringCalculation, ScatteringOutput, OrientationalDistribution)


def calculate_scattering(calculation: ScatteringCalculation):
    """ Main scattering calculation """

    start_time = time.time() # Track how long it takes

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

    sampling = calculation.spatial_sampling_method

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

    total_square_sld = 0.0

    for (x0, y0, z0), (x1, y1, z1) in calculation.spatial_sampling_method.pairs(calculation.sample_chunk_size_hint):

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
        # Mean SLD squared, note we have two samples here
        #

        total_square_sld += np.sum(sld0**2 + sld1**2)

    #
    # Calculate scattering from the histograms
    #

    if do_radial_distribution:
        bin_centres = 0.5*(radial_bin_edges[1:] + radial_bin_edges[:-1])
        radial_distribution_output = (bin_centres, radial_distribution)
    else:
        radial_distribution_output = None

    if no_orientation:
        if options.q_space is not None:
            q = calculation.output_options.q_space()

            bin_centres = r_xyz_bin_edges[1:] + r_xy_bin_edges[:-1]



            # We have to be very careful about how we do the numerical integration, specifically with respect to r=0
            qr = np.outer(q, r_xyz_correlation)

            np.sum(np.sinc(qr), axis=1)

            q_space = (q, )

        if options.q_space_2d:
            # USE: scipy.interpolate.CloughTocher2DInterpolator to do this

            pass

        # TODO: SESANS support
        sesans_output = None


    return ScatteringOutput(
        radial_distribution=radial_distribution_output,
        q_space=None,
        q_space_2d=None,
        sesans=None,
        calculation_time=time.time() - start_time,
        seed_used=seed)
