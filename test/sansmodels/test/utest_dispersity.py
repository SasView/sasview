"""
    Unit tests for dispersion functionality of 
    C++ model classes
"""

#Note: The 'sans.models.DisperseModel' is for only the test. We use 
#'sans.models.dispersion_models', instead in the application.
#The first uses width = sigma, while the second uses width = ratio (=sigma/mean)
#for length parameters and width = sigma for angle parameters.
#In Feb. 2011, we found and fixed the some precision problems in the C, so that
#this test was updated too.


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
        self.model.dispersion['radius']['width'] = 0.25
        self.model.dispersion['radius']['npts'] = 100
        self.model.dispersion['radius']['nsigmas'] = 2.5
        
        self.assertAlmostEqual(self.model.run(0.001), 1.021051*4527.47250339, 3)
        self.assertAlmostEqual(self.model.runXY([0.001, 0.001]), 
                               1.021048*4546.997777604715, 2)
        
    def test_gaussian(self):
        from sans.models.dispersion_models import GaussianDispersion
        disp = GaussianDispersion()
        self.model.set_dispersion('radius', disp)
        self.model.dispersion['radius']['width'] = 0.25
        self.model.dispersion['radius']['npts'] = 100
        self.model.dispersion['radius']['nsigmas'] = 2
        self.model.setParam('scale', 10.0)
        
        self.assertAlmostEqual(self.model.run(0.001), 
                               1.1804794*4723.32213339, 3)
        self.assertAlmostEqual(self.model.runXY([0.001,0.001]), 
                               1.180454*4743.56, 2)
        
    def test_clone(self):
        from sans.models.dispersion_models import GaussianDispersion
        disp = GaussianDispersion()
        self.model.set_dispersion('radius', disp)
        self.model.dispersion['radius']['width'] = 0.25
        self.model.dispersion['radius']['npts'] = 100
        self.model.dispersion['radius']['nsigmas'] = 2
        self.model.setParam('scale', 10.0)
        
        new_model = self.model.clone()
        self.assertAlmostEqual(new_model.run(0.001), 
                               1.1804794*4723.32213339, 3)
        self.assertAlmostEqual(new_model.runXY([0.001,0.001]), 
                               1.180454*4743.56, 2)
        
    def test_gaussian_zero(self):
        from sans.models.dispersion_models import GaussianDispersion
        disp = GaussianDispersion()
        self.model.set_dispersion('radius', disp)
        self.model.dispersion['radius']['width'] = 0.0
        self.model.dispersion['radius']['npts'] = 100
        self.model.dispersion['radius']['nsigmas'] = 2.5
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
        
class TestCoreShellCylinder(unittest.TestCase):
    """
        Testing C++ Cylinder model
    """
    def setUp(self):
        from sans.models.CoreShellCylinderModel import CoreShellCylinderModel
        self.model= CoreShellCylinderModel()
        
        self.model.setParam('scale', 1.0)
        self.model.setParam('radius', 20.0)
        self.model.setParam('thickness', 10.0)
        self.model.setParam('length', 400.0)
        self.model.setParam('core_sld', 1.e-6)
        self.model.setParam('shell_sld', 4.e-6)
        self.model.setParam('solvent_sld', 1.e-6)
        self.model.setParam('background', 0.0)
        self.model.setParam('axis_theta', 0.0)
        self.model.setParam('axis_phi', 90.0)
        
    def test_simple(self):
        """
            Test simple 1D and 2D values
            Numbers taken from model that passed validation, before
            the update to C++ underlying class.
        """
        self.assertAlmostEqual(self.model.run(0.001), 353.55013216754583, 3)
        self.assertAlmostEqual(self.model.runXY([0.001,0.001]), 
                               355.25355270620543, 3)
        
    def test_dispersion(self):
        """
            Test with dispersion
        """
        from sans.models.DisperseModel import DisperseModel
        disp = DisperseModel(self.model, ['radius', 
                                          'thickness', 
                                          'length'], [5, 2, 50])
        disp.setParam('n_pts', 10)
        self.assertAlmostEqual(disp.run(0.001), 358.44062724936009, 3)
        self.assertAlmostEqual(disp.runXY([0.001,0.001]), 360.22673635224584, 3)

    def test_new_disp(self):
        from sans.models.dispersion_models import GaussianDispersion
        disp_rm = GaussianDispersion()
        self.model.set_dispersion('radius', disp_rm)
        self.model.dispersion['radius']['width'] = 0.25
        self.model.dispersion['radius']['npts'] = 10
        self.model.dispersion['radius']['nsigmas'] = 2

        disp_rr = GaussianDispersion()
        self.model.set_dispersion('thickness', disp_rr)
        self.model.dispersion['thickness']['width'] = 0.2
        self.model.dispersion['thickness']['npts'] = 10
        self.model.dispersion['thickness']['nsigmas'] = 2

        disp_len = GaussianDispersion()
        self.model.set_dispersion('length', disp_len)
        self.model.dispersion['length']['width'] = 1.0/8.0
        self.model.dispersion['length']['npts'] = 10
        self.model.dispersion['length']['nsigmas'] = 2

        self.assertAlmostEqual(self.model.run(0.001), 
                               1.07832610*358.44062724936009, 3)
        self.assertAlmostEqual(self.model.runXY([0.001,0.001]), 
                               1.07844010*360.22673635224584, 3)
        

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
        
        self.model.set_dispersion('axis_theta', disp_th)
        self.model.set_dispersion('axis_phi', disp_ph)
        
        val_1d = self.model.run(math.sqrt(0.0002))
        val_2d = self.model.runXY([0.01,0.01]) 
        
        self.assertTrue(math.fabs(val_1d-val_2d)/val_1d < 0.02)
        
        
        
