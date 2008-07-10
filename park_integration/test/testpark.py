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
        """ test fitting for two set of data  and one model"""
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
        fitter.set_model(model1,"M1",1, {'A':2.5,'B':4})
        fitter.set_data(data1,1)
        
        fitter.set_model(model2,"M2",2, {'A':2,'B':3})
        fitter.set_data(data2,2)
        
        chisqr1, out1, cov1= fitter.fit()
        
        self.assert_(math.fabs(out1[1]-2.5)/math.sqrt(cov1[1][1]) < 2)
        print math.fabs(out1[0]-4.0)/math.sqrt(cov1[0][0])
        #self.assert_(math.fabs(out1[0]-4.0)/math.sqrt(cov1[0][0]) < 2)
        self.assert_(math.fabs(out1[3]-2.5)/math.sqrt(cov1[3][3]) < 2)
        self.assert_(math.fabs(out1[2]-4.0)/math.sqrt(cov1[2][2]) < 2)
        print chisqr1/len(data1.x)
        #self.assert_(chisqr1/len(data1.x) < 2)
        print chisqr1/len(data2.x)
        #self.assert_(chisqr2/len(data2.x) < 2)
        
        
        fitter.set_data(data3,1)
        chisqr2, out2, cov2= fitter.fit(None,None)
        self.assert_(math.fabs(out2[1]-2.5)/math.sqrt(cov2[1][1]) < 2)
        print math.fabs(out2[0]-4.0)/math.sqrt(cov2[0][0])
        #self.assert_(math.fabs(out1[0]-4.0)/math.sqrt(cov1[0][0]) < 2)
        self.assert_(math.fabs(out2[3]-2.5)/math.sqrt(cov2[3][3]) < 2)
        self.assert_(math.fabs(out2[2]-4.0)/math.sqrt(cov2[2][2]) < 2)
        print chisqr2/len(data1.x)
        #self.assert_(chisqr1/len(data1.x) < 2)
        print chisqr2/len(data2.x)
        #self.assert_(chisqr2/len(data2.x) < 2)
        
        fitter.remove_Fit_Problem(2)
        
        chisqr3, out3, cov3= fitter.fit()
        #print "park",chisqr3, out3, cov3
        self.assert_(math.fabs(out1[1]-2.5)/math.sqrt(cov1[1][1]) < 2)
        print math.fabs(out1[0]-4.0)
        #self.assert_(math.fabs(out1[0]-4.0)/math.sqrt(cov1[0][0]) < 2)
        print chisqr1/len(data1.x)
        #self.assert_(chisqr1/len(data1.x) < 2)
        #self.assert_(chisqr1/len(data2.x) < 2)
        #failing at 7 place
        self.assertAlmostEquals(out3[1],out1[1])
        self.assertAlmostEquals(out3[0],out1[0])
        self.assertAlmostEquals(cov3[1][1],cov1[1][1])
        self.assertAlmostEquals(cov3[0][0],cov1[0][0])
        
        self.assertAlmostEquals(out2[1],out1[1])
        self.assertAlmostEquals(out2[0],out1[0])
        self.assertAlmostEquals(cov2[1][1],cov1[1][1])
        self.assertAlmostEquals(cov2[0][0],cov1[0][0])
        
        self.assertAlmostEquals(out2[1],out3[1])
        self.assertAlmostEquals(out2[0],out3[0])
        self.assertAlmostEquals(cov2[1][1],cov3[1][1])
        self.assertAlmostEquals(cov2[0][0],cov3[0][0])
        print chisqr1,chisqr2,chisqr3
        #self.assertAlmostEquals(chisqr1,chisqr2)