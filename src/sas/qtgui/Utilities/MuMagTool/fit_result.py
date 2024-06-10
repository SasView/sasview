from dataclasses import dataclass

import numpy as np

from sas.qtgui.Utilities.MuMagTool.experimental_data import ExperimentalData
from sas.qtgui.Utilities.MuMagTool.fit_parameters import ExperimentGeometry, FitParameters
from sas.qtgui.Utilities.MuMagTool.least_squares_output import LeastSquaresOutputPerpendicular, \
    LeastSquaresOutputParallel
from sas.qtgui.Utilities.MuMagTool.sweep_output import SweepOutput


@dataclass
class FitResults:
    """ Output the MuMag fit """
    parameters: FitParameters
    input_data: list[ExperimentalData]
    sweep_data: SweepOutput
    refined_fit_data: LeastSquaresOutputParallel | LeastSquaresOutputPerpendicular
    optimal_exchange_A_uncertainty: float
