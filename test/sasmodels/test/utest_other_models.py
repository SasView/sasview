"""
    Unit tests for specific models.
    @since: 08/25/2009 
    @note:  The models are running also with numpy array as input.
            Some models return limit of the function at critical point .
            So the user should expect finite value for some critical points.
            Only critical q=0 will be tested. 
            
            Critical points tests that fail. the user is responsible of changing
            the model tested or document the failure.
            
            Initial values for models are given as the one of Igo software.
    @author: Gervaise Alina / UTK
    @summary: Run by G. Alina 10/21/2009
            Most of the lamellar tests are not passing. Check lamellar im
            plementation.
            critial points tested not passing for:
            - Flexible Cylinder
            - PeakLorenzt
            - Squarewell Structure
            - StickyHstructure
            - hardSphereStructure
            
    @ Note: We don't use matrix for 2D anymore so testEval2D can be ignored (JC)     
            
"""

import unittest
import numpy 
import math

class TestCoreShell(unittest.TestCase):
    """ Unit tests for coreshell model """
    
    def setUp(self):
        from sas.models.CoreShellModel import CoreShellModel
        self.comp = CoreShellModel()
        #Give initial value to model
        self.comp.setParam("scale", 1.0)
        self.comp.setParam("radius", 60.0)
        self.comp.setParam("thickness", 10.0)
        self.comp.setParam("core_sld", 1.0e-6)
        self.comp.setParam("shell_sld",2.0e-6)
        self.comp.setParam("solvent_sld",3.0e-6)
        self.comp.setParam("Background", 0.001)
   
        self.x = numpy.array([0.4, 1.3])
        self.y = numpy.array([0.5, 1.57])
        self.x_array = self.comp.evalDistribution(self.x)
        self.y_array = self.comp.evalDistribution(self.y)
        
        qx_prime = numpy.reshape(self.x, [1,len(self.x)])
        qy_prime = numpy.reshape(self.y, [len(self.y),1])
        self.xy_matrix = self.comp.evalDistribution([self.x, self.y])
        
    def test1D(self):
        """ Test 1D model for a coreshell """
        self.assertAlmostEquals(self.comp.run(0.4),0.00169, 4)
        
    def test1D_2(self):
        """ Test 2D model for a coreshell """
        self.assertAlmostEquals(self.comp.run([0.4, 1.3]),0.00169, 4)
        
    def testEval_1D(self):
        """ Test 1D model for a coreshell  with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for a coreshell  with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0],8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1], 8)

    # No more singular point    
    #def testCriticalPoint(self):
    #    """ Test coreshell at the critical point"""
    #    self.assert_(numpy.isfinite(self.comp.run(0.0)))
  
class TestMultiShellModel(unittest.TestCase):
    """ Unit tests for MultiShell Model """
    
    def setUp(self):
        from sas.models.MultiShellModel import MultiShellModel
        self.comp = MultiShellModel()
        #Give initial value to model
        self.comp.setParam("scale", 1.0)
        self.comp.setParam("core_radius", 60.0)
        self.comp.setParam("s_thickness", 10.0)
        self.comp.setParam("w_thickness",10.0 )
        self.comp.setParam("core_sld",6.4e-6)
        self.comp.setParam("shell_sld",4e-7)
        self.comp.setParam("n_pairs", 2)
        self.comp.setParam("Background", 0.001)
        
        self.x = numpy.array([0.4, 1.3])
        self.y = numpy.array([0.5, 1.57])
        self.x_array = self.comp.evalDistribution(self.x)
        self.y_array = self.comp.evalDistribution(self.y)
        qx_prime = numpy.reshape(self.x, [1,len(self.x)])
        qy_prime = numpy.reshape(self.y, [len(self.y),1])
        self.xy_matrix = self.comp.evalDistribution([self.x, self.y])
        
    def test1D(self):
        """ Test 1D model for a MultiShell Model """
        self.assertAlmostEquals(self.comp.run(0.001), 2442.81, 2)
        
    def test1D_2(self):
        """ Test 2D model for a MultiShell Model"""
        self.assertAlmostEquals(self.comp.run([0.001, 0.30903]), 2442.81, 2)
      
    def testEval_1D(self):
        """ Test 1D model for a MultiShell  with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for a MultiShell  with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0],8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1], 8)

    # No more singular point
    #def testCriticalPoint(self):
    #    """ Test multishell at the critical point"""
    #    self.assert_(numpy.isfinite(self.comp.run(0.0)))
    
class TestVesicleModel(unittest.TestCase):
    """ Unit tests for Vesicle Model """
    
    def setUp(self):
        from sas.models.VesicleModel import VesicleModel
        self.comp = VesicleModel()
        #Give initial value to model
        self.comp.setParam("scale", 1.0)
        self.comp.setParam("radius", 100.0)
        self.comp.setParam("solv_sld", 6.36e-6)
        self.comp.setParam("shell_sld",5e-7)
        self.comp.setParam("thickness",30.0 )
        self.comp.setParam("Background", 0.001)
        
        self.x = numpy.array([0.4, 1.3])
        self.y = numpy.array([0.5, 1.57])
        self.x_array = self.comp.evalDistribution(self.x)
        self.y_array = self.comp.evalDistribution(self.y)
        #qx_prime = numpy.reshape(self.x, [1,len(self.x)])
        #qy_prime = numpy.reshape(self.y, [len(self.y),1])
        self.xy_matrix = self.comp.evalDistribution([self.x, self.y])
        
    def test1D(self):
        """ Test 1D model for a Vesicle Model """
        self.assertAlmostEquals(self.comp.run(0.001), 1.71399e4,1)
        
    def test1D_2(self):
        """ Test 2D model for a Vesicle Model"""
        self.assertAlmostEquals(self.comp.run([0.001, 1.3]), 1.71399e4,1)
        
    def testEval_1D(self):
        """ Test 1D model for a Vesicle with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for a Vesicle with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0],8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1], 8)

    
    def testCriticalPoint(self):
        """ Test vesicle at the critical point"""
        self.assert_(numpy.isfinite(self.comp.run(0.0))) 
        
        
class TestBinaryHSModel(unittest.TestCase):
    """ Unit tests for BinaryHS Model"""
    
    def setUp(self):
        from sas.models.BinaryHSModel import BinaryHSModel
        self.comp = BinaryHSModel()
        #Give initial value to model
        self.comp.setParam("l_radius", 100.0)
        self.comp.setParam("ls_sld", 3.5e-6)
        self.comp.setParam("s_radius",25)
        self.comp.setParam("solvent_sld",6.36e-6 )
        self.comp.setParam("ss_sld", 5e-7)
        self.comp.setParam("vol_frac_ss", 0.1)
        self.comp.setParam("vol_frac_ls", 0.2)
        self.comp.setParam("Background", 0.001)
        
        self.x = numpy.array([0.4, 1.3])
        self.y = numpy.array([0.5, 1.57])
        self.x_array = self.comp.evalDistribution(self.x)
        self.y_array = self.comp.evalDistribution(self.y)
        #qx_prime = numpy.reshape(self.x, [1,len(self.x)])
        #qy_prime = numpy.reshape(self.y, [len(self.y),1])
        self.xy_matrix = self.comp.evalDistribution([self.x, self.y])
        
    def test1D(self):
        """ Test 1D model for a BinaryHS Model"""
        self.assertAlmostEquals(self.comp.run(0.001),60.6785, 4)
        
    def test1D_2(self):
        """ Test 2D model for a BinaryHS Model"""
        self.assertAlmostEquals(self.comp.run([0.001, 1.3]),60.6785, 4)
      
    def testEval_1D(self):
        """ Test 1D model for a BinaryHS with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for a BinaryHS with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0],8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1], 8)

    # No more singular point    
    #def testCriticalPoint(self):
    #    """ Test BinaryHS at the critical point"""
    #    self.assert_(numpy.isfinite(self.comp.run(0.0)))
       
     
