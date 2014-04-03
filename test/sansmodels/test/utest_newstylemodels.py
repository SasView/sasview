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

from sans.models.BaseModel import BaseModel, Parameter, ParameterProperty
class NewTestModel(BaseModel):
    scale = ParameterProperty('scale')
    
    def __init__(self):  
        BaseModel.__init__(self)  
        self.parameters = {}
        self.parameters['scale'] = Parameter('scale', 4.0) 
        
        
    def runXY(self, x):
        return self.scale*x
        
class TestBogusModel(unittest.TestCase):
    def setUp(self):
        self.model = NewTestModel()
        
    def test_call(self):
        self.assertEqual(self.model(1), 4.0)
        self.model.scale = 1.0
        self.assertEqual(self.model(1), 1.0)
        self.model.setParam('scale',2.0)
        self.assertEqual(self.model(1), 2.0)
        self.assertEqual(self.model.getParam('scale'), 2.0)
        
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
  
if __name__ == '__main__':
    unittest.main()
   