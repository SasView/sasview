"""
    Unit tests for fitting module 
"""
import unittest
from sans.guitools.plottables import Theory1D
from sans.guitools.plottables import Data1D
from sans.fit.ScipyFitting import Parameter
import math
class testFitModule(unittest.TestCase):
    
    def test2models2dataonconstraint(self):
        """ test fitting for two set of data  and one model with 2 constraint"""
        from sans.fit.Loader import Load
        load= Load()
        #Load the first set of data
        load.set_filename("testdata1.txt")
        load.set_values()
        data1 = Data1D(x=[], y=[],dx=None, dy=None)
        load.load_data(data1)
        
        #Load the second set of data
        load.set_filename("testdata2.txt")
        load.set_values()
        data2 = Data1D(x=[], y=[],dx=None, dy=None)
        load.load_data(data2)
        
        #Importing the Fit module
        from sans.fit.Fitting import Fit
        fitter= Fit('park')
        # Receives the type of model for the fitting
        from sans.guitools.LineModel import LineModel
        model1  = LineModel()
        model2  = LineModel()
        
        #Do the fit
        model1.setParam( 'A', 1)
        model1.setParam( 'B', 2)
        fitter.set_model(model1,"M1",1, ['A','B'])
        fitter.set_data(data1,1)
        
        model2.setParam( 'A', 'M1.A')
        model2.setParam( 'B','M1.B')
        fitter.set_model(model2,"M2",2, ['A','B'])
        fitter.set_data(data2,2)
    
        
        chisqr2, out2, cov2,result= fitter.fit()
        print "chisqr2",chisqr2
        print "out2", out2
        print " cov2", cov2
        print chisqr2/len(data1.x)
        
        self.assert_(math.fabs(out2[1]-2.5)/math.sqrt(cov2[1][1]) < 2)
        self.assert_(math.fabs(out2[0]-4.0)/math.sqrt(cov2[0][0]) < 2)
        #self.assert_(chisqr2/len(data1.x) < 2)
        #self.assert_(chisqr2/len(data2.x) < 2)
    def testmodel1data1param1(self):
        """ test fitting for two set of data  and one model with 2 constraint"""
        from sans.fit.Loader import Load
        load= Load()
        #Load the first set of data
        load.set_filename("testdata1.txt")
        load.set_values()
        data1 = Data1D(x=[], y=[],dx=None, dy=None)
        load.load_data(data1)
        
        #Load the second set of data
        load.set_filename("testdata2.txt")
        load.set_values()
        data2 = Data1D(x=[], y=[],dx=None, dy=None)
        load.load_data(data2)
        
        #Importing the Fit module
        from sans.fit.Fitting import Fit
        fitter= Fit('park')
        # Receives the type of model for the fitting
        from sans.guitools.LineModel import LineModel
        model1  = LineModel()
       
        
        #Do the fit
        model1.setParam( 'A', 1)
        fitter.set_model(model1,"M1",1, ['A'])
        fitter.set_data(data1,1)
       
     
        
        chisqr2, out2, cov2,result = fitter.fit()
        print "chisqr2",chisqr2
        print "out2", out2
        print " cov2", cov2
        print chisqr2/len(data1.x)
        
        self.assert_(math.fabs(out2[1]-2.5)/math.sqrt(cov2[1][1]) < 2)
        self.assert_(math.fabs(out2[0]-4.0)/math.sqrt(cov2[0][0]) < 2)
        #self.assert_(chisqr2/len(data1.x) < 2)
        #self.assert_(chisqr2/len(data2.x) < 2)
    