class TestCoreShellCylinderModel(unittest.TestCase):
    """ Unit tests for CoreShellCylinder Model"""
    
    def setUp(self):
        from sas.models.CoreShellCylinderModel import CoreShellCylinderModel
        self.comp = CoreShellCylinderModel()
        #Give initial value to model
        self.comp.setParam("scale", 1.0)
        self.comp.setParam("core_sld", 1e-6)
        self.comp.setParam("length", 400)
        self.comp.setParam("radius",20)
        self.comp.setParam("solvent_sld",1e-6 )
        self.comp.setParam("shell_sld", 4e-6)
        self.comp.setParam("thickness", 10.0)
        self.comp.setParam("Background", 0.01)
        
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
        """ Test 1D model for a CoreShellCylinder Model"""
        self.assertAlmostEqual(self.comp.run(0.001), 353.56,1)
        
    def test1D_2(self):
        """ Test 2D model for a CoreShellCylinder Model"""
        self.assertAlmostEqual(self.comp.run([self.q, self.phi]), 
                              self.comp.runXY([self.qx, self.qy]),1)
        
    def testEval_1D(self):
        """ Test 1D model for a CoreShellCylinder with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for a CoreShellCylinder with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0],8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1], 8)

    # No more singular point
    #def testCriticalPoint(self):
    #    """ Test CoreShellCylinder at the critical point"""
    #    self.assert_(numpy.isfinite(self.comp.run(0.0)))
 
     
class TestCoreShellBicelleModel(unittest.TestCase):
    """ Unit tests for CoreShellBicelle Model"""
    
    def setUp(self):
        from sas.models.CoreShellCylinderModel import CoreShellCylinderModel
        from sas.models.CoreShellBicelleModel import CoreShellBicelleModel
        self.comp1 = CoreShellCylinderModel()
        self.comp2 = CoreShellBicelleModel()
        # Using the default values of CSBiselle is same as CSCylinder
        
    def testcompare1D(self):
        """ Test 1D model for a CoreShellBicelle Model"""
        self.assertAlmostEqual(self.comp1.run(0.01), self.comp2.run(0.01), 8)
        
    def testcompareEval_2D(self):
        """ Test 2D model for a CoreShellBicelle with evalDistribution"""
        self.assertAlmostEquals(self.comp1.runXY([0.4, 0.5]),self.comp2.runXY([0.4, 0.5]),8)
        self.assertAlmostEquals(self.comp1.runXY([1.3,1.57]),self.comp2.runXY([1.3,1.57]),8)
        
                      
class TestHollowCylinderModel(unittest.TestCase):
    """ Unit tests for HollowCylinder Model"""
    
    def setUp(self):
        from sas.models.HollowCylinderModel import HollowCylinderModel
        self.comp = HollowCylinderModel()
        #Give initial value to model
        self.comp.setParam("scale", 1.0)
        self.comp.setParam("core_radius",20.0)
        self.comp.setParam("radius",30)
        self.comp.setParam("length", 400)
        self.comp.setParam("sldCyl",6.3e-6 )
        self.comp.setParam("sldSolv",1e-6 )
        self.comp.setParam("Background", 0.01)
        
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
        """ Test 1D model for a HollowCylinder Model"""
        self.assertAlmostEqual(self.comp.run(0.001), 1756.76, 1)
        
    def test1D_2(self):
        """ Test 2D model for a HollowCylinder Model"""
        self.assertAlmostEqual(self.comp.run([self.q, self.phi]), 
                              self.comp.runXY([self.qx, self.qy]),1) 
  
    def testEval_1D(self):
        """ Test 1D model for a HollowCylinder with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for a HollowCylinder with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0],8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1],8)

    # No more singular point    
    #def testCriticalPoint(self):
    #    """ Test HollowCylinder at the critical point"""
    #    self.assert_(numpy.isfinite(self.comp.run(0.0)))
        
        
class TestFlexibleCylinderModel(unittest.TestCase):
    """ Unit tests for FlexibleCylinder Model"""
    
    def setUp(self):
        from sas.models.FlexibleCylinderModel import FlexibleCylinderModel
        self.comp = FlexibleCylinderModel()
        #Give initial value to model
        self.comp.setParam("scale", 1.0)
        self.comp.setParam("sldSolv",6.3e-6 )
        self.comp.setParam("sldCyl",1e-6 )
        self.comp.setParam("kuhn_length",100)
        self.comp.setParam("length", 1000)
        self.comp.setParam("radius",20)
        self.comp.setParam("Background", 0.0001)
        
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
        """ Test 1D model for a FlexibleCylinder Model"""
        self.assertAlmostEqual(self.comp.run(0.001), 3509.22, 1)
        
    def test1D_2(self):
        """ Test 2D model for a FlexibleCylinder Model"""
        self.assertAlmostEqual(self.comp.run([self.q, self.phi]), 
                              self.comp.runXY([self.qx, self.qy]),1) 
    def testEval_1D(self):
        """ Test 1D model for a FlexibleCylinder Model with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for a FlexibleCylinder Model with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0],8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1], 8)

    # No more singular point
    #def testCriticalPoint(self):
    #    """ Test FlexibleCylinder at the critical point"""
    #    self.assert_(numpy.isfinite(self.comp.run(0.0)))
  
class TestFlexCylEllipXModel(unittest.TestCase):
    """ Unit tests for FlexCylEllipXModel"""
    
    def setUp(self):
        from sas.models.FlexCylEllipXModel import FlexCylEllipXModel
        self.comp = FlexCylEllipXModel()
        #Give initial value to model
        self.comp.setParam("scale", 1.0)
        self.comp.setParam("sldSolv",6.3e-6 )
        self.comp.setParam("sldCyl",1e-6 )
        self.comp.setParam("kuhn_length",100)
        self.comp.setParam("length", 1000)
        self.comp.setParam("radius",20)
        self.comp.setParam("background", 0.0001)
        self.comp.setParam("axis_ratio", 1.0)
        
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
        """ Test 1D model for FlexCylEllipXModel"""
        self.assertAlmostEqual(self.comp.run(0.001), 3509.22, 1)
        
    def test1D_2(self):
        """ Test 2D model for FlexCylEllipXModel"""
        self.assertAlmostEqual(self.comp.run([self.q, self.phi]), 
                              self.comp.runXY([self.qx, self.qy]),1) 
    def testEval_1D(self):
        """ Test 1D model for FlexCylEllipXModel with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for FlexCylEllipXModel with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0],8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1], 8)
              
              
