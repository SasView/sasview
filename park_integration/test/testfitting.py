"""
    Unit tests for fitting module 
"""
import unittest
from sans.guitools.plottables import Theory1D
from sans.guitools.plottables import Data1D
from FittingModule import Parameter
import math
class testFitModule(unittest.TestCase):
    """ test fitting """
    def testLoader(self):
        """ 
            test module Load
        """
        from Loader import Load
        load= Load()
        
        load.set_filename("testdata_line.txt")
        self.assertEqual(load.get_filename(),"testdata_line.txt")
        load.set_values()
        x=[]
        y=[]
        dx=[]
        dy=[]
        
        x,y,dx,dy = load.get_values()
        
        # test that values have been loaded
        self.assertNotEqual(x, None)
        self.assertNotEqual(y, [])
        self.assertNotEqual(dy, None)
        self.assertEqual(len(x),len(y))
        self.assertEqual(len(dy),len(y))
        
        # test data the two plottables contained values loaded
        data1 = Theory1D(x=[], y=[], dy=None)
        data2 = Data1D(x=[], y=[],dx=None, dy=None)
        data1.name = "data1"
        data2.name = "data2"
        load.load_data(data1)
        load.load_data(data2)
        
        
        for i in range(len(x)):
            self.assertEqual(data2.x[i],x[i])
            self.assertEqual(data1.y[i],y[i])
            self.assertEqual(data2.y[i],y[i])
            self.assertEqual(data1.dx[i],dx[i])
            self.assertEqual(data2.dy[i],dy[i])
            self.assertEqual(data1.x[i],data2.x[i])
            self.assertEqual(data2.y[i],data2.y[i])
            
           
    def testfit_1Data_1Model(self):
        """ test fitting for one data and one model"""
        #load data
        from Loader import Load
        load= Load()
        load.set_filename("testdata_line.txt")
        load.set_values()
        data1 = Data1D(x=[], y=[],dx=None, dy=None)
        load.load_data(data1)
        
        #Importing the Fit module
        from FittingModule import Fitting
        Fit= Fitting()
        # Receives the type of model for the fitting
        from sans.guitools.LineModel import LineModel
        model  = LineModel()
        
        #Do the fit
        Fit.set_data(data1,1)
        Fit.set_model(model,1)
        chisqr, out, cov=Fit.fit({'A':2,'B':1},None,None)
        #print"fit only one data",chisqr, out, cov   
        #Testing results
        self.assertEqual(Fit.fit_engine("scipy"),True)
        self.assert_(math.fabs(out[1]-2.5)/math.sqrt(cov[1][1]) < 2)
        self.assert_(math.fabs(out[0]-4.0)/math.sqrt(cov[0][0]) < 2)
        self.assert_(chisqr/len(data1.x) < 2)
        
        #print "chisqr",chisqr/len(data1.x)
        #print "Error on A",math.fabs(out[1]-2.5)/math.sqrt(cov[1][1])
        #print "Error on B",math.fabs(out[0]-4.0)/math.sqrt(cov[0][0])
        
    def testfit_2Data_1Model(self):
        """ test fitting for two set of data data and one model"""
        from Loader import Load
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
        from FittingModule import Fitting
        Fit= Fitting()
        # Receives the type of model for the fitting
        from sans.guitools.LineModel import LineModel
        model  = LineModel()
        
        #Do the fit
        Fit.set_data(data1,1)
        Fit.set_model(model,1)
        
        Fit.set_data(data2,2)
        Fit.set_model(model,2)
        
        chisqr, out, cov=Fit.fit({'A':2,'B':1},None,None)
        #print"fit only one data",chisqr, out, cov
        
        #Testing results
        self.assertEqual(Fit.fit_engine("scipy"),True)
        self.assert_(math.fabs(out[1]-2.5)/math.sqrt(cov[1][1]) < 2)
        self.assert_(math.fabs(out[0]-4.0)/math.sqrt(cov[0][0]) < 2)
        self.assert_(chisqr/len(data1.x) < 2)
        