from sas.qtgui.Perspectives.ParticleEditor.datamodel.calculation import ScatteringCalculation, OrientationalDistribution
from sas.qtgui.Perspectives.ParticleEditor.calculations.debye import debye
from sas.qtgui.Perspectives.ParticleEditor.calculations.boundary_check import (
    check_sld_continuity_at_boundary, check_mag_zero_at_boundary)

class SLDBoundaryMismatch(Exception):
    pass

class MagBoundaryNonZero(Exception):
    pass


def calculate_scattering(calculation: ScatteringCalculation):

    # If required, check that SLD/Mag at the boundary of the sample volume matches the rest of the space
    if calculation.bounding_surface_sld_check:
        if not check_sld_continuity_at_boundary(calculation):
            raise SLDBoundaryMismatch("SLD at sampling boundary does not match solvent SLD")

        if not check_mag_zero_at_boundary(calculation):
            raise MagBoundaryNonZero("Magnetism ")

    sld_def = calculation.particle_definition.sld
    mag_def = calculation.particle_definition.magnetism
    params = calculation.parameter_settings

    if calculation.orientation == OrientationalDistribution.UNORIENTED:
        if calculation.output_options.q_space:
            debye_data = debye(sld_def, mag_def, params, )
