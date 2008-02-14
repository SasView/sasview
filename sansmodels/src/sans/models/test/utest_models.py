"""
    Unit tests for specific models
    @author: Mathieu Doucet / UTK
"""

import unittest, time, math

# Disable "missing docstring" complaint
# pylint: disable-msg=C0111
# Disable "too many methods" complaint 
# pylint: disable-msg=R0904 
# Disable "could be a function" complaint 
# pylint: disable-msg=R0201


        
class TestSphere(unittest.TestCase):
    """ Unit tests for sphere model """
    
    def setUp(self):
        from sans.models.SphereModel import SphereModel
        self.comp = SphereModel()
        
    def test1D(self):
        """ Test 1D model for a sphere """
        self.assertAlmostEqual(self.comp.run(1.0), 56.3878, 4)
        
    def test1D_2(self):
        """ Test 2D model for a sphere """
        self.assertAlmostEqual(self.comp.run([1.0, 1.3]), 56.3878, 4)

class TestCyl(unittest.TestCase):
    """Unit tests for cylinder"""
    
    def setUp(self):

        from sans.models.CylinderModel import CylinderModel
        self.comp = CylinderModel()
        
    def test1D(self):
        """ Test 1D model of a cylinder """ 
        self.assertAlmostEqual(self.comp.run(0.2), 0.041761386790780453, 4)
       
    def testTime(self):
        """ Time profiling """
        self.comp.run(2.0)
        t0 = time.clock()
        self.assertTrue(time.clock()-t0<1e-5)
     
    def test2D(self):
        """ Test 2D model of a cylinder """ 
        self.assertAlmostEqual(self.comp.run([0.2, 2.5]), 
                               0.038176446608393366, 4)
       
    def testIO(self):
        from sans.models.ModelFactory import ModelFactory
        from sans.models.ModelIO import ModelIO
        factory = ModelFactory()
        io = ModelIO(factory)
        io.save(self.comp,"myModel.xml")
        value = self.comp.run(1)
        loaded = io.load("myModel.xml")
        self.assertEqual(value, loaded.run(1))
        
    def testIO_add(self):
        from sans.models.ModelFactory import ModelFactory
        from sans.models.ModelIO import ModelIO
        factory = ModelFactory()
        io = ModelIO(factory)
        sph = factory.getModel("SphereModel")
        cyl = factory.getModel("CylinderModel")
        combo = sph - cyl
        io.save(combo,"myModel.xml")
        value = combo.run(1)
        loaded = io.load("myModel.xml")
        self.assertEqual(value, loaded.run(1))
        
    def testIO_add2(self):
        from sans.models.ModelFactory import ModelFactory
        #from sans.models.ModelIO import ModelIO
        factory = ModelFactory()
        #io = ModelIO(factory)
        sph = factory.getModel("SphereModel")
        cyl = factory.getModel("CylinderModel")
        sph2 = factory.getModel("SphereModel")
        combo1 = cyl - sph
        combo = combo1 / sph2
        #combo1 = sph
        #io.save(combo,"myModel.xml")
        # Just check that we have some output
        self.assertTrue(math.fabs(combo.run(1))>0)
        #loaded = io.load("myModel.xml")
        #self.assertEqual(value, loaded.run(1))
        
        
      
       
class TestFactory(unittest.TestCase):
    """Unit tests for Model Factory"""
    
    def setUp(self):
        from sans.models.ModelFactory import ModelFactory
        self.comp = ModelFactory().getModel('CylinderModel')
        
    def test1D(self):
        """ Test 1D model of a cylinder """ 
        self.assertAlmostEqual(self.comp.run(0.2), 0.041761386790780453, 4)
        
class TestAddition(unittest.TestCase):
    """Unit tests for Model Factory"""
    
    def setUp(self):
        from sans.models.ModelFactory import ModelFactory
        self.comp1 = ModelFactory().getModel('CylinderModel')
        self.comp2 = ModelFactory().getModel('CylinderModel')
        self.comp3 = self.comp1+self.comp2
        
    def test1D(self):
        """ Test 1D model of a cylinder """
        self.assertAlmostEqual(self.comp3.run(0.2), 2*0.041761386790780453, 4)
        
 
