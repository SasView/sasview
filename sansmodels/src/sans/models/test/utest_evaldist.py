"""
    Test for the BaseComponent.evalDistribution
    See method documentation for more details
"""
import unittest
import numpy, math
from sans.models.SphereModel import SphereModel
from sans.models.Cos import Cos


class TestEvalPythonMethods(unittest.TestCase):
    """ Testing evalDistribution for pure python models """

    def setUp(self):
        self.model= Cos()
        
    def test_scalar_methods(self):
        """
            Simple test comparing the run(), runXY() and
            evalDistribution methods
        """
        q1 = self.model.run(0.001)
        q2 = self.model.runXY(0.001)
        qlist3 = numpy.asarray([0.001, 0.002])
        q3 = self.model.evalDistribution(qlist3)
        q4 = self.model.run(0.002)

        self.assertEqual(q1, q2)
        self.assertEqual(q1, q3[0])
        self.assertEqual(q4, q3[1])
        
    def test_XY_methods(self):
        """
            Compare to the runXY() method for 2D models.
            
                      +--------+--------+--------+
            qy=0.009  |        |        |        | 
                      +--------+--------+--------+
            qy-0.006  |        |        |        |
                      +--------+--------+--------+            
            qy=0.003  |        |        |        | 
                      +--------+--------+--------+
                      qx=0.001   0.002   0.003
            
        """
        # These are the expected values for all bins
        expected = numpy.zeros([3,3])
        for i in range(3):
            for j in range(3):
                q_length = math.sqrt( (0.001*(i+1.0))*(0.001*(i+1.0)) + (0.003*(j+1.0))*(0.003*(j+1.0)) )
                expected[i][j] = self.model.run(q_length)
        
        qx_values = [0.001, 0.002, 0.003]
        qy_values = [0.003, 0.006, 0.009]
        
        qx = numpy.asarray(qx_values)
        qy = numpy.asarray(qy_values)
        
        qx_prime = numpy.reshape(qx, [3,1])
        qy_prime = numpy.reshape(qy, [1,3])
        
        iq = self.model.evalDistribution([qx_prime, qy_prime])

        for i in range(3):
            for j in range(3):
                self.assertAlmostEquals(iq[i][j], expected[i][j])

    def test_rectangle_methods(self):
        """
            Compare to the runXY() method for 2D models
            with a non-square matrix.
            TODO: Doesn't work for C models apparently
        
                      +--------+--------+--------+
            qy-0.006  |        |        |        |
                      +--------+--------+--------+            
            qy=0.003  |        |        |        | 
                      +--------+--------+--------+
                      qx=0.001   0.002   0.003
            
        """
        # These are the expected values for all bins
        expected = numpy.zeros([3,3])
        for i in range(3):
            for j in range(2):
                q_length = math.sqrt( (0.001*(i+1.0))*(0.001*(i+1.0)) + (0.003*(j+1.0))*(0.003*(j+1.0)) )
                expected[i][j] = self.model.run(q_length)
        
        qx_values = [0.001, 0.002, 0.003]
        qy_values = [0.003, 0.006]
        
        qx = numpy.asarray(qx_values)
        qy = numpy.asarray(qy_values)
        
        qx_prime = numpy.reshape(qx, [3,1])
        qy_prime = numpy.reshape(qy, [1,2])
        
        iq = self.model.evalDistribution([qx_prime, qy_prime])
        
        for i in range(3):
            for j in range(2):
                self.assertAlmostEquals(iq[i][j], expected[i][j])


                
class TestEvalMethods(unittest.TestCase):
    """ Testing evalDistribution for C models """

    def setUp(self):
        self.model= SphereModel()
        
    def test_scalar_methods(self):
        """
            Simple test comparing the run(), runXY() and
            evalDistribution methods
        """
        q1 = self.model.run(0.001)
        q2 = self.model.runXY(0.001)
        q4 = self.model.run(0.002)
        qlist3 = numpy.asarray([0.001, 0.002])
        q3 = self.model.evalDistribution(qlist3)

        self.assertEqual(q1, q2)
        self.assertEqual(q1, q3[0])
        self.assertEqual(q4, q3[1])
        
    def test_XY_methods(self):
        """
            Compare to the runXY() method for 2D models.
            
                      +--------+--------+--------+
            qy=0.009  |        |        |        | 
                      +--------+--------+--------+
            qy-0.006  |        |        |        |
                      +--------+--------+--------+            
            qy=0.003  |        |        |        | 
                      +--------+--------+--------+
                      qx=0.001   0.002   0.003
            
        """
        # These are the expected values for all bins
        expected = numpy.zeros([3,3])
        for i in range(3):
            for j in range(3):
                q_length = math.sqrt( (0.001*(i+1.0))*(0.001*(i+1.0)) + (0.003*(j+1.0))*(0.003*(j+1.0)) )
                expected[i][j] = self.model.run(q_length)
        
        qx_values = [0.001, 0.002, 0.003]
        qy_values = [0.003, 0.006, 0.009]
        
        qx = numpy.asarray(qx_values)
        qy = numpy.asarray(qy_values)
        
        qx_prime = numpy.reshape(qx, [3,1])
        qy_prime = numpy.reshape(qy, [1,3])
        
        iq = self.model.evalDistribution([qx_prime, qy_prime])
        
        for i in range(3):
            for j in range(3):
                self.assertAlmostEquals(iq[i][j], expected[i][j])
                

if __name__ == '__main__':
    unittest.main()