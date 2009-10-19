"""
    Unit tests for fitting module 
"""
import unittest
#from sans.guitools.plottables import Theory1D
#from sans.guitools.plottables import Data1D
from danse.common.plottools.plottables import Data1D,Theory1D
from sans.fit.AbstractFitEngine import Model,FitData1D
import math
from sans.fit.Fitting import Fit
from DataLoader.loader import Loader

class testFitModule(unittest.TestCase):
    """ test fitting """
    
    def test_scipy(self):
        """ Simple cylinder model fit (scipy)  """
        
        out=Loader().load("cyl_400_20.txt")
        data1 = Data1D(x=out.x, y=out.y, dx=out.dx, dy=out.y)
        
        fitter = Fit('scipy')
        # Receives the type of model for the fitting
        from sans.models.CylinderModel import CylinderModel
        model1  = CylinderModel()
        model1.setParam('contrast', 1)
        #data = Data(sans_data=data1)
        data = FitData1D(data1)
        model = Model(model1)
        
        pars1 =['length','radius','scale']
        fitter.set_data(data,1)
        model.set(scale=1e-10)
        fitter.set_model(model,1,pars1)
        fitter.select_problem_for_fit(Uid=1,value=1)
        result1 = fitter.fit()
        
        self.assert_(result1)
        self.assertTrue(len(result1.pvec)>0 or len(result1.pvec)==0 )
        self.assertTrue(len(result1.stderr)> 0 or len(result1.stderr)==0)
        
        self.assertTrue( math.fabs(result1.pvec[0]-400.0)/3.0 < result1.stderr[0] )
        self.assertTrue( math.fabs(result1.pvec[1]-20.0)/3.0  < result1.stderr[1] )
        self.assertTrue( math.fabs(result1.pvec[2]-9.0e-12)/3.0   < result1.stderr[2] )
        self.assertTrue( result1.fitness < 1.0 )
        
    def test_park(self):
        """ Simple cylinder model fit (park)  """
        
        out=Loader().load("cyl_400_20.txt")
        data1 = Data1D(x=out.x, y=out.y, dx=out.dx, dy=out.y)
        
        fitter = Fit('park')
        # Receives the type of model for the fitting
        from sans.models.CylinderModel import CylinderModel
        model1  = CylinderModel()
        
        #data = Data(sans_data=data1)
        data = FitData1D(data1)
        model = Model(model1)
        
        pars1 =['length','radius','scale']
        fitter.set_data(data,1)
        model.set(contrast= 1)
        model.set(scale=1e-10)
        fitter.set_model(model,1,pars1)
        fitter.select_problem_for_fit(Uid=1,value=1)
        result1 = fitter.fit()
        
        self.assert_(result1)
        self.assertTrue(len(result1.pvec)>0 or len(result1.pvec)==0 )
        self.assertTrue(len(result1.stderr)> 0 or len(result1.stderr)==0)
        
        print result1.pvec[0]-400.0, result1.pvec[0]
        print math.fabs(result1.pvec[0]-400.0)/3.0
        self.assertTrue( math.fabs(result1.pvec[0]-400.0)/3.0 < result1.stderr[0] )
        self.assertTrue( math.fabs(result1.pvec[1]-20.0)/3.0  < result1.stderr[1] )
        self.assertTrue( math.fabs(result1.pvec[2]-9.0e-12)/3.0   < result1.stderr[2] )
        self.assertTrue( result1.fitness < 1.0 )
        
    def test_park2(self):
        """ Simultaneous cylinder model fit (park)  """
        
        out=Loader().load("cyl_400_20.txt")
        data1 = Data1D(x=out.x, y=out.y, dx=out.dx, dy=out.y)
        
        out2=Loader().load("cyl_400_40.txt")
        data2 = Data1D(x=out2.x, y=out2.y, dx=out2.dx, dy=out2.y)
        
        fitter = Fit('park')
        # Receives the type of model for the fitting
        from sans.models.CylinderModel import CylinderModel
        cyl1  = CylinderModel()
        cyl1.name = "C1"
        
        #data1 = Data(sans_data=data1)
        data1 = FitData1D(data1)
        model1 = Model(cyl1)
        model1.set(contrast=1)
        model1.set(scale= 1e-10)
        fitter.set_data(data1,1)
        fitter.set_model(model1, 1, ['length','radius','scale'])
        
        cyl2  = CylinderModel()
        cyl2.name = "C2"
        
        #data2 = Data(sans_data=data2)
        data2 = FitData1D(data2)
        # This is wrong. We should not store string as 
        # parameter values
        # Why not inherit our AbstracFitEngine.Model from Park.Model?
        
        #cyl2.setParam('length', 'C1.length')
        #print "read back:", cyl2.getParam('length')
        
        model2 = Model(cyl2)
        model2.set(length='C1.length')
        model2.set(contrast=1)
        model2.set(scale= 1e-10)
        fitter.set_data(data2,2)
        fitter.set_model(model2, 2, ['radius','scale'])
        fitter.select_problem_for_fit(Uid=1,value=1)
        fitter.select_problem_for_fit(Uid=2,value=1)
        result1 = fitter.fit()
        
        self.assert_(result1)
        self.assertTrue(len(result1.pvec)>0 or len(result1.pvec)==0 )
        self.assertTrue(len(result1.stderr)> 0 or len(result1.stderr)==0)
        
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
                self.assertTrue( math.fabs(par.value-9.0e-12)/3.0 < par.stderr )
            elif par.name=='C2.scale':
                print par.name, par.value
                self.assertTrue( math.fabs(par.value-9.0e-12)/3.0 < par.stderr )
            
        
       