"""
    Unit tests for dispersion functionality of 
    C++ model classes
"""

import unittest, math, numpy

class TestCylinder(unittest.TestCase):
    """
        Testing C++ Cylinder model
    """
    def setUp(self):
        from sans.models.CylinderModel import CylinderModel
        self.model= CylinderModel()
        
        self.model.setParam('scale', 1.0)
        self.model.setParam('radius', 20.0)
        self.model.setParam('length', 400.0)
        self.model.setParam('sldCyl', 4.e-6)
        self.model.setParam('sldSolv', 1.e-6)
        self.model.setParam('background', 0.0)
        self.model.setParam('cyl_theta', 0.0)
        self.model.setParam('cyl_phi', 90.0)
        
    def test_simple(self):
        self.assertAlmostEqual(self.model.run(0.001), 450.355, 3)
        self.assertAlmostEqual(self.model.runXY([0.001,0.001]), 452.299, 3)
        
    def test_constant(self):
        from sans.models.dispersion_models import DispersionModel
        disp = DispersionModel()
        self.model.setParam('scale', 10.0)
        self.model.set_dispersion('radius', disp)
        self.model.dispersion['radius']['width'] = 5.0/20.0
        self.model.dispersion['radius']['npts'] = 100
        self.model.dispersion['radius']['nsigmas'] = 2.0
        print "constant",self.model.run(0.001), self.model.dispersion
        self.assertAlmostEqual(self.model.run(0.001), 1.021051*4527.47250339, 3)
        self.assertAlmostEqual(self.model.runXY([0.001, 0.001]), 1.021048*4546.997777604715, 2)
        
    def test_gaussian(self):
        from sans.models.dispersion_models import GaussianDispersion
        disp = GaussianDispersion()
        self.model.set_dispersion('radius', disp)
        self.model.dispersion['radius']['width'] = 5.0/20.0
        self.model.dispersion['radius']['npts'] = 100
        self.model.dispersion['radius']['nsigmas'] = 2.0
        self.model.setParam('scale', 10.0)
        
        self.assertAlmostEqual(self.model.run(0.001), 1.1804794*4723.32213339, 3)
        self.assertAlmostEqual(self.model.runXY([0.001,0.001]), 1.180454*4743.56, 2)
        
    def test_clone(self):
        from sans.models.dispersion_models import GaussianDispersion
        disp = GaussianDispersion()
        self.model.set_dispersion('radius', disp)
        self.model.dispersion['radius']['width'] = 5.0/20.0
        self.model.dispersion['radius']['npts'] = 100
        self.model.dispersion['radius']['nsigmas'] = 2.0
        self.model.setParam('scale', 10.0)
        
        new_model = self.model.clone()
        print "gaussian",self.model.run(0.001)
        self.assertAlmostEqual(new_model.run(0.001), 1.1804794*4723.32213339, 3)
        self.assertAlmostEqual(new_model.runXY([0.001,0.001]), 1.180454*4743.56, 2)
        
    def test_schulz_zero(self):
        from sans.models.dispersion_models import SchulzDispersion
        disp = SchulzDispersion()
        self.model.set_dispersion('radius', disp)
        self.model.dispersion['radius']['width'] = 5.0/20.0
        #self.model.dispersion['radius']['width'] = 0.0
        self.model.dispersion['radius']['npts'] = 100
        self.model.dispersion['radius']['nsigmas'] = 2.0
        self.model.setParam('scale', 1.0)
        #self.model.setParam('scale', 10.0)
        print "schulz",self.model.run(0.001), self.model.dispersion
        self.assertAlmostEqual(self.model.run(0.001), 542.23568, 3)
        self.assertAlmostEqual(self.model.runXY([0.001,0.001]), 544.54864, 3)
        
    def test_lognormal_zero(self):
        from sans.models.dispersion_models import LogNormalDispersion
        disp = LogNormalDispersion()
        self.model.set_dispersion('radius', disp)
        self.model.dispersion['radius']['width'] = 5.0/20.0
        #self.model.dispersion['radius']['width'] = 0.0
        self.model.dispersion['radius']['npts'] = 100
        self.model.dispersion['radius']['nsigmas'] = 2.0
        self.model.setParam('scale', 1.0)
        #self.model.setParam('scale', 10.0)
        print "model dispersion",self.model.dispersion
        print "lognormal",self.model.run(0.001)
        self.assertAlmostEqual(self.model.run(0.001), 554.41257, 3)
        self.assertAlmostEqual(self.model.runXY([0.001,0.001]), 556.77560, 3)
        
    def test_gaussian_zero(self):
        from sans.models.dispersion_models import GaussianDispersion
        disp = GaussianDispersion()
        self.model.set_dispersion('radius', disp)
        self.model.dispersion['radius']['width'] = 0.0
        self.model.dispersion['radius']['npts'] = 100
        self.model.dispersion['radius']['nsigmas'] = 2.0
        self.model.setParam('scale', 1.0)
        
        self.assertAlmostEqual(self.model.run(0.001), 450.355, 3)
        self.assertAlmostEqual(self.model.runXY([0.001,0.001]), 452.299, 3)
        
    def test_array(self):
        """
            Perform complete rotational average and
            compare to 1D
        """
        from sans.models.dispersion_models import ArrayDispersion
        disp_ph = ArrayDispersion()
        disp_th = ArrayDispersion()
        
        values_ph = numpy.zeros(100)
        values_th = numpy.zeros(100)
        weights   = numpy.zeros(100)
        for i in range(100):
            values_ph[i]=(360/99.0*i)
            values_th[i]=(180/99.0*i)
            weights[i]=(1.0)
        
        disp_ph.set_weights(values_ph, weights)
        disp_th.set_weights(values_th, weights)
        
        self.model.set_dispersion('cyl_theta', disp_th)
        self.model.set_dispersion('cyl_phi', disp_ph)
        
        val_1d = self.model.run(math.sqrt(0.0002))
        val_2d = self.model.runXY([0.01,0.01]) 
        
        self.assertTrue(math.fabs(val_1d-val_2d)/val_1d < 0.02)
        

if __name__ == '__main__':
    unittest.main()
   