class TestStackedDisksModel(unittest.TestCase):
    """ Unit tests for StackedDisks Model"""
    
    def setUp(self):
        from sas.models.StackedDisksModel import StackedDisksModel
        self.comp = StackedDisksModel()
        #Give initial value to model
        self.comp.setParam("scale", 0.01 )
        self.comp.setParam("radius",3000.0 )
        self.comp.setParam("core_thick", 10.0)
        self.comp.setParam("layer_thick",15.0 )
        self.comp.setParam("core_sld",4e-006 )
        self.comp.setParam("layer_sld",-4e-007 )
        self.comp.setParam("solvent_sld", 5e-006 )
        self.comp.setParam("n_stacking",1.0 )
        self.comp.setParam("sigma_d", 0.0)
        self.comp.setParam("background",0.001)
        self.comp.setParam("axis_theta", 0.0 )
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
        """ Test 1D model for a StackedDisks Model"""
        self.assertAlmostEqual(self.comp.run(0.001), 5075.12, 1)
        
    def test1D_2(self):
        """ Test 2D model for a StackedDisks Model"""
        self.assertAlmostEqual(self.comp.run([self.q, self.phi]), 
                              self.comp.runXY([self.qx, self.qy]),1)
        
    def testEval_1D(self):
        """ Test 1D model for a StackedDisks Model with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for a StackedDisks Model with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0],8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1], 8)

    # No more singular point
    #def testCriticalPoint(self):
    #    """ Test StackedDisks at the critical point"""
    #    self.assert_(numpy.isfinite(self.comp.run(0.0))) 
   
  
class TestParallelepipedModel(unittest.TestCase):
    """ Unit tests for Parallelepiped Model"""
    
    def setUp(self):
        from sas.models.ParallelepipedModel import ParallelepipedModel
        self.comp = ParallelepipedModel()
        #Give initial value to model
        self.comp.setParam("background", 0.0 )
        self.comp.setParam("short_a",35)
        self.comp.setParam("short_b", 75)
        self.comp.setParam("long_c",400 )
        self.comp.setParam("sldPipe", 6.3e-006 )
        self.comp.setParam("sldSolv", 1e-006 )
        self.comp.setParam("scale",1.0 )
        
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
        """ Test 1D model for a Parallelepiped Model"""
        self.assertAlmostEqual(self.comp.run(0.001), 2935.82, 2)
        
    def test1D_2(self):
        """ Test 2D model for a Parallelepiped Model"""
        self.assertAlmostEqual(self.comp.run([self.q, self.phi]), 
                              self.comp.runXY([self.qx, self.qy]),1)
        
    def testEval_1D(self):
        """ Test 1D model for a Parallelepiped Model with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for a Parallelepiped Model with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0],8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1], 8)

   
    def testCriticalPoint(self):
        """ Test Parallelepiped at the critical point"""
        self.assert_(numpy.isfinite(self.comp.run(0.0)))
  
class TestEllipticalCylinderModel(unittest.TestCase):
    """ Unit tests for EllipticalCylinder Model"""
    
    def setUp(self):
        from sas.models.EllipticalCylinderModel import EllipticalCylinderModel
        self.comp = EllipticalCylinderModel()
        self.comp.setParam("scale",1.0) 
        self.comp.setParam("r_minor",20.0)
        self.comp.setParam("r_ratio",1.5) 
        self.comp.setParam("length",400.0)
        self.comp.setParam("sldCyl",4e-006)
        self.comp.setParam("sldSolv",1e-006)
        self.comp.setParam("background",0.0)
        self.comp.setParam("cyl_theta",0.0)
        self.comp.setParam("cyl_phi",0.0)
        self.comp.setParam("cyl_psi",0.0)
        
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
        """ Test 1D model for a EllipticalCylinder Model"""
        self.assertAlmostEqual(self.comp.run(0.001), 675.504402, 4)
        
    def test1D_2(self):
        """ Test 2D model for a EllipticalCylinder Model"""
        self.assertAlmostEqual(self.comp.run([self.q, self.phi]), 
                              self.comp.runXY([self.qx, self.qy]),1)
        
    def testEval_1D(self):
        """ Test 1D model for a EllipticalCylinder with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for a EllipticalCylinder with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0],8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1], 8)

    
    def testCriticalPoint(self):
        """ Test EllipticalCylinder at the critical point"""
        self.assert_(numpy.isfinite(self.comp.run(0.0))) 
  
        
class TestEllipsoidModel(unittest.TestCase):
    """ Unit tests for Ellipsoid Model"""
    
    def setUp(self):
        from sas.models.EllipsoidModel import EllipsoidModel
        self.comp = EllipsoidModel()
        self.comp.setParam("scale",1.0) 
        self.comp.setParam("radius_a",20.0)
        self.comp.setParam("radius_b",400.0)
        self.comp.setParam("sldEll",4e-006)
        self.comp.setParam("sldSolv",1e-006)
        self.comp.setParam("background",0.0)
        self.comp.setParam("axis_theta",1.57)
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
        """ Test 1D model for a Ellipsoid Model"""
        self.assertAlmostEqual(self.comp.run(1.0), 0.000733968, 4)
        
    def test1D_2(self):
        """ Test 2D model for a Ellipsoid Model"""
        self.assertAlmostEqual(self.comp.run([self.q, self.phi]), 
                              self.comp.runXY([self.qx, self.qy]),1)
    def testEval_1D(self):
        """ Test 1D model for a Ellipsoid Model with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for a Ellipsoid Model with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0],8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1], 8)

    
    def testCriticalPoint(self):
        """ Test Ellipsoid at the critical point"""
        self.assert_(numpy.isfinite(self.comp.run(0.0)))
        
class TestCoreShellEllipsoidModel(unittest.TestCase):
    """ Unit tests for CoreShellEllipsoid Model"""
    
    def setUp(self):
        from sas.models.CoreShellEllipsoidModel import CoreShellEllipsoidModel
        self.comp = CoreShellEllipsoidModel()
        #Give initial value to model
        self.comp.setParam("scale", 1.0)
        self.comp.setParam("equat_core", 200.0)
        self.comp.setParam("polar_core", 20.0)
        self.comp.setParam("equat_shell",250.0)
        self.comp.setParam("polar_shell", 30.0)
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
    
