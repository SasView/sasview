import numpy as np

from sas.sascalc.shape2sas.Typing import Vector3D


class Cuboid:
    def __init__(self, dimensions: list[float]):
        self.a = dimensions[0]
        self.b = dimensions[1]
        self.c = dimensions[2]

    def getVolume(self) -> float:
        """Returns the volume of a cuboid"""
        return self.a * self.b * self.c

    def getPointDistribution(self, Npoints: int) -> Vector3D:
        """Returns the point distribution of a cuboid"""
        x_add = np.random.uniform(-self.a, self.a, Npoints)
        y_add = np.random.uniform(-self.b, self.b, Npoints)
        z_add = np.random.uniform(-self.c, self.c, Npoints)
        return x_add, y_add, z_add

    def checkOverlap(self, x_eff: np.ndarray,
                           y_eff: np.ndarray,
                           z_eff: np.ndarray) -> np.ndarray:
        """Check for points within a Cuboid"""
        idx = np.where((abs(x_eff) >= self.a/2)
        | (abs(y_eff) >= self.b/2) | (abs(z_eff) >= self.c/2))
        return idx
