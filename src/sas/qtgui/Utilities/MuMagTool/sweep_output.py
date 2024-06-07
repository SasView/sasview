from dataclasses import dataclass

import numpy as np

from sas.qtgui.Utilities.MuMagTool.least_squares_output import LeastSquaresOutput

from typing import Generic, TypeVar

T = TypeVar("T", bound=LeastSquaresOutput)

@dataclass
class SweepOutput(Generic[T]):
    """
    Results from brute force optimisiation of the chi squared for the exchange A parameter
    """

    exchange_A_checked: np.ndarray
    exchange_A_chi_sq: np.ndarray
    optimal: T

