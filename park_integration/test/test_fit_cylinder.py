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
    def test1(self):
        """ Fit 1 data (cyl_testdata.txt)and 1 model(CylinderModel)  """
        #load data
        from sans.fit.Loader import Load
        load = Load()
        load.set_filename("cyl_testdata.txt")
        load.set_values()
        data1 = Data1D(x=[], y=[],dx=None, dy=None)
        load.load_data(data1)
        #Importing the Fit module
        from sans.fit.Fitting import Fit
        fitter = Fit('scipy')
        # Receives the type of model for the fitting
        from sans.models.CylinderModel import CylinderModel
        model1  = CylinderModel()
        model1.setParam('contrast',1)
        data = Data(sans_data=data1 )
        model = Model(model1)
        
        pars1 =['length','radius','scale']
        fitter.set_data(data,1)
        model.model.setParam('scale',10)
        fitter.set_model(model,"M1",1,pars1)
        result1 = fitter.fit()
        print "test scipy result:",result1.stderr,result1.pvec,result1.fitness
        self.assert_(result1)
        self.assertTrue(len(result1.pvec)>0 or len(result1.pvec)==0 )
        self.assertTrue(len(result1.stderr)> 0 or len(result1.stderr)==0)
        self.assertAlmostEquals( result1.pvec[0],0 )
        self.assertAlmostEquals( result1.pvec[1],3*math.pow(10,-6) )
        self.assertAlmostEquals( result1.pvec[2] , 1 )
        self.assertAlmostEquals( result1.pvec[3] , 1 )
        self.assertAlmostEquals( result1.pvec[4] , 400 )
        self.assertAlmostEquals( result1.pvec[5] , 20 )
        self.assertAlmostEquals ( result1.pvec[6] , 1 )
        self.assertTrue( result1.fitness/43 < 2 )
        
       