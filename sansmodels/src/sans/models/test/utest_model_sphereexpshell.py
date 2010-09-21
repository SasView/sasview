"""
    Unit tests for specific models
    @author: JHJ Cho / UTK
"""

import unittest

class TestSphereExpShell1(unittest.TestCase):
    """ 
        Unit tests for SphereExpShellModel
    """
    def setUp(self):

        from sans.models.SphereExpShellModel import SphereExpShellModel
        from sans.models.CoreMultiShellModel import CoreMultiShellModel
        from sans.models.VesicleModel import VesicleModel 

        self.model = SphereExpShellModel(n_shells=1)
        self.model2 = SphereExpShellModel(n_shells=1).model
        self.model3 = CoreMultiShellModel(n_shells=1)
        self.model4 = VesicleModel()
        
    def test_compare_Exp0_flat(self):
        """
        Check if Exp function with A_shell=0 gives the same value as Flat function
        """
        print "\n*****Note: All tests (test_compare_Exp0_flat and test_compare_Expsmall_line) were passes since Sept. 18, 2010..."
        # Exp: func_shell = 2, Line: func_shell =1 , Flat: func_shell = 0.
        # A_shell = The coefficient of the exponential function: exp(A_shell*(r-ro)/thick_shell)
        # exp function by default
        # exp function crosses over to flat func at A_shell=0
        self.model.setParam("A_shell1", 0)
        # set A_shell=1
        self.model2.setParam("A_shell1", 1)
        # change the function to flat function
        self.model2.setParam("func_shell1", 0)
        #self.model2.setParam("sld_in_shell1", 1.7e-006)
        #self.model2.setParam("sld_out_shell1", 1.7e-006)
        
        # model3: set param values as same as the model2
        self.model3.setParam("background", 0.0)
        self.model3.setParam("rad_core", 200.0)
        self.model3.setParam("scale", 1.0)
        self.model3.setParam("sld_core", 1.0e-006)
        self.model3.setParam("sld_shell1", 1.7e-006)
        self.model3.setParam("sld_solv", 6.4e-006)
        self.model3.setParam("thick_shell1", 50.0)
        
        #Compare exp(A=0) to flat (where A_shell is null) function
        self.assertEqual(self.model.run(0.1),self.model2.run(0.1))
        self.assertAlmostEqual(self.model2.run(0.1),self.model3.run(0.1),10)

    def test_compare_Exp0_flat_vesicle(self):
        """
        Check if Exp function with A_shell=0 gives the same value as Flat function of vesicle model when sld_solv=sld_core
        """
        print "\n*****Note: All tests (test_compare_Exp0_flat and test_compare_Expsmall_line) were passes since Sept. 18, 2010..."
        # Exp: func_shell = 2, Line: func_shell =1 , Flat: func_shell = 0.
        # A_shell = The coefficient of the exponential function: exp(A_shell*(r-ro)/thick_shell)
        # exp function by default
        # exp function crosses over to flat func at A_shell=0
        self.model.setParam("A_shell1", 0)
                # set A_shell=1
        self.model2.setParam("A_shell1", 1)
        # change the function to flat function
        self.model2.setParam("func_shell1", 0)
        
        # model: set param values as same as the model2
        self.model.setParam("background", 0.0)
        self.model.setParam("rad_core", 100.0)
        self.model.setParam("scale", 1.0)
        self.model.setParam("sld_core", 6.36e-006)
        self.model.setParam("sld_in_shell1", 5e-007)
        self.model.setParam("sld_solv", 6.36e-006)
        self.model.setParam("thick_shell1", 30.0)
        # model2: set param values as same as the model2
        self.model2.setParam("background", 0.0)
        self.model2.setParam("rad_core", 100.0)
        self.model2.setParam("scale", 1.0)
        self.model2.setParam("sld_core", 6.36e-006)
        self.model2.setParam("sld_in_shell1", 5e-007)
        self.model2.setParam("sld_solv", 6.36e-006)
        self.model2.setParam("thick_shell1", 30.0)
        #Compare exp(A=0) to flat (where A_shell is null) function
        self.assertEqual(self.model.run(0.1),self.model4.run(0.1))
        self.assertEqual(self.model2.run(0.1),self.model4.run(0.1))
        #self.assertAlmostEqual(self.model2.run(0.1),self.model3.run(0.1),10)

  
    def test_compare_Expsmall_line(self):
        """
        Check if Exp function with A_shell-->0 gives the same value as linear function
        """
        # exp function crosses over to line func as A_shell-->0
        self.model.setParam("A_shell1", 0.000001)
        self.model2.setParam("A_shell1", 1)
        # change the function to a line function
        self.model2.setParam("func_shell1", 1)
        
        #Compare exp(A=0.000001) to linear (where A_shell is null) function   
        self.assertAlmostEqual(self.model.run(0.1),self.model2.run(0.1),4)
        
  
                
if __name__ == '__main__':
    unittest.main()