"""
   Implementation of the use-case from a usage perspective. 
"""

import unittest
import numpy
from DataLoader.loader import  Loader
from sans.invariant import invariant
from sans.invariant.invariant_mapper import InvariantMapper

N_INVARIANT = 10
CONTRAST = 2.6e-6
POROD_CONSTANT = 2.0

class TestInvPolySphere(unittest.TestCase):
    """
        Test iteration through unsmeared data for invariant computation
    """
    def setUp(self):
        self.list_of_invariant = []
        self.list_of_contrast = []
        self.list_of_porod_const = []
        #Define an invariant mapper
        self.mapper = InvariantMapper()
        for i in range(N_INVARIANT):
            data = Loader().load("PolySpheres.txt")
            # Create invariant object. Background and scale left as defaults.
            inv = invariant.InvariantCalculator(data=data)
            self.list_of_invariant.append(inv)
            self.list_of_contrast.append(CONTRAST)
            self.list_of_porod_const.append(POROD_CONSTANT)
        
    def test_use_case_1(self):
        """
        Invariant without extrapolation
        """
        qstar_list = map(self.mapper.get_qstar, self.list_of_invariant)
        
        for qstar in qstar_list:
            self.assertAlmostEquals(qstar, 7.48959e-5, 2)
        
        v_list = map(self.mapper.get_volume_fraction_with_error,
                         self.list_of_invariant, self.list_of_contrast)
        for v, dv in v_list:
            self.assertAlmostEquals(v, 0.005644689, 4)
            
        s_list = map(self.mapper.get_surface_with_error,
                         self.list_of_invariant,
                         self.list_of_contrast,
                         self.list_of_porod_const)
        for s, ds in s_list:
            self.assertAlmostEquals(s , 941.7452, 3)
        
   