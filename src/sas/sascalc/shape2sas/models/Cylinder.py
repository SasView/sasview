import numpy as np
from sas.sascalc.shape2sas.Typing import Vector3D


class Cylinder:
    def __init__(self, dimensions: list[float]):
        self.R = dimensions[0]
        self.l = dimensions[1]

    def getVolume(self) -> float:
        """Returns the volume of a cylinder"""
        return np.pi * self.R**2 * self.l

    def getPointDistribution(self, Npoints: int) -> Vector3D:
        """Returns the point distribution of a cylinder"""
        Volume = self.getVolume()
        Volume_max = 2 * self.R * 2 * self.R * self.l
        Vratio = Volume_max / Volume

        N = int(Vratio * Npoints)
        x = np.random.uniform(-self.R, self.R, N)
        y = np.random.uniform(-self.R, self.R, N)
        z = np.random.uniform(-self.l / 2, self.l / 2, N)
        d = np.sqrt(x**2 + y**2)
        idx = np.where(d < self.R)
        x_add,y_add,z_add = x[idx],y[idx],z[idx]

        return x_add, y_add, z_add

    def checkOverlap(self, x_eff: np.ndarray,
                           y_eff: np.ndarray,
                           z_eff: np.ndarray) -> np.ndarray:
        """Check for points within a cylinder"""
        d = np.sqrt(x_eff**2+y_eff**2)
        idx = np.where((d > self.R) | (abs(z_eff) > self.l / 2))
        return idx
