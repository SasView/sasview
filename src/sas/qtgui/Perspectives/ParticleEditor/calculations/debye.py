from typing import Optional, Tuple
import time

import numpy as np
from scipy.interpolate import interp1d

from scipy.special import jv as bessel

from sas.qtgui.Perspectives.ParticleEditor.datamodel.calculation import (
    ScatteringCalculation, ScatteringOutput, OrientationalDistribution, SamplingDistribution,
    QPlotData, QSpaceCalcDatum, RealPlotData,
    SLDDefinition, MagnetismDefinition, SpatialSample, QSample, CalculationParameters)

from sas.qtgui.Perspectives.ParticleEditor.sampling.chunking import SingleChunk

from sas.qtgui.Perspectives.ParticleEditor.calculations.run_function import run_sld, run_magnetism

def debye(
        sld_definition: SLDDefinition,
        magnetism_definition: Optional[MagnetismDefinition],
        parameters: CalculationParameters,
        spatial_sample: SpatialSample,
        q_sample: QSample):

    # First chunking layer, chunks for dealing with VERY large sample densities
    # Uses less memory at the cost of using more processing power
    for (x1, y1, z1), (x2, y2, z2) in SingleChunk(spatial_sample):
        sld1 = run_sld(sld_definition, parameters, x1, y1, z1)
        sld2 = run_sld(sld_definition, parameters, x2, y2, z2)

        if magnetism_definition is not None:
            pass
            # TODO: implement magnetism

