
import numpy as np

from sas.qtgui.Perspectives.ParticleEditor.calculations.run_function import run_sld
from sas.qtgui.Perspectives.ParticleEditor.datamodel.calculation import (
    AngularDistribution,
    CalculationParameters,
    MagnetismDefinition,
    QSample,
    SLDDefinition,
)
from sas.qtgui.Perspectives.ParticleEditor.sampling.points import PointGeneratorStepper, SpatialDistribution


def scattering_via_fq(
        sld_definition: SLDDefinition,
        magnetism_definition: MagnetismDefinition | None,
        parameters: CalculationParameters,
        point_generator: SpatialDistribution,
        q_sample: QSample,
        angular_distribution: AngularDistribution,
        chunk_size=1_000_000) -> np.ndarray:

    q_magnitudes = q_sample()

    direction_vectors, direction_weights = angular_distribution.sample_points_and_weights()
    fq = np.zeros((angular_distribution.n_points, q_sample.n_points), dtype=complex)  # Dictionary for fq for all angles

    for x, y, z in PointGeneratorStepper(point_generator, chunk_size):

        sld = run_sld(sld_definition, parameters, x, y, z).reshape(-1, 1)

        # TODO: Magnetism

        for direction_index, direction_vector in enumerate(direction_vectors):

            projected_distance = x*direction_vector[0] + y*direction_vector[1] + z*direction_vector[2]

            i_r_dot_q = np.multiply.outer(projected_distance, 1j*q_magnitudes)

            if direction_index in fq:
                fq[direction_index, :] = np.sum(sld*np.exp(i_r_dot_q), axis=0)
            else:
                fq[direction_index, :] += np.sum(sld*np.exp(i_r_dot_q), axis=0)

    f_squared = fq.real**2 + fq.imag**2
    f_squared *= direction_weights.reshape(-1,1)

    return np.sum(f_squared, axis=0)



