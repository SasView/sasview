"""
    Unit tests for extra models
"""
import unittest
class TestPolymerExclVolume(unittest.TestCase):
    """
        Unit tests for PolymerexclVolume (non-shape) function
    """
    def setUp(self):
        from sans.models.PolymerExclVolume import PolymerExclVolume
        self.model= PolymerExclVolume()
        
    def test1D(self):          
        # the values are from Igor pro calculation    
        self.assertAlmostEqual(self.model.run(0.001), 0.998801, 6)
        self.assertAlmostEqual(self.model.run(0.21571), 0.00192041, 6)
        self.assertAlmostEqual(self.model.runXY(0.41959), 0.000261302, 6)
        
        
if __name__ == '__main__':
    unittest.main()