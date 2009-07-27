"""
    Unit tests for specific models using numpy array input
    @author: Gervaise B Alina/ UTK
"""

import unittest, time, math, numpy

        
class TestSphere(unittest.TestCase):
    """ Unit tests for sphere model """
    
    def setUp(self):
        from sans.models.SphereModel import SphereModel
        self.comp = SphereModel()
        self.x = numpy.array([1.0,2.0,3.0, 4.0])
        self.y = self.x +1
        
    def test1D(self):
        """ Test 1D model for a sphere  with vector as input"""
        answer=numpy.array([5.63877831e-05,2.57231782e-06,2.73704050e-07,2.54229069e-08])
       
        testvector= self.comp.run(self.x)
       
        self.assertAlmostEqual(len(testvector),4)
        for i in xrange(len(answer)):
            self.assertAlmostEqual(testvector[i],answer[i])
       
    def test1D_1(self):
        """ Test 2D model for a sphere  with scalar as input"""
        self.assertAlmostEqual(self.comp.run(1.0),5.63877831e-05, 4)
         
    def test1D_2(self):
        """ Test 2D model for a sphere for 2 scalar """
        self.assertAlmostEqual(self.comp.run([1.0, 1.3]), 56.3878e-06, 4)
   
        
class TestCylinder(unittest.TestCase):
    """ Unit tests for sphere model """
    
    def setUp(self):
        from sans.models.CylinderModel import CylinderModel
        self.comp = CylinderModel()
        self.x = numpy.array([1.0,2.0,3.0, 4.0])
        self.y = numpy.array([1.0,2.0,3.0, 4.0])
        
    def test1D(self):
        """ Test 1D model for a Cylinder  with vector as input"""
        answer = numpy.array([1.98860592e-04,7.03686335e-05,2.89144683e-06,2.04282827e-06])
        testvector= self.comp.run(self.x)
       
        self.assertAlmostEqual(len(testvector),4)
        for i in xrange(len(answer)):
            self.assertAlmostEqual(testvector[i],answer[i])
       
    def test1D_1(self):
        """ Test 2D model for a Cylinder with scalar as input"""
        self.assertAlmostEqual(self.comp.run(1.0),1.9886e-04, 4)
         
    def test1D_2(self):
        """ Test 2D model for a Cylinder for 2 scalar """
        self.assertAlmostEqual(self.comp.run([1.0, 1.3]), 56.3878e-06, 4)
        
    def test1D_3(self):
        """ Test 2D model for a Cylinder for 2 vectors as input """
        ans_input = numpy.zeros(len(self.x))
        temp_x = numpy.zeros(len(self.x))
        temp_y = numpy.zeros(len(self.y))
        
        for i in xrange(len(self.x)):
            qx = self.x[i]
            qy = self.y[i]
          
            temp_x[i]= qx*math.cos(qy)
            temp_y[i]= qx*math.sin(qy)
            
            value = math.sqrt(temp_x[i]*temp_x[i]+ temp_y[i]*temp_y[i] )#qx*qx +qy*qy)
            ans_input[i]= value
         
        vect_runXY_qx_qy = self.comp.runXY([temp_x, temp_y])
        vect_run_x_y = self.comp.run([self.x, self.y])
        
        for i in xrange(len(vect_runXY_qx_qy)):
            self.assertAlmostEqual(vect_runXY_qx_qy[i], vect_run_x_y[i])
            
        vect_run_x = self.comp.run(self.x)
        vect_run_answer = self.comp.run(ans_input)
        
        for i in xrange(len(vect_run_x )):
            self.assertAlmostEqual(vect_run_x [i], vect_run_answer[i])
            


if __name__ == '__main__':
    unittest.main()