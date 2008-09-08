"""
    Unit tests for fitting module 
"""
import unittest
from sans.guitools.plottables import Theory1D
from sans.guitools.plottables import Data1D
from sans.fit.ScipyFitting import Parameter
import math
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename='test_log.txt',
                    filemode='w')
class testFitModule(unittest.TestCase):
    def test0(self):
        """ test fitting for two set of data  and 2 models no constraint"""
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
        
        model2.setParam( 'A', 1)
        model2.setParam( 'B', 1)
        fitter.set_model(model2,"M2",2, ['A','B'])
        fitter.set_data(data2,2)
    
        
        chisqr1, out1, cov1,result= fitter.fit()
        print "chisqr1",chisqr1
        print "out1", out1
        print " cov1", cov1
        self.assert_(chisqr1)
        
    def test01(self):
        """ test fitting for two set of data  and 2 models and 2 constraints set on on model"""
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
        model1.setParam( 'B', 1)
        fitter.set_model(model1,"M1",1, ['A','B'])
        fitter.set_data(data1,1)
        
        model2.setParam( 'A','M1.A')
        model2.setParam( 'B', 'M1.B')
        fitter.set_model(model2,"M2",2, ['A','B'])
        fitter.set_data(data2,2)
    
        
        chisqr1, out1, cov1= fitter.fit()
        print "chisqr1",chisqr1
        print "out1", out1
        print " cov1", cov1
        self.assert_(chisqr1)
      
    
    
    def test1(self):
        """ test fitting for two set of data 2 model on constraint set on 1 model"""
        from sans.fit.Loader import Load
        load= Load()
        #Load the first set of data
        load.set_filename("testdata_line.txt")
        load.set_values()
        data1 = Data1D(x=[], y=[],dx=None, dy=None)
        load.load_data(data1)
        
        #Load the second set of data
        load.set_filename("testdata_line1.txt")
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
        model1.setParam( 'A',1)
        model1.setParam( 'B',1)
        fitter.set_model(model1,"M1",1, ['A','B'])
        fitter.set_data(data1,1)
        
        model2.setParam( 'A','M1.A')
        model2.setParam( 'B', 1)
        fitter.set_model(model2,"M2",2, ['A','B'])
        fitter.set_data(data2,2)
    
        
        chisqr1, out1, cov1= fitter.fit()
        print "chisqr1",chisqr1
        print "out1", out1
        print " cov1", cov1
        self.assert_(chisqr1)
      
    
    def test2(self):
        """ test fitting for two data 2 model not equal nombre of parameters fit"""
        from sans.fit.Loader import Load
        load= Load()
        #Load the first set of data
        load.set_filename("testdata_line.txt")
        load.set_values()
        data1 = Data1D(x=[], y=[],dx=None, dy=None)
        load.load_data(data1)
        
        #Load the second set of data
        load.set_filename("testdata_line1.txt")
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
        model1.setParam( 'A',1)
        model1.setParam( 'B',1)
        fitter.set_model(model1,"M1",1, ['A','B'])
        fitter.set_data(data1,1)
        
        model2.setParam( 'A',1)
       
        fitter.set_model(model2,"M2",2, ['A'])
        fitter.set_data(data2,2)
    
        
        chisqr1, out1, cov1= fitter.fit()
        print "chisqr1",chisqr1
        print "out1", out1
        print " cov1", cov1
        self.assert_(chisqr1)
        
       
        
       
    
      