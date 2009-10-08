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
        #Data iwth no slit smear information
        data0= Loader().load("PolySpheres.txt")
        self.I0 = InvariantCalculator( data= data0,contrast=2.6e-6, pConst=20)
        # data with smear info
        list = Loader().load("latex_smeared.xml")
        data1= list[0]
        self.I1= InvariantCalculator( data= data1,contrast=5.3e-6, pConst=20)
        data2= list[1]
        self.I2= InvariantCalculator( data= data2,contrast=5.3e-6, pConst=20)
     
    def testInvariant(self):
        """ test the invariant value for data with no slit smear"""
        self.assertAlmostEquals(self.I0.q_star, 7.48959e-5)
        
        
    def test_Computation(self):
        """
            Test identity smearing
        """
        # compute invariant with smear information
        print "invariant initialized only with data:", self.I1
        print "invariant q_star",self.I1.q_star
        print "invariant volume",self.I1.volume
        print "Invariant surface",self.I1.surface
        print
        print "invariant initialized __call__:", self.I1
        print "invariant q_star",self.I1.q_star
        print "invariant volume",self.I1.volume
        print "Invariant surface",self.I1.surface
        print
        # compute invariant with smear information
        print "invariant initialize with data, contrast,pConst:", self.I2
        print "invariant q_star",self.I2.q_star
        print "invariant volume",self.I2.volume
        print "Invariant surface",self.I2.surface
        print
      
        
if __name__ == '__main__':
    unittest.main()
