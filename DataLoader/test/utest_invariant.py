"""
    Unit tests for data manipulations
    @author Gervaise Alina: unittest imcoplete so far 
"""
import unittest
import numpy, math
from DataLoader.loader import  Loader
from DataLoader.data_info import Data1D, Data2D
from DataLoader.invariant import InvariantCalculator


class TestInvPolySphere(unittest.TestCase):
    """
        Test unsmeared data for invariant computation
    """
    def setUp(self):
        #Data with no slit smear information
        data= Loader().load("PolySpheres.txt")
        self.I = InvariantCalculator( data= data)
        
     
    def testWrongData(self):
        """ test receiving Data1D not of type loader"""
        #compute invariant with smear information
        from danse.common.plottools.plottables import Data1D
        data= Data1D(x=[1,2],y=[2,3] )
        try:
            self.assertRaises(ValueError,InvariantCalculator(data))
        except ValueError, msg:
            print "test pass "+ str(msg)
        else: raise ValueError, "fail to raise exception when expected"
    
    def testInvariant(self):
        """ test the invariant value for data without smearing"""
        self.assertAlmostEquals(self.I.q_star, 7.48959e-5,2)
        
    def testVolume(self):
        """ test volume fraction for polysphere"""
        volume = self.I.get_volume_fraction(contrast=2.6e-6)
        self.assert_(volume >= 0 and volume <=1)
        self.assertAlmostEqual(volume ,0.01)
        
    def testSurface(self):
        """ test surface for polysphere """
        surface = self.I.get_surface(contrast=2.6e-6, porod_const=20)
        self.assertAlmostEqual(surface,0.01)
      
      
class TestInvariantSmear(unittest.TestCase):
    """
        Test smeared data for invariant computation
    """
    def setUp(self):
        # data with smear info
        list = Loader().load("latex_smeared.xml")
        self.data_q_smear = list[0]
        self.I_q_smear = InvariantCalculator( data= self.data_q_smear)
        
        self.data_slit_smear = list[1]
        self.I_slit_smear = InvariantCalculator( data= self.data_slit_smear)
        
        from sans.models.PowerLawModel import PowerLawModel
        self.power_law = PowerLawModel()
        from sans.models.GuinierModel import GuinierModel
        self.guinier = GuinierModel()
     
     
    def test_invariant_slit(self):
        """ test the invariant value for data with slit smear"""
        self.assertTrue(self.I_slit_smear.q_star>0)
        self.assertAlmostEquals(self.I_slit_smear.q_star, 4.1539e-4)
   
    def test_volume_slit_smear(self):
        """ test volume fraction for data with slit smear"""
        volume = self.I_slit_smear.get_volume_fraction(contrast=2.6e-6)
        self.assert_(volume >= 0 and volume <=1)
        self.assertAlmostEqual(volume ,0.01)
        
    def test_invariant_slit_low_guinier(self):
        """ test the invariant with slit smear for data extrapolated low q range using guinier"""
        q_star_min = self.I_slit_smear.get_qstar_min( data= self.data_slit_smear,
                                                       model= self.guinier, npts=10)
        self.assertAlmostEquals(q_star_min, 4.89783e-8)
        self.assertAlmostEquals(self.I.q_star_min, q_star_min)
          
    def test_invariant_slit_low_power(self):
        """ test the invariant with slit smear for data extrapolated low q range using pow_law"""
        q_star_min = self.I_slit_smear.get_qstar_min( data=self.data_slit_smear,
                                                       model= self.power_law, npts=10)
        self.assertFalse(numpy.isfinite(q_star_min))
        self.assertEquals(self.I.q_star_min, q_star_min)
        
    def test_invariant_slit_high_power(self):
        """ test the invariant with slit smear for data extrapolated high q range using pow_law"""
        q_star_max = self.I_slit_smear.get_qstar_max( data= self.data_slit_smear,
                                                       model= self.power_law, npts=10)
        self.assertFalse(numpy.isfinite(q_star_max))
        self.assertEquals(self.I.q_star_max, q_star_max)
        
    def testSurface(self):
        """ test volume fraction for data with slit smear"""
        surface = self.I_q_smear.get_surface(contrast=2.6e-6, porod_const=20)
        self.assertAlmostEqual(surface,0.01)
        
    def test_invariant_q(self):
        """ test the invariant value for data with q smear"""
        self.assertTrue(self.I_q_smear.q_star>0)
        self.assertAlmostEquals(self.I_q_smear.q_star, 1.361677e-3)
        
    def test_invariant_q_low_guinier(self):
        """ test the invariant with q smear for data extrapolated low q range using guinier"""
        q_star_min = self.I_slit_smear.get_qstar_min( data= self.data_q_smear,
                                                       model= self.guinier, npts=10)
        self.assertAlmostEquals(q_star_min,6.76e-4)
        self.assertAlmostEquals(self.I.q_star_min, q_star_min)
          
    def test_invariant_q_low_power(self):
        """ test the invariant with q smear for data extrapolated low q range using pow_law"""
        q_star_min = self.I_slit_smear.get_qstar_min( data= self.data_q_smear,
                                                       model= self.power_law, npts=10)
        self.assertFalse(numpy.isfinite(q_star_min))
        self.assertEquals(self.I.q_star_min, q_star_min)
        
    def test_invariant_q_high_power(self):
        """ test the invariant with q smear for data extrapolated high q range using pow_law"""
        q_star_max = self.I_slit_smear.get_qstar_max( data= self.data_q_smear,
                                                       model= self.power_law, npts=10)
        self.assertAlmostEquals(q_star_max,1.2e-4)
        self.assertEquals(self.I.q_star_max, q_star_max)
      
    def test_volume_q_smear(self):
        """ test volume fraction for data with q smear"""
        volume = self.I_slit_smear.get_volume_fraction(contrast=2.6e-6)
        self.assert_(volume > 0 and volume <=1)
        self.assertAlmostEqual(volume ,0.01)
        
    def testSurface_q_smear(self):
        """ test surface for data with q smear"""
        surface = self.I_q_smear.get_surface(contrast=2.6e-6, porod_const=20)
        self.assertAlmostEqual(surface,0.01)
      
      
