"""
    Unit tests for fitting module 
    @author M. Doucet
"""
import unittest
from sans.fit.AbstractFitEngine import Model
import math
import numpy
from sans.fit.Fitting import Fit
from DataLoader.loader import Loader

class testFitModule(unittest.TestCase):
    """ test fitting """
    
    def test_scipy(self):
        """ Simple cylinder model fit (scipy)  """
        
        out=Loader().load("cyl_400_20.txt")
        # This data file has not error, add them
        out.dy = out.y
        
        fitter = Fit('scipy')
        fitter.set_data(out,1)
        
        # Receives the type of model for the fitting
        from sans.models.CylinderModel import CylinderModel
        model1  = CylinderModel()
        model1.setParam('contrast', 1)
        model = Model(model1)
        model.set(scale=1e-10)
        pars1 =['length','radius','scale']
        fitter.set_model(model,1,pars1)
        
        # What the hell is this line for?
        fitter.select_problem_for_fit(Uid=1,value=1)
        result1 = fitter.fit()
        
        self.assert_(result1)
        self.assertTrue(len(result1.pvec)>0 or len(result1.pvec)==0 )
        self.assertTrue(len(result1.stderr)> 0 or len(result1.stderr)==0)
        
        self.assertTrue( math.fabs(result1.pvec[0]-400.0)/3.0 < result1.stderr[0] )
        self.assertTrue( math.fabs(result1.pvec[1]-20.0)/3.0  < result1.stderr[1] )
        self.assertTrue( math.fabs(result1.pvec[2]-9.0e-12)/3.0   < result1.stderr[2] )
        self.assertTrue( result1.fitness < 1.0 )
        
    def test_scipy_dispersion(self):
        """
            Cylinder fit with dispersion
        """
        # Load data
        # This data is for a cylinder with 
        #   length=400, radius=20, radius disp=5, scale=1e-10
        out=Loader().load("cyl_400_20_disp5r.txt")
        out.dy = numpy.zeros(len(out.y))
        for i in range(len(out.y)):
            out.dy[i] = math.sqrt(out.y[i])
        
        # Set up the fit
        fitter = Fit('scipy')
        # Receives the type of model for the fitting
        from sans.models.CylinderModel import CylinderModel
        model1  = CylinderModel()
        model1.setParam('contrast', 1)
        
        # Dispersion parameters
        model1.dispersion['radius']['width'] = 0.001
        model1.dispersion['radius']['npts'] = 50        
        
        model = Model(model1)
        
        pars1 =['length','radius','scale','radius.width']
        fitter.set_data(out,1)
        model.set(scale=1e-10)
        fitter.set_model(model,1,pars1)
        fitter.select_problem_for_fit(Uid=1,value=1)
        result1 = fitter.fit()
        
        self.assert_(result1)
        self.assertTrue(len(result1.pvec)>0 or len(result1.pvec)==0 )
        self.assertTrue(len(result1.stderr)> 0 or len(result1.stderr)==0)
        
        self.assertTrue( math.fabs(result1.pvec[0]-400.0)/3.0 < result1.stderr[0] )
        self.assertTrue( math.fabs(result1.pvec[1]-20.0)/3.0  < result1.stderr[1] )
        self.assertTrue( math.fabs(result1.pvec[2]-1.0e-10)/3.0   < result1.stderr[2] )
        self.assertTrue( math.fabs(result1.pvec[3]-5.0)/3.0   < result1.stderr[3] )
        self.assertTrue( result1.fitness < 1.0 )
        
        
class smear_testdata(unittest.TestCase):
    """
        Test fitting with the smearing operations
        The output of the fits should be compated to fits
        done with IGOR for the same models and data sets.
    """
    def setUp(self):
        print "TEST DONE WITHOUT PROPER OUTPUT CHECK:"
        print "   ---> TEST NEEDS TO BE COMPLETED"
        from sans.models.SphereModel import SphereModel
        data = Loader().load("latex_smeared.xml")
        self.data_res = data[0]
        self.data_slit = data[1]
        
        self.sphere = SphereModel()
        self.sphere.setParam('radius', 5000.0)
        self.sphere.setParam('scale', 1.0e-13)
        self.sphere.setParam('radius.npts', 30)
        self.sphere.setParam('radius.width',500)
        
    def test_reso(self):
        from DataLoader.qsmearing import smear_selection
        
        # Let the data module find out what smearing the
        # data needs
        smear = smear_selection(self.data_res)
        self.assertEqual(smear.__class__.__name__, 'QSmearer')

        # Fit
        fitter = Fit('scipy')
        
        # Data: right now this is the only way to set the smearer object
        # We should improve that and have a way to get access to the
        # data for a given fit.
        fitter.set_data(self.data_res,1)
        fitter._engine.fitArrangeDict[1].dList[0].smearer = smear
        print "smear ",smear
        # Model: maybe there's a better way to do this.
        # Ideally we should have to create a new model from our sans model.
        fitter.set_model(Model(self.sphere),1, ['radius','scale'])
        
        # Why do we have to do this...?
        fitter.select_problem_for_fit(Uid=1,value=1)
        
        # Perform the fit (might take a while)
        result1 = fitter.fit()
        
        # Replace this with proper test once we know what the
        # result should be 
        print result1.pvec
        print result1.stderr
        
    def test_slit(self):
        from DataLoader.qsmearing import smear_selection
        
        smear = smear_selection(self.data_slit)
        self.assertEqual(smear.__class__.__name__, 'SlitSmearer')

        # Fit
        fitter = Fit('scipy')
        
        # Data: right now this is the only way to set the smearer object
        # We should improve that and have a way to get access to the
        # data for a given fit.
        fitter.set_data(self.data_slit,1)
        fitter._engine.fitArrangeDict[1].dList[0].smearer = smear
        fitter._engine.fitArrangeDict[1].dList[0].qmax = 0.003
        
        # Model
        fitter.set_model(Model(self.sphere),1, ['radius','scale'])
        fitter.select_problem_for_fit(Uid=1,value=1)
        
        result1 = fitter.fit()
        
        # Replace this with proper test once we know what the
        # result should be 
        print result1.pvec
        print result1.stderr
        
       
       
if __name__ == '__main__':
    unittest.main()