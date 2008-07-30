"""
    Unit tests for fitting module 
"""
import unittest
from sans.guitools.plottables import Theory1D
from sans.guitools.plottables import Data1D

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
        data1 = Data1D(x=[], y=[],dx=None, dy=None)
        load.load_data(data1)
        
        load.set_filename("testdata_line1.txt")
        load.set_values()
        data2 = Data1D(x=[], y=[],dx=None, dy=None)
        load.load_data(data2)
        
        #Importing the Fit module
        from sans.fit.Fitting import Fit
        fitter= Fit('park')
        
        # Receives the type of model for the fitting
        from sans.models.CylinderModel import CylinderModel
        model1  = CylinderModel()
        model2  = CylinderModel()
        
        #Do the fit SCIPY
        fitter.set_data(data1,1)
        fitter.set_model(model1,"M1",1,)
        
        fitter.set_data(data2,2)
        fitter.set_model(model1,"M1",2,None)
        
        chisqr1, out1, cov1=fitter.fit()
        print "park",chisqr1, out1, cov1
        self.assert_(chisqr1)
        
       
      