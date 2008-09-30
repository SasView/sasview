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
        """ Fit 1 data (testdata_line.txt)and 1 model(lineModel) """
        #load data
        from DataLoader.loader import Loader
        data1 = Loader().load("testdata_line.txt")
        #Importing the Fit module
        from sans.fit.Fitting import Fit
        fitter = Fit('scipy')
        # Receives the type of model for the fitting
        from sans.guitools.LineModel import LineModel
        model1  = LineModel()
        model1.name = "M1"
        data = Data(sans_data=data1 )
        model = Model(model1)
        #fit with scipy test
        
        pars1= ['param1','param2']
        fitter.set_data(data,1)
        try:fitter.set_model(model,1,pars1)
        except ValueError,msg:
           assert str(msg)=="wrong paramter %s used to set model %s. Choose\
                            parameter name within %s"%('param1', model.model.name,str(model.model.getParamList()))
        else: raise AssertError,"No error raised for scipy fitting with wrong parameters name to fit"
        pars1= ['A','B']
        fitter.set_model(model,1,pars1)
        fitter.select_problem_for_fit(Uid=1,value=1)
        result1 = fitter.fit()
        self.assert_(result1)
        
        self.assertTrue( ( math.fabs(result1.pvec[0]-4)/3 == result1.stderr[0] ) or 
                         ( math.fabs(result1.pvec[0]-4)/3 < result1.stderr[0]) ) 
        
        self.assertTrue( ( math.fabs(result1.pvec[1]-2.5)/3 == result1.stderr[1]) or
                         ( math.fabs(result1.pvec[1]-2.5)/3 < result1.stderr[1] ) )
        self.assertTrue( result1.fitness/49 < 2 )
        
        #fit with park test
        fitter = Fit('park')
        fitter.set_data(data,1)
        fitter.set_model(model,1,pars1)
        fitter.select_problem_for_fit(Uid=1,value=1)
        result2 = fitter.fit()
        
        self.assert_(result2)
        
        self.assertTrue( ( math.fabs(result2.pvec[0]-4)/3 == result2.stderr[0] ) or 
                         ( math.fabs(result2.pvec[0]-4)/3 < result2.stderr[0]) ) 
        
        self.assertTrue( ( math.fabs(result2.pvec[1]-2.5)/3 == result2.stderr[1] ) or
                         ( math.fabs(result2.pvec[1]-2.5)/3 < result2.stderr[1]) )
        self.assertTrue(result2.fitness/49 < 2)
        # compare fit result result for scipy and park
        self.assertAlmostEquals( result1.pvec[0], result2.pvec[0] )
        self.assertAlmostEquals( result1.pvec[1],result2.pvec[1] )
        self.assertAlmostEquals( result1.stderr[0],result2.stderr[0] )
        self.assertAlmostEquals( result1.stderr[1],result2.stderr[1] )
        self.assertAlmostEquals( result1.fitness,result2.fitness )
        
    def test2(self):
        """ fit 2 data and 2 model with no constrainst"""
        #load data
        from DataLoader.loader import Loader
        l = Loader()
        out=l.load("testdata_line.txt")
        data11 = Data1D(x=out.x, y=out.y, dx=out.dx, dy=out.y)
        out=l.load("testdata_line1.txt")
        data22 = Data1D(x=out.x, y=out.y, dx=out.dx, dy=out.y)
        #Importing the Fit module
        from sans.fit.Fitting import Fit
        fitter = Fit('scipy')
        # Receives the type of model for the fitting
        from sans.guitools.LineModel import LineModel
        model11  = LineModel()
        model11.name= "M1"
        model22  = LineModel()
        model11.name= "M2"
        data1 = Data(sans_data=data11 )
        data2 = Data(sans_data=data22 )
        model1 = Model(model11)
        model2 = Model(model22)
        #fit with scipy test
        pars1= ['A','B']
        fitter.set_data(data1,1)
        fitter.set_model(model1,1,pars1)
        fitter.select_problem_for_fit(Uid=1,value=0)
        fitter.set_data(data2,2)
        fitter.set_model(model2,2,pars1)
        fitter.select_problem_for_fit(Uid=2,value=0)
        
        try: result1 = fitter.fit()
        except RuntimeError,msg:
           assert str(msg)=="No Assembly scheduled for Scipy fitting."
        else: raise AssertError,"No error raised for scipy fitting with no model"
        fitter.select_problem_for_fit(Uid=1,value=1)
        fitter.select_problem_for_fit(Uid=2,value=1)
        try: result1 = fitter.fit()
        except RuntimeError,msg:
           assert str(msg)=="Scipy can't fit more than a single fit problem at a time."
        else: raise AssertError,"No error raised for scipy fitting with more than 2 models"
        
        #fit with park test
        fitter = Fit('park')
        fitter.set_data(data1,1)
        fitter.set_model(model1,1,pars1)
        fitter.set_data(data2,2)
        fitter.set_model(model2,2,pars1)
        fitter.select_problem_for_fit(Uid=1,value=1)
        fitter.select_problem_for_fit(Uid=2,value=1)
        result2 = fitter.fit()
        
        self.assert_(result2)
        self.assertTrue( ( math.fabs(result2.pvec[0]-4)/3 == result2.stderr[0] ) or 
                         ( math.fabs(result2.pvec[0]-4)/3 < result2.stderr[0]) ) 
        
        self.assertTrue( ( math.fabs(result2.pvec[1]-2.5)/3 == result2.stderr[1] ) or
                         ( math.fabs(result2.pvec[1]-2.5)/3 < result2.stderr[1]) )
        self.assertTrue(result2.fitness/49 < 2)
        
        
    def test3(self):
        """ fit 2 data and 2 model with 1 constrainst"""
        #load data
        from DataLoader.loader import Loader
        l = Loader()
        out=l.load("testdata_line.txt")
        data11 = Data1D(x=out.x, y=out.y, dx=out.dx, dy=out.y)
        out=l.load("testdata_cst.txt")
        data22 = Data1D(x=out.x, y=out.y, dx=out.dx, dy=out.y)
        #Importing the Fit module
        from sans.fit.Fitting import Fit
        fitter = Fit('park')
        # Receives the type of model for the fitting
        from sans.guitools.LineModel import LineModel
        from sans.models.Constant import Constant
        model11  = LineModel()
        model11.name= "line"
       
        model22  = Constant()
        model22.name= "cst"
        # Constrain the constant value to be equal to parameter B (the real value is 2.5)
        
        
        data1 = Data(sans_data=data11 )
        data2 = Data(sans_data=data22 )
        model1 = Model(model11)
        model2 = Model(model22)
        model1.set(A=4)
        model1.set(B=3)
        model2.set(value='line.B')
        #fit with scipy test
        pars1= ['A','B']
        pars2= ['value']
        
        fitter.set_data(data1,1)
        fitter.set_model(model1,1,pars1)
        fitter.set_data(data2,2)
        fitter.set_model(model2,2,pars2)
        fitter.select_problem_for_fit(Uid=1,value=1)
        fitter.select_problem_for_fit(Uid=2,value=1)
        
        result2 = fitter.fit()
        self.assert_(result2)
        self.assertTrue( ( math.fabs(result2.pvec[0]-4.0)/3. < result2.stderr[0]) ) 
        
        self.assertTrue( ( math.fabs(result2.pvec[1]-2.5)/3. < result2.stderr[1]) )
        self.assertTrue(result2.fitness/49 < 2)
        
        
    def test4(self):
        """ fit 2 data concatenates with limited range of x and  one model """
            #load data
        from DataLoader.loader import Loader
        l = Loader()
        out=l.load("testdata_line.txt")
        data11 = Data1D(x=out.x, y=out.y, dx=out.dx, dy=out.y)
        out=l.load("testdata_line1.txt")
        data22 = Data1D(x=out.x, y=out.y, dx=out.dx, dy=out.y)
        #Importing the Fit module
        from sans.fit.Fitting import Fit
        fitter = Fit('scipy')
        # Receives the type of model for the fitting
        from sans.guitools.LineModel import LineModel
        model1  = LineModel()
        model1.name= "M1"
      
        data1 = Data(sans_data=data11 )
        data2 = Data(sans_data=data22 )
        model = Model(model1)
        
        #fit with scipy test
        pars1= ['A','B']
        fitter.set_data(data1,1,qmin=0, qmax=7)
        fitter.set_model(model,1,pars1)
        fitter.set_data(data2,1,qmin=1,qmax=10)
        fitter.select_problem_for_fit(Uid=1,value=1)
        
        result1 = fitter.fit()
        self.assert_(result1)

        self.assertTrue( ( math.fabs(result1.pvec[0]-4)/3 == result1.stderr[0] ) or 
                         ( math.fabs(result1.pvec[0]-4)/3 < result1.stderr[0]) ) 
        
        self.assertTrue( ( math.fabs(result1.pvec[1]-2.5)/3 == result1.stderr[1]) or
                         ( math.fabs(result1.pvec[1]-2.5)/3 < result1.stderr[1] ) )
        self.assertTrue( result1.fitness/49 < 2 )
        
        
        #fit with park test
        fitter = Fit('park')
        fitter.set_data(data1,1,qmin=0, qmax=7)
        fitter.set_model(model,1,pars1)
        fitter.set_data(data2,1,qmin=1,qmax=10)
        fitter.select_problem_for_fit(Uid=1,value=1)
        result2 = fitter.fit()
        
        self.assert_(result2)
        self.assertTrue( ( math.fabs(result2.pvec[0]-4)/3 == result2.stderr[0] ) or 
                         ( math.fabs(result2.pvec[0]-4)/3 < result2.stderr[0]) ) 
        
        self.assertTrue( ( math.fabs(result2.pvec[1]-2.5)/3 == result2.stderr[1] ) or
                         ( math.fabs(result2.pvec[1]-2.5)/3 < result2.stderr[1]) )
        self.assertTrue(result2.fitness/49 < 2)
        # compare fit result result for scipy and park
        self.assertAlmostEquals( result1.pvec[0], result2.pvec[0] )
        self.assertAlmostEquals( result1.pvec[1],result2.pvec[1] )
        self.assertAlmostEquals( result1.stderr[0],result2.stderr[0] )
        self.assertAlmostEquals( result1.stderr[1],result2.stderr[1] )
        self.assertAlmostEquals( result1.fitness,result2.fitness )
    