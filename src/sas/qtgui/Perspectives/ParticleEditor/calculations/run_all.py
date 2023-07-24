from sas.qtgui.Perspectives.ParticleEditor.datamodel.calculation import ScatteringCalculation, OrientationalDistribution
from sas.qtgui.Perspectives.ParticleEditor.calculations.debye import debye

def calculate_scattering(calculation: ScatteringCalculation):
    if calculation.bounding_surface_sld_check:
        pass

    sld_def = calculation.particle_definition.sld
    mag_def = calculation.particle_definition.magnetism
    params = calculation.parameter_settings

    if calculation.orientation == OrientationalDistribution.UNORIENTED:
        if calculation.output_options.q_space:
            debye_data = debye(sld_def, mag_def, params, )
