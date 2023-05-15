from typing import Dict, Callable
from enum import Enum

import numpy as np

CoordinateTransform = Callable[[np.ndarray, np.ndarray, np.ndarray], (np.ndarray, np.ndarray, np.ndarray)]

class OutputType(Enum):
    SLD_1D = "1D"
    SLD_2D = "2D"
    MAGNETIC_1D = "Magnetic 1D"
    MAGNETIC_2D = "Magnetic 2D"

class OrientationalDistribution(Enum):
    FIXED = "Fixed"
    UNORIENTED = "Unoriented"


class ScatteringCalculation:
    def __init__(self,
                 radius: float,
                 solvent_sld: float,
                 output_type: OutputType,
                 sld_function: Callable,
                 sld_function_from_cartesian: CoordinateTransform,
                 sld_function_parameters: Dict[str, float],
                 magnetism_function: Callable,
                 magnetism_function_from_cartesian: CoordinateTransform,
                 magnetism_function_parameters: Dict[str, float],

                 ):
        pass