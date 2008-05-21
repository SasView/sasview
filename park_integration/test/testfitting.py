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
            
           
    def testfit(self):
        """ test fitting"""
        from Loader import Load
        load= Load()
        load.set_filename("testdata_line.txt")
        load.set_values()
        x,y,dx,dy = load.get_values()
        data1 = Data1D(x=[], y=[],dx=None, dy=None)
        load.load_data(data1)
        
        # Receives the type of model for the fitting
        from sans.guitools.LineModel import LineModel
        model  = LineModel()
        
        from FittingModule import Fitting
        Fit= Fitting()
        Fit.set_data(data1)
        Fit.set_model(model)
        
        default_A = model.getParam('A') 
        default_B = model.getParam('B') 
        cstA = Parameter(model, 'A', default_A)
        cstB  = Parameter(model, 'B', default_B)
        chisqr, out, cov=Fit.fit([cstA,cstB],None,None)
        print"fit only one data",chisqr, out, cov   
       
        self.assertEqual(Fit.fit_engine(),True)
        
        self.assert_(math.fabs(out[1]-2.5)/math.sqrt(cov[1][1]) < 2)
        print "chisqr",chisqr/len(data1.x)
        self.assert_(chisqr/len(data1.x) < 2)
#        self.assertAlmostEqual(out[1],2.5)
        #self.assertAlmostEquals(out[0],4.0)
        #self.assertAlmostEquals(out[1]+cov[1][1],2.5)
        #self.assertAlmostEquals(out[0]+cov[0][0],4.0)
        