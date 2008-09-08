"""
    Unit tests for specific models
    @author: Mathieu Doucet / UTK
"""

import unittest
from pyre.applications.Script import Script
from sans.models.ModelFactory import ModelFactory

# Disable "missing docstring" complaint
# pylint: disable-msg=C0111
# Disable "too many methods" complaint 
# pylint: disable-msg=R0904 
# Disable "could be a function" complaint 
# pylint: disable-msg=R0201

class TestScript(Script):
    
    def main(self, *args, **kwds):
        pass

    def newModel(self, model_name):
        """
            Instantiate a new model
            @param model_name: name of new model [string]
        """
        import pyre.inventory
        
        fac = pyre.inventory.facility('model', default = model_name)
        new_model, locator = fac._getDefaultValue(self.inventory)
        new_model._configure()
        new_model._init()
        
        return new_model

class TestPyreComponent(unittest.TestCase):
    """ Unit tests for sphere model """
    
    def setUp(self):
        self.pyre_script = TestScript('test')
        self.pyre_script.run()

    def testSphere(self):
        sphere = self.pyre_script.newModel('sphere')
        oracle = ModelFactory().getModel("SphereModel")
        self.assertEqual(sphere(1.0), oracle.run(1.0))

    def testCylinder(self):
        sphere = self.pyre_script.newModel('cylinder')
        oracle = ModelFactory().getModel("CylinderModel")
        self.assertEqual(sphere(1.0), oracle.run(1.0))

    def test2DSphere(self):
        sphere = self.pyre_script.newModel('sphere')
        oracle = ModelFactory().getModel("SphereModel")
        self.assertEqual(sphere([1.0, 1.57]), oracle.run(1.0))

    def testSetParam(self):
        sphere = self.pyre_script.newModel('sphere')
        sphere.set('radius', 10.0)
        oracle = ModelFactory().getModel("SphereModel")
        oracle.setParam('radius', 10.0)
        self.assertEqual(sphere(1.0), oracle.run(1.0))

 

if __name__ == '__main__':
    unittest.main()