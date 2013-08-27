"""
    Unit tests for specific models
    @author: Mathieu Doucet / UTK
"""

import unittest
from SmearList import Smear

# Disable "missing docstring" complaint
# pylint: disable-msg=C0111
# Disable "too many methods" complaint 
# pylint: disable-msg=R0904 
# Disable "could be a function" complaint 
# pylint: disable-msg=R0201

from sans.models.sans_extension.c_models import Disperser
from sans.models.CylinderModel import CylinderModel
from sans.models.DisperseModel import DisperseModel
      
class TestDisperser(unittest.TestCase):
    """ Unit tests for sphere model """
    
    def setUp(self):
        self.model = CylinderModel()
        self.model.setParam("cyl_theta", 1.57)
        self.model.setParam("cyl_phi", 0.1)
        
        

    def testNoDisp(self):
        """ Test 1D model for a sphere """
        q = 0.005
        d = Disperser(self.model, [], [])
        value = d.run([q, 0])
        self.assertEqual(value, self.model.run([q, 0]))

    def testComp(self):
        q = 0.005
        phi = 0.10
        sigma = 0.3
        value_0 = self.model.run([q, phi])
        app = Smear(self.model, ['cyl_phi'], [sigma])
        val_py = app.run([q, phi])
        
        # Check that the parameters were returned to original values
        self.assertEqual(value_0, self.model.run([q, phi]))
        d = Disperser(self.model, ["cyl_phi"], [sigma])
        val_c = d.run([q, phi])
        self.assertEqual(val_py, val_c)
        
    def test2Disp(self):
        q = 0.005
        phi = 0.10
        sigma = 0.3
        value_0 = self.model.run([q, phi])
        app = Smear(self.model, ['cyl_phi', 'cyl_theta'], [sigma, sigma])
        val_py = app.run([q, phi])
        
        # Check that the parameters were returned to original values
        self.assertEqual(value_0, self.model.run([q, phi]))
        d = Disperser(self.model, ["cyl_phi", "cyl_theta"], [sigma, sigma])
        val_c = d.run([q, phi])
        self.assertEqual(val_py, val_c)
        
    def test3Disp(self):
        q = 0.005
        phi = 0.10
        sigma = 0.3
        value_0 = self.model.run([q, phi])
        app = Smear(self.model, 
                    ['cyl_phi', 'cyl_theta', 'radius'], [sigma, sigma, 1.0])
        val_py = app.run([q, phi])
        
        # Check that the parameters were returned to original values
        self.assertEqual(value_0, self.model.run([q, phi]))
        d = Disperser(self.model, 
                      ["cyl_phi", "cyl_theta", 'radius'], [sigma, sigma, 1.0])
        val_c = d.run([q, phi])
        self.assertEqual(val_py, val_c)
        
        
class TestDisperserModel(unittest.TestCase):
    """ Unit tests for sphere model """
    
    def setUp(self):
        self.model = CylinderModel()
        self.model.setParam("cyl_theta", 1.57)
        self.model.setParam("cyl_phi", 0.1)
        
    def test2Disp(self):
        q = 0.005
        phi = 0.10
        sigma = 0.3
        value_0 = self.model.run([q, phi])
        app = Smear(self.model, ['cyl_phi', 'cyl_theta'], [sigma, sigma])
        val_py = app.run([q, phi])
        
        # Check that the parameters were returned to original values
        self.assertEqual(value_0, self.model.run([q, phi]))
        d = DisperseModel(self.model, ["cyl_phi", "cyl_theta"], [sigma, sigma])
        val_c = d.run([q, phi])
        self.assertEqual(val_py, val_c)


if __name__ == '__main__':
    unittest.main()