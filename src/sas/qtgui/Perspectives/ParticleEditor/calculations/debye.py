from typing import Optional, Tuple
import time

import numpy as np
from scipy.interpolate import interp1d

from scipy.special import jv as bessel

from sas.qtgui.Perspectives.ParticleEditor.datamodel.calculation import (
    ScatteringCalculation, ScatteringOutput, OrientationalDistribution, SamplingDistribution,
    QPlotData, QSpaceCalcDatum, RealPlotData,
    SLDDefinition, MagnetismDefinition, SpatialSample, QSample, CalculationParameters)

def debye(
        sld_function: SLDDefinition,
        magnetism_function: Optional[MagnetismDefinition],
        parameters: CalculationParameters,
        spatial_sample: SpatialSample,
        q_sample: QSample):

    for (x1, y1, z1), (x2, y2, z2) in