class TestCoreShell(unittest.TestCase):
    """
        Testing C++ Cylinder model
    """
    def setUp(self):
        from sans.models.CoreShellModel import CoreShellModel
        self.model= CoreShellModel()
        
        self.model.setParam('scale', 1.0)
        self.model.setParam('radius', 60.0)
        self.model.setParam('thickness', 10.0)
        self.model.setParam('core_sld', 1.e-6)
        self.model.setParam('shell_sld', 2.e-6)
        self.model.setParam('solvent_sld', 3.e-6)
        self.model.setParam('background', 0.0)
        
    def test_simple(self):
        """
            Test simple 1D and 2D values
            Numbers taken from model that passed validation, before
            the update to C++ underlying class.
        """
        self.assertAlmostEqual(self.model.run(0.001), 
                               381.27304697150055, 3)
        self.assertAlmostEqual(self.model.runXY([0.001,0.001]), 
                               380.93779156218682, 3)
        
    def test_dispersion(self):
        """
            Test with dispersion
        """
        from sans.models.DisperseModel import DisperseModel
        disp = DisperseModel(self.model, ['radius', 'thickness'], [10, 2])
        disp.setParam('n_pts', 10)
        self.assertAlmostEqual(disp.run(0.001), 407.344127907553, 3)
    
    def test_new_disp(self):
        from sans.models.dispersion_models import GaussianDispersion
        disp_rm = GaussianDispersion()
        self.model.set_dispersion('radius', disp_rm)
        self.model.dispersion['radius']['width'] = 0.1666666667
        self.model.dispersion['radius']['npts'] = 10
        self.model.dispersion['radius']['nsigmas'] = 2

        disp_rr = GaussianDispersion()
        self.model.set_dispersion('thickness', disp_rr)
        self.model.dispersion['thickness']['width'] = 0.2
        self.model.dispersion['thickness']['npts'] = 10
        self.model.dispersion['thickness']['nsigmas'] = 2

        self.assertAlmostEqual(self.model.run(0.001), 
                               1.16747510*407.344127907553, 3)

        
