from typing import Sequence

import logging

import numpy as np

import matplotlib as mpl

from OpenGL.GL import glColor4f

logger = logging.getLogger("GL.Color")

class Color():
    def __init__(self, r: float, g: float, b: float, alpha: float=1.0):
        self.r = float(r)
        self.g = float(g)
        self.b = float(b)
        self.alpha = float(alpha)

    def set(self):
        glColor4f(self.r, self.g, self.b, self.alpha)

    def to_array(self):
        return np.array([self.r, self.g, self.b, self.alpha])

    def __repr__(self):
        return f"{self.__class__.__name__}({self.r}, {self.g}, {self.b}, {self.alpha})"


class ColorMap():

    _default_colormap = 'rainbow'
    def __init__(self, colormap_name=_default_colormap, min_value=0.0, max_value=1.0):

        try:
            self.colormap = mpl.colormaps[colormap_name]
        except KeyError:
            logger.warning(f"Bad colormap name '{colormap_name}'")
            self.colormap = mpl.colormaps[ColorMap._default_colormap]

        self.min_value = min_value
        self.max_value = max_value

    def color(self, value):
        scaled = (value - self.min_value) / (self.max_value - self.min_value)
        scaled = np.clip(scaled, 0, 1)
        return Color(*self.colormap(scaled))

    def color_array(self, values: Sequence[float]) -> Sequence[Color]:
        return [self.color(value) for value in values]
