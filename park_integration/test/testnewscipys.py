"""
    Unit tests for fitting module 
"""
import unittest
from sans.guitools.plottables import Theory1D
from sans.guitools.plottables import Data1D
from sans.fit.AbstractFitEngine import Data, Model
from sans.fit.AbstractFitEngine import sansAssembly
import math
class testFitModule(unittest.TestCase):
    """ test fitting """
    
    def test_Data(self):
        """ test data"""
        #load data
        from sans.fit.Loader import Load
        load= Load()
        load.set_filename("cyl_testdata.txt")
        load.set_values()
        data11 = Data1D(x=[], y=[],dx=None, dy=None)
        load.load_data(data11)
        
        #Importing the Fit module
        from sans.fit.Fitting import Fit
        fitter= Fit('scipy')
        
        # Receives the type of model for the fitting
        from sans.guitools.LineModel import LineModel
        model1  = LineModel()
        data1=Data(sans_data=data11)
        model =Model(model1)
        #Do the fit SCIPY0.007778 1.78E+14 13335629 
        v=[0.007778,0.023333,0.031111,0.038889,0.046667,0.054444]
        for i in range(len(v)):
            self.assertEquals(data1.x[i],v[i])
        #fitter.set_data_assembly(data1,1)
        #fitter.set_model_assembly(model,"M1",1,['A','B'])
    def test_Model(self):
        """ test model"""
        #load data
        from sans.fit.Loader import Load
        load= Load()
        load.set_filename("cyl_testdata.txt")
        load.set_values()
        data11 = Data1D(x=[], y=[],dx=None, dy=None)
        load.load_data(data11)
        
        #Importing the Fit module
        from sans.fit.Fitting import Fit
        fitter= Fit('scipy')
        
        # Receives the type of model for the fitting
        from sans.models.CylinderModel import CylinderModel
        model1  = CylinderModel()
        data1=Data(sans_data=data11)
        model =Model(model1)
        for item in data1.x:
            self.assertEquals(model.eval(item),model.model.run(item))
        p=[0.0, 3.0000000000000001e-006, 1.0, 1.0, 400.0, 20.0, 1.0]  
        model.setParams(p)
        res=[]
        for i in range(len(data1.x)):
            res.append((data1.y[i]-model.eval(data1.x[i]))/data1.dy[i])
            self.assertEquals(model.eval(data1.x[i]),model.model.run(data1.x[i]))  
        print res
    def test_funtor(self):
        """ test functor"""
        #load data
        from sans.fit.Loader import Load
        load= Load()
        load.set_filename("cyl_testdata.txt")
        load.set_values()
        data11 = Data1D(x=[], y=[],dx=None, dy=None)
        load.load_data(data11)
        
        #Importing the Fit module
        from sans.fit.Fitting import Fit
        fitter= Fit('scipy')
        
        # Receives the type of model for the fitting
        from sans.models.CylinderModel import CylinderModel
        model1  = CylinderModel()
        data1=Data(sans_data=data11)
        model =Model(model1)
        functor= sansAssembly(model,data1)
        for item in data1.x:
            self.assertEquals(model.eval(item),model.model.run(item))
        p=[0.0, 3.0000000000000001e-006, 1.0, 1.0, 400.0, 20.0, 1.0]  
        model.setParams(p)
        res=[]
        for i in range(len(data1.x)):
            res.append((data1.y[i]-model.eval(data1.x[i]))/data1.dy[i])
            self.assertEquals(model.eval(data1.x[i]),model.model.run(data1.x[i]))  
        f=functor(p)

        for i in range(len(res)):
            self.assertEquals(res[i],f[i])    
       