class TestEllipsoid(unittest.TestCase):
    """
        Testing C++ Cylinder model
    """
    def setUp(self):
        from sans.models.EllipsoidModel import EllipsoidModel
        self.model= EllipsoidModel()
        
        self.model.setParam('scale', 1.0)
        self.model.setParam('radius_a', 20.0)
        self.model.setParam('radius_b', 400.0)
        self.model.setParam('sldEll', 4.e-6)
        self.model.setParam('sldSolv', 1.e-6)
        self.model.setParam('background', 0.0)
        self.model.setParam('axis_theta', 0.0)
        self.model.setParam('axis_phi', 0.0)
        
    def test_simple(self):
        """
            Test simple 1D and 2D values
            Numbers taken from model that passed validation, before
            the update to C++ underlying class.
        """
        self.assertAlmostEqual(self.model.run(0.001), 
                               11808.842896863147, 3)
        self.assertAlmostEqual(self.model.runXY([0.001,0.001]), 
                               11681.990374929677, 3)

    def test_dispersion(self):
        """
            Test with dispersion
        """
        from sans.models.DisperseModel import DisperseModel
        disp = DisperseModel(self.model, ['radius_a', 'radius_b'], [5, 50])
        disp.setParam('n_pts', 10)

        self.assertAlmostEqual(disp.run(0.001), 11948.72581312305, 3)
        self.assertAlmostEqual(disp.runXY([0.001,0.001]), 11811.972359807551, 3)
        
    def test_new_disp(self):
        from sans.models.dispersion_models import GaussianDispersion
        disp_rm = GaussianDispersion()
        self.model.set_dispersion('radius_a', disp_rm)
        self.model.dispersion['radius_a']['width'] = 0.25
        self.model.dispersion['radius_a']['npts'] = 10
        self.model.dispersion['radius_a']['nsigmas'] = 2

        disp_rr = GaussianDispersion()
        self.model.set_dispersion('radius_b', disp_rr)
        self.model.dispersion['radius_b']['width'] = 0.125
        self.model.dispersion['radius_b']['npts'] = 10
        self.model.dispersion['radius_b']['nsigmas'] = 2

        self.assertAlmostEqual(self.model.run(0.001), 
                               1.10650710*11948.72581312305, 3)
        self.assertAlmostEqual(self.model.runXY([0.001,0.001]), 
                               1.105898*11811.972359807551, 2)

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
        
        self.model.set_dispersion('axis_theta', disp_th)
        self.model.set_dispersion('axis_phi', disp_ph)
        
        val_1d = self.model.run(math.sqrt(0.0002))
        val_2d = self.model.runXY([0.01,0.01]) 
        
        self.assertTrue(math.fabs(val_1d-val_2d)/val_1d < 0.02)
        
        
        
class TestSphere(unittest.TestCase):
    """
        Testing C++ Cylinder model
    """
    def setUp(self):
        from sans.models.SphereModel import SphereModel
        self.model= SphereModel()
        
        self.model.setParam('scale', 1.0)
        self.model.setParam('radius', 60.0)
        self.model.setParam('sldSph', 2.0)
        self.model.setParam('sldSolv', 1.0)
        self.model.setParam('background', 0.0)
        
    def test_simple(self):
        """
            Test simple 1D and 2D values
            Numbers taken from model that passed validation, before
            the update to C++ underlying class.
        """
        self.assertTrue(math.fabs(self.model.run(0.001)-90412744456148.094)<=50.0)
        self.assertAlmostEqual(self.model.runXY([0.001,0.001]), 
                               90347660670656.391, 1)

    def test_dispersion(self):
        """
            Test with dispersion
        """
        from sans.models.DisperseModel import DisperseModel
        disp = DisperseModel(self.model, ['radius'], [10])
        disp.setParam('n_pts', 10)
        disp.setParam('radius.npts', 10)
        disp.setParam('radius.nsigmas', 2.5)
        self.assertTrue(math.fabs(disp.run(0.001)-96795008379475.219<50.0))
        
    def test_new_disp(self):
        from sans.models.dispersion_models import GaussianDispersion
        disp_rm = GaussianDispersion()
        self.model.set_dispersion('radius', disp_rm)
        self.model.dispersion['radius']['width'] = 0.1666666667
        self.model.dispersion['radius']['npts'] = 10
        self.model.dispersion['radius']['nsigmas'] = 2

        #self.assertAlmostEqual(self.model.run(0.001), 96795008379475.25,3)
        
        
        
