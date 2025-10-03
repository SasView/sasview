import numpy as np

from sas.sascalc.shape2sas.HelperFunctions import sinc
from sas.sascalc.shape2sas.Typing import *


class StructureDecouplingApprox:
    def __init__(self, q: np.ndarray,
                 x_new: np.ndarray,
                 y_new: np.ndarray,
                 z_new: np.ndarray,
                 p_new: np.ndarray):
        self.q = q
        self.x_new = x_new
        self.y_new = y_new
        self.z_new = z_new
        self.p_new = p_new

    def calc_com_dist(self) -> np.ndarray:
        """ 
        calc contrast-weighted com distance
        """
        w = np.abs(self.p_new)

        if np.sum(w) == 0:
            w = np.ones(len(self.x_new))

        x_com, y_com, z_com = np.average(self.x_new, weights=w), np.average(self.y_new, weights=w), np.average(self.z_new, weights=w)
        dx, dy, dz = self.x_new - x_com, self.y_new - y_com, self.z_new - z_com
        com_dist = np.sqrt(dx**2 + dy**2 + dz**2)

        return com_dist

    def calc_A00(self) -> np.ndarray:
        """
        calc zeroth order sph harm, for decoupling approximation
        """
        d_new = self.calc_com_dist()
        M = len(self.q)
        A00 = np.zeros(M)

        for i in range(M):
            qr = self.q[i] * d_new

            A00[i] = sum(self.p_new * sinc(qr))
        A00 = A00 / A00[0] # normalise, A00[0] = 1

        return A00

    def decoupling_approx(self, Pq: np.ndarray, S: np.ndarray) -> np.ndarray:
        """
        modify structure factor with the decoupling approximation
        for combining structure factors with non-spherical (or polydisperse) particles

        see, for example, Larsen et al 2020: https://doi.org/10.1107/S1600576720006500
        and refs therein

        input
        q
        x,y,z,p    : coordinates and contrasts
        Pq         : form factor
        S          : structure factor

        output
        S_eff      : effective structure factor, after applying decoupl. approx
        """

        A00 = self.calc_A00()
        const = 1e-3 # add constant in nominator and denominator, for stability (numerical errors for small values dampened)
        Beta = (A00**2 + const) / (Pq + const)
        S_eff = 1 + Beta * (S - 1)

        return S_eff


'''#template for the structure factor classes
class <NAME OF STRUCTURE FACTOR HERE>(StructureDecouplingApprox):
    def __init__(self, q: np.ndarray,
                    x_new: np.ndarray,
                    y_new: np.ndarray,
                    z_new: np.ndarray,
                    p_new: np.ndarray,
                    par: List[float]):
            super(<NAME OF STRUCTURE FACTOR HERE>, self).__init__(q, x_new, y_new, z_new, p_new)
            self.q = q
            self.x_new = x_new
            self.y_new = y_new
            self.z_new = z_new
            self.p_new = p_new
            self.par = par[0] <WRITE YOUR PARAMETERS HERE>

    def structure_eff(self, Pq: np.ndarray) -> np.ndarray:
        S = <STRUCTURE FACTOR HERE>
        S_eff = self.decoupling_approx(Pq, S)

        return S_eff
'''
