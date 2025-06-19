from sas.sascalc.shape2sas.Typing import *
from sas.sascalc.shape2sas.structure_factors import *
import numpy as np

class StructureFactor:
    def __init__(self, q: np.ndarray, 
                 x_new: np.ndarray, 
                 y_new: np.ndarray, 
                 z_new: np.ndarray, 
                 p_new: np.ndarray,
                 Stype: str,
                 par: Optional[List[float]]):
        self.q = q
        self.x_new = x_new
        self.y_new = y_new
        self.z_new = z_new
        self.p_new = p_new
        self.Stype = Stype
        self.par = par
        self.setAvailableStructureFactors()

    def setAvailableStructureFactors(self):
        """Available structure factors"""
        self.structureFactor = {
            'HS': HardSphereStructure,
            'Hard Sphere': HardSphereStructure,
            'aggregation': Aggregation,
            'Aggregation': Aggregation,
            'None': NoStructure
        }
    
    def getStructureFactorClass(self):
        """Return chosen structure factor"""
        if self.Stype in self.structureFactor:
            return self.structureFactor[self.Stype](self.q, self.x_new, self.y_new, self.z_new, self.p_new, self.par)
        
        else:
            try:
                return globals()[self.Stype](self.q, self.x_new, self.y_new, self.z_new, self.p_new, self.par)
            except KeyError:
                ValueError(f"Structure factor '{self.Stype}' was not found in structureFactor or global scope.")

    @staticmethod
    def getparname(name: str) -> List[str]:
        """Return the name of the parameters"""
        pars = {
            'HS': {'conc': 0.02,'r_hs': 50},
            'Hard Sphere': {'conc': 0.02,'r_hs': 50},
            'Aggregation': {'R_eff': 50, 'N_aggr': 80, 'frac': 0.1},
            'aggregation': {'R_eff': 50, 'N_aggr': 80, 'frac': 0.1},
            'None': {}
        }
        return pars[name]

    @staticmethod
    def save_S(q: np.ndarray, S_eff: np.ndarray, Model: str):
        """ 
        save S to file
        """

        with open('Sq%s.dat' % Model,'w') as f:
            f.write('# Structure factor, S(q), used in: I(q) = P(q)*S(q)\n')
            f.write('# Default: S(q) = 1.0\n')
            f.write('# %-17s %-17s\n' % ('q','S(q)'))
            for (q_i, S_i) in zip(q, S_eff):
                f.write('  %-17.5e%-17.5e\n' % (q_i, S_i))
