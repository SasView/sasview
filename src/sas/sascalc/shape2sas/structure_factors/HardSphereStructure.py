import numpy as np

from sas.sascalc.shape2sas.structure_factors.StructureDecouplingApprox import StructureDecouplingApprox


class HardSphereStructure(StructureDecouplingApprox):
    def __init__(self, q: np.ndarray,
                 x_new: np.ndarray,
                 y_new: np.ndarray,
                 z_new: np.ndarray,
                 p_new: np.ndarray,
                 par: list[float]):
        super(HardSphereStructure, self).__init__(q, x_new, y_new, z_new, p_new)
        self.q = q
        self.x_new = x_new
        self.y_new = y_new
        self.z_new = z_new
        self.p_new = p_new
        self.conc = par[0]
        self.R_HS = par[1]

    def calc_S_HS(self) -> np.ndarray:
        """
        calculate the hard-sphere structure factor
        calls function calc_G()

        input
        q       : momentum transfer
        eta     : volume fraction
        R       : estimation of the hard-sphere radius

        output
        S_HS    : hard-sphere structure factor
        """

        if self.conc > 0.0:
            A = 2 * self.R_HS * self.q
            G = self.calc_G(A, self.conc)
            S_HS = 1 / (1 + 24 * self.conc * G / A) #percus-yevick approximation for
        else:                         #calculating the structure factor
            S_HS = np.ones(len(self.q))

        return S_HS

    @staticmethod
    def calc_G(A: np.ndarray, eta: float) -> np.ndarray:
        """ 
        calculate G in the hard-sphere potential

        input
        A  : 2*R*q
        q  : momentum transfer
        R  : hard-sphere radius
        eta: volume fraction

        output:
        G  
        """

        a = (1 + 2 * eta)**2 / (1 - eta)**4
        b = -6 * eta * (1 + eta / 2)**2/(1 - eta)**4
        c = eta * a / 2
        sinA = np.sin(A)
        cosA = np.cos(A)
        fa = sinA - A * cosA
        fb = 2 * A * sinA + (2 - A**2) * cosA-2
        fc = -A**4 * cosA + 4 * ((3 * A**2 - 6) * cosA + (A**3 - 6 * A) * sinA + 6)
        G = a * fa / A**2 + b * fb / A**3 + c * fc / A**5

        return G

    def structure_eff(self, Pq: np.ndarray) -> np.ndarray:
        S = self.calc_S_HS()
        S_eff = self.decoupling_approx(Pq, S)
        return S_eff