class TestTriaxialEllipsoidModel(unittest.TestCase):
    """ Unit tests for TriaxialEllipsoid Model"""
    
    def setUp(self):
        from sas.models.TriaxialEllipsoidModel import TriaxialEllipsoidModel
        self.comp = TriaxialEllipsoidModel()
        self.comp.setParam("scale",1.0)
        self.comp.setParam("semi_axisA",35.0)
        self.comp.setParam("semi_axisB", 100.0)
        self.comp.setParam("semi_axisC",400.0 )
        self.comp.setParam("sldSolv",6.3e-6)
        self.comp.setParam("sldEll",1e-6)
        self.comp.setParam("background",0.0)
        self.comp.setParam("axis_theta", 1.0)
        self.comp.setParam("axis_phi",0.0 )
        self.comp.setParam("axis_psi",0.0 )
        
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
        """ Test 1D model for a TriaxialEllipsoid Model"""
        self.assertAlmostEquals(self.comp.run(0.001),16285.6, 1)
        
    def test1D_2(self):
        """ Test 2D model for a TriaxialEllipsoid Model"""
        self.assertAlmostEqual(self.comp.run([self.q, self.phi]), 
                              self.comp.runXY([self.qx, self.qy]),1)
     
    def testEval_1D(self):
        """ Test 1D model for a TriaxialEllipsoid Model with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for a TriaxialEllipsoid Model with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0],8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1], 8)

    
    def testCriticalPoint(self):
        """ Test TriaxialEllipsoid at the critical point"""
        self.assert_(numpy.isfinite(self.comp.run(0.0)))            
   
class TestLamellarModel(unittest.TestCase):
    """ Unit tests for Lamellar Model"""
    
    def setUp(self):
        from sas.models.LamellarModel import LamellarModel
        self.comp = LamellarModel()
        self.comp.setParam("scale",1.0) 
        self.comp.setParam("bi_thick",50.0)
        self.comp.setParam("sld_bi",1e-006)
        self.comp.setParam("sld_sol",6.3e-006)
        self.comp.setParam("background",0.0)

        self.x = numpy.array([0.4, 1.3])
        self.y = numpy.array([0.5, 1.57])
        
        self.x_array = self.comp.evalDistribution(self.x)
        self.y_array = self.comp.evalDistribution(self.y)
        qx_prime = numpy.reshape(self.x, [1,len(self.x)])
        qy_prime = numpy.reshape(self.y, [len(self.y),1])
        self.xy_matrix = self.comp.evalDistribution([self.x, self.y])
        
    def test1D(self):
        """ Test 1D model for a Lamellar Model"""
        self.assertAlmostEquals(self.comp.run(0.001), 882289.54309, 3)
        
    def test1D_2(self):
        """ Test 2D model for a Lamellar Model"""
        self.assertAlmostEquals(self.comp.run([0.001, 1.3]),882289.54309, 3)     
    
    def testEval_1D(self):
        """ Test 1D model for a Lamellar Model with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for a Lamellar Model with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0],8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1], 8)
       
    # No more singular point
    #def testCriticalPoint(self):
    #    """ Test Lamellar at the critical point"""
    #    self.assert_(numpy.isfinite(self.comp.run(0.0)))
     
class TestLamellarFFHGModel(unittest.TestCase):
    """ Unit tests for LamellarFFHG Model"""
    
    def setUp(self):
        from sas.models.LamellarFFHGModel import LamellarFFHGModel
        self.comp = LamellarFFHGModel()
        self.comp.setParam("scale",1.0) 
        self.comp.setParam("t_length",15.0)
        self.comp.setParam("h_thickness",10.0)
        self.comp.setParam("sld_tail",4e-007)
        self.comp.setParam("sld_head",3e-006)
        self.comp.setParam("sld_solvent",6e-006)
        self.comp.setParam("background",0.0)
        
        self.x = numpy.array([0.4, 1.3])
        self.y = numpy.array([0.5, 1.57])
        
        self.x_array = self.comp.evalDistribution(self.x)
        self.y_array = self.comp.evalDistribution(self.y)
        qx_prime = numpy.reshape(self.x, [1,len(self.x)])
        qy_prime = numpy.reshape(self.y, [len(self.y),1])
        self.xy_matrix = self.comp.evalDistribution([self.x, self.y])
        
        
    def test1D(self):
        """ Test 1D model for a LamellarFFHG Model"""
        self.assertAlmostEquals(self.comp.run(0.001),653143.9209, 3)
        
    def test1D_2(self):
        """ Test 2D model for a LamellarFFHG Model"""
        self.assertAlmostEquals(self.comp.run([0.001, 1.3]),653143.9209, 3)
    
    def testEval_1D(self):
        """ Test 1D model for a LamellarFFHG Model with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for a LamellarFFHG Model with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0],8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1], 8)
      
    # No more singular point
    #def testCriticalPoint(self):
    #    """ Test LamellarFFHG at the critical point"""
    #    self.assert_(numpy.isfinite(self.comp.run(0.0)))              
    
class TestLamellarPSModel(unittest.TestCase):
    """ Unit tests for LamellarPS Model"""
    
    def setUp(self):
        from sas.models.LamellarPSModel import LamellarPSModel
        self.comp = LamellarPSModel()
        self.comp.setParam("scale",1.0) 
        self.comp.setParam("spacing",400.0)
        self.comp.setParam("delta",30.0)
        self.comp.setParam("sld_bi",6.3e-006)
        self.comp.setParam("sld_sol",1e-006)
        self.comp.setParam("n_plates",20.0) 
        self.comp.setParam("caille", 0.1)
        self.comp.setParam("background",0.0)

        self.x = numpy.array([0.4, 1.3])
        self.y = numpy.array([0.5, 1.57])
        
        self.x_array = self.comp.evalDistribution(self.x)
        self.y_array = self.comp.evalDistribution(self.y)
        qx_prime = numpy.reshape(self.x, [1,len(self.x)])
        qy_prime = numpy.reshape(self.y, [len(self.y),1])
        self.xy_matrix = self.comp.evalDistribution([self.x, self.y])
        
        
    def test1D(self):
        """ Test 1D model for a LamellarPS Model"""
        self.assertAlmostEquals(self.comp.run(0.001), 28895.13397, 1)
        
    def test1D_2(self):
        """ Test 2D model for a LamellarPS Model"""
        self.assertAlmostEquals(self.comp.run([0.001, 1.3]),28895.13397, 1) 
    
    def testEval_1D(self):
        """ Test 1D model for a LamellarPS Model with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for a LamellarPS Model with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0],8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1], 8)
      
    # No more singular point        
    #def testCriticalPoint(self):
    #    """ Test LamellarPS at the critical point"""
    #    self.assert_(numpy.isfinite(self.comp.run(0.0)))
     
