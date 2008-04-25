"""
    Unit tests for Invertor class
"""
# Disable "missing docstring" complaint
# pylint: disable-msg=C0111
# Disable "too many methods" complaint 
# pylint: disable-msg=R0904 


import unittest, math, numpy
from sans.pr.invertor import Invertor
        
class TestBasicComponent(unittest.TestCase):
    
    def setUp(self):
        self.invertor = Invertor()
        self.invertor.d_max = 100.0
        
        # Test array
        self.ntest = 5
        self.x_in = numpy.ones(self.ntest)
        for i in range(self.ntest):
            self.x_in[i] = 1.0*i


    def testset_dmax(self):
        """
            Set and read d_max
        """
        value = 15.0
        self.invertor.d_max = value
        self.assertEqual(self.invertor.d_max, value)
        
    def testset_x_1(self):
        """
            Setting and reading the x array the hard way
        """
        # Set x
        self.invertor.x = self.x_in
        
        # Read it back
        npts = self.invertor.get_nx()
        x_out = numpy.ones(npts)
        
        self.invertor.get_x(x_out)

        for i in range(self.ntest):
            self.assertEqual(self.x_in[i], x_out[i])
            
    def testset_x_2(self):
        """
            Setting and reading the x array the easy way
        """
        # Set x
        self.invertor.x = self.x_in
        
        # Read it back
        x_out = self.invertor.x
        
        for i in range(self.ntest):
            self.assertEqual(self.x_in[i], x_out[i])
       
    def testset_y(self):
        """
            Setting and reading the y array the easy way
        """
        # Set y
        self.invertor.y = self.x_in
        
        # Read it back
        y_out = self.invertor.y
        
        for i in range(self.ntest):
            self.assertEqual(self.x_in[i], y_out[i])
       
    def testset_err(self):
        """
            Setting and reading the err array the easy way
        """
        # Set err
        self.invertor.err = self.x_in
        
        # Read it back
        err_out = self.invertor.err
        
        for i in range(self.ntest):
            self.assertEqual(self.x_in[i], err_out[i])
       
    def test_iq(self):
        """
            Test iq calculation
        """
        q = 0.11
        v1 = 8.0*math.pi**2/q * self.invertor.d_max *math.sin(q*self.invertor.d_max)
        v1 /= ( math.pi**2 - (q*self.invertor.d_max)**2.0 )
        
        pars = numpy.ones(1)
        self.assertAlmostEqual(self.invertor.iq(pars, q), v1, 2)
        
    def test_pr(self):
        """
            Test pr calculation
        """
        r = 10.0
        v1 = 2.0*r*math.sin(math.pi*r/self.invertor.d_max)
        pars = numpy.ones(1)
        self.assertAlmostEqual(self.invertor.pr(pars, r), v1, 2)
        
    def test_getsetters(self):
        self.invertor.new_data = 1.0
        self.assertEqual(self.invertor.new_data, 1.0)
        
        self.assertEqual(self.invertor.test_no_data, None)
        
if __name__ == '__main__':
    unittest.main()