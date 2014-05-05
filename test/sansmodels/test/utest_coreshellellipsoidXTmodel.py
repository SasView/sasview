# rkh 4Apr14, hacked from utest_other_models, then run sansrealspace\utest_sansview.py as python
# (some OTHER tests compare data files produced by igor nist e.g. see utest_sphere_dispersity )
# this one checks output at a single point in I(Q) against a value from igor code.
# Here have used same results as original CoreShellEllipsoidModel
# !!!!!!!!!!!!!!!!! THERE ARE NO TESTS ON THE POLYDISPERS VERSION !!!!!!!!!!!!!!!!!
import unittest
import numpy 
import math
import time

class TestCoreShellEllipsoidXTModel(unittest.TestCase):
    """ Unit tests for CoreShellEllipsoidXT Model"""
    
    def setUp(self):
        from sans.models.CoreShellEllipsoidXTModel import CoreShellEllipsoidXTModel
        self.comp = CoreShellEllipsoidXTModel()
        #Give initial value to model
        self.comp.setParam("scale", 1.0)
        self.comp.setParam("equat_core", 200.0)
#        self.comp.setParam("polar_core", 20.0)
#        self.comp.setParam("equat_shell",250.0)
#        self.comp.setParam("polar_shell", 30.0)
        self.comp.setParam("X_core", 0.1)
        self.comp.setParam("T_shell", 50.0)
        self.comp.setParam("XpolarShell",0.2)
        self.comp.setParam("sld_shell",1e-006)
        self.comp.setParam("sld_core",2e-006)
        self.comp.setParam("sld_solvent",6.3e-006)
        self.comp.setParam("background",0.001)
        self.comp.setParam("axis_theta", 0.0)
        self.comp.setParam("axis_phi",0.0)
         
        self.x = numpy.array([0.4, 1.3])
        self.y = numpy.array([0.5, 1.57])
        self.x_array = self.comp.evalDistribution(self.x)
        self.y_array = self.comp.evalDistribution(self.y)
        
        qx_prime = numpy.reshape(self.x, [1,len(self.x)])
        qy_prime = numpy.reshape(self.y, [len(self.y),1])
        self.xy_matrix = self.comp.evalDistribution([self.x, self.y])
        
        self.q = 0.001
        self.phi= math.pi/2
        self.qx= self.q*math.cos(self.phi)
        self.qy= self.q*math.sin(self.phi)
        
    def test1D(self):
        """ Test 1D model for a CoreShellEllipsoid Model"""
        self.assertAlmostEqual(self.comp.run(1.0), 0.001894, 4)
        
    def test1D_2(self):
        """ Test 2D model for a CoreShellEllipsoid Model"""
        self.assertAlmostEqual(self.comp.run([self.q, self.phi]), 
                              self.comp.runXY([self.qx, self.qy]),1)
        
    def testEval_1D(self):
        """ Test 1D model for a CoreShellEllipsoid with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for a CoreShellEllipsoid with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0],8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1], 8)

    
    def testCriticalPoint(self):
        """ Test CoreShellEllipsoid at the critical point"""
        self.assert_(numpy.isfinite(self.comp.run(0.0)))
        
# rkh 05Apr14 hacked from utest_model_calculate_ER        
class TestCoreShellEllipsoidXT(unittest.TestCase):
    """ Unit tests for calculate_ER (CoreShellEllipsoidXT model) """
    
    def setUp(self):
        from sans.models.CoreShellEllipsoidXTModel import CoreShellEllipsoidXTModel
        from sans.models.DiamEllipFunc import DiamEllipFunc
        self.comp = CoreShellEllipsoidXTModel()
        self.diam = DiamEllipFunc()
        
    def test(self):
        """ Test 1D model for a CoreShellEllipsoidXT """
        #self.comp.setParam("polar_shell", 20)
        #self.comp.setParam("equat_shell",400)       
        self.comp.setParam("equat_core",350)       
        self.comp.setParam("X_core", .05)
        self.comp.setParam("T_shell", 50.0)
        self.comp.setParam("XpolarShell",0.05)
        self.diam.setParam("radius_a", 20)
        self.diam.setParam("radius_b",400)
        self.assertAlmostEqual(self.comp.calculate_ER(), self.diam.run(0.1)/2) 
  
