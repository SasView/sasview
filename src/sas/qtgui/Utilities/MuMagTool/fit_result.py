from dataclasses import dataclass

import numpy as np

from sas.qtgui.Utilities.MuMagTool.experimental_data import ExperimentalData
from sas.qtgui.Utilities.MuMagTool.fit_parameters import ExperimentGeometry


@dataclass
class FitResults:
    """ Output the MuMag fit """
    truncated_input_data: list[ExperimentalData]

    q: np.ndarray
    I_fit: np.ndarray

    S_H: np.ndarray
    S_M: np.ndarray

    I_residual: np.ndarray  # Nuclear + Magnetic cross section at complete magnetic saturation

    exchange_A: np.ndarray
    exchange_A_chi_sq: np.ndarray

    optimal_A: float
    optimal_A_chi_sq: float
    optimal_A_stdev: float # check

    geometry: ExperimentGeometry

