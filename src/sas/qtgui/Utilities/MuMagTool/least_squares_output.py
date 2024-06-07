from dataclasses import dataclass

import numpy as np


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

