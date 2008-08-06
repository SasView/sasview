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
        load.set_filename("cyl_testdata.txt")
        load.set_values()
        data1 = Data1D(x=[], y=[],dx=None, dy=None)
        load.load_data(data1)
       
        
        #Importing the Fit module
        from sans.fit.Fitting import Fit
        fitter= Fit('scipy')
        
        # Receives the type of model for the fitting
        from sans.models.CylinderModel import CylinderModel
        model1  = CylinderModel()
      
        
        #Do the fit SCIPY
        fitter.set_data(data1,1)
        import math
        pars1={'background':0,'contrast':3*math.pow(10, -6),\
                'cyl_phi':1,'cyl_theta':1,'length':400,'radius':20,'scale':1}
        fitter.set_model(model1,"M1",1,pars1)
       
        
        chisqr1, out1, cov1=fitter.fit()
        print "scipy1",chisqr1, out1, cov1
        pars2={'background':1.0,'contrast':400,\
                'cyl_phi':20,'cyl_theta':0.0,'length':1.0,\
                'radius':3*math.pow(10, -6),'scale':1.0}
        fitter.set_model(model1,"M1",1,pars2)
        chisqr2, out2, cov2=fitter.fit()
        print "scipy2",chisqr2, out2, cov2
        
        pars3={'background':5.85693826,'contrast': 5.86071451,\
                'cyl_phi':1.04547760*math.pow(10,-5),'cyl_theta':1.0,'length':0.0,\
                'radius':1.39397013*math.pow(10, 3),'scale':20}
        fitter.set_model(model1,"M1",1,pars3)
        chisqr3, out3, cov3=fitter.fit()
        print "scipy3",chisqr3, out3, cov3
        self.assert_(chisqr1)
        
       
      
    def testfit_11Data_1Model(self):
        """ test fitting for one data and one model park vs scipy"""
        #load data
        from sans.fit.Loader import Load
        load= Load()
        load.set_filename("cyl_testdata.txt")
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
        #model2  = CylinderModel()
        
        #Do the fit SCIPY
        fitter.set_data(data1,1)
        import math
        pars1={'background':0,'contrast':3*math.pow(10, -6),\
                'cyl_phi':1,'cyl_theta':1,'length':400,'radius':20,'scale':1}
        fitter.set_model(model1,"M1",1,pars1)
        
        #fitter.set_data(data2,2)
        #fitter.set_model(model1,"M1",2,pars1)
        
        chisqr1, out1, cov1=fitter.fit()
        print "park",chisqr1, out1, cov1
        self.assert_(chisqr1)
        
       
      