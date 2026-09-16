from dataclasses import dataclass
from enum import Enum
from typing import Generic, TypeVar

import numpy as np

from sasdata.quantities.quantity import Quantity
from sasdata.trend import Trend

""" Data structures used in MuMag"""

#
# Errors
#


class LoadFailure(Exception):
    """ File loading failed """
    pass


class FitFailure(Exception):
    """ Fit failed """
    pass

#
# Enums
#


class ExperimentGeometry(Enum):
    """ Type of experiment """
    PARALLEL = 1
    PERPENDICULAR = 2

#
# Data classes
#


@dataclass
class FitParameters:
    """ Input parameters for the fit"""
    q_max: Quantity
    min_applied_field: Quantity
    exchange_A_min: Quantity
    exchange_A_max: Quantity
    exchange_A_n: int
    experiment_geometry: ExperimentGeometry


@dataclass
class LeastSquaresOutput:
    """ Output from least squares method"""
    exchange_A: float
    exchange_A_chi_sq: float
    q: np.ndarray
    I_simulated: np.ndarray
    I_residual: np.ndarray
    S_H: np.ndarray
    I_residual_stdev: np.ndarray
    S_H_stdev: np.ndarray


@dataclass
class LeastSquaresOutputParallel(LeastSquaresOutput):
    """ Output from least squares method for parallel case"""
    pass


@dataclass
class LeastSquaresOutputPerpendicular(LeastSquaresOutput):
    """ Output from least squares method for perpendicular case"""
    S_M: np.ndarray
    S_M_stdev: np.ndarray


T = TypeVar("T", bound=LeastSquaresOutput)


@dataclass
class SweepOutput(Generic[T]):
    """
    Results from brute force optimisiation of the chi squared for the exchange A parameter
    """

    exchange_A_checked: np.ndarray
    exchange_A_chi_sq: np.ndarray
    optimal: T


@dataclass
class FitResults:
    """ Output the MuMag fit """
    parameters: FitParameters
    input_trend: Trend
    sweep_data: SweepOutput
    refined_fit_data: LeastSquaresOutputParallel | LeastSquaresOutputPerpendicular
    optimal_exchange_A_uncertainty: float
