"""
    Unit tests for data manipulations
"""


import unittest
import numpy, math
from sas.dataloader.loader import  Loader
from sas.dataloader.data_info import Data1D, Data2D
#from DataLoader.qsmearing import SlitSmearer, QSmearer, smear_selection
from sas.models.qsmearing import SlitSmearer, QSmearer, smear_selection
from sas.models.SphereModel import SphereModel
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
      
class smear_test_1Dpinhole(unittest.TestCase):
    
    def setUp(self):
        # NIST sample data
        self.data = Loader().load("CMSphere5.txt")
        # NIST smeared sphere w/ param values below
        self.answer = Loader().load("CMSphere5smearsphere.txt")
        # call spheremodel
        self.model = SphereModel()
        # setparams consistent with Igor default
        self.model.setParam('scale', 1.0)
        self.model.setParam('background', 0.01)
        self.model.setParam('radius', 60.0)
        self.model.setParam('sldSolv', 6.3e-06)
        self.model.setParam('sldSph', 1.0e-06)
        
    def test_q(self):
        """
        Compare Pinhole resolution smearing with NIST
        """
        # x values
        input = numpy.zeros(len(self.data.x))
        # set time
        st1 = time()
        # cal I w/o smear
        input = self.model.evalDistribution(self.data.x)
        # Cal_smear (first call)
        for i in range(1000):
            s = QSmearer(self.data, self.model)
        # stop and record time taken
        first_call_time = time()-st1
        # set new time
        st = time()
        # cal I w/o smear (this is not neccessary to call but just to be fare
        input = self.model.evalDistribution(self.data.x)
        # smear cal (after first call done above)
        for i in range(1000):
            output = s(input)

        # record time taken
        last_call_time = time()-st
        # compare the ratio of ((NIST_answer-SsanView_answer)/NIST_answer)
        # If the ratio less than 1%, pass the test 
        for i in range(len(self.data.x)):
            ratio  = math.fabs((self.answer.y[i]-output[i])/self.answer.y[i])
            if ratio > 0.006:
                ratio = 0.006
            self.assertEqual(math.fabs((self.answer.y[i]-output[i])/ \
                                       self.answer.y[i]), ratio) 
        # print
        print "\n NIST_time = 10sec:"
        print "Cal_time(1000 times of first_calls; ) = ",  first_call_time  
        print "Cal_time(1000 times of calls) = ",  last_call_time 
        
if __name__ == '__main__':
    unittest.main()
   
