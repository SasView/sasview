from OpenGL.GL import glColor4f
import numpy as np

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