import numpy as np

from sas.qtgui.Perspectives.ParticleEditor.datamodel.calculation import ScatteringCalculation


def check_sld_continuity_at_boundary(calculation: ScatteringCalculation, tol=1e-9):
    """ Checks the continuity of the SLD at the sampling boundary

    :returns: True if boundary conditions are good
    """

    expected_sld = calculation.parameter_settings.solvent_sld

    x, y, z = calculation.spatial_sampling_method.bounding_surface_check_points()

    a, b, c = calculation.particle_definition.sld.to_cartesian_conversion(x, y, z)

    parameters = calculation.parameter_settings.sld_parameters
    slds = calculation.particle_definition.sld.sld_function(a, b, c, **parameters)

    return np.all(np.abs(slds - expected_sld) < tol)


def check_mag_zero_at_boundary(calculation: ScatteringCalculation, tol=1e-9):
    """ Checks the magnetism vector is zero at the sampling boundary

    :returns: True if boundary conditions are good"""

    if calculation.particle_definition.magnetism is None:
        return True

    x, y, z = calculation.spatial_sampling_method.bounding_surface_check_points()

    a, b, c = calculation.particle_definition.sld.to_cartesian_conversion(x, y, z)

    parameters = calculation.parameter_settings.sld_parameters
    mag_vectors = calculation.particle_definition.sld.sld_function(a, b, c, **parameters)

    # TODO: Double check this is the right axis, should be quite obvious if it isn't
    return np.all(np.sum(mag_vectors**2, axis=1) < tol**2)
