from sas.sascalc.shape2sas.Typing import *


class Cube:
    def __init__(self, dimensions: list[float]):
        self.a = dimensions[0]

    def getVolume(self) -> float:
        """Returns the volume of a cube"""
        return self.a**3

    def getPointDistribution(self, Npoints: int) -> Vector3D:
        """Returns the point distribution of a cube"""

        #Volume = self.getVolume()
        N = Npoints
        x_add = np.random.uniform(-self.a / 2, self.a / 2, N)
        y_add = np.random.uniform(-self.a / 2, self.a / 2, N)
        z_add = np.random.uniform(-self.a / 2, self.a / 2, N)
        return x_add, y_add, z_add

    def checkOverlap(self, x_eff: np.ndarray, 
                           y_eff: np.ndarray, 
                           z_eff: np.ndarray) -> np.ndarray:
        """Check for points within a cube"""
        idx = np.where((abs(x_eff) >= self.a/2) | (abs(y_eff) >= self.a/2) | 
            (abs(z_eff) >= self.a/2))
        return idx