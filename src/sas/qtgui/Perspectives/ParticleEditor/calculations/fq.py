from typing import Optional, Tuple
import time

import numpy as np
from scipy.interpolate import interp1d
from scipy.special import jv as bessel
from scipy.spatial.distance import cdist

from sas.qtgui.Perspectives.ParticleEditor.datamodel.calculation import (
    ScatteringCalculation, ScatteringOutput, OrientationalDistribution, SamplingDistribution,
    QPlotData, QSpaceCalcDatum, RealPlotData,
    SLDDefinition, MagnetismDefinition, SpatialSample, QSample, CalculationParameters)

from sas.qtgui.Perspectives.ParticleEditor.sampling.chunking import SingleChunk, pairwise_chunk_iterator
from sas.qtgui.Perspectives.ParticleEditor.sampling.points import PointGenerator, PointGeneratorStepper

from sas.qtgui.Perspectives.ParticleEditor.calculations.run_function import run_sld, run_magnetism

def scattering_via_fq(
        sld_definition: SLDDefinition,
        magnetism_definition: Optional[MagnetismDefinition],
        parameters: CalculationParameters,
        point_generator: PointGenerator,
        q_sample: QSample,
        q_normal_vector: np.ndarray,
        chunk_size=1_000_000) -> np.ndarray:

    q_magnitudes = q_sample()

    fq = None

    for x, y, z in PointGeneratorStepper(point_generator, chunk_size):

        sld = run_sld(sld_definition, parameters, x, y, z)

        # TODO: Magnetism

        r = np.sqrt(x*q_normal_vector[0] + y*q_normal_vector[1] + z*q_normal_vector[2])

        i_r_dot_q = np.multiply.outer(r, 1j*q_magnitudes)

        if fq is None:
            fq = np.sum(sld*np.exp(i_r_dot_q), axis=0)
        else:
            fq += np.sum(sld*np.exp(i_r_dot_q), axis=0)

    return fq.real**2 + fq.imag**2 # Best way to avoid pointless square roots in np.abs



