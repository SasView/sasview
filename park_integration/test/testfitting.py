"""
    Unit tests for fitting module 
"""
import unittest
from sans.guitools.plottables import Theory1D
from sans.guitools.plottables import Data1D
from sans.fit.ScipyFitting import Parameter
import math
class testFitModule(unittest.TestCase):
    """ test fitting """
    def testLoader(self):
        """ 
            test module Load
        """
        from sans.fit.Loader import Load
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
        from sans.fit.Loader import Load
        load= Load()
        load.set_filename("testdata_line.txt")
        load.set_values()
        data1 = Data1D(x=[], y=[],dx=None, dy=None)
        load.load_data(data1)
        
        #Importing the Fit module
        from sans.fit.Fitting import Fit
        fitter= Fit()
        fitter.fit_engine('scipy')
        engine = fitter.returnEngine()
        # Receives the type of model for the fitting
        from sans.guitools.LineModel import LineModel
        model  = LineModel()
        
        #Do the fit SCIPY
        engine.set_data(data1,1)
        engine.set_model(model,1)
        
        chisqr1, out1, cov1=engine.fit({'A':2,'B':1},None,None)
        """ testing SCIPy results"""
        self.assert_(math.fabs(out1[1]-2.5)/math.sqrt(cov1[1][1]) < 2)
        self.assert_(math.fabs(out1[0]-4.0)/math.sqrt(cov1[0][0]) < 2)
        self.assert_(chisqr1/len(data1.x) < 2)
        # PARK
        fitter= Fit()
        fitter.fit_engine('park')
        engine = fitter.returnEngine()
        
        #Do the fit
        engine.set_data(data1,1)
        engine.set_model(model,1)
       
        engine.fit({'A':2,'B':1},None,None)
        """
            
            self.assert_(math.fabs(out2[1]-2.5)/math.sqrt(cov2[1][1]) < 2)
            self.assert_(math.fabs(out2[0]-4.0)/math.sqrt(cov2[0][0]) < 2)
            self.assert_(chisqr2/len(data1.x) < 2)
            
            self.assertEqual(out1[1], out2[1])
            self.assertEquals(out1[0], out2[0])
            self.assertEquals(cov1[0][0], cov2[0][0])
            self.assertEquals(cov1[1][1], cov2[1][1])
            self.assertEquals(chisqr1, chisqr2)
        """
    def testfit_2Data_1Model(self):
        """ test fitting for two set of data  and one model"""
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
        fitter= Fit()
        # Receives the type of model for the fitting
        from sans.guitools.LineModel import LineModel
        model  = LineModel()
        #set engine for scipy 
        fitter.fit_engine('scipy')
        engine = fitter.returnEngine()
        #Do the fit
        engine.set_model(model,1)
        engine.set_data(data1,1)
        engine.set_data(data2,1)
    
        
        chisqr1, out1, cov1= engine.fit({'A':2,'B':1},None,None)
      
        """ Testing results for SCIPY"""
        self.assert_(math.fabs(out1[1]-2.5)/math.sqrt(cov1[1][1]) < 2)
        self.assert_(math.fabs(out1[0]-4.0)/math.sqrt(cov1[0][0]) < 2)
        self.assert_(chisqr1/len(data1.x+data2.x) < 2)
        #self.assert_(chisqr1/len(data2.x) < 2)
        
        #set engine for park 
        fitter= Fit()
        fitter.fit_engine('park')
        engine = fitter.returnEngine()
        #Do the fit
        engine.set_data(data1,1)
        engine.set_model(model,1)
        engine.set_data(data2,1)
        engine.fit({'A':2,'B':1},None,None)
        """
            chisqr2, out2, cov2= engine.fit({'A':2,'B':1},None,None)
            
            
            self.assert_(math.fabs(out2[1]-2.5)/math.sqrt(cov2[1][1]) < 2)
            self.assert_(math.fabs(out2[0]-4.0)/math.sqrt(cov2[0][0]) < 2)
            self.assert_(chisqr2/len(data1.x) < 2)
            self.assert_(chisqr2/len(data2.x) < 2)
            
            self.assertEqual(out1[0],out2[0])
            self.assertEqual(out1[1],out2[1])
            self.assertEqual(chisqr1,chisqr2)
            self.assertEqual(cov1[0][0],cov2[0][0])
            self.assertEqual(cov1[1][1],cov2[1][1])
        """