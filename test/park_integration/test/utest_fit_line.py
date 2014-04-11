"""
    Unit tests for fitting module 
    @author Gervaise Alina
"""
import unittest
import math

from sans.fit.AbstractFitEngine import Model, FitHandler
from sans.dataloader.loader import Loader
from sans.fit.Fitting import Fit
from sans.models.LineModel import LineModel
from sans.models.Constant import Constant

class testFitModule(unittest.TestCase):
    """ test fitting """

    def test_bad_pars(self):
        fitter = Fit('bumps')

        data = Loader().load("testdata_line.txt")
        data.name = data.filename
        fitter.set_data(data,1)

        model1  = LineModel()
        model1.name = "M1"
        model = Model(model1, data)
        pars1= ['param1','param2']
        try:
            fitter.set_model(model,1,pars1)
        except ValueError,exc:
            #print "ValueError was correctly raised: "+str(msg)
            assert str(exc).startswith('wrong parameter')
        else:
            raise AssertionError("No error raised for scipy fitting with wrong parameters name to fit")

    def fit_single(self, fitter_name, isdream=False):
        fitter = Fit(fitter_name)

        data = Loader().load("testdata_line.txt")
        data.name = data.filename
        fitter.set_data(data,1)

        # Receives the type of model for the fitting
        model1  = LineModel()
        model1.name = "M1"
        model = Model(model1,data)
        #fit with scipy test

        pars1= ['A','B']
        fitter.set_model(model,1,pars1)
        fitter.select_problem_for_fit(id=1,value=1)
        result1, = fitter.fit(handler=FitHandler())

        # The target values were generated from the following statements
        p,s,fx = result1.pvec, result1.stderr, result1.fitness
        #print "p0,p1,s0,s1,fx_ = %g, %g, %g, %g, %g"%(p[0],p[1],s[0],s[1],fx)
        p0,p1,s0,s1,fx_ = 3.68353, 2.61004, 0.336186, 0.105244, 1.20189

        if isdream:
            # Dream is not a minimizer: just check that the fit is within
            # uncertainty
            self.assertTrue( abs(p[0]-p0) <= s0 )
            self.assertTrue( abs(p[1]-p1) <= s1 )
        else:
            self.assertTrue( abs(p[0]-p0) <= 1e-5 )
            self.assertTrue( abs(p[1]-p1) <= 1e-5 )
            self.assertTrue( abs(fx-fx_) <= 1e-2 )

    def fit_bumps(self, alg, **opts):
        #Importing the Fit module
        from bumps import fitters
        fitters.FIT_DEFAULT = alg
        fitters.FIT_OPTIONS[alg].options.update(opts)
        fitters.FIT_OPTIONS[alg].options.update(monitors=[])
        #print "fitting",alg,opts
        #kprint "options",fitters.FIT_OPTIONS[alg].__dict__
        self.fit_single('bumps', isdream=(alg=='dream'))

    def test_bumps_de(self):
        self.fit_bumps('de')

    def test_bumps_dream(self):
        self.fit_bumps('dream', burn=500, steps=100)

    def test_bumps_amoeba(self):
        self.fit_bumps('amoeba')

    def test_bumps_newton(self):
        self.fit_bumps('newton')

    def test_scipy(self):
        #print "fitting scipy"
        self.fit_single('scipy')

    def test_park(self):
        #print "fitting park"
        self.fit_single('park')

        
    def test2(self):
        """ fit 2 data and 2 model with no constrainst"""
        #load data
        l = Loader()
        data1=l.load("testdata_line.txt")
        data1.name = data1.filename
      
        data2=l.load("testdata_line1.txt")
        data2.name = data2.filename
     
        #Importing the Fit module
        fitter = Fit('scipy')
        # Receives the type of model for the fitting
        model11  = LineModel()
        model11.name= "M1"
        model22  = LineModel()
        model11.name= "M2"
      
        model1 = Model(model11,data1)
        model2 = Model(model22,data2)
        #fit with scipy test
        pars1= ['A','B']
        fitter.set_data(data1,1)
        fitter.set_model(model1,1,pars1)
        fitter.select_problem_for_fit(id=1,value=0)
        fitter.set_data(data2,2)
        fitter.set_model(model2,2,pars1)
        fitter.select_problem_for_fit(id=2,value=0)
        
        try: result1, = fitter.fit(handler=FitHandler())
        except RuntimeError,msg:
           assert str(msg)=="No Assembly scheduled for Scipy fitting."
        else: raise AssertionError,"No error raised for scipy fitting with no model"
        fitter.select_problem_for_fit(id=1,value=1)
        fitter.select_problem_for_fit(id=2,value=1)
        try: result1, = fitter.fit(handler=FitHandler())
        except RuntimeError,msg:
           assert str(msg)=="Scipy can't fit more than a single fit problem at a time."
        else: raise AssertionError,"No error raised for scipy fitting with more than 2 models"

        #fit with park test
        fitter = Fit('park')
        fitter.set_data(data1,1)
        fitter.set_model(model1,1,pars1)
        fitter.set_data(data2,2)
        fitter.set_model(model2,2,pars1)
        fitter.select_problem_for_fit(id=1,value=1)
        fitter.select_problem_for_fit(id=2,value=1)
        R1,R2 = fitter.fit(handler=FitHandler())
        
        self.assertTrue( math.fabs(R1.pvec[0]-4)/3 <= R1.stderr[0] )
        self.assertTrue( math.fabs(R1.pvec[1]-2.5)/3 <= R1.stderr[1] )
        self.assertTrue( R1.fitness/(len(data1.x)+len(data2.x)) < 2)
        
        
    def test3(self):
        """ fit 2 data and 2 model with 1 constrainst"""
        #load data
        l = Loader()
        data1= l.load("testdata_line.txt")
        data1.name = data1.filename
        data2= l.load("testdata_cst.txt")
        data2.name = data2.filename
       
        # Receives the type of model for the fitting
        model11  = LineModel()
        model11.name= "line"
        model11.setParam("A", 1.0)
        model11.setParam("B",1.0)
        
        model22  = Constant()
        model22.name= "cst"
        model22.setParam("value", 1.0)
        
        model1 = Model(model11,data1)
        model2 = Model(model22,data2)
        model1.set(A=4)
        model1.set(B=3)
        # Constraint the constant value to be equal to parameter B (the real value is 2.5)
        model2.set(value='line.B')
        #fit with scipy test
        pars1= ['A','B']
        pars2= ['value']
        
        #Importing the Fit module
        fitter = Fit('park')
        fitter.set_data(data1,1)
        fitter.set_model(model1,1,pars1)
        fitter.set_data(data2,2,smearer=None)
        fitter.set_model(model2,2,pars2)
        fitter.select_problem_for_fit(id=1,value=1)
        fitter.select_problem_for_fit(id=2,value=1)
        
        R1,R2 = fitter.fit(handler=FitHandler())
        self.assertTrue( math.fabs(R1.pvec[0]-4.0)/3. <= R1.stderr[0])
        self.assertTrue( math.fabs(R1.pvec[1]-2.5)/3. <= R1.stderr[1])
        self.assertTrue( R1.fitness/(len(data1.x)+len(data2.x)) < 2)
        
        
    def test4(self):
        """ fit 2 data concatenates with limited range of x and  one model """
            #load data
        l = Loader()
        data1 = l.load("testdata_line.txt")
        data1.name = data1.filename
        data2 = l.load("testdata_line1.txt")
        data2.name = data2.filename

        # Receives the type of model for the fitting
        model1  = LineModel()
        model1.name= "M1"
        model1.setParam("A", 1.0)
        model1.setParam("B",1.0)
        model = Model(model1,data1)
      
        #fit with scipy test
        pars1= ['A','B']
        #Importing the Fit module
        fitter = Fit('scipy')
        fitter.set_data(data1,1,qmin=0, qmax=7)
        fitter.set_model(model,1,pars1)
        fitter.set_data(data2,1,qmin=1,qmax=10)
        fitter.select_problem_for_fit(id=1,value=1)
        
        result1, = fitter.fit(handler=FitHandler())
        #print(result1)
        self.assert_(result1)

        self.assertTrue( math.fabs(result1.pvec[0]-4)/3 <= result1.stderr[0] )
        self.assertTrue( math.fabs(result1.pvec[1]-2.5)/3 <= result1.stderr[1])
        self.assertTrue( result1.fitness/len(data1.x) < 2 )

        #fit with park test
        fitter = Fit('park')
        fitter.set_data(data1,1,qmin=0, qmax=7)
        fitter.set_model(model,1,pars1)
        fitter.set_data(data2,1,qmin=1,qmax=10)
        fitter.select_problem_for_fit(id=1,value=1)
        result2, = fitter.fit(handler=FitHandler())
        
        self.assert_(result2)
        self.assertTrue( math.fabs(result2.pvec[0]-4)/3 <= result2.stderr[0] )
        self.assertTrue( math.fabs(result2.pvec[1]-2.5)/3 <= result2.stderr[1] )
        self.assertTrue( result2.fitness/len(data1.x) < 2)
        # compare fit result result for scipy and park
        self.assertAlmostEquals( result1.pvec[0], result2.pvec[0] )
        self.assertAlmostEquals( result1.pvec[1],result2.pvec[1] )
        self.assertAlmostEquals( result1.stderr[0],result2.stderr[0] )
        self.assertAlmostEquals( result1.stderr[1],result2.stderr[1] )
        self.assertTrue( result2.fitness/(len(data2.x)+len(data1.x)) < 2 )


if __name__ == "__main__":
    unittest.main()
    
