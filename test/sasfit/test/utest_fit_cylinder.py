"""
    Unit tests for fitting module 
    @author G.alina
"""
import unittest
import math

from sas.sascalc.fit.AbstractFitEngine import Model
from sas.sascalc.fit.BumpsFitting import BumpsFit as Fit
from sas.sascalc.dataloader.loader import Loader

class TestSingleFit(unittest.TestCase):
    """ test single fitting """
    def setUp(self):
        """ initialize data"""
        self.data = Loader().load("cyl_400_20.txt")
        # Create model that fitter understands
        from sas.models.CylinderModel import CylinderModel
        self.model  = CylinderModel()
        self.model.setParam("scale", 1.0)
        self.model.setParam("radius",18)
        self.model.setParam("length", 397)
        self.model.setParam("sldCyl",3e-006 )
        self.model.setParam("sldSolv",0.0 )
        self.model.setParam("background", 0.0)
        #select parameters to fit
        self.pars1 =['length','radius','scale']
        
    def test_fit(self):
        """Simple cylinder model fit"""
        fitter = Fit()
        fitter.set_data(self.data,1)
        fitter.set_model(self.model,1,self.pars1)
        fitter.select_problem_for_fit(id=1,value=1)
        result1, = fitter.fit()

        self.assert_(result1)
        self.assertTrue(len(result1.pvec)>0 or len(result1.pvec)==0 )
        self.assertTrue(len(result1.stderr)> 0 or len(result1.stderr)==0)

        self.assertTrue( math.fabs(result1.pvec[0]-400.0)/3.0 < result1.stderr[0] )
        self.assertTrue( math.fabs(result1.pvec[1]-20.0)/3.0  < result1.stderr[1] )
        self.assertTrue( math.fabs(result1.pvec[2]-1.0)/3.0   < result1.stderr[2] )
        self.assertTrue( result1.fitness < 1.0 )


        
class TestSimultaneousFit(unittest.TestCase):
    """ test simultaneous fitting """
    def setUp(self):
        """ initialize data"""
        
        self.data1=Loader().load("cyl_400_20.txt")
        self.data2=Loader().load("cyl_400_40.txt")
    
        # Receives the type of model for the fitting
        from sas.models.CylinderModel import CylinderModel
        cyl1  = CylinderModel()
        cyl1.name = "C1"
        self.model1 = Model(cyl1)
        self.model1.set(scale= 1.0)
        self.model1.set(radius=18)
        self.model1.set(length=200)
        self.model1.set(sldCyl=3e-006, sldSolv=0.0)
        self.model1.set(background=0.0)

        cyl2  = CylinderModel()
        cyl2.name = "C2"
        self.model2 = Model(cyl2)
        self.model2.set(scale= 1.0)
        self.model2.set(radius=37)
        self.model2.set(length=300)
        self.model2.set(sldCyl=3e-006, sldSolv=0.0)
        self.model2.set(background=0.0)


    def test_constrained_bumps(self):
        """ Simultaneous cylinder model fit  """
        self._run_fit(Fit())

    #@unittest.skip("")
    def _run_fit(self, fitter):
        result1, result2 = self._fit(fitter)
        self.assert_(result1)
        self.assertTrue(len(result1.pvec)>0)
        self.assertTrue(len(result1.stderr)>0)

        for n, v, dv in zip(result1.param_list, result1.pvec, result1.stderr):
            if n == "length":
                self.assertTrue( math.fabs(v-400.0)/3.0 < dv )
            elif n=='radius':
                self.assertTrue( math.fabs(v-20.0)/3.0 < dv )
            elif n=='scale':
                self.assertTrue( math.fabs(v-1.0)/3.0 < dv )
        for n, v, dv in zip(result2.param_list, result2.pvec, result2.stderr):
            if n=='radius':
                self.assertTrue( math.fabs(v-40.0)/3.0 < dv )
            elif n=='scale':
                self.assertTrue( math.fabs(v-1.0)/3.0 < dv )

    def _fit(self, fitter):
        """ return fit result """
        fitter.set_data(self.data1,1)
        fitter.set_model(self.model1, 1, ['length','radius','scale'])

        fitter.set_data(self.data2,2)
        fitter.set_model(self.model2, 2, ['length','radius','scale'],
                         constraints=[("length","C1.length")])
        fitter.select_problem_for_fit(id=1,value=1)
        fitter.select_problem_for_fit(id=2,value=1)
        return fitter.fit()


if __name__ == '__main__':
    unittest.main()        
       
