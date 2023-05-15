from typing import Dict, DefaultDict, Callable, Optional, Any, Tuple, Union
from enum import Enum
from dataclasses import dataclass

import time

import numpy as np

from sampling import SpatialSample, QSample

CoordinateTransform = Callable[[np.ndarray, np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray, np.ndarray]]

class OutputType(Enum):
    SLD_1D = "1D"
    SLD_2D = "2D"
    MAGNETIC_1D = "Magnetic 1D"
    MAGNETIC_2D = "Magnetic 2D"

class OrientationalDistribution(Enum):
    FIXED = "Fixed"
    UNORIENTED = "Unoriented"


@dataclass
class ScatteringCalculation:
    """ Specification for a scattering calculation """
    solvent_sld: float
    output_type: OutputType
    orientation: OrientationalDistribution
    spatial_sampling_method: SpatialSample
    q_sampling_method: QSample
    sld_function: Any
    sld_function_from_cartesian: CoordinateTransform
    sld_function_parameters: Dict[str, float]
    magnetism_function: Any
    magnetism_function_from_cartesian: Optional[CoordinateTransform]
    magnetism_function_parameters: Optional[Dict[str, float]]
    magnetism_vector: Optional[np.ndarray]


@dataclass
class ScatteringOutput:
    output_type: OutputType
    q_sampling_method: QSample
    spatial_sampling_method: SpatialSample
    intensity_data: np.ndarray
    calculation_time: float

def calculate_scattering(calculation: ScatteringCalculation) -> ScatteringOutput:
    """ Main function for calculating scattering"""

    start_time = time.time() # Track how long it takes

    # Calculate contribution of SLD
    if calculation.orientation == OrientationalDistribution.UNORIENTED:

        if calculation.output_type == OutputType.SLD_2D:
            raise NotImplementedError("2D scattering not implemented yet")

        # input samples
        q = calculation.q_sampling_method()
        x, y, z = calculation.spatial_sampling_method()

        # evaluate sld
        input_coordinates = calculation.sld_function_from_cartesian(x,y,z)
        sld = calculation.sld_function(*input_coordinates, **calculation.sld_function_parameters)
        sld -= calculation.solvent_sld

        # Do the integration
        r = np.sqrt(x**2 + y**2 + z**2)
        qr = np.outer(q, r)

        intensity = np.sum(np.sin(qr) / qr, axis=1)**2



    elif calculation.orientation == OrientationalDistribution.FIXED:

        raise NotImplementedError("Oriented particle not implemented yet")



    # Calculate magnet contribution
    # TODO: implement magnetic scattering


    # Wrap up

    calculation_time = time.time() - start_time

    return ScatteringOutput(
        output_type=calculation.output_type,
        q_sampling_method=calculation.q_sampling_method,
        spatial_sampling_method=calculation.spatial_sampling_method,
        intensity_data=intensity,
        calculation_time=calculation_time)