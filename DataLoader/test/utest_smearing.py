"""
    Unit tests for data manipulations
"""


import unittest
import numpy, math
from DataLoader.loader import  Loader
from DataLoader.data_info import Data1D, Data2D
from DataLoader.qsmearing import SlitSmearer, QSmearer, smear_selection
from sans.models.SphereModel import SphereModel
import os.path

class smear_tests(unittest.TestCase):
    
    def setUp(self):
        self.data = Loader().load("cansas1d_slit.xml")
        
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
        # The following commented line was the correct output for even bins 
        # [see smearer.cpp for details] 
        #answer = [ 9.666,  9.056,  8.329,  7.494,  6.642,  5.721,  4.774, \
        #  3.824,  2.871, 2.   ]
        # The following answer was from numerical weighting algorithm.
        #answer = [ 9.2302,  8.6806,  7.9533,  7.1673,  6.2889,  5.4,   \
        #  4.5028,  3.5744,  2.6083, 2.    ]
        # For the new analytical algorithm, the small difference between 
        #these two could be from the first edge of the q bin size. 
        answer = [ 9.0618,  8.64018,  8.11868,  7.13916,  6.15285,  5.55556,  \
                     4.55842,  3.56061,  2.56235, 2.    ]
        for i in range(len(input)):
            self.assertAlmostEqual(answer[i], output[i], 2)
        
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
            
class smear_slit_h_w_tests(unittest.TestCase):
    
    def setUp(self):
        self.data = Loader().load("1000A_sphere_sm.xml")
        self.model = SphereModel()
        # The answer could be improved by developing better algorithm.
        self.answer1 = Loader().load("slit_1000A_sphere_sm_w_0_0002.txt")
        self.answer2 = Loader().load("slit_1000A_sphere_sm_h.txt")
        self.answer3 = Loader().load("slit_1000A_sphere_sm_w_0_0001.txt")
        # Get inputs
        self.model.params['scale'] = 0.05
        self.model.params['background'] = 0.01
        self.model.params['radius'] = 10000.0
        self.model.params['sldSolv'] = 6.3e-006
        self.model.params['sldSph'] = 3.4e-006
        
    def test_slit_h_w(self):
        """
            Test identity slit smearing w/ h=0.117 w = 0.002
        """
        # Set params and dQl
        data = self.data
        data.dxw = 0.0002 * numpy.ones(len(self.data.x))
        data.dxl = 0.117 * numpy.ones(len(self.data.x))
        # Create smearer for our data
        s = SlitSmearer(data, self.model)
        # Get smear
        input  = self.model.evalDistribution(data.x)
        output = s(input)
        # Get pre-calculated values
        answer = self.answer1.y
        # Now compare
        for i in range(len(input)):
            self.assertAlmostEqual(answer[i], output[i], 0)
     
    def test_slit_h(self):
        """
            Test identity slit smearing w/ h=0.117 w = 0.0
        """
        # Set params and dQl
        data = self.data
        data.dxw = 0.0 * numpy.ones(len(self.data.x))
        data.dxl = 0.117 * numpy.ones(len(self.data.x))
        # Create smearer for our data
        s = SlitSmearer(data, self.model)
        # Get smear
        input  = self.model.evalDistribution(data.x)
        output = s(input)
        # Get pre-calculated values
        answer = self.answer2.y
        # Now compare
        for i in range(len(input)):
            self.assertAlmostEqual(answer[i], output[i], 0)
     
    def test_slit_w(self):
        """
            Test identity slit smearing w/ h=0.0 w = 0.001
        """
        # Set params and dQl
        data = self.data
        data.dxw = 0.0001 * numpy.ones(len(self.data.x))
        data.dxl = 0.0 * numpy.ones(len(self.data.x))
        # Create smearer for our data
        s = SlitSmearer(data, self.model)
        # Get smear
        input  = self.model.evalDistribution(data.x)
        output = s(input)
        # Get pre-calculated values
        answer = self.answer3.y
        # Now compare
        for i in range(len(input)):
             if i <= 40:
                 self.assertAlmostEqual(answer[i], output[i], -3)    
             else:
                self.assertAlmostEqual(answer[i], output[i], 0)       
                
if __name__ == '__main__':
    unittest.main()
   