class TestLamellarPSHGModel(unittest.TestCase):
    """ Unit tests for LamellarPSHG Model"""
    
    def setUp(self):
        from sas.models.LamellarPSHGModel import LamellarPSHGModel
        self.comp = LamellarPSHGModel()
        self.comp.setParam("scale",1.0)
        self.comp.setParam("spacing",40.0)
        self.comp.setParam("deltaT",10.0)
        self.comp.setParam("deltaH",2.0)
        self.comp.setParam("sld_tail",4e-7)
        self.comp.setParam("sld_head",2e-6)
        self.comp.setParam("sld_solvent",6e-6)
        self.comp.setParam("n_plates",30)
        self.comp.setParam("caille",0.001)
        self.comp.setParam("background",0.001)

        self.x = numpy.array([0.4, 1.3])
        self.y = numpy.array([0.5, 1.57])
        
        self.x_array = self.comp.evalDistribution(self.x)
        self.y_array = self.comp.evalDistribution(self.y)
        qx_prime = numpy.reshape(self.x, [1,len(self.x)])
        qy_prime = numpy.reshape(self.y, [len(self.y),1])
        self.xy_matrix = self.comp.evalDistribution([self.x, self.y])
        
    def test1D(self):
        """ Test 1D model for a LamellarPSHG Model"""
        self.assertAlmostEquals(self.comp.run(0.001),6838238.571488, 3)
        
    def test1D_2(self):
        """ Test 2D model for a LamellarPSHG Model"""
        self.assertAlmostEquals(self.comp.run([0.001, 1.3]),6838238.571488,3)
        
    def testEval_1D(self):
        """ Test 1D model for a LamellarPSHG Model with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for a LamellarPSHG Model with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0],8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1], 8)
       
    # No more singular point
    #def testCriticalPoint(self):
    #    """ Test LamellarPSHG at the critical point"""
    #    self.assert_(numpy.isfinite(self.comp.run(0.0)))
     
class TestSquareWellStructure(unittest.TestCase):
    """ Unit tests for SquareWellStructure """
    
    def setUp(self):
        from sas.models.SquareWellStructure import SquareWellStructure
        self.comp = SquareWellStructure()
        self.comp.setParam("effect_radius",50.0)
        self.comp.setParam("volfraction",0.04)
        self.comp.setParam("welldepth",1.5 )
        self.comp.setParam("wellwidth",1.2)
        
        self.x = numpy.array([0.4, 1.3])
        self.y = numpy.array([0.5, 1.57])
        
        self.x_array = self.comp.evalDistribution(self.x)
        self.y_array = self.comp.evalDistribution(self.y)
        qx_prime = numpy.reshape(self.x, [1,len(self.x)])
        qy_prime = numpy.reshape(self.y, [len(self.y),1])
        self.xy_matrix = self.comp.evalDistribution([self.x, self.y])
        
        
    def test1D(self):
        """ Test 1D model for a SquareWellStructure"""
        self.assertAlmostEqual(self.comp.run(0.001), 0.976657, 2)
        
    def test1D_2(self):
        """ Test 2D model for a SquareWellStructure"""
        self.assertAlmostEqual(self.comp.run([0.001, 1.3]),0.9776657,2)     
    
    def testEval_1D(self):
        """ Test 1D model for a SquareWellStructure with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for a SquareWellStructure with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0],8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1], 8)

    # No more singular point
    #def testCriticalPoint(self):
    #    """ Test SquareWellStructure at the critical point"""
    #    self.assert_(numpy.isfinite(self.comp.run(0.0)))                     
     
class TestHardsphereStructure(unittest.TestCase):
    """ Unit tests for HardsphereStructure"""
    
    def setUp(self):
        from sas.models.HardsphereStructure import HardsphereStructure
        self.comp = HardsphereStructure()
        self.comp.setParam("effect_radius",50.0)
        self.comp.setParam("volfraction", 0.2)
        self.x = numpy.array([0.4, 1.3])
        self.y = numpy.array([0.5, 1.57])
        
        self.x_array = self.comp.evalDistribution(self.x)
        self.y_array = self.comp.evalDistribution(self.y)
        qx_prime = numpy.reshape(self.x, [1,len(self.x)])
        qy_prime = numpy.reshape(self.y, [len(self.y),1])
        self.xy_matrix = self.comp.evalDistribution([self.x, self.y])
        
        
    def test1D(self):
        """ Test 1D model for a HardsphereStructure"""
        self.assertAlmostEqual(self.comp.run(0.001),0.209128, 4)
        
    def test1D_2(self):
        """ Test 2D model for a HardsphereStructure"""
        self.assertAlmostEqual(self.comp.run([0.001, 1.3]),0.209128, 4)
        
    def testEval_1D(self):
        """ Test 1D model for a HardsphereStructure with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for a HardsphereStructure with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0],8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1], 8)

    # No more singular point
    #def testCriticalPoint(self):
    #    """ Test HardsphereStructure at the critical point"""
    #    self.assert_(numpy.isfinite(self.comp.run(0.0)))                  
    
class TestStickyHSStructure(unittest.TestCase):
    """ Unit tests for StickyHSStructure"""
    
    def setUp(self):
        from sas.models.StickyHSStructure import StickyHSStructure
        self.comp = StickyHSStructure()
        self.comp.setParam("effect_radius",50.0)
        self.comp.setParam("volfraction",0.1)
        self.comp.setParam("perturb",0.05)
        self.comp.setParam("stickiness",0.2)

        self.x = numpy.array([0.4, 1.3])
        self.y = numpy.array([0.5, 1.57])
        
        self.x_array = self.comp.evalDistribution(self.x)
        self.y_array = self.comp.evalDistribution(self.y)
        qx_prime = numpy.reshape(self.x, [1,len(self.x)])
        qy_prime = numpy.reshape(self.y, [len(self.y),1])
        self.xy_matrix = self.comp.evalDistribution([self.x, self.y])
        
    def test1D(self):
        """ Test 1D model for a StickyHSStructure"""
        self.assertAlmostEqual(self.comp.run(0.001),1.09718, 4)
        
    def test1D_2(self):
        """ Test 2D model for a StickyHSStructure"""
        self.assertAlmostEqual(self.comp.run([0.001, 1.3]),1.09718, 4)
        
    def testEval_1D(self):
        """ Test 1D model for a StickyHSStructure with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for a StickyHSStructure with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0],8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1], 8)

    # No more singular point           
    #def testCriticalPoint(self):
    #    """ Test StickyHSStructure at the critical point"""
    #    self.assert_(numpy.isfinite(self.comp.run(0.0))) 
        
class TestHayterMSAStructure(unittest.TestCase):
    """ Unit tests for HayterMSAStructure"""
    
    def setUp(self):
        from sas.models.HayterMSAStructure import HayterMSAStructure
        self.comp = HayterMSAStructure()
        self.comp.setParam("effect_radius",20.75)
        self.comp.setParam("charge",19.0)
        self.comp.setParam("volfraction",0.0192 )
        self.comp.setParam("temperature",298)
        self.comp.setParam("saltconc",0.0)
        self.comp.setParam("dielectconst",78)
        
        self.x = numpy.array([0.4, 1.3])
        self.y = numpy.array([0.5, 1.57])
        
        self.x_array = self.comp.evalDistribution(self.x)
        self.y_array = self.comp.evalDistribution(self.y)
        qx_prime = numpy.reshape(self.x, [1,len(self.x)])
        qy_prime = numpy.reshape(self.y, [len(self.y),1])
        self.xy_matrix = self.comp.evalDistribution([self.x, self.y])

    def test1D(self):
        """ Test 1D model for a HayterMSAStructure"""
        self.assertAlmostEqual(self.comp.run(0.001),0.0712928, 4)
        
    def test1D_2(self):
        """ Test 2D model for a HayterMSAStructure"""
        self.assertAlmostEqual(self.comp.run([0.001, 1.3]),0.0712928, 4) 
        
    def testEval_1D(self):
        """ Test 1D model for a HayterMSAStructure with evalDistribution"""
        self.assertTrue(math.fabs(self.comp.run(0.4)-self.x_array[0])<0.025, "Difference too big: %g" % math.fabs(self.comp.run(0.4)-self.x_array[0]))
        self.assertTrue(math.fabs(self.comp.run(1.3)-self.x_array[1])<0.025, "Difference too big: %g" % math.fabs(self.comp.run(1.3)-self.x_array[1]))
        
    def testEval_2D(self):
        """ Test 2D model for a HayterMSAStructure with evalDistribution"""
        self.assertTrue(math.fabs(self.comp.runXY([0.4, 0.5])-self.xy_matrix[0])<0.05, "Difference too big: %g" % math.fabs(self.comp.runXY([0.4, 0.5])-self.xy_matrix[0]))
        self.assertTrue(math.fabs(self.comp.runXY([1.3,1.57])-self.xy_matrix[1])<0.05, "Difference too big: %g" % math.fabs(self.comp.runXY([1.3,1.57])-self.xy_matrix[1]))

    
    def testCriticalPoint(self):
        """ Test HayterMSAStructure at the critical point"""
        self.assert_(numpy.isfinite(self.comp.run(0.0)))                   
     
     
