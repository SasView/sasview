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
        """ test fitting for one data and one model park vs scipy"""
        #load data
        from sans.fit.Loader import Load
        load= Load()
        load.set_filename("testdata_line.txt")
        load.set_values()
        data11 = Data1D(x=[], y=[],dx=None, dy=None)
        load.load_data(data11)
        
        #Importing the Fit module
        from sans.fit.Fitting import Fit
        fitter= Fit('scipy')
        
        # Receives the type of model for the fitting
        from sans.guitools.LineModel import LineModel
        model11  = LineModel()
        model22  = LineModel()
        
        #Do the fit SCIPY
        model11.setParam( 'A', 2)
        model11.setParam( 'B', 1)
        data1=Data(sans_data=data11)
        model1 =Model(model11)
        model2 =Model(model22)
      
        fitter.set_data(data1,1)
        fitter.set_model(model1,"M1",1,['A','B'])
        
        result= fitter.fit()
        out1=result.pvec
        chisqr1=result.fitness
        cov1=result.cov
        print "scipy",chisqr1, out1, cov1
        """ testing SCIPy results"""
        self.assert_(math.fabs(out1[1]-2.5)/math.sqrt(cov1[1][1]) < 2)
        self.assert_(math.fabs(out1[0]-4.0)/math.sqrt(cov1[0][0]) < 2)
        self.assert_(chisqr1/len(data1.x) < 2)
        # PARK
        fitter= Fit('park')
        
        #Do the fit
        fitter.set_data(data1,1)
        model2.setParams( [2,1])
    
        fitter.set_model(model2,"M1",1,['A','B'])
       
        result2=fitter.fit(None,None)
        out2=result2.pvec
        chisqr2=result2.fitness
        cov2=result2.cov
        self.assert_(math.fabs(out2[1]-2.5)/math.sqrt(cov2[1][1]) < 2)
        self.assert_(math.fabs(out2[0]-4.0)/math.sqrt(cov2[0][0]) < 2)
        self.assert_(chisqr2/len(data1.x) < 2)
        print "scipy",chisqr1, out1, cov1
        print "park",chisqr2, out2, cov2
        self.assertAlmostEquals(out1[1], out2[1],0)
        self.assertAlmostEquals(out1[0], out2[0],0)
        self.assertAlmostEquals(cov1[0][0], cov2[0][0],1)
        self.assertAlmostEquals(cov1[1][1], cov2[1][1],1)
        self.assertAlmostEquals(chisqr1, chisqr2)
         
    def testfit_1Data_1Model(self):
        """ test fitting for one data and one model cipy"""
        #load data
        from sans.fit.Loader import Load
        load= Load()
        load.set_filename("testdata_line.txt")
        load.set_values()
        data11 = Data1D(x=[], y=[],dx=None, dy=None)
        load.load_data(data11)
        data1=Data(sans_data=data11)
    
        #Importing the Fit module
        from sans.fit.Fitting import Fit
        fitter= Fit('scipy')
        
        # Receives the type of model for the fitting
        from sans.guitools.LineModel import LineModel
        model1  = LineModel()
        model =Model(model1)
        
        #Do the fit SCIPY
        fitter.set_data(data1,1)
        import math
       
        pars1=['A','B']
        pars1.sort()
        fitter.set_model(model,"M1",1,pars1)
        result=fitter.fit()
        print "scipy",result.fitness,result.cov, result.pvec
    
        self.assert_(result.fitness)
        
       
    
      