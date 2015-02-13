"""
    Unit tests for specific models
    @author: JHJ Cho / UTK
"""

import unittest

class TestSphericalSLDModel(unittest.TestCase):
    """ 
        Unit tests for OnionExpShellModel
    """
    def setUp(self):

        from sas.models.SphericalSLDModel import SphericalSLDModel
        from sas.models.OnionExpShellModel import OnionExpShellModel
        
        # intit models and the multifactor
        # layer 
        self.model = SphericalSLDModel(1)
        self.model2 = OnionExpShellModel(3)
        
    def test_compare_SphericalSLD_OnionExpShell(self):
        """
        Check if SphericalSLD equals (up to 1%) to 
        OnionExpShellModel with an equivalent SLD profile 
        """
        note = "\n*****Note: This test was passes since Nov. 1st, 2010..."
        print note
        # set params
        self.model.setParam("npts_inter", 35)
        self.model.setParam("rad_core0", 100)
        self.model.setParam("thick_inter0", 200)
        self.model.setParam("nu_inter0", 4)
        # Rexp func
        self.model.setParam("func_inter0", 3)
        self.model.setParam("thick_inter1", 200)
        self.model.setParam("nu_inter1", 4)
        self.model.setParam("func_inter1", 3)
        # set A_shell=1
        self.model2.setParam("sld_core0", 2.07e-006)
        # change the function to flat function
        self.model2.setParam("rad_core0", 100)
        self.model2.setParam("thick_shell1", 200)
        self.model2.setParam("sld_out_shell1", 4e-006)
        self.model2.setParam("sld_in_shell1", 2.07e-006)
        self.model2.setParam("A_shell1", -4)
        self.model2.setParam("thick_shell2", 100)
        self.model2.setParam("sld_out_shell2", 4e-006)
        self.model2.setParam("sld_in_shell2", 4e-006)
        self.model2.setParam("A_shell2", 0)
        self.model2.setParam("thick_shell3", 200)
        self.model2.setParam("sld_out_shell3", 1e-006)
        self.model2.setParam("sld_in_shell3", 4e-006)
        self.model2.setParam("A_shell3", -4)
        self.model2.setParam("sld_solv", 1e-006)
        
        #sphericalsld model runs
        model_run_0_1 = self.model.run(0.1)
        model_run_0_01 = self.model.run(0.01)
        model_run_0_001 = self.model.run(0.001)
        #onionexp model runs
        model2_run_0_1 = self.model2.run(0.1)
        model2_run_0_01 = self.model2.run(0.01)
        model2_run_0_001 = self.model2.run(0.001)
        import time
        st = time.time()
        qs = []
        qs = [i/10000 for i in range(1,1000)]
        out = map(self.model.run,qs)
        print time.time()-st
        #Compare exp(A=0) to flat (where A_shell is null) function
        self.assertAlmostEqual(self.model.run(0.1),self.model2.run(0.1),4)
        self.assertAlmostEqual(self.model.run(0.01),self.model2.run(0.01),0)
        self.assertAlmostEqual(self.model.run(0.001),self.model2.run(0.001),-3)
                        
if __name__ == '__main__':
    unittest.main()
