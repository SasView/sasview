"""
    Unit tests for fitting module 
    @author G.alina
"""
import unittest

from sans.fit.AbstractFitEngine import Model
import math
from sans.fit.Fitting import Fit
from DataLoader.loader import Loader

class TestSingleFit(unittest.TestCase):
    """ test single fitting """
    def setUp(self):
        """ initialize data"""
        self.data = Loader().load("cyl_400_20.txt")
        # Create model that fitting engine understands
        from sans.models.CylinderModel import CylinderModel
        self.model  = CylinderModel()
        self.model.setParam("scale", 1.0)
        self.model.setParam("radius",18)
        self.model.setParam("length", 397)
        self.model.setParam("contrast",3e-006 )
        self.model.setParam("background", 0.0)
        #select parameters to fit
        self.pars1 =['length','radius','scale']
        
    def _fit(self, name="scipy"):
        """ return fit result """
        fitter = Fit(name)
        fitter.set_data(self.data,1)
        fitter.set_model(self.model,1,self.pars1)
        fitter.select_problem_for_fit(Uid=1,value=1)
        return  fitter.fit()
       

    def test_scipy(self):
        """ Simple cylinder model fit (scipy)  """
        
        result1 = self._fit("scipy")
        
        self.assert_(result1)
        self.assertTrue(len(result1.pvec)>0 or len(result1.pvec)==0 )
        self.assertTrue(len(result1.stderr)> 0 or len(result1.stderr)==0)
        
        self.assertTrue( math.fabs(result1.pvec[0]-400.0)/3.0 < result1.stderr[0] )
        self.assertTrue( math.fabs(result1.pvec[1]-20.0)/3.0  < result1.stderr[1] )
        self.assertTrue( math.fabs(result1.pvec[2]-1.0)/3.0   < result1.stderr[2] )
        self.assertTrue( result1.fitness < 1.0 )
        
        
    def test_park(self):
        """ Simple cylinder model fit (park)  """
        result1 = self._fit("park")
        
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
        from sans.models.CylinderModel import CylinderModel
        cyl1  = CylinderModel()
        cyl1.name = "C1"
        self.model1 = Model(cyl1)
        self.model1.set(scale= 1.0)
        self.model1.set(radius=18)
        self.model1.set(length=396)
        self.model1.set(contrast=3e-006 )
        self.model1.set(background=0.0)
        
        cyl2  = CylinderModel()
        cyl2.name = "C2"
        self.model2 = Model(cyl2)
        self.model2.set(scale= 1.0)
        self.model2.set(radius=37)
        self.model2.set(length='C1.length')
        self.model2.set(contrast=3e-006 )
        self.model2.set(background=0.0)
       
    def _fit(self, name="park"):
        """ return fit result """
        fitter = Fit(name)
        fitter.set_data(self.data1,1)
        fitter.set_model(self.model1, 1, ['length','radius','scale'])
        
        fitter.set_data(self.data2,2)
        fitter.set_model(self.model2, 2, ['radius','scale'])
        fitter.select_problem_for_fit(Uid=1,value=1)
        fitter.select_problem_for_fit(Uid=2,value=1)
        return fitter.fit()
    
    
    def test_park2(self):
        """ Simultaneous cylinder model fit (park)  """
        
        result1= self._fit('park')
        self.assert_(result1)
        self.assertTrue(len(result1.pvec)>=0  )
        self.assertTrue(len(result1.stderr)>= 0)
      
        for par in result1.parameters:
            if par.name=='C1.length':
                print par.name, par.value
                self.assertTrue( math.fabs(par.value-400.0)/3.0 < par.stderr )
            elif par.name=='C1.radius':
                print par.name, par.value
                self.assertTrue( math.fabs(par.value-20.0)/3.0 < par.stderr )
            elif par.name=='C2.radius':
                print par.name, par.value
                self.assertTrue( math.fabs(par.value-40.0)/3.0 < par.stderr )
            elif par.name=='C1.scale':
                print par.name, par.value
                self.assertTrue( math.fabs(par.value-1.0)/3.0 < par.stderr )
            elif par.name=='C2.scale':
                print par.name, par.value
                self.assertTrue( math.fabs(par.value-1.0)/3.0 < par.stderr )
            

if __name__ == '__main__':
    unittest.main()        
       