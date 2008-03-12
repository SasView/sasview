"""
    Unit tests for non shape based model (Task 8.2.1)
    These tests are part of the requirements
"""

import unittest, time, math

# Disable "missing docstring" complaint
# pylint: disable-msg=C0111
# Disable "too many methods" complaint 
# pylint: disable-msg=R0904 
# Disable "could be a function" complaint 
# pylint: disable-msg=R0201

 
class TestGuinier(unittest.TestCase):
    """
        Unit tests for Guinier function
        
        F(x) = exp[ [A] + [B]*Q**2 ]
        
        The model has two parameters: A and B
    """
    def _func(self, a, b, x):
        return math.exp(a+b*x**2)
    
    def setUp(self):
        from GuinierModel import GuinierModel
        self.model= GuinierModel()
        
    def test1D(self):
        self.model.setParam('A', 2.0)
        self.model.setParam('B', 1.0)
        
        self.assertEqual(self.model.run(0.0), math.exp(2.0))
        self.assertEqual(self.model.run(2.0), math.exp(2.0+1.0*(2.0)**2))
        
    def test2D(self):
        self.model.setParam('A', 2.0)
        self.model.setParam('B', 1.0)
        
        value = self._func(2.0, 1.0, 1.0)*self._func(2.0, 1.0, 2.0)
        self.assertEqual(self.model.runXY([0.0,0.0]), math.exp(2.0)*math.exp(2.0))
        self.assertEqual(self.model.runXY([1.0,2.0]), value)
        
    def test2Dphi(self):
        self.model.setParam('A', 2.0)
        self.model.setParam('B', 1.0)
        
        x = 1.0
        y = 2.0
        r = math.sqrt(x**2 + y**2)
        phi = math.atan2(y, x)
        
        value = self._func(2.0, 1.0, x)*self._func(2.0, 1.0, y)
        
        #self.assertEqual(self.model.run([r, phi]), value)
        self.assertAlmostEquals(self.model.run([r, phi]), value,1)
class TestPorod(unittest.TestCase):
    """
        Unit tests for Porod function
        
        F(x) = exp[ [C]/Q**4 ]
        
        The model has one parameter: C
    """
    def _func(self, c, x):
        return math.exp(c/(x*x*x*x))
    
    def setUp(self):
        from PorodModel import PorodModel
        self.model= PorodModel()
        self.model.setParam('c', 2.0)        
        
    def test1D(self):
        value = self._func(2.0, 3.0)
        self.assertEqual(self.model.run(3.0), value)
        
    def test2D(self):
        value = self._func(2.0, 1.0)*self._func(2.0, 2.0)
        self.assertEqual(self.model.runXY([1.0,2.0]), value)
        
    def test2Dphi(self):
        x = 1.0
        y = 2.0
        r = math.sqrt(x**2 + y**2)
        phi = math.atan2(y, x)
        
        value = self._func(2.0, 1.0)*self._func(2.0, 2.0)
        
        #self.assertEqual(self.model.run([r, phi]), value)
        self.assertAlmostEquals(self.model.run([r, phi]), value,1)
        
if __name__ == '__main__':
    unittest.main()