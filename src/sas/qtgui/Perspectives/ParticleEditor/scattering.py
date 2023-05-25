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
    sample_chunk_size_hint: int = 100_000


@dataclass
class ScatteringOutput:
    output_type: OutputType
    q_sampling_method: QSample
    spatial_sampling_method: SpatialSample
    intensity_data: np.ndarray
    r_values: np.ndarray
    realspace_intensity: np.ndarray
    calculation_time: float

def calculate_scattering(calculation: ScatteringCalculation) -> ScatteringOutput:
    """ Main function for calculating scattering"""

    start_time = time.time() # Track how long it takes

    # Calculate contribution of SLD
    if calculation.orientation == OrientationalDistribution.UNORIENTED:

        if calculation.output_type == OutputType.SLD_2D:
            raise NotImplementedError("2D scattering not implemented yet")

        # Try a different method, estimate the radial distribution
        n_r = 1000
        n_r_upscale = 10000
        bin_edges = np.linspace(0,2*calculation.spatial_sampling_method.radius, n_r+1)
        bin_size = 2*calculation.spatial_sampling_method.radius / n_r

        sld_total = None
        counts = None

        for (x0, y0, z0), (x1, y1, z1) in calculation.spatial_sampling_method.pairs(calculation.sample_chunk_size_hint):

            # evaluate sld
            input_coordinates1 = calculation.sld_function_from_cartesian(x0, y0, z0)
            input_coordinates2 = calculation.sld_function_from_cartesian(x1, y1, z1)

            sld1 = calculation.sld_function(*input_coordinates1, **calculation.sld_function_parameters)
            sld1 -= calculation.solvent_sld
            #
            sld2 = calculation.sld_function(*input_coordinates2, **calculation.sld_function_parameters)
            sld2 -= calculation.solvent_sld

            rho = sld1*sld2
            # rho = sld1

            # Do the integration
            sample_rs = np.sqrt((x1 - x0)**2 + (y1 - y0)**2 + (z1 - z0)**2)
            # sample_rs = np.sqrt(x0**2 + y0**2 + z0**2)

            if sld_total is None:
                sld_total = np.histogram(sample_rs, bins=bin_edges, weights=rho)[0]
                counts = np.histogram(sample_rs, bins=bin_edges)[0]
            else:
                sld_total += np.histogram(sample_rs, bins=bin_edges, weights=rho)[0]
                counts += np.histogram(sample_rs, bins=bin_edges)[0]

        if counts is None or sld_total is None:
            raise ValueError("No sample points")


        # Remove all zero count bins
        non_empty_bins = counts > 0

        # print(np.count_nonzero(non_empty_bins))

        r_small = (bin_edges[:-1] + 0.5 * bin_size)[non_empty_bins]
        averages = sld_total[non_empty_bins] / counts[non_empty_bins]

        r_large = np.arange(1, n_r_upscale + 1) * (2*calculation.spatial_sampling_method.radius / n_r_upscale)


        # Upscale, and weight by 1/r^2
        new_averages = np.interp(r_large, r_small, averages)

        # Do transform
        q = calculation.q_sampling_method()
        qr = np.outer(q, r_large)

        # Power of q must be -1 for correct slope at low q

        # f = np.sum((new_averages * (r_large * r_large)) * np.sin(qr) / qr, axis=1) # Correct for sphere with COM sampling
        f = np.sum((new_averages * (r_large ** 3)) * np.sin(qr) / qr, axis=1) # Correct for sphere with COM sampling
        # f = np.sum((new_averages * (r_large ** 4)) * np.sin(qr) / qr, axis=1) # Correct for sphere with COM sampling
        # f = np.sum((new_averages*r_large*r_large) * np.sin(qr) / (qr**3), axis=1)
        # f = np.sum((new_averages * r_large) * np.sin(qr) / qr, axis=1)
        # f = np.sum(new_averages * np.sin(qr) / qr, axis=1)
        # f = np.sum(new_averages / r_large * np.sin(qr) / qr, axis=1)
        # f = np.sum(new_averages / (r_large**2) * np.sin(qr) / qr, axis=1)

        intensity = f*f # Correct for sphere with COM sampling
        # intensity = np.abs(f)
        # intensity = f

        # Calculate magnet contribution
        # TODO: implement magnetic scattering

        # Wrap up

        calculation_time = time.time() - start_time

        return ScatteringOutput(
            output_type=calculation.output_type,
            q_sampling_method=calculation.q_sampling_method,
            spatial_sampling_method=calculation.spatial_sampling_method,
            intensity_data=intensity,
            calculation_time=calculation_time,
            r_values=r_large,
            realspace_intensity=new_averages)


    elif calculation.orientation == OrientationalDistribution.FIXED:

        raise NotImplementedError("Oriented particle not implemented yet")


