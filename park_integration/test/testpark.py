"""
    Unit tests for fitting module  using park integration
    fitting 2 data with 2 model and one constraint on only one parameter is not working
"""
import unittest
from sans.guitools.plottables import Theory1D
from sans.guitools.plottables import Data1D
from sans.fit.AbstractFitEngine import Model,Data
import math
class testFitModule(unittest.TestCase):
    
    def test2models2data2constraints(self):
        """ test fitting for two data , 2 model , 2 constraints"""
        from sans.fit.Loader import Load
        load= Load()
        #Load the first data
        load.set_filename("testdata1.txt")
        load.set_values()
        data1 = Data1D(x=[], y=[],dx=None, dy=None)
        load.load_data(data1)
        
        #Load the second data
        load.set_filename("testdata2.txt")
        load.set_values()
        data2 = Data1D(x=[], y=[],dx=None, dy=None)
        load.load_data(data2)
        
        #Load the third data
        load.set_filename("testdata_line.txt")
        load.set_values()
        data3 = Data1D(x=[], y=[],dx=None, dy=None)
        load.load_data(data3)
        
        #Importing the Fit module
        from sans.fit.Fitting import Fit
        fitter= Fit('park')
        # Receives the type of model for the fitting
        from sans.guitools.LineModel import LineModel
        model1  = LineModel()
        model2  = LineModel()
        
        #Do the fit
        model1.setParam( 'A', 2.5)
        model1.setParam( 'B', 4)
        model1.name="M1"
        fitter.set_model(Model(model1),"M1",1, ['A','B'])
        fitter.set_data(Data(sans_data=data1),1)
        model2.name="M2"
        model2.setParam( 'A', "M1.A+1")
        model2.setParam( 'B', 'M1.B*2')
        
        fitter.set_model(Model(model2),"M2",2, ['A','B'])
        fitter.set_data(Data(sans_data=data2),2)
        
        result = fitter.fit()
        chisqr1 = result.fitness
        out1 = result.pvec
        cov1 = result.cov
        self.assert_(math.fabs(out1[1]-2.5)/math.sqrt(cov1[1][1]) < 2)
        print math.fabs(out1[0]-4.0)/math.sqrt(cov1[0][0])
        #self.assert_(math.fabs(out1[0]-4.0)/math.sqrt(cov1[0][0]) < 2)
        self.assert_(math.fabs(out1[3]-2.5)/math.sqrt(cov1[3][3]) < 2)
        self.assert_(math.fabs(out1[2]-4.0)/math.sqrt(cov1[2][2]) < 2)
        print chisqr1/len(data1.x)
        #self.assert_(chisqr1/len(data1.x) < 2)
        print chisqr1/len(data2.x)
        #self.assert_(chisqr2/len(data2.x) < 2)
    
    def test2models2data1constraint(self):
        """ test fitting for two data , 2 model ,1 constraint"""
        from sans.fit.Loader import Load
        load= Load()
        #Load the first data
        load.set_filename("testdata1.txt")
        load.set_values()
        data1 = Data1D(x=[], y=[],dx=None, dy=None)
        load.load_data(data1)
        
        #Load the second data
        load.set_filename("testdata2.txt")
        load.set_values()
        data2 = Data1D(x=[], y=[],dx=None, dy=None)
        load.load_data(data2)
        
        #Load the third data
        load.set_filename("testdata_line.txt")
        load.set_values()
        data3 = Data1D(x=[], y=[],dx=None, dy=None)
        load.load_data(data3)
        
        #Importing the Fit module
        from sans.fit.Fitting import Fit
        fitter= Fit('park')
        # Receives the type of model for the fitting
        from sans.guitools.LineModel import LineModel
        model1  = LineModel()
        model2  = LineModel()
        
        #Do the fit
        model1.setParam( 'A', 2.5)
        model1.setParam( 'B', 4)
        model1.name="M1"
        fitter.set_model(Model(model1),"M1",1, ['A','B'])
        fitter.set_data(Data(sans_data=data1),1)
        model2.name="M2"
        model2.setParam( 'A', 2)
        model2.setParam( 'B', 'M1.B*2')
        
        fitter.set_model(Model(model2),"M2",2, ['A','B'])
        fitter.set_data(Data(sans_data=data2),2)
        
        result = fitter.fit()
        chisqr1 = result.fitness
        out1 = result.pvec
        cov1 = result.cov
        self.assert_(math.fabs(out1[1]-2.5)/math.sqrt(cov1[1][1]) < 2)
        print math.fabs(out1[0]-4.0)/math.sqrt(cov1[0][0])
        #self.assert_(math.fabs(out1[0]-4.0)/math.sqrt(cov1[0][0]) < 2)
        self.assert_(math.fabs(out1[3]-2.5)/math.sqrt(cov1[3][3]) < 2)
        self.assert_(math.fabs(out1[2]-4.0)/math.sqrt(cov1[2][2]) < 2)
        print chisqr1/len(data1.x)
        #self.assert_(chisqr1/len(data1.x) < 2)
        print chisqr1/len(data2.x)
        #self.assert_(chisqr2/len(data2.x) < 2)
    
        
    def test2models2dataNoconstraint(self):
        """ test fitting for two data  and 2 models no cosntrainst"""
        from sans.fit.Loader import Load
        load= Load()
        #Load the first data
        load.set_filename("testdata1.txt")
        load.set_values()
        data1 = Data1D(x=[], y=[],dx=None, dy=None)
        load.load_data(data1)
        
        #Load the second data
        load.set_filename("testdata2.txt")
        load.set_values()
        data2 = Data1D(x=[], y=[],dx=None, dy=None)
        load.load_data(data2)
        
        #Load the third data
        load.set_filename("testdata_line.txt")
        load.set_values()
        data3 = Data1D(x=[], y=[],dx=None, dy=None)
        load.load_data(data3)
        
        #Importing the Fit module
        from sans.fit.Fitting import Fit
        fitter= Fit('park')
        # Receives the type of model for the fitting
        from sans.guitools.LineModel import LineModel
        model1  = LineModel()
        model2  = LineModel()
        
        #Do the fit
        model1.setParam( 'A', 2.5)
        model1.setParam( 'B', 4)
        model1.name="M1"
        fitter.set_model(Model(model1),"M1",1, ['A','B'])
        fitter.set_data(Data(sans_data=data1),1)
        model2.name="M2"
        model2.setParam( 'A', 1)
        model2.setParam( 'B', 2)
        
        fitter.set_model(Model(model2),"M2",2, ['A','B'])
        fitter.set_data(Data(sans_data=data2),2)
    
        result = fitter.fit()
        chisqr1 = result.fitness
        out1 = result.pvec
        cov1 = result.cov
        self.assert_(math.fabs(out1[1]-2.5)/math.sqrt(cov1[1][1]) < 2)
        print math.fabs(out1[0]-4.0)/math.sqrt(cov1[0][0])
        #self.assert_(math.fabs(out1[0]-4.0)/math.sqrt(cov1[0][0]) < 2)
        self.assert_(math.fabs(out1[3]-2.5)/math.sqrt(cov1[3][3]) < 2)
        self.assert_(math.fabs(out1[2]-4.0)/math.sqrt(cov1[2][2]) < 2)
        print chisqr1/len(data1.x)
        #self.assert_(chisqr1/len(data1.x) < 2)
        print chisqr1/len(data2.x)
        #self.assert_(chisqr2/len(data2.x) < 2)
    
        
    