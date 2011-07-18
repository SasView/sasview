"""
Unit tests for extra models,PolymerexclVolume, RPA10Model
The reference values are calculated on IGOR/NIST package(Oct.,2010)
@author: JHJ Cho / UTK
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
        
class TestRPA10Case(unittest.TestCase):
    """
    Unit tests for RPA10Model (non-shape) function
    """
    def setUp(self):
        from sans.models.RPA10Model import RPA10Model
        self.model0= RPA10Model(0)
        self.model1= RPA10Model(1)
        self.model2= RPA10Model(2)
        self.model3= RPA10Model(3)
        self.model4= RPA10Model(4)
        self.model5= RPA10Model(5)
        self.model6= RPA10Model(6)
        self.model7= RPA10Model(7)
        self.model8= RPA10Model(8)
        self.model9= RPA10Model(9)
        
    def test1D(self):          
        # the test values are from Igor pro calculation   
        # case 0 
        # set default of vol fration consistent with IGor
        self.model0.setParam('Phic',0.5)
        self.model0.setParam('Phid',0.5)
        self.assertAlmostEqual(self.model0.run(0.001), 0.0716863, 6)
        self.assertAlmostEqual(self.model0.runXY(0.414955), 0.00396997, 6)
        # case 1
        # set default of vol fration consistent with IGor
        self.model1.setParam('Phic',0.5)
        self.model1.setParam('Phid',0.5)
        self.assertAlmostEqual(self.model1.run(0.001), 0.00395016, 6)
        self.assertAlmostEqual(self.model1.runXY(0.414955), 0.00396735, 6)
        # case 2 
        # set default of vol fration consistent with IGor
        self.model2.setParam('Phib',0.33)
        self.model2.setParam('Phic',0.33)
        self.model2.setParam('Phid',0.33)
        self.assertAlmostEqual(self.model2.run(0.001), 0.0932902, 6)
        self.assertAlmostEqual(self.model2.runXY(0.414955), 0.00355736, 6)
        # case 3
        # set default of vol fration consistent with IGor
        self.model3.setParam('Phib',0.33)
        self.model3.setParam('Phic',0.33)
        self.model3.setParam('Phid',0.33)
        self.assertAlmostEqual(self.model3.run(0.001), 0.026254, 6)
        self.assertAlmostEqual(self.model3.runXY(0.414955), 0.00355577, 6)
        # case 4
        # set default of vol fration consistent with IGor
        self.model4.setParam('Phib',0.33)
        self.model4.setParam('Phic',0.33)
        self.model4.setParam('Phid',0.33)
        self.assertAlmostEqual(self.model4.run(0.001), 0.0067433, 6)
        self.assertAlmostEqual(self.model4.runXY(0.414955), 0.00355656, 6)
        # case 5
        self.assertAlmostEqual(self.model5.run(0.001), 0.102636, 6)
        self.assertAlmostEqual(self.model5.runXY(0.414955), 0.00305812, 6)
        # case 6
        self.assertAlmostEqual(self.model6.run(0.001), 0.0370357, 6)
        self.assertAlmostEqual(self.model6.runXY(0.414955), 0.00305708, 6)
        # case 7
        self.assertAlmostEqual(self.model7.run(0.001), 0.0167775, 6)
        self.assertAlmostEqual(self.model7.runXY(0.414955), 0.00305743, 6)
        # case 8
        self.assertAlmostEqual(self.model8.run(0.001), 0.0378691, 6)
        self.assertAlmostEqual(self.model8.runXY(0.414955), 0.00305743, 6)
        # case 9
        self.assertAlmostEqual(self.model9.run(0.001), 0.00839376, 6)
        self.assertAlmostEqual(self.model9.runXY(0.414955), 0.00305777, 6)  
              
class TestBarBell(unittest.TestCase):
    """
    Unit tests for BarBell function
    """
    def setUp(self):
        from sans.models.BarBellModel import BarBellModel
        self.model= BarBellModel()
        
    def test1D(self):          
        # the values are from Igor pro calculation    
        self.assertAlmostEqual(self.model.run(0.001), 2864.7, 1)
        self.assertAlmostEqual(self.model.run(0.215268), 0.526351, 4)
        self.assertAlmostEqual(self.model.runXY(0.414467), 0.0685892, 6)

class TestCappedCylinder(unittest.TestCase):
    """
    Unit tests for CappedCylinder function
    """
    def setUp(self):
        from sans.models.CappedCylinderModel import CappedCylinderModel
        self.model= CappedCylinderModel()
        
    def test1D(self):          
        # the values are from Igor pro calculation  
        # the different digits are due to precision of q values  
        self.assertAlmostEqual(self.model.run(0.001), 1424.72, 2)
        self.assertAlmostEqual(self.model.run(0.215268), 0.360736, 4)
        self.assertAlmostEqual(self.model.runXY(0.414467), 0.110283, 5)

class TestLamellarParaCrystal(unittest.TestCase):
    """
    Unit tests for LamellarParaCystal function
    """
    def setUp(self):
        from sans.models.LamellarPCrystalModel import LamellarPCrystalModel
        self.model= LamellarPCrystalModel()
        
    def test1D(self):    
        self.model.setParam("pd_spacing", 0.2)      
        # the values are from Igor pro calculation  
        # the different digits are due to precision of q values  
        self.assertAlmostEqual(self.model.run(0.001), 21829.3, 1)
        self.assertAlmostEqual(self.model.run(0.215268), 0.00487686, 6)
        self.assertAlmostEqual(self.model.runXY(0.414467), 0.00062029, 6)


class TestSCParaCrystal(unittest.TestCase):
    """
    Unit tests for Simple Cubic ParaCrystal Model function
    """
    def setUp(self):
        from sans.models.SCCrystalModel import SCCrystalModel
        self.model= SCCrystalModel()
        
    def test1D(self):        
        # the values are from Igor pro calculation  
        # the different digits are due to precision of q values  
        self.assertAlmostEqual(self.model.run(0.001), 10.3038, 4)
        self.assertAlmostEqual(self.model.run(0.215268), 0.00714905, 6)
        self.assertAlmostEqual(self.model.runXY(0.414467), 0.000313289, 6)

class TestFCParaCrystal(unittest.TestCase):
    """
    Unit tests for Face Centered Cubic ParaCrystal Model function
    """
    def setUp(self):
        from sans.models.FCCrystalModel import FCCrystalModel
        self.model= FCCrystalModel()
        
    def test1D(self):       
        self.model.setParam("d_factor", 0.05)  
        # the values are from Igor pro calculation  
        # the different digits are due to precision of q values  
        self.assertAlmostEqual(self.model.run(0.001), 0.121017, 6)
        self.assertAlmostEqual(self.model.run(0.215268), 0.0107218, 6)
        self.assertAlmostEqual(self.model.runXY(0.414467), 0.000443282, 6)

class TestBCParaCrystal(unittest.TestCase):
    """
    Unit tests for Body Centered Cubic ParaCrystal Model function
    """
    def setUp(self):
        from sans.models.BCCrystalModel import BCCrystalModel
        self.model= BCCrystalModel()
        
    def test1D(self):        
        # the values are from Igor pro calculation  
        # the different digits are due to precision of q values  
        self.assertAlmostEqual(self.model.run(0.001), 1.77267, 4)
        self.assertAlmostEqual(self.model.run(0.215268), 0.00927739, 6)
        self.assertAlmostEqual(self.model.runXY(0.414467), 0.000406973, 6)
                               

class TestGuinierPorod(unittest.TestCase):
    """
    Unit tests for GuinierPorod Model function
    """
    def setUp(self):
        from sans.models.GuinierPorodModel import GuinierPorodModel 
        self.model= GuinierPorodModel()
        
    def test1D(self):        
        # the values are from Igor pro calculation  
        # the different digits are due to precision of q values  
        self.assertAlmostEqual(self.model.run(0.001), 995.112, 3)
        self.assertAlmostEqual(self.model.run(0.105363), 0.162904, 5)
        self.assertAlmostEqual(self.model.runXY(0.441623), 0.100854, 6)

class TestGaussLorentzGel(unittest.TestCase):
    """
    Unit tests for GuinierPorod Model function
    """
    def setUp(self):
        from sans.models.GaussLorentzGelModel import GaussLorentzGelModel
        self.model= GaussLorentzGelModel()
        
    def test1D(self):        
        # the values are from Igor pro calculation  
        # the different digits are due to precision of q values  
        self.assertAlmostEqual(self.model.run(0.001), 149.481, 3)
        self.assertAlmostEqual(self.model.run(0.105363), 9.1903, 4)
        self.assertAlmostEqual(self.model.runXY(0.441623), 0.632811, 5)
                                

class TestTwoPowerLaw(unittest.TestCase):
    """
    Unit tests for TwoPowerLaw Model function
    """
    def setUp(self):
        from sans.models.TwoPowerLawModel import TwoPowerLawModel
        self.model= TwoPowerLawModel()
        
    def test1D(self):        
        # the values are from Igor pro calculation  
        # the different digits are due to precision of q values  
        self.assertEqual(self.model.run(0.001), 1000)
        self.assertAlmostEqual(self.model.run(0.150141), 0.125945, 5)
        self.assertAlmostEqual(self.model.runXY(0.442528), 0.00166884, 7)
                                
class TestTwoLorentzian(unittest.TestCase):
    """
    Unit tests for TwoLorentzian Model function
    """
    def setUp(self):
        from sans.models.TwoLorentzianModel import TwoLorentzianModel
        self.model= TwoLorentzianModel()
        
    def test1D(self):        
        # the values are from Igor pro calculation  
        # the different digits are due to precision of q values  
        self.assertAlmostEqual(self.model.run(0.001), 11.0899, 3)
        self.assertAlmostEqual(self.model.run(0.150141), 0.410245, 5)
        self.assertAlmostEqual(self.model.runXY(0.442528), 0.148699, 6)
                                

class TestCorrLengthLaw(unittest.TestCase):
    """
    Unit tests for CorrLength Model function
    """
    def setUp(self):
        from sans.models.CorrLengthModel import CorrLengthModel
        self.model= CorrLengthModel()
        
    def test1D(self):        
        # the values are from Igor pro calculation  
        # the different digits are due to precision of q values  
        self.assertAlmostEqual(self.model.run(0.001), 1010.08, 1)
        self.assertAlmostEqual(self.model.run(0.150141), 0.274645, 5)
        self.assertAlmostEqual(self.model.runXY(0.442528), 0.120396, 6)
                                

class TestBroadPeak(unittest.TestCase):
    """
    Unit tests for BroadPeak Model function
    """
    def setUp(self):
        from sans.models.BroadPeakModel import BroadPeakModel
        self.model= BroadPeakModel()
        
    def test1D(self):        
        # the values are from Igor pro calculation  
        # the different digits are due to precision of q values  
        self.assertAlmostEqual(self.model.run(0.001), 10000.5, 1)
        self.assertAlmostEqual(self.model.run(0.1501412), 1.47557, 5)
        self.assertAlmostEqual(self.model.runXY(0.4425284), 0.134093, 6)
        
class TestFractalCoreShell(unittest.TestCase):
    """
    Unit tests for FractalCoreShell Model function
    """
    def setUp(self):
        from sans.models.FractalCoreShellModel import FractalCoreShellModel
        self.model= FractalCoreShellModel()
        
    def test1D(self):        
        #self.model.setParam('radius.width', 2.0)
        # the values are from Igor pro calculation  
        # the different digits are due to precision of q values  
        self.assertAlmostEqual(self.model.run(0.001), 273.742, 3)
        self.assertAlmostEqual(self.model.run(0.1501412), 0.040079, 6)
        self.assertAlmostEqual(self.model.runXY(0.4425284), 0.00141167, 8)  
         
    def test1DSchulzDispersion(self):      
        # Same test w/ test1D up there but w/ Schulzdispersion
        from sans.models.dispersion_models import SchulzDispersion
        disp = SchulzDispersion()
        self.model.set_dispersion('radius', disp)
        # 'width' is a ratio now for non-angular parameters
        self.model.dispersion['radius']['width'] = 0.1
        self.model.dispersion['radius']['npts'] = 100
        self.model.dispersion['radius']['nsigmas'] = 3.0
        # the values are from Igor pro calculation
        # the run does not neccessary to be exactly same with NIST 
        # 'cause we used different method.
        self.assertAlmostEqual(self.model.run(0.001), 287.851, -1)
        self.assertAlmostEqual(self.model.run(0.1501412), 0.0500775, 3)
        self.assertAlmostEqual(self.model.runXY(0.4425284), 0.00390948, 3)         
       

class TestUnifiedPowerRg(unittest.TestCase):
    """
    Unit tests for FractalCoreShell Model function
    """
    def setUp(self):
        from sans.models.UnifiedPowerRgModel import UnifiedPowerRgModel
        self.model1= UnifiedPowerRgModel(1)
        self.model4= UnifiedPowerRgModel(4)
        
    def test1DLabel1(self):        
        # Label #1
        # the values are from Igor pro calculation  
        # the different digits are due to precision of q values  
        self.assertAlmostEqual(self.model1.run(0.001), 2.99956, 5)
        self.assertAlmostEqual(self.model1.run(0.1501412), 0.126506, 6)
        self.assertAlmostEqual(self.model1.runXY(0.4425284), 0.00306386, 8)                             
 
    def test1DLabel4(self):        
        # Label #4
        # Set params consistent w/NIST
        # No. 4 already same
        # No. 3
        self.model4.setParam('Rg3', 200)
        self.model4.setParam('B3', 5e-06)
        self.model4.setParam('G3', 400)
        # No. 2
        self.model4.setParam('Rg2', 600)
        self.model4.setParam('B2', 2e-07)
        self.model4.setParam('G2', 4000)
        # No. 1
        self.model4.setParam('Rg1', 2000)
        self.model4.setParam('B1', 1e-08)
        self.model4.setParam('G1', 40000)
        
        # the values are from Igor pro calculation  
        # the different digits are due to precision of q values  
        self.assertAlmostEqual(self.model4.run(0.001), 14778.4, 1)
        self.assertAlmostEqual(self.model4.run(0.0301614), 7.88115, 4)
        self.assertAlmostEqual(self.model4.run(0.1501412), 0.126864, 6)
        self.assertAlmostEqual(self.model4.runXY(0.4425284), 0.00306386, 8)  
                                                                              

class TestCSPP(unittest.TestCase):
    """
    Unit tests for CSParallelepiped Model function
    """
    def setUp(self):
        from sans.models.CSParallelepipedModel import CSParallelepipedModel
        self.model= CSParallelepipedModel()
        
    def test1D(self):        
        # the values are from Igor pro calculation  
        # the different digits are due to precision of q values  
        self.assertAlmostEqual(self.model.run(0.001), 1383.96, 2)
        self.assertAlmostEqual(self.model.run(0.1501412), 2.51932, 4)
        self.assertAlmostEqual(self.model.runXY(0.4425284), 0.0736735, 6)
                                                                                                                                                          
if __name__ == '__main__':
    unittest.main()