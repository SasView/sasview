from sas.sascalc.shape2sas.Typing import *
from scipy.special import gamma

class SuperEllipsoid:
    def __init__(self, dimensions: List[float]):
        self.R = dimensions[0]
        self.eps = dimensions[1]
        self.t = dimensions[2]
        self.s = dimensions[3]

    @staticmethod
    def beta(a, b) -> float:
        """beta function"""

        return gamma(a) * gamma(b) / gamma(a + b)

    def getVolume(self) -> float:
        """Returns the volume of a superellipsoid"""

        return (8 / (3 * self.t * self.s) * self.R**3 * self.eps * 
                self.beta(1 / self.s, 1 / self.s) * self.beta(2 / self.t, 1 / self.t))

    def getPointDistribution(self, Npoints: int) -> Vector3D:
        """Returns the point distribution of a superellipsoid"""
        Volume = self.getVolume()
        Volume_max = 2 * self.R * self.eps * 2 * self.R * 2 * self.R
        Vratio = Volume_max / Volume

        N = int(Vratio * Npoints)
        x = np.random.uniform(-self.R, self.R, N)
        y = np.random.uniform(-self.R, self.R, N)
        z = np.random.uniform(-self.R * self.eps, self.R * self.eps, N)

        d = ((np.abs(x)**self.s + np.abs(y)**self.s)**(self.t/ self.s) 
            + np.abs(z / self.eps)**self.t)
        idx = np.where(d < np.abs(self.R)**self.t)
        x_add, y_add, z_add = x[idx], y[idx], z[idx]

        return x_add, y_add, z_add

    def checkOverlap(self, x_eff: np.ndarray, 
                           y_eff: np.ndarray, 
                           z_eff: np.ndarray) -> np.ndarray:
        """Check for points within a superellipsoid"""
        d = ((np.abs(x_eff)**self.s + np.abs(y_eff)**self.s)**(self.t / self.s) 
        + np.abs(z_eff / self.eps)**self.t)
        idx = np.where(d >= np.abs(self.R)**self.t)

        return idx