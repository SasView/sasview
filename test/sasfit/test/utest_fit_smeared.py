"""
    Unit tests for fitting module 
    @author M. Doucet
"""
import unittest
import math

import numpy
from sas.fit.AbstractFitEngine import Model
from sas.fit.BumpsFitting import BumpsFit as Fit
from sas.dataloader.loader import Loader
from sas.models.qsmearing import smear_selection
from sas.models.CylinderModel import CylinderModel
from sas.models.SphereModel import SphereModel


from bumps import fitters
try:
    from bumps.options import FIT_CONFIG
    def set_fitter(alg, opts):
        FIT_CONFIG.selected_id= alg
        FIT_CONFIG.values[alg].update(opts, monitors=[])
except:
    # CRUFT: Bumps changed its handling of fit options around 0.7.5.6
    def set_fitter(alg, opts):
        #print "fitting",alg,opts
        #print "options",fitters.FIT_OPTIONS[alg].__dict__
        fitters.FIT_DEFAULT = alg
        fitters.FIT_OPTIONS[alg].options.update(opts, monitors=[])


class testFitModule(unittest.TestCase):
    """ test fitting """
    
    def test_without_resolution(self):
        """ Simple cylinder model fit  """
        
        out=Loader().load("cyl_400_20.txt")
        # This data file has not error, add them
        #out.dy = out.y
        
        fitter = Fit()
        fitter.set_data(out,1)
        
        # Receives the type of model for the fitting
        model1  = CylinderModel()
        model1.setParam("scale", 1.0)
        model1.setParam("radius",18)
        model1.setParam("length", 397)
        model1.setParam("sldCyl",3e-006 )
        model1.setParam("sldSolv",0.0 )
        model1.setParam("background", 0.0)
        model = Model(model1)
        pars1 =['length','radius','scale']
        fitter.set_model(model,1,pars1)
        
        # What the hell is this line for?
        fitter.select_problem_for_fit(id=1,value=1)
        result1, = fitter.fit()
        #print "result1",result1

        self.assert_(result1)
        self.assertTrue(len(result1.pvec) > 0)
        self.assertTrue(len(result1.stderr) > 0)
        
        self.assertTrue( math.fabs(result1.pvec[0]-400.0)/3.0 < result1.stderr[0] )
        self.assertTrue( math.fabs(result1.pvec[1]-20.0)/3.0  < result1.stderr[1] )
        self.assertTrue( math.fabs(result1.pvec[2]-1)/3.0   < result1.stderr[2] )
        self.assertTrue( result1.fitness < 1.0 )

    def test_dispersion(self):
        """
            Cylinder fit with dispersion
        """
        set_fitter('lm', {})
        self._dispersion(fitter = Fit())

    def _dispersion(self, fitter):
        # Load data
        # This data is for a cylinder with 
        #   length=400, radius=20, radius disp=5, scale=1e-10
        out=Loader().load("cyl_400_20_disp5r.txt")
        out.dy = numpy.zeros(len(out.y))
        for i in range(len(out.y)):
            out.dy[i] = math.sqrt(out.y[i])
        
        # Receives the type of model for the fitting
        model1  = CylinderModel()
        model1.setParam("scale", 10.0)
        model1.setParam("radius",18)
        model1.setParam("length", 397)
        model1.setParam("sldCyl",3e-006 )
        model1.setParam("sldSolv",0.0 )
        model1.setParam("background", 0.0)

        # Dispersion parameters
        model1.dispersion['radius']['width'] = 0.25
        model1.dispersion['radius']['npts'] = 50

        model = Model(model1)

        pars1 =['length','radius','scale','radius.width']
        fitter.set_data(out,1)
        fitter.set_model(model,1,pars1)
        fitter.select_problem_for_fit(id=1,value=1)
        #import time; T0 = time.time()
        result1, = fitter.fit()

        self.assert_(result1)
        self.assertTrue(len(result1.pvec)>0)
        self.assertTrue(len(result1.stderr)>0)

        #print [z for z in zip(result1.param_list,result1.pvec,result1.stderr)]
        self.assertTrue( math.fabs(result1.pvec[0]-399.8)/3.0 < result1.stderr[0] )
        self.assertTrue( math.fabs(result1.pvec[1]-17.5)/3.0  < result1.stderr[1] )
        self.assertTrue( math.fabs(result1.pvec[2]-11.1)/3.0   < result1.stderr[2] )
        self.assertTrue( math.fabs(result1.pvec[3]-0.276)/3.0   < result1.stderr[3] )
        self.assertTrue( result1.fitness < 1.0 )
        
        
class smear_testdata(unittest.TestCase):
    """
        Test fitting with the smearing operations
        The output of the fits should be compated to fits
        done with IGOR for the same models and data sets.
    """
    def setUp(self):
        data = Loader().load("latex_smeared.xml")
        self.data_res = data[0]
        self.data_slit = data[1]
        
        self.sphere = SphereModel()
        self.sphere.setParam('background', 0)
        self.sphere.setParam('radius', 5000.0)
        self.sphere.setParam('scale', 0.4)
        self.sphere.setParam('sldSolv',0)
        self.sphere.setParam('sldSph',1e-6)
        #self.sphere.setParam('radius.npts', 30)
        #self.sphere.setParam('radius.width',50)

    def test_reso(self):

        # Let the data module find out what smearing the
        # data needs
        smear = smear_selection(self.data_res)
        #self.assertEqual(smear.__class__.__name__, 'QSmearer')
        #self.assertEqual(smear.__class__.__name__, 'PySmearer')

        # Fit
        fitter = Fit()
        
        # Data: right now this is the only way to set the smearer object
        # We should improve that and have a way to get access to the
        # data for a given fit.
        fitter.set_data(self.data_res,1)
        fitter.fit_arrange_dict[1].data_list[0].smearer = smear

        # Model: maybe there's a better way to do this.
        # Ideally we should have to create a new model from our sas model.
        fitter.set_model(Model(self.sphere),1, ['radius','scale', 'background'])
        
        # Why do we have to do this...?
        fitter.select_problem_for_fit(id=1,value=1)

        # Perform the fit (might take a while)
        result1, = fitter.fit()
        
        #print "v",result1.pvec
        #print "dv",result1.stderr
        #print "chisq(v)",result1.fitness

        self.assertTrue( math.fabs(result1.pvec[0]-5000) < 20 )
        self.assertTrue( math.fabs(result1.pvec[1]-0.48) < 0.02 )
        self.assertTrue( math.fabs(result1.pvec[2]-0.060)  < 0.002 )


    def test_slit(self):
        smear = smear_selection(self.data_slit)
        #self.assertEqual(smear.__class__.__name__, 'SlitSmearer')
        #self.assertEqual(smear.__class__.__name__, 'PySmearer')

        fitter = Fit()
        
        # Data: right now this is the only way to set the smearer object
        # We should improve that and have a way to get access to the
        # data for a given fit.
        fitter.set_data(self.data_slit,1)
        fitter.fit_arrange_dict[1].data_list[0].smearer = smear
        fitter.fit_arrange_dict[1].data_list[0].qmax = 0.003
        
        # Model
        fitter.set_model(Model(self.sphere),1, ['radius','scale'])
        fitter.select_problem_for_fit(id=1,value=1)
        
        result1, = fitter.fit()

        #print "v",result1.pvec
        #print "dv",result1.stderr
        #print "chisq(v)",result1.fitness

        numpy.testing.assert_allclose(result1.pvec, [2323.466,0.22137], rtol=0.001)

if __name__ == '__main__':
    unittest.main()
