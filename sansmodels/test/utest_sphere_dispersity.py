"""
    Unit tests for Gauss and Shulz dispersion functionality of 
    C++ model classes
"""

import unittest, math, numpy
from sans.dataloader.loader import  Loader

        
class TestSphereGauss(unittest.TestCase):
    """
        Testing C++  Polydispersion w/ sphere comparing to IGOR/NIST computation
    """
    def setUp(self):
        loader = Loader()
        ## IGOR/NIST computation
        self.output_gauss=loader.load('Gausssphere.txt')
        self.output_shulz=loader.load('Schulzsphere.txt')

        from sans.models.SphereModel import SphereModel
        self.model= SphereModel()

        self.model.setParam('scale', 0.01)
        self.model.setParam('radius', 60.0)
        self.model.setParam('sldSph', 1.e-6)
        self.model.setParam('sldSolv', 3.e-6)
        self.model.setParam('background', 0.001)

    def test_gauss(self):
        from sans.models.dispersion_models import GaussianDispersion
        disp_g = GaussianDispersion()
        self.model.set_dispersion('radius', disp_g)
        self.model.dispersion['radius']['width'] = 0.2
        self.model.dispersion['radius']['npts'] = 100
        self.model.dispersion['radius']['nsigmas'] = 10
        for ind in range(len(self.output_gauss.x)):
            self.assertAlmostEqual(self.model.run(self.output_gauss.x[ind]), 
                                   self.output_gauss.y[ind], 2)
        
    def test_shulz(self):
        from sans.models.dispersion_models import SchulzDispersion
        disp_s = SchulzDispersion()
        self.model.set_dispersion('radius', disp_s)
        self.model.dispersion['radius']['width'] = 0.2
        self.model.dispersion['radius']['npts'] = 100
        self.model.dispersion['radius']['nsigmas'] = 10
        for ind in range(len(self.output_shulz.x)):
            self.assertAlmostEqual(self.model.run(self.output_gauss.x[ind]), 
                                   self.output_shulz.y[ind], 3)        

if __name__ == '__main__':
    unittest.main()
   