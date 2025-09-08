
import numpy as np

from sas.qtgui.Perspectives.ParticleEditor.calculations.run_function import run_sld
from sas.qtgui.Perspectives.ParticleEditor.datamodel.calculation import (
    CalculationParameters,
    MagnetismDefinition,
    QSample,
    SLDDefinition,
)
from sas.qtgui.Perspectives.ParticleEditor.sampling.chunking import SingleChunk, pairwise_chunk_iterator
from sas.qtgui.Perspectives.ParticleEditor.sampling.points import SpatialDistribution


def debye(
        sld_definition: SLDDefinition,
        magnetism_definition: MagnetismDefinition | None,
        parameters: CalculationParameters,
        point_generator: SpatialDistribution,
        q_sample: QSample,
        minor_chunk_size=1000,
        preallocate=True):

    q = q_sample()

    output = np.zeros_like(q)


    # First chunking layer, chunks for dealing with VERY large sample densities
    # Uses less memory at the cost of using more processing power
    for (x1_large, y1_large, z1_large), (x2_large, y2_large, z2_large) in SingleChunk(point_generator):
        sld1 = run_sld(sld_definition, parameters, x1_large, y1_large, z1_large)
        sld2 = run_sld(sld_definition, parameters, x2_large, y2_large, z2_large)

        if magnetism_definition is None:

            sld1_total_large = sld1
            sld2_total_large = sld2

        else:
            raise NotImplementedError("Magnetism not implemented yet")
            # TODO: implement magnetism



        # TODO: Preallocation, do we want it
        if preallocate:
            r_data_1 = np.zeros((minor_chunk_size, minor_chunk_size))
            r_data_2 = np.zeros((minor_chunk_size, minor_chunk_size))
            rq_data = np.zeros((minor_chunk_size**2, q_sample.n_points))

        for one, two in pairwise_chunk_iterator(
                left_data=(x1_large, y1_large, z1_large, sld1_total_large),
                right_data=(x2_large, y2_large, z2_large, sld2_total_large),
                chunk_size=minor_chunk_size):

            (x1, y1, z1, sld_total_1) = one
            (x2, y2, z2, sld_total_2) = two

            # Optimised calculation of euclidean distance, use pre-allocated memory

            if preallocate:
                n1 = len(x1)
                n2 = len(x2)

                r_data_1[:n1, :n2] = np.subtract.outer(x1, x2)
                r_data_1 **= 2

                r_data_2[:n1, :n2] = np.subtract.outer(y1, y2)
                r_data_1[:n1, :n2] += r_data_2[:n1, :n2] ** 2

                r_data_2[:n1, :n2] = np.subtract.outer(z1, z2)
                r_data_1[:n1, :n2] += r_data_2[:n1, :n2] ** 2

                np.sqrt(r_data_1, out=r_data_1) # in place sqrt

                r_data_2[:n1, :n2] = np.multiply.outer(sld_total_1, sld_total_2)

                # Build a table of r times q values

                rq_data[:(n1 * n2), :] = np.multiply.outer(r_data_1[:n1, :n2].reshape(-1), q)

                # Calculate sinc part
                rq_data[:(n1 * n2), :] = np.sinc(rq_data[:(n1 * n2), :])


                # Multiply by paired density
                rq_data[:(n1 * n2), :] *= r_data_2[:n1, :n2].reshape(-1, 1)


                # Multiply by r squared
                np.multiply(r_data_1, r_data_1, out=r_data_1)
                rq_data[:(n1 * n2), :] *= r_data_1[:n1, :n2].reshape(-1, 1)

                # Add to q data
                output += np.sum(rq_data, axis=0)

            else:

                # Non optimised
                r_squared = np.subtract.outer(x1, x2) ** 2 + \
                                np.subtract.outer(y1, y2) ** 2 + \
                                np.subtract.outer(z1, z2) ** 2

                # print(r_squared.shape)

                correl = sld_total_1.reshape(1, -1) * sld_total_2.reshape(-1, 1)
                correl = correl.reshape(-1, 1)

                rq = np.sqrt(r_squared.reshape(-1, 1)) * q.reshape(1,-1)

                # print(rq.shape)

                output += np.sum(r_squared.reshape(-1, 1) * correl * np.sinc(rq), axis=0)
                # output += np.sum(r_squared.reshape(-1, 1) * correl * np.sinc(rq), axis=0)


    return output
