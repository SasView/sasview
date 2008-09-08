"""
    Unit tests for BaseComponent 
    @author: Mathieu Doucet / UTK
"""
# Disable "missing docstring" complaint
# pylint: disable-msg=C0111
# Disable "too many methods" complaint 
# pylint: disable-msg=R0904 


import unittest, math
from sans.models.BaseComponent import BaseComponent

class ConstantComponent(BaseComponent):
    """ Test component """
    def __init__(self, value=0):
        BaseComponent.__init__(self)
        self.params['value'] = value
        self.dim = 0
        self.name = 'constant'
    def run(self, x=0):
        """ Evaluate method """
        return self.params['value']
        
class IdentityComponent(BaseComponent):
    """ Test identity component """
    def __init__(self):
        BaseComponent.__init__(self)
        self.dim = 1
        self.name = 'id'
    def run(self, x=0):
        """ Evaluate method """
        return x
        
class SinComponent(BaseComponent):
    """ Test sin(x) component """
    def __init__(self):
        BaseComponent.__init__(self)
        self.params['norm'] = 1
        self.dim = 1
        self.name = 'sin'
    def run(self, x=0):
        """ Evaluate method """
        return self.params['norm']*math.sin(x)
        
class TwoDimComponent(BaseComponent):
    """ Test 2D component """
    def __init__(self):
        BaseComponent.__init__(self)
        self.params['norm'] = 1
        self.dim = 2
        self.name = '2D'
    def run(self, x):
        """ Evaluate method """
        return self.params['norm']*x[0]*math.sin(x[1])
        
class ThreeDimComponent(BaseComponent):
    """ Test 3D component """
    def __init__(self):
        BaseComponent.__init__(self)
        self.params['norm'] = 1
        self.dim = 3
        self.name = '3D'
    def run(self, x):
        """ Evaluate method """
        return self.params['norm']*x[0]*math.sin(x[1])*x[2]*x[2]
        


class TestBasicComponent(unittest.TestCase):
    
    def setUp(self):
        self.comp = BaseComponent()

    def testrun(self):
        input = 45
        self.assertEqual(self.comp.run(input), 0)
        
class TestArithmetic(unittest.TestCase):
    def setUp(self):
        self.value1 = 5
        self.comp1 = ConstantComponent(self.value1)
        
        self.value2 = 7
        self.comp2 = ConstantComponent(self.value2)
        
    def testrun(self):
        self.assertEqual(self.comp1.run(45), self.value1)
        
    def testadd(self):
        newcomp = self.comp1+self.comp2
        self.assertEqual(newcomp.run(45), self.value1+self.value2)
        
    def testmultiply(self):
        newcomp = self.comp1*self.comp2
        self.assertEqual(newcomp.run(45), self.value1*self.value2)
        
    def testsubtract(self):
        newcomp = self.comp1-self.comp2
        self.assertEqual(newcomp.run(45), self.value1-self.value2)
        
    def testdivide(self):
        newcomp = self.comp1/self.comp2
        self.assertEqual(newcomp.run(45), self.value1/self.value2)
        print newcomp
        
    def vtestcomplic1(self):
        val = (self.value1+self.value2)/self.value2
        newcomp = (self.comp1+self.comp2)
        newcomp2 = newcomp/self.comp2
        self.assertEqual(newcomp2.run(45), val)

    def testcomplic2(self):
        # A + B 
        newcomp = self.comp1+self.comp2
        # Value of A
        self.assertEqual(newcomp.operateOn.params['value'], self.value1)
        # Value of B
        self.assertEqual(newcomp.other.params['value'], self.value2)
        # Value of D = A+B
        self.assertEqual(newcomp.run(), self.value1+self.value2)
        # D + C
        newcomp2 = newcomp+self.comp2
        # Value of D
        self.assertEqual(newcomp2.operateOn.run(), self.value1+self.value2)
        # Value of B
        self.assertEqual(newcomp2.other.params['value'], self.value2)
        
        
        self.assertEqual(newcomp2.run(45), self.value1+self.value2+self.value2)

    def testcomplic3(self):
        # Same as testcomplic2, but all in one go
        newcomp = self.comp1+self.comp2+self.comp2
        self.assertEqual(newcomp.run(45), self.value1+self.value2+self.value2)
        
    def testcomplic4(self):
        output = (self.value1+self.value1)/(self.value1+self.value2)
        newcomp = (self.comp1+self.comp1)/(self.comp1+self.comp2)
        self.assertEqual(newcomp.run(45), output)
                
class TestIO(unittest.TestCase):
    def setUp(self):
        from sans.models.ModelFactory import ModelFactory
        from sans.models.ModelIO import ModelIO
        self.factory = ModelFactory()
        self.io = ModelIO(self.factory)
        self.sph = self.factory.getModel("SphereModel")
        self.cyl = self.factory.getModel("CylinderModel")
        
        
    def saveLoadAndCompare(self, combo):
        # Save
        self.io.save(combo,"test_io.xml")
        # Load
        loaded = self.io.load("test_io.xml")
        
        # Check that the model is the same
        # ONLY WORKS FOR DEFAULT PARAMETERS
        # print combo.run(1)
        self.assertEqual(combo.run(1), loaded.run(1))
        return loaded
        
    def testSimple(self):
        self.saveLoadAndCompare(self.sph)
        
    def testAdd(self):
        combo = self.sph+self.cyl
        self.saveLoadAndCompare(combo)

    def testSub(self):
        combo = self.sph-self.cyl
        self.saveLoadAndCompare(combo)

    def testMul(self):
        combo = self.sph*self.cyl
        self.saveLoadAndCompare(combo)

    def testDiv(self):
        combo = self.sph/self.cyl
        self.saveLoadAndCompare(combo)
        
    def testDegree2(self):
        combo = (self.sph+self.sph)/self.cyl
        self.saveLoadAndCompare(combo)
        
    def testDegree3(self):
        combo = self.sph*(self.cyl+self.sph/self.cyl)
        self.saveLoadAndCompare(combo)

    def testReSave(self):
        combo = self.sph+self.cyl
        loaded = self.saveLoadAndCompare(combo)
        self.saveLoadAndCompare(loaded)

