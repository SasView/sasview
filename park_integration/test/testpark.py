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
        model1  = LineModel()
        model2  = LineModel()
        #set engine for scipy 
        fitter.fit_engine('park')
        engine = fitter.returnEngine()
        #Do the fit
        engine.set_param( model1,"M1", {'A':2.5,'B':4})
        engine.set_model(model1,1)
        engine.set_data(data1,1)
        
        import numpy
        #print engine.fit({'A':2,'B':1},None,None)
        #engine.remove_data(2,data2)
        #engine.remove_model(2)
        
        engine.set_param( model2,"M2", {'A':2.5,'B':4})
        engine.set_model(model2,2)
        engine.set_data(data2,2)
        print engine.fit({'A':2,'B':1},None,None)

        if True:
            import pylab
            x1 = engine.problem[0].data.x
            x2 = engine.problem[1].data.x
            y1 = engine.problem[0].data.y
            y2 = engine.problem[1].data.y
            fx1 = engine.problem[0].data.fx
            fx2 = engine.problem[1].data.fx
            pylab.plot(x1,y1,'xb',x1,fx1,'-b',x2,y2,'xr',x2,fx2,'-r')
            pylab.show()
        if False:
            print "current"
            print engine.problem.chisq
            print engine.problem.residuals
            print "M1.y",engine.problem[0].data.y
            print "M1.fx",engine.problem[0].data.fx
            print "M1 delta",numpy.asarray(engine.problem[0].data.y)-engine.problem[0].data.fx
            print "M2.y",engine.problem[0].data.y
            print "M2.fx",engine.problem[0].data.fx
            print "M2 delta",numpy.asarray(engine.problem[1].data.y)-engine.problem[1].data.fx
            print "target"
            engine.problem(numpy.array([4,2.5,4,2.5]))
            print engine.problem.chisq
            print engine.problem.residuals
            print "M1.y",engine.problem[0].data.y
            print "M1.fx",engine.problem[0].data.fx
            print "M1 delta",numpy.asarray(engine.problem[0].data.y)-engine.problem[0].data.fx
            print "M2.y",engine.problem[0].data.y
            print "M2.fx",engine.problem[0].data.fx
            print "M2 delta",numpy.asarray(engine.problem[1].data.y)-engine.problem[1].data.fx
            