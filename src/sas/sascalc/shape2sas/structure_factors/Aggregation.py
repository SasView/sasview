import numpy as np

from sas.sascalc.shape2sas.structure_factors.StructureDecouplingApprox import StructureDecouplingApprox
from sas.sascalc.shape2sas.Typing import *


class Aggregation(StructureDecouplingApprox):
    def __init__(self, q: np.ndarray, 
                 x_new: np.ndarray, 
                 y_new: np.ndarray, 
                 z_new: np.ndarray, 
                 p_new: np.ndarray, 
                 par: List[float]):
        super(Aggregation, self).__init__(q, x_new, y_new, z_new, p_new)
        self.q = q
        self.x_new = x_new
        self.y_new = y_new
        self.z_new = z_new
        self.p_new = p_new
        self.Reff = par[0]
        self.Naggr = par[1]
        self.fracs_aggr = par[2]

    def calc_S_aggr(self) -> np.ndarray:
        """
        calculates fractal aggregate structure factor with dimensionality 2

        S_{2,D=2} in Larsen et al 2020, https://doi.org/10.1107/S1600576720006500

        input 
        q      :
        Naggr  : number of particles per aggregate
        Reff   : effective radius of one particle 

        output
        S_aggr :
        """

        qR = self.q * self.Reff
        S_aggr = 1 + (self.Naggr - 1)/(1 + qR**2 * self.Naggr / 3)

        return S_aggr

    def structure_eff(self, Pq: np.ndarray) -> np.ndarray:
        """Return effective structure factor for aggregation"""

        S = self.calc_S_aggr()
        S_eff = self.decoupling_approx(Pq, S)
        S_eff = (1 - self.fracs_aggr) + self.fracs_aggr * S_eff
        return S_eff