class TestGaussian(unittest.TestCase):
    """Unit tests for Gaussian function"""
    
    def setUp(self):
        from sans.models.Gaussian import Gaussian
        self.gauss= Gaussian()
        
    def test1D(self):
        self.gauss.setParam('scale', 2.0)
        self.gauss.setParam('center', 1.0)
        self.gauss.setParam('sigma', 1.0)
        self.assertEqual(self.gauss.run(1.0), 2.0)
        value = math.exp(-0.5)
        self.assertEqual(self.gauss.run(2.0), 2.0*value)
        
    def test2D(self):
        self.gauss.setParam('scale', 2.0)
        self.gauss.setParam('center', 1.0)
        self.gauss.setParam('sigma', 1.0)
        self.assertEqual(self.gauss.runXY([1.0,1.0]), 2.0*2.0)
        value = math.exp(-0.5)
        self.assertEqual(self.gauss.runXY([1.0,2.0]), 2.0*2.0*value)
        self.assertEqual(self.gauss.runXY([2.0,2.0]), 2.0*2.0*value*value)
        
    def test2Dphi(self):
        self.gauss.setParam('scale', 2.0)
        self.gauss.setParam('center', 1.0)
        self.gauss.setParam('sigma', 1.0)
        value = math.exp(-0.5)
        self.assertEqual(self.gauss.run([math.sqrt(8.0), math.pi/4.0]), 2.0*2.0*value*value)
        
class TestLorentzian(unittest.TestCase):
    """Unit tests for Lorentzian function"""
    
    def setUp(self):
        from sans.models.Lorentzian import Lorentzian
        self.lor= Lorentzian()
        
    def test1D(self):
        self.lor.setParam('scale', 2.0)
        self.lor.setParam('center', 1.0)
        self.lor.setParam('gamma', 1.0)
        self.assertEqual(self.lor.run(1.0), 4.0/math.pi)
        value = 1/math.pi*0.5/(1+.25)
        self.assertEqual(self.lor.run(2.0), 2.0*value)
        
    def test2D(self):
        self.lor.setParam('scale', 0.5*math.pi)
        self.lor.setParam('center', 1.0)
        self.lor.setParam('gamma', 1.0)
        self.assertEqual(self.lor.run(1.0), 1.0)
        value = 0.25/(1+.25)
        self.assertEqual(self.lor.runXY([1.0,2.0]), value)
        self.assertEqual(self.lor.runXY([2.0,2.0]), value*value)
        
    def test2Dphi(self):
        self.lor.setParam('scale', 0.5*math.pi)
        self.lor.setParam('center', 1.0)
        self.lor.setParam('gamma', 1.0)
        self.assertEqual(self.lor.run(1.0), 1.0)
        value = 0.25/(1+.25)
        self.assertEqual(self.lor.run([math.sqrt(8.0), math.pi/4.0]), value*value)
        
class TestSin(unittest.TestCase):
    """Unit tests for Sin(x) function"""
    
    def setUp(self):
        from sans.models.Sin import Sin
        self.sin = Sin()

    def test1D(self):
        self.assertEqual(self.sin.run(1.13), math.sin(1.13))
        
    def test2D(self):
        self.assertEqual(self.sin.run([1.13,0.56]), math.sin(1.13*math.cos(0.56))*math.sin(1.13*math.sin(0.56)))
        self.assertEqual(self.sin.runXY([1.13,0.56]), math.sin(1.13)*math.sin(0.56))
        
class TestCos(unittest.TestCase):
    """Unit tests for Cos(x) function"""
    
    def setUp(self):
        from sans.models.Cos import Cos
        self.cos = Cos()

    def test1D(self):
        self.assertEqual(self.cos.run(1.13), math.cos(1.13))
        
    def test2D(self):
        self.assertEqual(self.cos.run([1.13,0.56]), math.cos(1.13*math.cos(0.56))*math.cos(1.13*math.sin(0.56)))
        self.assertEqual(self.cos.runXY([1.13,0.56]), math.cos(1.13)*math.cos(0.56))
        
class TestConstant(unittest.TestCase):
    """Unit tests for Cos(x) function"""
    
    def setUp(self):
        from sans.models.Constant import Constant
        self.const = Constant()
        self.const.setParam('value',56.1)

    def test1D(self):
        self.assertEqual(self.const.run(1.13), 56.1)
        
    def test2D(self):
        self.assertEqual(self.const.run([1.13,0.56]), 56.1)
        self.assertEqual(self.const.runXY([1.13,0.56]), 56.1)
        
    def testFunction(self):
        from sans.models.Sin import Sin
        s = Sin()
        A = self.const
        A.setParam('Value',1.5)
        B = self.const.clone()
        B.setParam('value',2.0)
        C = self.const.clone()
        C.setParam('value',3.0)
        
        f = A+B*s*s+C
        answer = 1.5+2.0*math.sin(1.1)**2+3.0
        self.assertEqual(f.run(1.1), answer)
    
        

if __name__ == '__main__':
    unittest.main()