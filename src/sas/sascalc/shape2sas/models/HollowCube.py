from sas.sascalc.shape2sas.Typing import *


class HollowCube:
    def __init__(self, dimensions: list[float]):
        self.a = dimensions[0]
        self.b = dimensions[1]

    def getVolume(self) -> float:
        """Returns the volume of a hollow cube"""

        if self.a < self.b:
            self.a, self.b = self.b, self.a

        if self.a == self.b:
            return 6 * self.a**2 #surface area of a cube

        else:
            return (self.a - self.b)**3

    def getPointDistribution(self, Npoints: int) -> Vector3D:
        """Returns the point distribution of a hollow cube"""

        Volume = self.getVolume()

        if self.a == self.b:
            #The hollow cube is a shell
            d = self.a / 2
            N = int(Npoints / 6)
            one = np.ones(N)

            #make each side of the cube at a time
            x_add, y_add, z_add = [], [], []
            for sign in [-1, 1]:
                x_add = np.concatenate((x_add, sign * one * d))
                y_add = np.concatenate((y_add, np.random.uniform(-d, d, N)))
                z_add = np.concatenate((z_add, np.random.uniform(-d, d, N)))

                x_add = np.concatenate((x_add, np.random.uniform(-d, d, N)))
                y_add = np.concatenate((y_add, sign * one * d))
                z_add = np.concatenate((z_add, np.random.uniform(-d, d, N)))

                x_add = np.concatenate((x_add, np.random.uniform(-d, d, N)))
                y_add = np.concatenate((y_add, np.random.uniform(-d, d, N)))
                z_add = np.concatenate((z_add, sign * one * d))
            return x_add, y_add, z_add

        Volume_max = self.a**3
        Vratio = Volume_max / Volume
        N = int(Vratio * Npoints)

        x = np.random.uniform(-self.a / 2,self.a / 2, N)
        y = np.random.uniform(-self.a / 2,self.a / 2, N)
        z = np.random.uniform(-self.a / 2,self.a / 2, N)

        d = np.maximum.reduce([abs(x), abs(y), abs(z)])
        idx = np.where(d >= self.b / 2)
        x_add,y_add,z_add = x[idx], y[idx], z[idx]

        return x_add, y_add, z_add

    def checkOverlap(self, x_eff: np.ndarray,
                           y_eff: np.ndarray,
                           z_eff: np.ndarray) -> np.ndarray:
        """Check for points within a hollow cube"""

        if self.a < self.b:
            self.a, self.b = self.b, self.a

        if self.a == self.b:
            idx = np.where((abs(x_eff)!=self.a/2) | (abs(y_eff)!=self.a/2) | (abs(z_eff)!=self.a/2))
            return idx

        else:
            idx = np.where((abs(x_eff) >= self.a/2) | (abs(y_eff) >= self.a/2) |
            (abs(z_eff) >= self.a/2) | ((abs(x_eff) <= self.b/2)
            & (abs(y_eff) <= self.b/2) & (abs(z_eff) <= self.b/2)))

        return idx
