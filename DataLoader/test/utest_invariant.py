"""
    Unit tests for data manipulations
    @author Gervaise Alina: unittest imcoplete so far 
"""


import unittest
import numpy, math
from DataLoader.loader import  Loader
from DataLoader.data_info import Data1D, Data2D
from DataLoader.invariant import InvariantCalculator


class InvariantTest(unittest.TestCase):
    
    def setUp(self):
        #Data with no slit smear information
        data0 = Loader().load("PolySpheres.txt")
        self.I0 = InvariantCalculator( data=data0)
        
        # data with smear info
        list = Loader().load("latex_smeared.xml")
        data1= list[0]
        self.I1= InvariantCalculator( data= data1)
        
        data2= list[1]
        self.I2= InvariantCalculator( data= data2)
     
    def test_invariant(self):
        """ test the invariant value for data with no slit smear"""
        self.assertAlmostEquals(self.I0.q_star, 7.48959e-5)
        self.assertTrue(self.I1.q_star>0)
        self.assertTrue(self.I2.q_star>0)
        
    def test_computation(self):
        """
            Test identity smearing
        """
        vol = self.I0.get_volume_fraction(contrast=2.6e-6)
        surface = self.I0.get_surface(contrast=2.6e-6, porod_const=20)
        
        # TODO: Need to test output values
        #self.assertAlmostEquals(vol, 0)
        #self.assertAlmostEquals(surface, 0)
        vol = self.I1.get_volume_fraction(contrast=5.3e-6)
        surface = self.I1.get_surface(contrast=5.3e-6, porod_const=20)
        
        # TODO: Need to test output values
        #self.assertAlmostEquals(vol, 0)
        #self.assertAlmostEquals(surface, 0)
        
        vol = self.I2.get_volume_fraction(contrast=5.3e-6)
        surface = self.I2.get_surface(contrast=5.3e-6, porod_const=20)
        
        # TODO: Need to test output values
        self.assertAlmostEquals(vol, 0)
        self.assertAlmostEquals(surface, 0)
        
      
        
if __name__ == '__main__':
    unittest.main()
