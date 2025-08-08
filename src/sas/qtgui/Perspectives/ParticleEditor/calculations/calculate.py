import time

from sas.qtgui.Perspectives.ParticleEditor.calculations.boundary_check import (
    check_mag_zero_at_boundary,
    check_sld_continuity_at_boundary,
)
from sas.qtgui.Perspectives.ParticleEditor.calculations.fq import scattering_via_fq
from sas.qtgui.Perspectives.ParticleEditor.datamodel.calculation import (
    QSpaceScattering,
    ScatteringCalculation,
    ScatteringOutput,
)


class SLDBoundaryMismatch(Exception):
    pass

class MagBoundaryNonZero(Exception):
    pass


def calculate_scattering(calculation: ScatteringCalculation) -> ScatteringOutput:

    start_time = time.time()

    # If required, check that SLD/Mag at the boundary of the sample volume matches the rest of the space
    if calculation.bounding_surface_sld_check:
        if not check_sld_continuity_at_boundary(calculation):
            raise SLDBoundaryMismatch("SLD at sampling boundary does not match solvent SLD")

        if not check_mag_zero_at_boundary(calculation):
            raise MagBoundaryNonZero("Magnetism is non-zero at sampling boundary")

    # Perform the calculation
    sld_def = calculation.particle_definition.sld
    mag_def = calculation.particle_definition.magnetism
    params = calculation.parameter_settings
    spatial_dist = calculation.spatial_sampling_method
    q_dist = calculation.q_sampling
    angular_dist = calculation.angular_sampling

    scattering = scattering_via_fq(
        sld_definition=sld_def,
        magnetism_definition=mag_def,
        parameters=params,
        point_generator=spatial_dist,
        q_sample=q_dist,
        angular_distribution=angular_dist)

    q_data = QSpaceScattering(q_dist, scattering)

    output = ScatteringOutput(
        q_space=q_data,
        calculation_time=time.time() - start_time,
        seed_used=None)

    return output

















