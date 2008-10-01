"""
    Unit tests for data manipulations
"""


import unittest
import numpy, math
from DataLoader.loader import  Loader
from DataLoader.data_info import Data1D, Data2D
from DataLoader.qsmearing import SlitSmearer, QSmearer
 
import os.path

class smear_tests(unittest.TestCase):
    
    def setUp(self):
        self.data = Loader().load("cansas1d_slit.xml")
        
        x = 0.001*numpy.arange(1,11)
        y = 12.0-numpy.arange(1,11)
        dxl = 0.00*numpy.ones(10)
        dxw = 0.00*numpy.ones(10)
        
        self.data.x = x
        self.data.y = y
        self.data.dxl = dxl
        self.data.dxw = dxw
        
    def test_slit(self):
        """
            Test identity smearing
        """
        # Create smearer for our data
        s = SlitSmearer(self.data)
        
        input = 12.0-numpy.arange(1,11)
        output = s(input)
        for i in range(len(input)):
            self.assertEquals(input[i], output[i])

    def test_slit2(self):
        """
            Test basic smearing
        """
        dxl = 0.005*numpy.ones(10)
        dxw = 0.0*numpy.ones(10)
        self.data.dxl = dxl
        self.data.dxw = dxw
        # Create smearer for our data
        s = SlitSmearer(self.data)
        
        input = 12.0-numpy.arange(1,11)
        output = s(input)
        answer = [ 9.666,  9.056,  8.329,  7.494,  6.642,  5.721,  4.774,  3.824,  2.871, 2.   ]
        for i in range(len(input)):
            self.assertAlmostEqual(answer[i], output[i], 5)
        
    def test_q(self):
        """
            Test identity resolution smearing
        """
        # Create smearer for our data
        s = QSmearer(self.data)
        
        input = 12.0-numpy.arange(1,11)
        output = s(input)
        for i in range(len(input)):
            self.assertEquals(input[i], output[i])

    def test_q2(self):
        """
            Test basic smearing
        """
        dx = 0.001*numpy.ones(10)
        self.data.dx = dx

        # Create smearer for our data
        s = QSmearer(self.data)
        
        input = 12.0-numpy.arange(1,11)
        output = s(input)
        
        answer = [ 10.44785079,   9.84991299,   8.98101708,   
                  7.99906585,   6.99998311,   6.00001689,
                  5.00093415,   4.01898292,   3.15008701,   2.55214921]
        for i in range(len(input)):
            self.assertAlmostEqual(answer[i], output[i], 5)
      

if __name__ == '__main__':
    unittest.main()
   