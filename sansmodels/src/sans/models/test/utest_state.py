#!/usr/bin/env python
""" 
    Test for setstate and reduce_ex operations for models
"""
import unittest

from sans.models.SphereModel import SphereModel

class TestSphere(unittest.TestCase):
    def setUp(self):
        self.sphere = SphereModel()
        
    def test_state_IO(self):
        """
            Check that a state oject is independent from the model object it
            was generated with
        """
        self.sphere.setParam('radius', 44.0)
        _, _, state, _, _ = self.sphere.__reduce_ex__(0)
        
        sphere_copy = SphereModel()
        sphere_copy.__setstate__(state)
        sphere_clone = sphere_copy.clone()
        self.assertEqual(sphere_copy.getParam('radius'), 44)
        
        self.sphere.setParam('radius', 33.0)
        
        self.assertEqual(sphere_clone.getParam('radius'), 44)
        
    
if __name__ == '__main__':
    unittest.main()