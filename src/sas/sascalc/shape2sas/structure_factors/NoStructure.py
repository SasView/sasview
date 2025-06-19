from sas.sascalc.shape2sas.Typing import *
from sas.sascalc.shape2sas.structure_factors.StructureDecouplingApprox import StructureDecouplingApprox
import numpy as np

class NoStructure(StructureDecouplingApprox):
    def __init__(self, q: np.ndarray, 
                 x_new: np.ndarray, 
                 y_new: np.ndarray, 
                 z_new: np.ndarray, 
                 p_new: np.ndarray, 
                 par: Any):
        super(NoStructure, self).__init__(q, x_new, y_new, z_new, p_new)
        self.q = q

    def structure_eff(self, Pq: Any) -> np.ndarray:
        """Return effective structure factor for no structure"""
        return np.ones(len(self.q))
