"""
    Unit tests for dispersion functionality of 
    C++ model classes
"""
print "New style models are still under development"
import unittest, math, numpy

class TestModel(object):
    """
        An old-style model
    """
    def __init__(self):
        ## Parameter dictionary
        self.params = {}
        self.params['scale']       = 0.05
        
        ## Parameter details [units, min, max]
        self.details = {}
        self.details['scale']       = ['',     None, None]

    def run(self, x):
        return self.params['scale']*x

from sans.models.BaseModel import BaseModel,ParameterProperty
class NewTestModel(BaseModel):
    scale = ParameterProperty('scale')
    
    def __init__(self):  
        BaseModel.__init__(self)  
        self.parameters = {}
        self.parameters['scale'] = Parameter('scale', 4.0) 
        
    def run(self, x):
        return self.scale*x
        

class TestBaseModel(unittest.TestCase):
    """
        Testing C++ Cylinder model
    """
    def setUp(self):
        from sans.models.BaseModel import BaseModel
        self.model = BaseModel()
        
        
    def test_removed_attrs(self):
        def setop():
            print self.model.operateOn
        self.assertRaises(AttributeError, setop)
        def setother():
            print self.model.other
        self.assertRaises(AttributeError, setother)
        
class TestAdaptor(unittest.TestCase):
    """
        Testing C++ Cylinder model
    """
    def setUp(self):
        from sans.models.NewCylinderModel import CylinderModel
        self.model = CylinderModel()
        
        
    def test_setparam(self):
        self.model.setParam("length", 151.0)
        self.assertEquals(self.model.getParam("length"), 151.0)
        
        
        print self.model.parameters
        
        print self.model(0.001)
        self.model.setParam("length", 250.0)
        print self.model(0.001)
        
    
  
if __name__ == '__main__':
    unittest.main()
   