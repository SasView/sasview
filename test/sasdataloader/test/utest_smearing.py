"""
    Unit tests for data manipulations
"""


import unittest
import numpy, math
from sas.sascalc.dataloader.loader import  Loader
from sas.sascalc.dataloader.data_info import Data1D, Data2D
#from DataLoader.qsmearing import SlitSmearer, QSmearer, smear_selection
from sas.sascalc.data_util.qsmearing import SlitSmearer, QSmearer, smear_selection
import os.path
from time import time
class smear_tests(unittest.TestCase):
    
    def setUp(self):
        data = Loader().load("cansas1d_slit.xml")
        self.data = data[0]
        
        x = 0.001*numpy.arange(1,11)
        y = 12.0-numpy.arange(1,11)
        dxl = 0.00*numpy.ones(10)
        dxw = 0.00*numpy.ones(10)
        dx = 0.00*numpy.ones(10)
        
        self.data.dx = dx
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
        # The following commented line was the correct output for even bins [see smearer.cpp for details] 
        #answer = [ 9.666,  9.056,  8.329,  7.494,  6.642,  5.721,  4.774,  3.824,  2.871, 2.   ]
        answer = [ 9.0618,  8.6401,  8.1186,  7.1391,  6.1528,  5.5555,     4.5584,  3.5606,  2.5623, 2.    ]
        for i in range(len(input)):
            self.assertAlmostEqual(answer[i], output[i], 3)
        
    def test_q(self):
        """
            Test identity resolution smearing
        """
        # Create smearer for our data
        s = QSmearer(self.data)
        
        input = 12.0-numpy.arange(1,11)
        output = s(input)
        for i in range(len(input)):
            self.assertAlmostEquals(input[i], output[i], 5)

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
            self.assertAlmostEqual(answer[i], output[i], 2)
        
if __name__ == '__main__':
    unittest.main()
   
