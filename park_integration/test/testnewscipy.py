"""
    Unit tests for fitting module 
"""
import unittest
from sans.guitools.plottables import Theory1D
from sans.guitools.plottables import Data1D
from sans.fit.AbstractFitEngine import Data, Model
import math
class testFitModule(unittest.TestCase):
    """ test fitting """
    
    def testfit_1Data_1Model(self):
        """ test fitting for one data and one model park vs scipy"""
        #load data
        from sans.fit.Loader import Load
        load= Load()
        load.set_filename("testdata_line.txt")
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
        #Do the fit SCIPY
       
        fitter.set_data_assembly(data1,1)
        fitter.set_model_assembly(model,"M1",1,['A','B'])
    
        result=fitter.fit()
        print "scipy",result.pvec,
        chisqr1, out1, cov1=fitter.fit()
        """ testing SCIPy results"""
        self.assert_(math.fabs(out1[1]-2.5)/math.sqrt(cov1[1][1]) < 2)
        self.assert_(math.fabs(out1[0]-4.0)/math.sqrt(cov1[0][0]) < 2)
        self.assert_(chisqr1/len(data1.x) < 2)
       
      