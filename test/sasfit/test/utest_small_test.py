"""
    Unit tests for fitting module 
"""
import unittest
import math
from sas.fit.BumpsFitting import BumpsFit as Fit
from sas.dataloader.loader import Loader
import bumps.fitters
bumps.fitters.FIT_DEFAULT = 'lm'

class testFitModule(unittest.TestCase):
    """ test fitting """
    def test_cylinder_fit(self):
        """ Simple cylinder model fit """
        
        out= Loader().load("cyl_400_20.txt")
       
        fitter = Fit()
        # Receives the type of model for the fitting
        from sas.models.CylinderModel import CylinderModel
        model  = CylinderModel()
        model.setParam('sldCyl', 1)
        model.setParam('sldSolv', 0)
        model.setParam('scale', 1e-10)

        pars1 =['length','radius','scale']
        fitter.set_data(out,1)
        fitter.set_model(model,1,pars1, constraints=())
        fitter.select_problem_for_fit(id=1,value=1)
        result1, = fitter.fit()
        #print result1
        #print result1.__dict__

        self.assert_(result1)
        self.assertTrue(len(result1.pvec)>0 or len(result1.pvec)==0 )
        self.assertTrue(len(result1.stderr)> 0 or len(result1.stderr)==0)

        self.assertTrue( math.fabs(result1.pvec[0]-400.0)/3.0 < result1.stderr[0] )
        self.assertTrue( math.fabs(result1.pvec[1]-20.0)/3.0  < result1.stderr[1] )
        self.assertTrue( math.fabs(result1.pvec[2]-9.0e-12)/3.0   < result1.stderr[2] )
        self.assertTrue( result1.fitness < 1.0 )
        
