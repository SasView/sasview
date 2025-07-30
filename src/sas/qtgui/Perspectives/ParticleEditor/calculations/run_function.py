""" Helper functions that run SLD and magnetism functions """
import numpy as np

from sas.qtgui.Perspectives.ParticleEditor.datamodel.calculation import (
    CalculationParameters,
    MagnetismDefinition,
    SLDDefinition,
)
from sas.qtgui.Perspectives.ParticleEditor.datamodel.types import VectorComponents3


def run_sld(sld_definition: SLDDefinition, parameters: CalculationParameters, x: np.ndarray, y: np.ndarray, z: np.ndarray) -> np.ndarray:
    """ Evaluate the SLD function from the definition object at specified coordinates """

    sld_function = sld_definition.sld_function
    coordinate_transform = sld_definition.to_cartesian_conversion

    a, b, c = coordinate_transform(x, y, z)

    solvent_sld = parameters.solvent_sld # Hopefully the function can see this, but TODO: take py file environment with us from editor
    parameter_dict = parameters.sld_parameters.copy()

    return sld_function(a, b, c, **parameter_dict) - solvent_sld


def run_magnetism(magnetism_definition: MagnetismDefinition, parameters: CalculationParameters, x: np.ndarray, y: np.ndarray, z: np.ndarray) -> VectorComponents3:
    """ Evaluate the magnetism function from the definition at specified coordinates """

    magnetism_function = magnetism_definition.magnetism_function
    coordinate_transform = magnetism_definition.to_cartesian_conversion

    a, b, c = coordinate_transform(x, y, z)

    solvent_sld = parameters.solvent_sld # Hopefully the function can see this, but TODO: take py file environment with us from editor
    parameter_dict = parameters.sld_parameters.copy()

    return magnetism_function(a, b, c, **parameter_dict)
