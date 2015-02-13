"""
    Unit tests for calculate_ER of specific models
    @author: JHJ Cho / UTK
"""

import unittest, time, math, numpy

        
class TestSphere(unittest.TestCase):
    """ Unit tests for calculate_ER (sphere model) """
    
    def setUp(self):
        from sas.models.SphereModel import SphereModel
        self.comp = SphereModel()
        
    def test(self):
        """ Test 1D model for a sphere """
        self.comp.setParam("radius", 20)
        self.assertAlmostEqual(self.comp.calculate_ER(), 20)
        
class TestCoreShell(unittest.TestCase):
    """ Unit tests for calculate_ER (CoreShellModel) """
    
    def setUp(self):
        from sas.models.CoreShellModel import CoreShellModel
        self.comp = CoreShellModel()
        
    def test(self):
        """ Test 1D model for a CoreShell """
        self.comp.setParam("radius", 20)
        self.comp.setParam("thickness", 20)
        self.assertAlmostEqual(self.comp.calculate_ER(), 40)       
         
class TestMultiShell(unittest.TestCase):
    """ Unit tests for calculate_ER (MultiShellModel) """
    
    def setUp(self):
        from sas.models.MultiShellModel import MultiShellModel
        self.comp = MultiShellModel()
        
    def test(self):
        """ Test 1D model for a MultiShell """
        self.comp.setParam("core_radius", 60)
        self.comp.setParam("s_thickness", 10)
        self.comp.setParam("w_thickness", 15)
        self.comp.setParam("n_pairs", 2)
        self.assertAlmostEqual(self.comp.calculate_ER(), 95)      

class TestVesicle(unittest.TestCase):
    """ Unit tests for calculate_ER (VesicleModel) """
    
    def setUp(self):
        from sas.models.VesicleModel import VesicleModel
        self.comp = VesicleModel()
        
    def test(self):
        """ Test 1D model for a Vesicle """
        self.comp.setParam("radius", 60)
        self.comp.setParam("thickness", 30)
        self.assertAlmostEqual(self.comp.calculate_ER(), 90)   

class TestCylinder(unittest.TestCase):
    """ Unit tests for calculate_ER (cylinder model) """
    
    def setUp(self):
        from sas.models.CylinderModel import CylinderModel
        from sas.models.DiamCylFunc import DiamCylFunc
        self.comp = CylinderModel()
        self.diam = DiamCylFunc()
        
    def test(self):
        """ Test 1D model for a Cylinder """
        self.comp.setParam("radius", 20)
        self.comp.setParam("length",400)
        self.diam.setParam("radius", 20)
        self.diam.setParam("length",400)       
        self.assertAlmostEqual(self.comp.calculate_ER(), self.diam.run(0.1)/2)  
         
class TestCoreShellCylinder(unittest.TestCase):
    """ Unit tests for calculate_ER (CoreShellcylinder model) """
    
    def setUp(self):
        from sas.models.CoreShellCylinderModel import CoreShellCylinderModel
        from sas.models.DiamCylFunc import DiamCylFunc
        self.comp = CoreShellCylinderModel()
        self.diam = DiamCylFunc()
        
    def test(self):
        """ Test 1D model for a CoreShellCylinder """
        self.comp.setParam("radius", 20)
        self.comp.setParam("thickness", 10)
        self.comp.setParam("length",400)
        self.diam.setParam("radius", 30)
        self.diam.setParam("length",420)       
        self.assertAlmostEqual(self.comp.calculate_ER(), self.diam.run(0.1)/2)   

class TestHollowCylinder(unittest.TestCase):
    """ Unit tests for calculate_ER (Hollowcylinder model) """
    
    def setUp(self):
        from sas.models.HollowCylinderModel import HollowCylinderModel
        from sas.models.DiamCylFunc import DiamCylFunc
        self.comp = HollowCylinderModel()
        self.diam = DiamCylFunc()
        
    def test(self):
        """ Test 1D model for a Hollowcylinder """
        self.comp.setParam("radius", 20)
        self.comp.setParam("length",400)
        self.diam.setParam("radius", 20)
        self.diam.setParam("length",400)       
        self.assertAlmostEqual(self.comp.calculate_ER(), self.diam.run(0.1)/2)        

class TestStackedDisksModel(unittest.TestCase):
    """ Unit tests for calculate_ER (StackedDisks model) """
    
    def setUp(self):
        from sas.models.StackedDisksModel import StackedDisksModel
        from sas.models.DiamCylFunc import DiamCylFunc
        self.comp = StackedDisksModel()
        self.diam = DiamCylFunc()
        
    def test(self):
        """ Test 1D model for a StackedDisks """
        self.comp.setParam("radius", 3000)
        self.comp.setParam("n_stacking", 2)
        self.comp.setParam("core_thick",10)
        self.comp.setParam("layer_thick", 15)
        self.diam.setParam("radius", 3000)
        self.diam.setParam("length",80)       
        self.assertAlmostEqual(self.comp.calculate_ER(), self.diam.run(0.1)/2)  
             