class TestBEPolyelectrolyte(unittest.TestCase):
    """ Unit tests for BEPolyelectrolyte"""
    
    def setUp(self):
        from sas.models.BEPolyelectrolyte import BEPolyelectrolyte
        self.comp = BEPolyelectrolyte()
       
        self.comp.setParam('k',10)
        self.comp.setParam('lb',7.1)
        self.comp.setParam('h',12)
        self.comp.setParam('b',10)
        self.comp.setParam('cs', 0.0)
        self.comp.setParam('alpha',0.05)
        self.comp.setParam('c', 0.7)
        self.comp.setParam('background',0.001)
         
        self.x = numpy.array([0.4, 1.3])
        self.y = numpy.array([0.5, 1.57])
        
        self.x_array = self.comp.evalDistribution(self.x)
        self.y_array = self.comp.evalDistribution(self.y)
        qx_prime = numpy.reshape(self.x, [1,len(self.x)])
        qy_prime = numpy.reshape(self.y, [len(self.y),1])
        self.xy_matrix = self.comp.evalDistribution([self.x, self.y])

    def test1D(self):
        """ Test 1D model for a BEPolyelectrolyte"""
        self.assertAlmostEqual(self.comp.run(0.001),0.0948, 3)
        
    def test1D_2(self):
        """ Test 2D model for a BEPolyelectrolyte"""
        self.assertAlmostEqual(self.comp.run([0.001, 1.3]),0.0948, 3)
      
    def testEval_1D(self):
        """ Test 1D model for a BEPolyelectrolyte with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for a BEPolyelectrolyte with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0],8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1], 8)

   
    def testCriticalPoint(self):
        """ Test BEPolyelectrolyte at the critical point"""
        self.assert_(numpy.isfinite(self.comp.run(0.0)))            
             
             
class TestDABModel(unittest.TestCase):
    """ Unit tests for DABModel"""
    
    def setUp(self):
        from sas.models.DABModel import DABModel
        self.comp = DABModel()
        self.comp.setParam('length',40.0)
        self.comp.setParam('scale',10.0)
        self.comp.setParam('background',1.0)
        
        self.x = numpy.array([0.4, 1.3])
        self.y = numpy.array([0.5, 1.57])
    
        self.x_array = self.comp.evalDistribution(self.x)
        self.y_array = self.comp.evalDistribution(self.y)
        qx_prime = numpy.reshape(self.x, [1,len(self.x)])
        qy_prime = numpy.reshape(self.y, [len(self.y),1])
        self.xy_matrix = self.comp.evalDistribution([self.x, self.y])
        
    def test1D(self):
        """ Test 1D model for a DABModel"""
        self.assertAlmostEqual(self.comp.run(0.001),637957.9047, 3)
        
    def test1D_2(self):
        """ Test 2D model for a DABModel"""
        self.assertAlmostEqual(self.comp.run([0.001, 1.3]),637957.90473, 3)
         
    def testEval_1D(self):
        """ Test 1D model for a DABModel with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for a DABModel with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0],8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1], 8)

    
    def testCriticalPoint(self):
        """ Test DABModel at the critical point"""
        self.assert_(numpy.isfinite(self.comp.run(0.0)))           

             
    
class TestGuinierModel(unittest.TestCase):
    """ Unit tests for Guinier Model"""
    
    def setUp(self):
        from sas.models.GuinierModel import GuinierModel
        self.comp = GuinierModel()
        self.comp.setParam('scale',1.0)
        self.comp.setParam('rg', 1)
        
        self.x = numpy.array([0.4, 1.3])
        self.y = numpy.array([0.5, 1.57])
        
        self.x_array = self.comp.evalDistribution(self.x)
        self.y_array = self.comp.evalDistribution(self.y)
        qx_prime = numpy.reshape(self.x, [1,len(self.x)])
        qy_prime = numpy.reshape(self.y, [len(self.y),1])
        self.xy_matrix = self.comp.evalDistribution([self.x, self.y])
        
    def test1D(self):
        """ Test 1D model for a GuinierModel"""
        self.assertAlmostEqual(self.comp.run(1.0),0.716531, 4)
        
    def test1D_2(self):
        """ Test 2D model for a GuinierModel"""
        self.assertAlmostEqual(self.comp.run([1.0, 1.3]),0.716531, 4)
     
    def testEval_1D(self):
        """ Test 1D model for a GuinierModel with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for a GuinierModel with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0],8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1], 8)

    
    def testCriticalPoint(self):
        """ Test GuinierModel at the critical point"""
        self.assert_(numpy.isfinite(self.comp.run(0.0)))
        
        
class TestDebyeModel(unittest.TestCase):
    """ Unit tests for Debye Model"""
    
    def setUp(self):
        from sas.models.DebyeModel import DebyeModel
        self.comp = DebyeModel()
        self.comp.setParam('rg', 50.0)
        self.comp.setParam('scale',1.0)
        self.comp.setParam('background',0.001)
        
        self.x = numpy.array([0.4, 1.3])
        self.y = numpy.array([0.5, 1.57])
        
        self.x_array = self.comp.evalDistribution(self.x)
        self.y_array = self.comp.evalDistribution(self.y)
        qx_prime = numpy.reshape(self.x, [1,len(self.x)])
        qy_prime = numpy.reshape(self.y, [len(self.y),1])
        self.xy_matrix = self.comp.evalDistribution([self.x, self.y])
        
    def test1D(self):
        """ Test 1D model for a DebyeModel"""
        self.assertAlmostEqual(self.comp.run(0.001),1.00017,4)
        
    def test1D_2(self):
        """ Test 2D model for a DebyeModel"""
        self.assertAlmostEqual(self.comp.run([0.001, 1.3]),1.00017,4)
        
    def testEval_1D(self):
        """ Test 1D model for a DebyeModel with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for a DebyeModel with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0],8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1], 8)

    
    def testCriticalPoint(self):
        """ Test DebyeModel at the critical point"""
        self.assertEquals(self.comp.run(0.0),1.001)
        
       