class TestGetSet(unittest.TestCase):
    def setUp(self):
        from sans.models.ModelFactory import ModelFactory
        self.factory = ModelFactory()
        self.sph = self.factory.getModel("SphereModel")
        
    def testGet(self):
        # The default value is 1.0e-6
        self.assertEqual(self.sph.getParam("scale"), 1.0e-6)
        
    def testGetCaseSensitivity(self):
        # The default value is 1.0e-6
        self.assertEqual(self.sph.getParam("sCale"), 1.0e-6)
        
    def testGetException(self):
        self.assertRaises(ValueError, self.sph.getParam, "scalee")
        
    def testSet(self):
        value_0 = self.sph.run(1)
        scale = 2.0e-6
        self.sph.setParam("scale", scale)
        self.assertEqual(self.sph.getParam("scale"), scale)
        self.assertEqual(self.sph.run(1), 2*value_0)
        
    def testSetCaseSensitivity(self):
        value_0 = self.sph.run(1)
        scale = 2.0e-6
        self.sph.setParam("sCale", scale)
        self.assertEqual(self.sph.getParam("scale"), scale)
        self.assertEqual(self.sph.run(1), 2*value_0)
        
    def testSetException(self):
        self.assertRaises(ValueError, self.sph.setParam, "scalee", 2.0)
        
    def testCompositeAdd(self):
        sph2 = self.factory.getModel("SphereModel")
        sph2.setParam("scale", 2.0e-6)
        model = sph2+self.sph  
        self.assertEqual(model.getParam('Base.scale'), 2.0e-6)
        self.assertEqual(model.getParam('add.scale'), 1.0e-6)
        
    def testCompositeSub(self):
        sph2 = self.factory.getModel("SphereModel")
        sph2.setParam("scale", 2.0e-6)
        model = sph2-self.sph  
        self.assertEqual(model.getParam('Base.scale'), 2.0e-6)
        self.assertEqual(model.getParam('sub.scale'), 1.0e-6)
        
    def testCompositeMul(self):
        sph2 = self.factory.getModel("SphereModel")
        sph2.setParam("scale", 2.0e-6)
        model = sph2*self.sph  
        self.assertEqual(model.getParam('Base.scale'), 2.0e-6)
        self.assertEqual(model.getParam('mul.scale'), 1.0e-6)
        
    def testCompositeDiv(self):
        sph2 = self.factory.getModel("SphereModel")
        sph2.setParam("scale", 2.0e-6)
        model = sph2/self.sph  
        self.assertEqual(model.getParam('Base.scale'), 2.0e-6)
        self.assertEqual(model.getParam('div.scale'), 1.0e-6)
        
    def testSetCompositeAdd(self):
        sph2 = self.factory.getModel("SphereModel")
        #sph2.setParam("scale", 2.0e-6)
        model = sph2+self.sph  
        value = model.run(1)
        scale = 2.0e-6
        model.setParam("base.scale", scale)
        model.setParam("add.scale", scale)
       
        self.assertEqual(model.getParam("base.scale"), scale)
        self.assertEqual(model.getParam("add.scale"), scale)
        self.assertEqual(model.run(1), 2*value)
        
    def testSetCompositeSub(self):
        sph2 = self.factory.getModel("SphereModel")
        #sph2.setParam("scale", 2.0e-6)
        model = sph2-self.sph  
        value = model.run(1)
        scale = 2.0e-6
        model.setParam("base.scale", scale)
        model.setParam("sub.scale", scale)
       
        self.assertEqual(model.getParam("base.scale"), scale)
        self.assertEqual(model.getParam("sub.scale"), scale)
        self.assertEqual(model.run(1), 2*value)
        
    def testSetCompositeMul(self):
        sph2 = self.factory.getModel("SphereModel")
        #sph2.setParam("scale", 2.0e-6)
        model = sph2*self.sph  
        value = model.run(1)
        scale = 2.0e-6
        model.setParam("mul.scale", scale)
       
        self.assertEqual(model.getParam("mul.scale"), scale)
        self.assertEqual(model.run(1), 2*value)
        
    def testSetCompositeDiv(self):
        sph2 = self.factory.getModel("SphereModel")
        #sph2.setParam("scale", 2.0e-6)
        model = sph2/self.sph  
        value = model.run(1)
        scale = 2.0e-6
        model.setParam("div.scale", scale)
       
        self.assertEqual(model.getParam("div.scale"), scale)
        self.assertEqual(model.run(1), 0.5*value)
        
    def testParamList(self):
        sph2 = self.factory.getModel("SphereModel")
        model = sph2/self.sph  
        p_list = model.getParamList()
        #print p_list
        check_list = ['base.scale', 'base.radius', 'base.background', 
                      'base.contrast', 
                      'div.scale', 'div.radius', 'div.contrast', 
                      'div.background']
        self.assertEqual(check_list, p_list)
         
if __name__ == '__main__':
    unittest.main()