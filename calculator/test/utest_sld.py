
import unittest
from sans.calculator.sld_calculator import SldCalculator
_SCALE = 1e-6


class TestH2O(unittest.TestCase):
    """
        Sld calculator test for H2O
    """
    
    def setUp(self):
        """Inititialze variables"""
        # the calculator default value for wavelength is 6
        self.calculator = SldCalculator()
        user_formula = "H2O"
        self.calculator.set_value(user_formula=user_formula,
                                  density=1.0, wavelength=6.0)
    def test_neutron_sld(self):
        """
           check the output of the neutron sld calculator
        """
        #Compute incoherence , absorption, and incoherence
        coh, abs, incoh = self.calculator.calculate_neutron_sld()
        #Compute absortion imaginary part id available
        coh_im = self.calculator.calculate_coherence_im()
        self.assertAlmostEquals(coh * _SCALE, -5.6e-7, 1)
        self.assertAlmostEquals(coh_im * _SCALE, 0)
    
    def test_absorption(self):
        """
            test absorption result
        """
        #Compute incoherence , absorption, and incoherence
        coh, abs, incoh = self.calculator.calculate_neutron_sld()
        #test absorption value
        self.assertAlmostEquals(abs, 0.0741, 2)
        
    def test_incoherence(self):
        """
            test incoherence
        """
        #Compute incoherence , absorption, and incoherence
        coh, abs, incoh = self.calculator.calculate_neutron_sld()
        self.assertAlmostEquals(incoh, 5.62)
        
    def test_cu_xray(self):
        """
            test Cu sld 
        """
        #Compute x-ray sld of Cu
        cu_reel, cu_im = self.calculator.calculate_xray_sld("Cu")
        #test Cu sld
        self.assertAlmostEquals(cu_reel * _SCALE, 9.46e-6, 1)
        self.assertAlmostEquals(cu_im * _SCALE, 3.01e-8)
        
    def test_mo_xray(self):
        """
            test Mo sld
        """
        #Compute x-ray sld of Mo
        mo_reel, mo_im = self.calculator.calculate_xray_sld("Mo")
        #test Mo sld
        self.assertAlmostEquals(mo_reel * _SCALE, 9.43e-6)
        self.assertAlmostEquals(mo_im * _SCALE, 5.65e-7,1)
        
    def test_length(self):
        """
            test length
        """
        #Compute incoherence , absorption, and incoherence
        coh, abs, incoh = self.calculator.calculate_neutron_sld()
        #Compute neutron 1/e length
        length = self.calculator.calculate_length()
        #Test length
        self.assertAlmostEquals(length, 0.17755)

class TestD2O(unittest.TestCase):
    """
        Sld calculator test for D2O
    """
    
    def setUp(self):
        """Inititialze variables"""
        # the calculator default value for wavelength is 6
        self.calculator = SldCalculator()
        user_formula = "D2O"
        self.calculator.set_value(user_formula=user_formula,
                                  density=1.1, wavelength=6.0)
    def test_neutron_sld(self):
        """
           check the output of the neutron sld calculator
        """
        #Compute incoherence , absorption, and incoherence
        coh, abs, incoh = self.calculator.calculate_neutron_sld()
        #Compute absortion imaginary part id available
        coh_im = self.calculator.calculate_coherence_im()
        self.assertAlmostEquals(coh * _SCALE, 6.33e-6, 1)
        self.assertAlmostEquals(coh_im * _SCALE, 0)
    
    def test_absorption(self):
        """
            test absorption result
        """
        #Compute incoherence , absorption, and incoherence
        coh, abs, incoh = self.calculator.calculate_neutron_sld()
        #test absorption value
        self.assertAlmostEquals(abs, 1.35e-4, 2)
        
    def test_incoherence(self):
        """
            test incoherence
        """
        #Compute incoherence , absorption, and incoherence
        coh, abs, incoh = self.calculator.calculate_neutron_sld()
        self.assertAlmostEquals(incoh, 0.138, 2)
        
    def test_cu_xray(self):
        """
            test Cu sld 
        """
        #Compute x-ray sld of Cu
        cu_reel, cu_im = self.calculator.calculate_xray_sld("Cu")
        #test Cu sld
        self.assertAlmostEquals(cu_reel * _SCALE, 9.36e-6, 1)
        self.assertAlmostEquals(cu_im * _SCALE, 2.98e-8)
        
    def test_mo_xray(self):
        """
            test Mo sld
        """
        #Compute x-ray sld of Mo
        mo_reel, mo_im = self.calculator.calculate_xray_sld("Mo")
        #test Mo sld
        self.assertAlmostEquals(mo_reel * _SCALE, 9.33e-6)
        self.assertAlmostEquals(mo_im * _SCALE, 5.59e-9,1)
        
    def test_length(self):
        """
            test length
        """
        #Compute incoherence , absorption, and incoherence
        coh, abs, incoh = self.calculator.calculate_neutron_sld()
        #Compute neutron 1/e length
        length = self.calculator.calculate_length()
        #Test length
        self.assertAlmostEquals(length, 1.549)
        
class TestCd(unittest.TestCase):
    """
        Sld calculator test for Cd
    """
    
    def setUp(self):
        """Inititialze variables"""
        # the calculator default value for wavelength is 6
        self.calculator = SldCalculator()
        user_formula = "Cd"
        self.calculator.set_value(user_formula=user_formula,
                                  density=4.0, wavelength=6.0)
    def test_neutron_sld(self):
        """
           check the output of the neutron sld calculator
        """
        #Compute incoherence , absorption, and incoherence
        coh, abs, incoh = self.calculator.calculate_neutron_sld()
        #Compute absortion imaginary part id available
        coh_im = self.calculator.calculate_coherence_im()
        self.assertAlmostEquals(coh * _SCALE, 1.04e-6, 1)
        self.assertAlmostEquals(coh_im * _SCALE, -1.5e-7, 1)
    
    def test_absorption(self):
        """
            test absorption result
        """
        #Compute incoherence , absorption, and incoherence
        coh, abs, incoh = self.calculator.calculate_neutron_sld()
        #test absorption value
        self.assertAlmostEquals(abs, 180.0, 1)
        
    def test_incoherence(self):
        """
            test incoherence
        """
        #Compute incoherence , absorption, and incoherence
        coh, abs, incoh = self.calculator.calculate_neutron_sld()
        self.assertAlmostEquals(incoh, 0.0754, 2)
        
    def test_cu_xray(self):
        """
            test Cu sld 
        """
        #Compute x-ray sld of Cu
        cu_reel, cu_im = self.calculator.calculate_xray_sld("Cu")
        #test Cu sld
        self.assertAlmostEquals(cu_reel * _SCALE, 2.89e-5, 1)
        self.assertAlmostEquals(cu_im * _SCALE, 2.81e-6)
        
    def test_mo_xray(self):
        """
            test Mo sld
        """
        #Compute x-ray sld of Mo
        mo_reel, mo_im = self.calculator.calculate_xray_sld("Mo")
        #test Mo sld
        self.assertAlmostEquals(mo_reel * _SCALE, 2.84e-5)
        self.assertAlmostEquals(mo_im * _SCALE, 7.26e-7,1)
        
    def test_length(self):
        """
            test length
        """
        #Compute incoherence , absorption, and incoherence
        coh, abs, incoh = self.calculator.calculate_neutron_sld()
        #Compute neutron 1/e length
        length = self.calculator.calculate_length()
        #Test length
        self.assertAlmostEquals(length, 0.005551)
        
if __name__ == '__main__':
    unittest.main()