class TestPorodModel(unittest.TestCase):
    """ Unit tests for PorodModel"""
    
    def setUp(self):
        from sas.models.PorodModel import PorodModel
        self.comp = PorodModel()
        self.comp.setParam('scale', 1.0)
        self.comp.setParam('background', 0.0)
         
        self.x = numpy.array([0.4, 1.3])
        self.y = numpy.array([0.5, 1.57])
        
        self.x_array = self.comp.evalDistribution(self.x)
        self.y_array = self.comp.evalDistribution(self.y)
        qx_prime = numpy.reshape(self.x, [1,len(self.x)])
        qy_prime = numpy.reshape(self.y, [len(self.y),1])
        self.xy_matrix = self.comp.evalDistribution([self.x, self.y])
        
    def test1D(self):
        """ Test 1D model for a PorodModel"""
        self.assertEquals(self.comp.run(0.5), 16)
        
    def test1D_2(self):
        """ Test 2D model for a PorodModel"""
        self.assertEquals(self.comp.run([0.5, 1.3]),16)  
        
    def testEval_1D(self):
        """ Test 1D model for a PorodModel with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for a PorodModel with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0],8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1], 8)

    
    def testCreaticalPoint(self):
        """ Test for critical point for PorodModel run"""
        self.assertRaises(ZeroDivisionError, self.comp.run, 0.0)
        
        
class TestPeakGaussModel(unittest.TestCase):
    """ Unit tests for PeakGaussModel"""
    
    def setUp(self):
        from sas.models.PeakGaussModel import PeakGaussModel
        self.comp = PeakGaussModel()
        self.comp.setParam('scale', 100)
        self.comp.setParam('B', 0.005)
        self.comp.setParam('q0',0.05)
        self.comp.setParam('background',1.0)
        
        self.x = numpy.array([0.4, 1.3])
        self.y = numpy.array([0.5, 1.57])
        
        self.x_array = self.comp.evalDistribution(self.x)
        self.y_array = self.comp.evalDistribution(self.y)
        qx_prime = numpy.reshape(self.x, [1,len(self.x)])
        qy_prime = numpy.reshape(self.y, [len(self.y),1])
        self.xy_matrix = self.comp.evalDistribution([self.x, self.y])
        
    def test1D(self):
        """ Test 1D model for a PeakGauss Model"""
        self.assertEquals(self.comp.run(0.001),1)
        
    def test1D_2(self):
        """ Test 2D model for a PeakGauss Model"""
        self.assertEquals(self.comp.run([0.001, 1.3]),1)  
        
    def testEval_1D(self):
        """ Test 1D model for a PeakGauss Model with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for a PeakGauss Model with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0],8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1], 8)
    
    def testCriticalPoint(self):
        """ Test PeakGauss at the critical point"""
        self.assert_(numpy.isfinite(self.comp.run(0.0)))    
        
class TestPeakLorentzModel(unittest.TestCase):
    """ Unit tests for PeakLorentzModel"""
    
    def setUp(self):
        from sas.models.PeakLorentzModel import PeakLorentzModel
        self.comp = PeakLorentzModel()
        self.comp.setParam('scale', 100)
        self.comp.setParam('B', 0.005)
        self.comp.setParam('q0',0.05)
        self.comp.setParam('background',1.0)
        
        self.x = numpy.array([0.4, 1.3])
        self.y = numpy.array([0.5, 1.57])
        
        self.x_array = self.comp.evalDistribution(self.x)
        self.y_array = self.comp.evalDistribution(self.y)
        qx_prime = numpy.reshape(self.x, [1,len(self.x)])
        qy_prime = numpy.reshape(self.y, [len(self.y),1])
        self.xy_matrix = self.comp.evalDistribution([self.x, self.y])
        
    def test1D(self):
        """ Test 1D model for a PeakLorentz Model"""
        self.assertAlmostEqual(self.comp.run(0.001), 2.0305, 3)
        
    def test1D_2(self):
        """ Test 2D model for a PeakLorentz Model"""
        self.assertAlmostEqual(self.comp.run([0.001, 1.3]), 2.0305, 3)
        
    def testEval_1D(self):
        """ Test 1D model for a PeakLorentz Model with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for a PeakLorentz Model with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0],8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1], 8)

        
    def testCriticalPoint(self):
        """ Test PeakLorentz at the critical point"""
        self.comp.setParam('B', 0.0)
        self.assertRaises(ZeroDivisionError, self.comp.run, 10)
        #self.assert_(numpy.isfinite(self.comp.run(0.0)))       
   
class TestFractalModel(unittest.TestCase):
    """ Unit tests for FractalModel"""
    
    def setUp(self):
        from sas.models.FractalModel import FractalModel
        self.comp = FractalModel()
        self.comp.setParam('scale', 0.05)
        self.comp.setParam('radius', 5.0)
        self.comp.setParam('fractal_dim', 2.0)
        self.comp.setParam('cor_length',100.0)
        self.comp.setParam('sldBlock', 2.0e-6)
        self.comp.setParam('sldSolv', 6.35e-6)
        self.comp.setParam('background',0.0)
        
        self.x = numpy.array([0.4, 1.3])
        self.y = numpy.array([0.5, 1.57])
        
        self.x_array = self.comp.evalDistribution(self.x)
        self.y_array = self.comp.evalDistribution(self.y)
        qx_prime = numpy.reshape(self.x, [1,len(self.x)])
        qy_prime = numpy.reshape(self.y, [len(self.y),1])
        self.xy_matrix = self.comp.evalDistribution([self.x, self.y])
        
    def test1D(self):
        """ Test 1D model for a Fractal Model"""
        self.assertAlmostEqual(self.comp.run(0.001), 39.2881, 3)
        
    def test1D_2(self):
        """ Test 2D model for a Fractal Model"""
        self.assertAlmostEqual(self.comp.run([0.001, 1.3]), 39.2881, 3)
        
    def testEval_1D(self):
        """ Test 1D model for a Fractal Model with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for a Fractal Model with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0],8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1], 8)

    # No more singular point    
    #def testCriticalPoint(self):
    #    """ Test Fractal at the critical point"""
    #    self.assert_(numpy.isfinite(self.comp.run(0.0)))
    
class TestLorentzModel(unittest.TestCase):
    """ Unit tests for LorentzModel"""
    
    def setUp(self):
        from sas.models.LorentzModel import LorentzModel
        self.comp = LorentzModel()
        self.comp.setParam("background",1)
        self.comp.setParam("length",50)
        self.comp.setParam("scale",100)
        
        self.x = numpy.array([0.4, 1.3])
        self.y = numpy.array([0.5, 1.57])
        
        self.x_array = self.comp.evalDistribution(self.x)
        self.y_array = self.comp.evalDistribution(self.y)
        qx_prime = numpy.reshape(self.x, [1,len(self.x)])
        qy_prime = numpy.reshape(self.y, [len(self.y),1])
        self.xy_matrix = self.comp.evalDistribution([self.x, self.y])
        
    def test1D(self):
        """ Test 1D model for a Lorentz Model"""
        self.assertAlmostEqual(self.comp.run(0.001),100.751, 2)
        
    def test1D_2(self):
        """ Test 2D model for a Lorentz Model"""
        self.assertAlmostEqual(self.comp.run([0.001, 1.3]),100.751, 2)
    
    def testEval_1D(self):
        """ Test 1D model for a Lorentz Model with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for a Lorentz Model with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0],8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1], 8)

          
    def testCriticalPoint(self):
        """ Test Lorentz at the critical point"""
        self.assert_(numpy.isfinite(self.comp.run(0.0)))
        
          
class TestPowerLawAbsModel(unittest.TestCase):
    """ Unit tests for PowerLawAbsModel"""
    
    def setUp(self):
        from sas.models.PowerLawAbsModel import PowerLawAbsModel
        self.comp = PowerLawAbsModel()
        self.comp.setParam("background",1)
        self.comp.setParam("m",4)
        self.comp.setParam("scale",1e-6)
        
        self.x = numpy.array([0.4, 1.3])
        self.y = numpy.array([0.5, 1.57])
        self.x_array = self.comp.evalDistribution(self.x)
        self.y_array = self.comp.evalDistribution(self.y)
        qx_prime = numpy.reshape(self.x, [1,len(self.x)])
        qy_prime = numpy.reshape(self.y, [len(self.y),1])
        self.xy_matrix = self.comp.evalDistribution([self.x, self.y])
        
    def test1D(self):
        """ Test 1D model for a PowerLawAbs Model"""
        self.assertAlmostEqual(self.comp.run(0.19189), 1.00074,4)
        
    def test1D_2(self):
        """ Test 2D model for a PowerLawAbs Model"""
        self.assertAlmostEqual(self.comp.run([0.19189,1.3]), 1.00074,4)
        
    def testEval_1D(self):
        """ Test 1D model for a PowerLawAbs Model with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for a PowerLawAbs Model with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0],8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1], 8)

    
    def testCriticalPoint(self):
        """ Test PowerLawAbs at the critical point"""
        self.assert_(numpy.isfinite(self.comp.run(0.0)))
        
        
