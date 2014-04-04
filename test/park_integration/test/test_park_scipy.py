"""
    Unit tests for fitting module 
    @author: G. Alina
"""
import unittest
import math

from sans.guiframe.dataFitting import Data1D 
from sans.fit.AbstractFitEngine import Model,FitData1D
from sans.fit.Fitting import Fit
from sans.dataloader.loader import Loader
from sans.models.MultiplicationModel import MultiplicationModel
from sans.models.CylinderModel import CylinderModel
from sans.models.SquareWellStructure import SquareWellStructure

class testFitModule(unittest.TestCase):
    """ test fitting """
   
        
    def test_scipy(self):
        """ Simple cylinder model fit (scipy)  """
        
        out=Loader().load("cyl_400_20.txt")
        data = Data1D(x=out.x, y=out.y, dx=out.dx, dy=out.dy)
        # Receives the type of model for the fitting
        model1  =  MultiplicationModel(CylinderModel(),SquareWellStructure())
        model1.setParam('background', 0.0)
        model1.setParam('sldCyl', 3e-006)
        model1.setParam('sldSolv', 0.0)
        model1.setParam('length', 420)
        model1.setParam('radius', 40)
        model1.setParam('scale_factor', 2)
        model1.setParam('volfraction', 0.04)
        model1.setParam('welldepth', 1.5)
        model1.setParam('wellwidth', 1.2)
      
        model = Model(model1)
    
        pars1 =['length','radius','scale_factor']
        fitter = Fit('scipy')
        fitter.set_data(data,1)
        fitter.set_model(model,1,pars1)
        fitter.select_problem_for_fit(id=1,value=1)
        result1, = fitter.fit()

        self.assert_(result1)
        self.assertTrue(len(result1.pvec)>=0 )
        self.assertTrue(len(result1.stderr)>= 0)

        print "results",list(zip(result1.pvec, result1.stderr))
        self.assertTrue( math.fabs(result1.pvec[0]-605)/3.0 <= result1.stderr[0] )
        self.assertTrue( math.fabs(result1.pvec[1]-20.0)/3.0  <= result1.stderr[1] )
        self.assertTrue( math.fabs(result1.pvec[2]-1)/3.0 <= result1.stderr[2] )
        
        self.assertTrue( result1.fitness/len(data.x) < 1.0 )
        
       
if __name__ == '__main__':
    unittest.main()  