class TestEllipticalCylinder(unittest.TestCase):
    """ Unit tests for calculate_ER (EllipticalCylindermodel) """
    
    def setUp(self):
        from sas.models.EllipticalCylinderModel import EllipticalCylinderModel
        from sas.models.DiamCylFunc import DiamCylFunc
        self.comp = EllipticalCylinderModel()
        self.diam = DiamCylFunc()
        
    def test(self):
        """ Test 1D model for a EllipticalCylinder """
        self.comp.setParam("r_minor", 20)
        self.comp.setParam("r_ratio",1.5)  
        self.comp.setParam("length",400)  
        r_value = math.sqrt(20*20*1.5)    
        self.diam.setParam("radius", r_value)
        self.diam.setParam("length",400)       
        self.assertAlmostEqual(self.comp.calculate_ER(), self.diam.run(0.1)/2)  
         
class TestParallelepiped(unittest.TestCase):
    """ Unit tests for calculate_ER (Parallelepipedmodel) """
    
    def setUp(self):
        from sas.models.ParallelepipedModel import ParallelepipedModel
        from sas.models.DiamCylFunc import DiamCylFunc
        self.comp = ParallelepipedModel()
        self.diam = DiamCylFunc()
        
    def test(self):
        """ Test 1D model for a Parallelepiped """
        self.comp.setParam("short_a", 35)
        self.comp.setParam("short_b", 75)  
        self.comp.setParam("long_c",400)  
        r_value = math.sqrt(35*75/math.pi)    
        self.diam.setParam("radius", r_value)
        self.diam.setParam("length",400)   
        self.assertAlmostEqual(self.comp.calculate_ER(), self.diam.run(0.1)/2)   
                                                  
class TestEllipsoid(unittest.TestCase):
    """ Unit tests for calculate_ER (Ellipsoid model) """
    
    def setUp(self):
        from sas.models.EllipsoidModel import EllipsoidModel
        from sas.models.DiamEllipFunc import DiamEllipFunc
        self.comp = EllipsoidModel()
        self.diam = DiamEllipFunc()
        
    def test(self):
        """ Test 1D model for a Ellipsoid """
        self.comp.setParam("radius_a", 20)
        self.comp.setParam("radius_b",400)
        self.diam.setParam("radius_a", 20)
        self.diam.setParam("radius_b",400)       
        self.assertAlmostEqual(self.comp.calculate_ER(), self.diam.run(0.1)/2)   

class TestCoreShellEllipsoid(unittest.TestCase):
    """ Unit tests for calculate_ER (CoreShellEllipsoid model) """
    
    def setUp(self):
        from sas.models.CoreShellEllipsoidModel import CoreShellEllipsoidModel
        from sas.models.DiamEllipFunc import DiamEllipFunc
        self.comp = CoreShellEllipsoidModel()
        self.diam = DiamEllipFunc()
        
    def test(self):
        """ Test 1D model for a CoreShellEllipsoid """
        self.comp.setParam("polar_shell", 20)
        self.comp.setParam("equat_shell",400)       
        self.diam.setParam("radius_a", 20)
        self.diam.setParam("radius_b",400)
        self.assertAlmostEqual(self.comp.calculate_ER(), self.diam.run(0.1)/2) 

class TestTriaxialEllipsoid(unittest.TestCase):
    """ Unit tests for calculate_ER (TriaxialEllipsoid model) """
    
    def setUp(self):
        from sas.models.TriaxialEllipsoidModel import TriaxialEllipsoidModel
        from sas.models.DiamEllipFunc import DiamEllipFunc
        self.comp = TriaxialEllipsoidModel()
        self.diam = DiamEllipFunc()
        
    def test(self):
        """ Test 1D model for a TriaxialEllipsoid """
        self.comp.setParam("semi_axisA", 35)
        self.comp.setParam("semi_axisB", 100)
        self.comp.setParam("semi_axisC", 400)  
        r_value = math.sqrt(35*100)    
        self.diam.setParam("radius_a", 400)
        self.diam.setParam("radius_b",r_value)
        self.assertAlmostEqual(self.comp.calculate_ER(), self.diam.run(0.1)/2) 
                    
class TestLamellar(unittest.TestCase):
    """ Unit tests for calculate_ER (Lamellarmodel)"""
    
    def setUp(self):
        from sas.models.LamellarModel import LamellarModel
        self.comp = LamellarModel()
        
    def test(self):
        """ Test 1D model for a Lamellar """
        #No finite number should return from Lamellar models.
        self.assertTrue(numpy.isfinite(self.comp.calculate_ER())) 
         
class TestGuinier(unittest.TestCase):
    """ Unit tests for calculate_ER (Guinier model) """
    
    def setUp(self):
        from sas.models.GuinierModel import GuinierModel
        self.comp = GuinierModel()
        
    def test(self):
        """ Test 1D model for Guinier """    
        #calculate_ER() is not implemented for pure python model functions
        self.assertEqual(self.comp.calculate_ER(), NotImplemented)  
        
if __name__ == '__main__':
    unittest.main()