class TestPowerLawModel(unittest.TestCase):
    """ Unit tests for PowerLawModel"""
    
    def setUp(self):
        from sas.models.PowerLawModel import PowerLawModel
        self.comp = PowerLawModel()
        self.comp.setParam("background",1)
        self.comp.setParam("m",4)
        self.comp.setParam("scale",1e-6)
        
        self.x = numpy.array([0.4, 1.3])
        self.y = numpy.array([0.5, 1.57])
        self.x_array = self.comp.evalDistribution(self.x)
        self.y_array = self.comp.evalDistribution(self.y)
        qx_prime = numpy.reshape(self.x, [1,len(self.x)])
        qy_prime = numpy.reshape(self.y, [len(self.y),1])
        self.xy_matrix = self.comp.evalDistribution([self.x, self.y])
        
    def test1D(self):
        """ Test 1D model for a PowerLaw Model"""
        self.assertAlmostEquals(self.comp.run(0.19189), 1.00074,4)
        
    def test1D_2(self):
        """ Test 2D model for a PowerLawModel"""
        self.assertAlmostEquals(self.comp.run([0.19189,1.3]), 1.00074,4)
        
    def testEval_1D(self):
        """ Test 1D model for a PowerLawModel with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for a PowerLawModel with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0],8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1], 8)

    
    def testCriticalPoint(self):
        """ Test PowerLawModel at the critical point"""
        self.assert_(numpy.isfinite(self.comp.run(0.0)))
      
      
class TestTeubnerStreyModel(unittest.TestCase):
    """ Unit tests for TeubnerStreyModel"""
    
    def setUp(self):
        from sas.models.TeubnerStreyModel import TeubnerStreyModel
        self.comp = TeubnerStreyModel()
        self.comp.setParam("background",0.1)
        self.comp.setParam("c1",-30)
        self.comp.setParam("c2",5000)
        self.comp.setParam("scale",0.1)
        
        self.x = numpy.array([0.4, 1.3])
        self.y = numpy.array([0.5, 1.57])
        self.x_array = self.comp.evalDistribution(self.x)
        self.y_array = self.comp.evalDistribution(self.y)
        qx_prime = numpy.reshape(self.x, [1,len(self.x)])
        qy_prime = numpy.reshape(self.y, [len(self.y),1])
        self.xy_matrix = self.comp.evalDistribution([self.x, self.y])
        
    def test1D(self):
        """ Test 1D model for a TeubnerStrey Model"""
        self.assertAlmostEqual(self.comp.run(0.001),10.103, 1)
        
    def test1D_2(self):
        """ Test 2D model for a TeubnerStrey Model"""
        self.assertAlmostEqual(self.comp.run([0.001, 1.3]),10.103, 1)
        
    def testEval_1D(self):
        """ Test 1D model for a TeubnerStrey  with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for a TeubnerStrey  with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0],8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1], 8)

    
    def testCriticalPoint(self):
        """ Test TeubnerStrey at the critical point"""
        self.assert_(numpy.isfinite(self.comp.run(0.0)))    
      
      
class TestLineModel(unittest.TestCase):
    """ Unit tests for LineModel"""
    
    def setUp(self):
        from sas.models.LineModel import LineModel
        self.comp = LineModel()
        self.comp.setParam("A",1)
        self.comp.setParam("B",1)
        
        self.x = numpy.array([0.4, 1.3])
        self.y = numpy.array([0.5, 1.57])
        self.x_array = self.comp.evalDistribution(self.x)
        self.y_array = self.comp.evalDistribution(self.y)
        qx_prime = numpy.reshape(self.x, [1,len(self.x)])
        qy_prime = numpy.reshape(self.y, [len(self.y),1])
        self.xy_matrix = self.comp.evalDistribution([self.x, self.y])
        
    def test1D(self):
        """ Test 1D model for a Line Model"""
        self.assertEquals(self.comp.run(1.0),2)
        
    def testEval_1D(self):
        """ Test 1D model for a Line  with evalDistribution"""
        self.assertEquals(self.comp.run(0.4),self.x_array[0])
        self.assertEquals(self.comp.run(1.3),self.x_array[1])
        
    def testEval_2D(self):
        """ Test 2D model for a Line  with evalDistribution"""
        self.assertAlmostEquals(self.comp.runXY([0.4, 0.5]),self.xy_matrix[0], 8)
        self.assertAlmostEquals(self.comp.runXY([1.3,1.57]),self.xy_matrix[1], 8)

    
    def testCriticalPoint(self):
        """ Test line at the critical point"""
        self.assert_(numpy.isfinite(self.comp.run(0.0)))

class TestMassFractalModel(unittest.TestCase):
    """ Unit tests for MassFractalModel: Need to verify the test value"""
    
    def setUp(self):
        from sas.models.MassFractalModel import MassFractalModel
        self.comp = MassFractalModel()
        
    def testEval_1D(self):
        """ Test 1D model for a MassFractalModel"""
        self.assertAlmostEquals(self.comp.run(0.05), 279.59322, 4)

class TestSurfaceFractalModel(unittest.TestCase):
    """ Unit tests for SurfaceFractalModel: Need to verify the test value"""
    
    def setUp(self):
        from sas.models.SurfaceFractalModel import SurfaceFractalModel
        self.comp = SurfaceFractalModel()
        
    def testEval_1D(self):
        """ Test 1D model for a SurfaceFractal"""
        self.assertAlmostEquals(self.comp.run(0.05), 301428.65916, 4)

class TestMassSurfaceFractal(unittest.TestCase):
    """ Unit tests for MassSurfaceFractal: Need to verify the test value"""
    
    def setUp(self):
        from sas.models.MassSurfaceFractal import MassSurfaceFractal
        self.comp = MassSurfaceFractal()
        
    def testEval_1D(self):
        """ Test 1D model for a MassSurfaceFractal"""
        self.assertAlmostEquals(self.comp.run(0.05), 1.77537e-05, 4)
        
if __name__ == '__main__':
    unittest.main()
