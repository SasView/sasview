"""
    Unit tests for fitting module 
    @author: G. Alina
"""
import unittest

from sans.guiframe.dataFitting import Data1D 
from sans.fit.AbstractFitEngine import Model,FitData1D
import math
from sans.fit.Fitting import Fit
from DataLoader.loader import Loader

class testFitModule(unittest.TestCase):
    """ test fitting """
   
        
    def test_scipy(self):
        """ Simple cylinder model fit (scipy)  """
        
        out=Loader().load("cyl_400_20.txt")
        data = Data1D(x=out.x, y=out.y, dx=out.dx, dy=out.dy)
        # Receives the type of model for the fitting
        from sans.models.MultiplicationModel import MultiplicationModel
        from sans.models.CylinderModel import CylinderModel
        from sans.models.SquareWellStructure import SquareWellStructure
        model1  =  MultiplicationModel(CylinderModel(),SquareWellStructure())
        model1.setParam('background', 0.0)
        model1.setParam('contrast', 3e-006)
        model1.setParam('length', 600)
        model1.setParam('radius', 20)
        model1.setParam('scale', 10)
        model1.setParam('volfraction', 0.04)
        model1.setParam('welldepth', 1.5)
        model1.setParam('wellwidth', 1.2)
      
        model = Model(model1)
    
        pars1 =['length','radius','scale']
        fitter = Fit('scipy')
        fitter.set_data(data,1)
        fitter.set_model(model,1,pars1)
        fitter.select_problem_for_fit(Uid=1,value=1)
        result1 = fitter.fit()
      
        self.assert_(result1)
        self.assertTrue(len(result1.pvec)>=0 )
        self.assertTrue(len(result1.stderr)>= 0)
        
        self.assertTrue( math.fabs(result1.pvec[0]-605)/3.0 <= result1.stderr[0] )
        self.assertTrue( math.fabs(result1.pvec[1]-20.0)/3.0  <= result1.stderr[1] )
        self.assertTrue( math.fabs(result1.pvec[2]-1)/3.0 <= result1.stderr[2] )
        
        self.assertTrue( result1.fitness/len(data.x) < 1.0 )
        
       
if __name__ == '__main__':
    unittest.main()  