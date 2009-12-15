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
        state = self.sphere.__getstate__()
        
        sphere_copy = SphereModel()
        sphere_copy.__setstate__(state)
        
        self.assertEqual(sphere_copy.getParam('radius'), 44)
        
        self.sphere.setParam('radius', 33.0)
        
        self.assertEqual(sphere_copy.getParam('radius'), 44)
        
    
if __name__ == '__main__':
    unittest.main()