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
    do_r_xyz_correlation = no_orientation and (options.q_space or options.q_space_2d or options.sesans)

    # Radial correlation based on distance in x, y - this is the quantity that matters for 2D
    do_r_xy_correlation = fixed_orientation and options.q_space

    # XY correlation - this is what we need for standard 2D SANS
    do_xy_correlations = fixed_orientation and options.q_space_2d

    # Z correlation - this is what we need for SESANS when the particles are oriented
    do_z_correlations = fixed_orientation and options.sesans

    #
    # Set up output variables
    #

    # Define every output as None initially and update if the calculation is required
    radial_distribution: Optional[Tuple[np.ndarray, np.ndarray]] = None
    r_xyz_correlation: Optional[Tuple[np.ndarray, np.ndarray]] = None
    q_space: Optional[Tuple[np.ndarray, np.ndarray]] = None
    q_space_2d: Optional[Tuple[np.ndarray, np.ndarray]] = None
    sesans: Optional[Tuple[np.ndarray, np.ndarray]] = None



    if calculation.seed is None:
        seed = None
    else:
        seed = calculation.seed

    if calculation.orientation == OrientationalDistribution.UNORIENTED:
        # Unoriented System
        pass

    elif calculation.orientation == OrientationalDistribution.FIXED:
        # Oriented System
        pass

    else:
        raise ValueError("Unknown orientational distribution:", calculation.orientation)

    return ScatteringOutput(
        radial_distribution=radial_distribution,
        radial_correlation=radial_correlation,
        p_of_r=p_of_r,
        q_space=q_space,
        q_space_2d=q_space_2d,
        sesans=sesans,
        sesans_2d=sesans_2d,
        calculation_time=time.time() - start_time,
        seed_used=seed)

