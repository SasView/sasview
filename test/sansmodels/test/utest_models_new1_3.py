"""
    Unit tests for specific models II
"""

import unittest, time, math
     
class TestFuzzySphere(unittest.TestCase):
    """ Unit tests for fuzzysphere model """
    
    def setUp(self):
        from sans.models.FuzzySphereModel import FuzzySphereModel
        self.comp = FuzzySphereModel()
        
    def test1D(self):
        """ Test 1D model for a fuzzysphere """
        self.assertAlmostEqual(self.comp.run(1), 0.001, 3)
        
    def test1D_2(self):
        """ Test 2D model for a fuzzysphere """
        self.assertAlmostEqual(self.comp.run([1, 1.3]), 0.001, 3)
        
class TestPolyGaussCoil(unittest.TestCase):
    """ Unit tests for PolyGaussCoil """
    
    def setUp(self):
        from sans.models.Poly_GaussCoil import Poly_GaussCoil
        self.comp = Poly_GaussCoil()
        
    def test1D(self):
        """ Test 1D model for a PolyGaussCoil """
        self.assertAlmostEqual(self.comp.run(0.107000453), 0.0688476, 4)
        
    def test1D_2(self):
        """ Test 2D model for a PolyGaussCoil """
        self.assertAlmostEqual(self.comp.run([0.107000453, 0.2]), 0.0688476, 4)
                
class TestCoreFourShellModel(unittest.TestCase):
    """ Unit tests for CoreFourShellModel """
    
    def setUp(self):
        from sans.models.CoreFourShellModel import CoreFourShellModel
        self.comp = CoreFourShellModel()
        
    def test1D(self):
        """ Test 1D model for a CoreFourShellModel """
        print "sldsolv",self.comp.getParam("sld_solv")
        self.assertAlmostEqual(self.comp.run(0.001), 3318.19548, 4)
        
    def test1D_2(self):
        """ Test 2D model for a CoreFourShellModel """
        self.assertAlmostEqual(self.comp.run([0.001, 0.2]), 3318.19548, 4)

class TestFractal(unittest.TestCase):
    """ Unit tests for Fractal model """
    
    def setUp(self):
        from sans.models.FractalModel import FractalModel
        self.comp = FractalModel()
        
    def test1D(self):
        """ Test 1D model for a Fractal """
        self.assertAlmostEqual(self.comp.run(0.001), 39.288146, 4)
        
    def test1D_2(self):
        """ Test 2D model for a Fractal """
        self.assertAlmostEqual(self.comp.run([0.001, 1]), 39.288146, 4)
                                
class TestLamella(unittest.TestCase):
    """ Unit tests for Lamella model """
    
    def setUp(self):
        from sans.models.LamellarModel import LamellarModel
        self.comp = LamellarModel()
        
    def test1D(self):
        """ Test 1D model for a Lamellar """
        self.assertAlmostEqual(self.comp.run(1.0), 5.6387e-5, 4)
        
    def test1D_2(self):
        """ Test 2D model for a Lamellar """
        self.assertAlmostEqual(self.comp.run([1.0, 1.3]), 5.6387e-5, 4)
                
        

if __name__ == '__main__':
    unittest.main()