class ExtrapolationTest(unittest.TestCase):
    
    def setUp(self):
        #Data with no slit smear information
        self.data= Loader().load("PolySpheres.txt")
        from sans.models.PowerLawModel import PowerLawModel
        self.power_law = PowerLawModel()
        from sans.models.GuinierModel import GuinierModel
        self.guinier = GuinierModel()
        self.I = InvariantCalculator( data= self.data)
       
        
    def testInvariant(self):
        """ test the invariant value for data extrapolated"""
        self.assertAlmostEquals(self.I.q_star, 7.48959e-5)
        
    def testInvariantLowGuinier(self):
        """ test the invariant value for data extrapolated low range using guinier"""
        q_star_min = self.I.get_qstar_min( data= self.data, model= self.guinier, npts=10)
        self.assertAlmostEquals(q_star_min, 4.89783e-8)
        self.assertAlmostEquals(self.I.q_star_min, q_star_min)
          
    def testInvariantLowPower(self):
        """ test the invariant value for data extrapolated low range using pow_law"""
        q_star_min = self.I.get_qstar_min( data= self.data, model= self.power_law, npts=10)
        self.assertFalse(numpy.isfinite(q_star_min))
        self.assertEquals(self.I.q_star_min, q_star_min)
          
    def testInvariantHigh(self):
        """ test the invariant value for data extrapolated high range"""
        q_star_max = self.I.get_qstar_max( self.data, model=self.power_law, npts=10)
        self.assertAlmostEquals(q_star_max, 4.066202e-6)
        self.assertAlmostEquals(self.I0.q_star_max, q_star_max)
        
    def testInvariantTotal(self):
        """ test the total invariant value for data extrapolated"""
        self.assertAlmostEquals(self.I.q_star_total, 7.88981e-5)  
        
    def testVolume(self):
        """ test volume fraction for data extrapolated"""
        volume = self.I.get_volume_fraction(contrast=2.6e-6)
        self.assert_(volume > 0 and volume <=1)
        self.assertAlmostEqual(volume ,0.01)
    
    def testSurface(self):
        """ test surface for data extrapolated"""
        surface = self.I.get_surface(contrast=2.6e-6, porod_const=20)
        self.assertAlmostEqual(surface,0.01)
            
if __name__ == '__main__':
    unittest.main()
