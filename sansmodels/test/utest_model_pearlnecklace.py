"""
    Unit tests for specific models II
"""

import unittest, time, math
     
class TestPerlNecklace(unittest.TestCase):
    """ Unit tests for PerlNecklace """
    
    def setUp(self):
        from sans.models.PearlNecklaceModel import PearlNecklaceModel
        self.pnl = PearlNecklaceModel()
        from sans.models.LinearPearlsModel import LinearPearlsModel
        self.lpm = LinearPearlsModel()
        from sans.models.SphereModel import SphereModel
        self.sphere = SphereModel()
        from sans.models.BarBellModel import BarBellModel
        self.bar = BarBellModel()
        
    def testwithsphere(self):
        """ Compare 1D model with sphere """
        self.pnl.setParam("radius", 60)
        self.pnl.setParam("num_pearls", 1)
        self.pnl.setParam("sld_pearl", 2e-06)
        self.pnl.setParam("sld_solv", 1e-06)
        self.assertAlmostEqual(self.pnl.run(0.001), self.sphere.run(0.001), 5)
        self.assertAlmostEqual(self.pnl.run(0.005), self.sphere.run(0.005), 5)
        self.assertAlmostEqual(self.pnl.run(0.01), self.sphere.run(0.01), 5)
        self.assertAlmostEqual(self.pnl.run(0.05), self.sphere.run(0.05), 5)
        self.assertAlmostEqual(self.pnl.run(0.1), self.sphere.run(0.1), 5)
        self.assertAlmostEqual(self.pnl.run(0.5), self.sphere.run(0.5), 5)
        
    def testwithbarbell(self):
        """ 
        Compare 1D model with barbell
        
        Note:  pearlnecklace assumes infinite thin rod
        """
        self.pnl.setParam("radius", 20)
        self.pnl.setParam("num_pearls", 2)
        self.pnl.setParam("sld_pearl", 1e-06)
        self.pnl.setParam("sld_string", 1e-06)
        self.pnl.setParam("sld_solv", 6.3e-06)
        self.pnl.setParam("thick_string", 0.1)
        self.pnl.setParam("edge_separation", 400)
        self.bar.setParam("rad_bar", 0.1)
        self.bar.setParam("rad_bell", 20)
        self.lpm.setParam("radius", 20)
        self.lpm.setParam("num_pearls", 2)
        self.lpm.setParam("sld_pearl", 1e-06)
        self.lpm.setParam("sld_solv", 6.3e-06)
        self.lpm.setParam("edge_separation", 400)
                
        self.assertAlmostEqual(self.pnl.run(0.001), self.bar.run(0.001), 1)
        self.assertAlmostEqual(self.pnl.run(0.005), self.bar.run(0.005), 1)
        self.assertAlmostEqual(self.pnl.run(0.01), self.bar.run(0.01), 1)
        self.assertAlmostEqual(self.pnl.run(0.05), self.bar.run(0.05), 1)
        self.assertAlmostEqual(self.pnl.run(0.1), self.bar.run(0.1), 1)
        self.assertAlmostEqual(self.pnl.run(0.5), self.bar.run(0.5), 1)
        
        self.assertAlmostEqual(self.pnl.run(0.001), self.lpm.run(0.001), 1)
        self.assertAlmostEqual(self.pnl.run(0.005), self.lpm.run(0.005), 1)
        self.assertAlmostEqual(self.pnl.run(0.01), self.lpm.run(0.01), 1)
        self.assertAlmostEqual(self.pnl.run(0.05), self.lpm.run(0.05), 1)
        self.assertAlmostEqual(self.pnl.run(0.1), self.lpm.run(0.1), 1)
        self.assertAlmostEqual(self.pnl.run(0.5), self.lpm.run(0.5), 1)
        

if __name__ == '__main__':
    unittest.main()