class TestEllipticalCylinder(unittest.TestCase):
    """
        Testing C++ Cylinder model
    """
    def setUp(self):
        from sans.models.EllipticalCylinderModel import EllipticalCylinderModel
        self.model= EllipticalCylinderModel()
        
        self.model.setParam('scale', 1.0)
        self.model.setParam('r_minor', 20.0)
        self.model.setParam('r_ratio', 1.5)
        self.model.setParam('length', 400.0)
        self.model.setParam('sldCyl', 4.0e-6)
        self.model.setParam('sldSolv', 1.0e-6)
        self.model.setParam('background', 0.0)
        self.model.setParam('cyl_theta', 90)
        self.model.setParam('cyl_phi', 0.0)
        self.model.setParam('cyl_psi', 0.0)
        
    def test_simple(self):
        """
            Test simple 1D and 2D values
            Numbers taken from model that passed validation, before
            the update to C++ underlying class.
        """
        self.assertAlmostEqual(self.model.run(0.001), 
                               675.50440232504991, 3)
        self.assertAlmostEqual(self.model.runXY([0.001,0.001]), 
                               669.5173937622792, 0)
        
    def test_dispersion(self):
        """
            Test with dispersion
        """
        from sans.models.DisperseModel import DisperseModel
        disp = DisperseModel(self.model, ['r_minor', 'r_ratio', 'length'], 
                             [5, 0.25, 50])
        disp.setParam('n_pts', 10)
        self.assertAlmostEqual(disp.run(0.001), 711.18048194151925, 3)
        self.assertAlmostEqual(disp.runXY([0.001,0.001]), 704.63525988095705, 0)

    def test_new_disp(self):
        from sans.models.dispersion_models import GaussianDispersion
        disp_rm = GaussianDispersion()
        self.model.set_dispersion('r_minor', disp_rm)
        self.model.dispersion['r_minor']['width'] = 0.25
        self.model.dispersion['r_minor']['npts'] = 10
        self.model.dispersion['r_minor']['nsigmas'] = 2

        disp_rr = GaussianDispersion()
        self.model.set_dispersion('r_ratio', disp_rr)
        self.model.dispersion['r_ratio']['width'] = 0.25/1.5
        self.model.dispersion['r_ratio']['npts'] = 10
        self.model.dispersion['r_ratio']['nsigmas'] = 2

        disp_len = GaussianDispersion()
        self.model.set_dispersion('length', disp_len)
        self.model.dispersion['length']['width'] = 50.0/400
        self.model.dispersion['length']['npts'] = 10
        self.model.dispersion['length']['nsigmas'] = 2

        self.assertAlmostEqual(self.model.run(0.001), 
                               1.23925910*711.18048194151925, 3)
        self.assertAlmostEqual(self.model.runXY([0.001,0.001]), 
                               1.238955*704.63525988095705, 0)
        

    def test_array(self):
        """
            Perform complete rotational average and
            compare to 1D
        """
        from sans.models.dispersion_models import ArrayDispersion
        disp_ph = ArrayDispersion()
        disp_th = ArrayDispersion()
        disp_ps = ArrayDispersion()
        
        values_ph = numpy.zeros(100)
        values_th = numpy.zeros(100)
        values_ps = numpy.zeros(100)
        weights   = numpy.zeros(100)
        for i in range(100):
            values_ps[i]=(360/99.0*i)
            values_ph[i]=(360/99.0*i)
            values_th[i]=(180/99.0*i)
            weights[i]=(1.0)
        
        disp_ph.set_weights(values_ph, weights)
        disp_th.set_weights(values_th, weights)
        disp_ps.set_weights(values_ps, weights)
        
        self.model.set_dispersion('cyl_theta', disp_th)
        self.model.set_dispersion('cyl_phi', disp_ph)
        self.model.set_dispersion('cyl_psi', disp_ps)
        
        val_1d = self.model.run(math.sqrt(0.0002))
        val_2d = self.model.runXY([0.01,0.01]) 
        
        self.assertTrue(math.fabs(val_1d-val_2d)/val_1d < 0.02)
        
class TestDispModel(unittest.TestCase):
    def setUp(self):
        from sans.models.CylinderModel import CylinderModel
        self.model = CylinderModel()
        
        
    def test_disp_params(self):
        
        self.assertEqual(self.model.dispersion['radius']['width'], 0.0)
        self.model.setParam('radius.width', 0.25)
        self.assertEqual(self.model.dispersion['radius']['width'], 0.25)
        self.assertEqual(self.model.getParam('radius.width'), 0.25)
        self.assertEqual(self.model.dispersion['radius']['type'], 'gaussian')
        
  
if __name__ == '__main__':
    unittest.main()
   