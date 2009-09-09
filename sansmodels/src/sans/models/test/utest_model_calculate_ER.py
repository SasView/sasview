"""
    Unit tests for specific models
"""

import unittest, time, math

# Disable "missing docstring" complaint
# pylint: disable-msg=C0111
# Disable "too many methods" complaint 
# pylint: disable-msg=R0904 
# Disable "could be a function" complaint 
# pylint: disable-msg=R0201


        
class TestSphere(unittest.TestCase):
    """ Unit tests for calculate_ER (sphere model) """
    
    def setUp(self):
        from sans.models.SphereModel import SphereModel
        self.comp = SphereModel()
        
    def test(self):
        """ Test 1D model for a sphere """
        self.comp.setParam("radius", 20)
        self.assertAlmostEqual(self.comp.calculate_ER(), 20)
        
class TestCoreShell(unittest.TestCase):
    """ Unit tests for calculate_ER (CoreShellModel) """
    
    def setUp(self):
        from sans.models.CoreShellModel import CoreShellModel
        self.comp = CoreShellModel()
        
    def test(self):
        """ Test 1D model for a CoreShell """
        self.comp.setParam("radius", 20)
        self.comp.setParam("thickness", 20)
        self.assertAlmostEqual(self.comp.calculate_ER(), 40)       
         
class TestMultiShell(unittest.TestCase):
    """ Unit tests for calculate_ER (MultiShellModel) """
    
    def setUp(self):
        from sans.models.MultiShellModel import MultiShellModel
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
        from sans.models.VesicleModel import VesicleModel
        self.comp = VesicleModel()
        
    def test(self):
        """ Test 1D model for a Vesicle """
        self.comp.setParam("radius", 60)
        self.comp.setParam("thickness", 30)
        self.assertAlmostEqual(self.comp.calculate_ER(), 90)   

class TestCylinder(unittest.TestCase):
    """ Unit tests for calculate_ER (cylinder model) """
    
    def setUp(self):
        from sans.models.CylinderModel import CylinderModel
        from sans.models.DiamCylFunc import DiamCylFunc
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
        from sans.models.CoreShellCylinderModel import CoreShellCylinderModel
        from sans.models.DiamCylFunc import DiamCylFunc
        self.comp = CoreShellCylinderModel()
        self.diam = DiamCylFunc()
        
    def test(self):
        """ Test 1D model for a CoreShellCylinder """
        self.comp.setParam("radius", 20)
        self.comp.setParam("thickness", 10)
        self.comp.setParam("length",400)
        self.diam.setParam("radius", 30)
        self.diam.setParam("length",400)       
        self.assertAlmostEqual(self.comp.calculate_ER(), self.diam.run(0.1)/2)   

class TestHollowCylinder(unittest.TestCase):
    """ Unit tests for calculate_ER (Hollowcylinder model) """
    
    def setUp(self):
        from sans.models.HollowCylinderModel import HollowCylinderModel
        from sans.models.DiamCylFunc import DiamCylFunc
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
        from sans.models.StackedDisksModel import StackedDisksModel
        from sans.models.DiamCylFunc import DiamCylFunc
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

class TestEllipsoid(unittest.TestCase):
    """ Unit tests for calculate_ER (Ellipsoid model) """
    
    def setUp(self):
        from sans.models.EllipsoidModel import EllipsoidModel
        from sans.models.DiamEllipFunc import DiamEllipFunc
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
        from sans.models.CoreShellEllipsoidModel import CoreShellEllipsoidModel
        from sans.models.DiamEllipFunc import DiamEllipFunc
        self.comp = CoreShellEllipsoidModel()
        self.diam = DiamEllipFunc()
        
    def test(self):
        """ Test 1D model for a CoreShellEllipsoid """
        self.comp.setParam("polar_shell", 20)
        self.comp.setParam("equat_shell",400)       
        self.diam.setParam("radius_a", 20)
        self.diam.setParam("radius_b",400)
        self.assertAlmostEqual(self.comp.calculate_ER(), self.diam.run(0.1)/2)                      
if __name__ == '__main__':
    unittest.main()