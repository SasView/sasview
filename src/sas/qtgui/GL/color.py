from typing import Sequence, Union

import logging
import numpy as np
import matplotlib as mpl
from enum import Enum
from dataclasses import dataclass

from OpenGL.GL import glColor4f

"Helper classes for dealing with colours"

logger = logging.getLogger("GL.Color")

class ColorSpecificationMethod(Enum):
    """ Specifies how to colour an object"""
    UNIFORM = 1         # Whole object a single colour
    BY_COMPONENT = 2    # Each mesh or edge within the object a single colour
    BY_VERTEX = 3       # Vertex colouring for the whole object

@dataclass
class ColorSpecification:
    """ Specification of how to colour an object, and the data needed to do so"""
    method: ColorSpecificationMethod
    data: np.ndarray


def uniform_coloring(r, g, b, alpha=1.0):
    """ Create a ColorSpecification for colouring with a single colour"""
    return ColorSpecification(
        method=ColorSpecificationMethod.UNIFORM,
        data=np.array([r, g, b, alpha]))


def edge_coloring(data: Sequence[Union[Sequence[float], np.ndarray]]) -> ColorSpecification:
    """ Create a ColorSpecification for colouring each edge within an object a single colour"""
    return _component_coloring(data)


def mesh_coloring(data: Sequence[Union[Sequence[float], np.ndarray]]) -> ColorSpecification:
    """ Create a ColorSpecification for colouring each mesh within an object a single colour"""
    return _component_coloring(data)


def _component_coloring(data: Sequence[Union[Sequence[float], np.ndarray]]) -> ColorSpecification:
    """ Create a ColorSpecification for colouring each mesh/edge within an object a single colour"""
    try:
        data = np.array(data)
    except:
        raise ValueError("Colour data should be all n-by-3 or n-by-4")

    if data.shape[1] == 3:
        data = np.concatenate((data, np.ones((data.shape[0], 1))), axis=1)
    elif data.shape[1] == 4:
        pass
    else:
        raise ValueError("Colour data should be all n-by-3 or n-by-4")

    return ColorSpecification(ColorSpecificationMethod.BY_COMPONENT, data)


def vertex_coloring(data: np.ndarray) -> ColorSpecification:
    """ Create a ColorSpecification for using vertex colouring"""
    try:
        data = np.array(data)
    except:
        raise ValueError("Colour data should be all n-by-3 or n-by-4")

    if data.shape[1] == 3:
        data = np.concatenate((data, np.ones((data.shape[0], 1))), axis=1)
    elif data.shape[1] == 4:
        pass
    else:
        raise ValueError("Colour data should be all n-by-3 or n-by-4")

    return ColorSpecification(ColorSpecificationMethod.BY_VERTEX, data)


class ColorMap():

    _default_colormap = 'rainbow'
    def __init__(self, colormap_name=_default_colormap, min_value=0.0, max_value=1.0):
        """ Utility class for colormaps, principally used for mapping data in Surface"""
        try:
            self.colormap = mpl.colormaps[colormap_name]
        except KeyError:
            logger.warning(f"Bad colormap name '{colormap_name}'")
            self.colormap = mpl.colormaps[ColorMap._default_colormap]

        self.min_value = min_value
        self.max_value = max_value

    def vertex_coloring(self, values: np.ndarray):
        """ Evaluate the color map and return a ColorSpecification object"""
        scaled = (values - self.min_value) / (self.max_value - self.min_value)
        scaled = np.clip(scaled, 0, 1)
        return vertex_coloring(self.colormap(scaled))
