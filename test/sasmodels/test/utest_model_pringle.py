"""
    Unit tests for specific model
"""

import unittest, time, math
     
class TestPringle(unittest.TestCase):
    
    def setUp(self):
        from sas.models.PringlesModel import PringlesModel
        self.pm = PringlesModel()
        
    def test1D(self):
        '''Test 1D model of a pringle particle'''
        self.assertAlmostEqual(self.pm.run(0.1), 10.0729, 4)
        
if __name__ == '__main__':
    unittest.main()
