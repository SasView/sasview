from typing import Optional, Tuple
import time

import numpy as np
from scipy.interpolate import interp1d

from scipy.special import jv as bessel

from sas.qtgui.Perspectives.ParticleEditor.datamodel.calculation import (
    ScatteringCalculation, ScatteringOutput, OrientationalDistribution, SamplingDistribution,
    QPlotData, QSpaceCalcDatum, RealPlotData,
    SLDDefinition, MagnetismDefinition, SpatialSample, QSample, CalculationParameters)

from sas.qtgui.Perspectives.ParticleEditor.sampling.chunking import SingleChunk, pairwise_chunk_iterator

from sas.qtgui.Perspectives.ParticleEditor.calculations.run_function import run_sld, run_magnetism

def debye(
        sld_definition: SLDDefinition,
        magnetism_definition: Optional[MagnetismDefinition],
        parameters: CalculationParameters,
        spatial_sample: SpatialSample,
        q_sample: QSample,
        minor_chunk_size=1000,
        preallocate=True):

    q = q_sample().reshape(1,-1)

    output = np.zeros_like(q)


    # First chunking layer, chunks for dealing with VERY large sample densities
    # Uses less memory at the cost of using more processing power
    for (x1_large, y1_large, z1_large), (x2_large, y2_large, z2_large) in SingleChunk(spatial_sample):
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

        for (x1, y1, z1, sld_total_1), (x2, y2, z2, sld_total_2) in pairwise_chunk_iterator(
                left_data=(x1_large, y1_large, z1_large, sld1_total_large),
                right_data=(x2_large, y2_large, z2_large, sld2_total_large),
                chunk_size=minor_chunk_size):



            # Optimised calculation of euclidean distance, use pre-allocated memory

            if preallocate:
                n1 = len(x1)
                n2 = len(x2)

                r_data_1[:n1, :n2] = x1.reshape(1, -1) - x2.reshape(-1, 1)
                r_data_1 **= 2

                r_data_2[:n1, :n2] = y1.reshape(1, -1) - y2.reshape(-1, 1)
                r_data_1[:n1, :n2] += r_data_2**2

                r_data_2[:n1, :n2] += z1.reshape(1, -1) - z2.reshape(-1, 1)
                r_data_1[:n1, :n2] += r_data_2 ** 2

                np.sqrt(r_data_1, out=r_data_1) # in place sqrt

                r_data_2[:n1, :n2] = sld_total_1.reshape(1, -1) * sld_total_2.reshape(-1, 1)

                # Build a table of r times q values

                rq_data[:(n1 * n2), :] = r_data_1.reshape(-1, 1) * q.reshape(1, -1)

                # Calculate sinc part
                rq_data[:(n1 * n2), :] = np.sinc(rq_data[:(n1 * n2), :])


                # Multiply by paired density
                rq_data[:(n1 * n2), :] *= r_data_2.reshape(-1, 1)


                # Multiply by r squared
                np.multiply(r_data_1, r_data_1, out=r_data_1)
                rq_data[:(n1 * n2), :] *= r_data_1.reshape(-1, 1)

                # Add to q data
                output += np.sum(rq_data, axis=1)

            else:

                # Non optimised
                r_squared = (x1.reshape(1, -1) - x2.reshape(-1, 1)) ** 2 + \
                            (y1.reshape(1, -1) - y2.reshape(-1, 1)) ** 2 + \
                            (z1.reshape(1, -1) - z2.reshape(-1, 1)) ** 2
