"""
    Unit tests for specific models using numpy array input
    @author: Gervaise B Alina/ UTK
"""

import unittest, time, math, numpy

        
class TestSphere(unittest.TestCase):
    """ Unit tests for sphere model using evalDistribution function """
    
    def setUp(self):
        from sans.models.SphereModel import SphereModel
        self.comp = SphereModel()
        self.x = numpy.array([1.0,2.0,3.0, 4.0])
        self.y = self.x +1
        
    def test1D(self):
        """ Test 1D model for a sphere  with vector as input"""
        answer = numpy.array([5.63877831e-05,2.57231782e-06,2.73704050e-07,2.54229069e-08])
       
       
        testvector= self.comp.evalDistribution(self.x)
       
        self.assertAlmostEqual(len(testvector),4)
        for i in xrange(len(answer)):
            self.assertAlmostEqual(testvector[i],answer[i])
       
    def test1D_1(self):
        """ Test 2D model for a sphere  with scalar as input"""
        self.assertAlmostEqual(self.comp.run(1.0),5.63877831e-05, 4)
         
    def test1D_2(self):
        """ Test 2D model for a sphere for 2 scalar """
        self.assertAlmostEqual(self.comp.run([1.0, 1.3]), 56.3878e-06, 4)
        
    def test1D_3(self):
        """ Test 2D model for a Shpere for 2 vectors as input """
        #x= numpy.reshape(self.x, [len(self.x),1])
        #y= numpy.reshape(self.y, [1,len(self.y)])
        vect = self.comp.evalDistribution([self.x,self.y])
        self.assertAlmostEqual(vect[0],9.2985e-07, 4)
        self.assertAlmostEqual(vect[len(self.x)-1],1.3871e-08, 4)
        
        
class TestCylinder(unittest.TestCase):
    """ Unit tests for Cylinder model using evalDistribution function """
    
    def setUp(self):
        from sans.models.CylinderModel import CylinderModel
        self.comp = CylinderModel()
        self.x = numpy.array([1.0,2.0,3.0, 4.0])
        self.y = self.x +1
        
    def test1D(self):
        """ Test 1D model for a cylinder with vector as input"""
        
        answer = numpy.array([1.98860592e-04,7.03686335e-05,2.89144683e-06,2.04282827e-06])

        testvector= self.comp.evalDistribution(self.x)
        self.assertAlmostEqual(len(testvector),4)
        for i in xrange(len(answer)):
            self.assertAlmostEqual(testvector[i],answer[i])
       
    def test1D_1(self):
        """ Test 2D model for a cylinder  with scalar as input"""
        self.assertAlmostEqual(self.comp.run(0.2), 0.041761386790780453, 4)
         
    def test1D_2(self):
        """ Test 2D model of a cylinder """ 
        self.comp.setParam('cyl_theta', 10.0)
        self.comp.setParam('cyl_phi', 10.0)
        self.assertAlmostEqual(self.comp.run([0.2, 2.5]), 
                               0.038176446608393366, 2)
        
    def test1D_3(self):
        """ Test 2D model for a cylinder for 2 vectors as input """
        vect = self.comp.evalDistribution([self.x,self.y])
      
        self.assertAlmostEqual(vect[0],5.06121018e-08,4)
        self.assertAlmostEqual(vect[len(self.x)-1],2.5978e-11, 4)
        
        

if __name__ == '__main__':
    unittest.main()