"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

See the license text in license.txt

copyright 2010, University of Tennessee
"""
import unittest
import math
import numpy as np
from sas.sascalc.dataloader.loader import  Loader
from sas.sascalc.dataloader.data_info import Data1D

from sas.sascalc.invariant import invariant
    
class TestLinearFit(unittest.TestCase):
    """
        Test Line fit 
    """
    def setUp(self):
        x = np.asarray([1.,2.,3.,4.,5.,6.,7.,8.,9.])
        y = np.asarray([1.,2.,3.,4.,5.,6.,7.,8.,9.])
        dy = y/10.0
        
        self.data = Data1D(x=x,y=y,dy=dy)
        
    def test_fit_linear_data(self):
        """ 
            Simple linear fit
        """
        
        # Create invariant object. Background and scale left as defaults.
        fit = invariant.Extrapolator(data=self.data)
        #a,b = fit.fit()
        p, dp = fit.fit()

        # Test results
        self.assertAlmostEquals(p[0], 1.0, 5)
        self.assertAlmostEquals(p[1], 0.0, 5)

    def test_fit_linear_data_with_noise(self):
        """ 
            Simple linear fit with noise
        """
        import random, math
        
        for i in range(len(self.data.y)):
            self.data.y[i] = self.data.y[i]+.1*(random.random()-0.5)
            
        # Create invariant object. Background and scale left as defaults.
        fit = invariant.Extrapolator(data=self.data)
        p, dp = fit.fit()

        # Test results
        self.assertTrue(math.fabs(p[0]-1.0)<0.05)
        self.assertTrue(math.fabs(p[1])<0.1)        
        
    def test_fit_with_fixed_parameter(self):
        """
            Linear fit for y=ax+b where a is fixed.
        """
        # Create invariant object. Background and scale left as defaults.
        fit = invariant.Extrapolator(data=self.data)
        p, dp = fit.fit(power=-1.0)

        # Test results
        self.assertAlmostEquals(p[0], 1.0, 5)
        self.assertAlmostEquals(p[1], 0.0, 5)

    def test_fit_linear_data_with_noise_and_fixed_par(self):
        """ 
            Simple linear fit with noise
        """
        import random, math
        
        for i in range(len(self.data.y)):
            self.data.y[i] = self.data.y[i]+.1*(random.random()-0.5)
            
        # Create invariant object. Background and scale left as defaults.
        fit = invariant.Extrapolator(data=self.data)
        p, dp = fit.fit(power=-1.0)

        # Test results
        self.assertTrue(math.fabs(p[0]-1.0)<0.05)
        self.assertTrue(math.fabs(p[1])<0.1)        
        


class TestInvariantCalculator(unittest.TestCase):
    """
        Test main functionality of the Invariant calculator
    """
    def setUp(self):
        data = Loader().load("latex_smeared_slit.xml")
        self.data = data[0]
        self.data.dxl = None
        
    def test_initial_data_processing(self):
        """ 
            Test whether the background and scale are handled properly 
            when creating an InvariantCalculator object
        """
        length = len(self.data.x)
        self.assertEqual(length, len(self.data.y))
        inv = invariant.InvariantCalculator(self.data)
        
        self.assertEqual(length, len(inv._data.x))
        self.assertEqual(inv._data.x[0], self.data.x[0])

        # Now the same thing with a background value
        bck = 0.1
        inv = invariant.InvariantCalculator(self.data, background=bck)
        self.assertEqual(inv._background, bck)
        
        self.assertEqual(length, len(inv._data.x))
        self.assertEqual(inv._data.y[0]+bck, self.data.y[0])
        
        # Now the same thing with a scale value
        scale = 0.1
        inv = invariant.InvariantCalculator(self.data, scale=scale)
        self.assertEqual(inv._scale, scale)
        
        self.assertEqual(length, len(inv._data.x))
        self.assertAlmostEqual(inv._data.y[0]/scale, self.data.y[0],7)
        
    
    def test_incompatible_data_class(self):
        """
            Check that only classes that inherit from Data1D are allowed as data.
        """
        class Incompatible():
            pass
        self.assertRaises(ValueError, invariant.InvariantCalculator, Incompatible())
        
    def test_error_treatment(self):
        x = np.asarray(np.asarray([0,1,2,3]))
        y = np.asarray(np.asarray([1,1,1,1]))
        
        # These are all the values of the dy array that would cause
        # us to set all dy values to 1.0 at __init__ time.
        dy_list = [ [], None, [0,0,0,0] ]
        
        for dy in dy_list:
            data = Data1D(x=x, y=y, dy=dy)
            inv = invariant.InvariantCalculator(data)
            self.assertEqual(len(inv._data.x), len(inv._data.dy))
            self.assertEqual(len(inv._data.dy), 4)
            for i in range(4):
                self.assertEqual(inv._data.dy[i],1)
                
    def test_qstar_low_q_guinier(self):
        """
            Test low-q extrapolation with a Guinier
        """
        inv = invariant.InvariantCalculator(self.data)
        
        # Basic sanity check
        _qstar = inv.get_qstar()
        qstar, dqstar = inv.get_qstar_with_error()
        self.assertEqual(qstar, _qstar)
        
        # Low-Q Extrapolation
        # Check that the returned invariant is what we expect given
        # the result we got without extrapolation
        inv.set_extrapolation('low', npts=10, function='guinier')
        qs_extr, dqs_extr = inv.get_qstar_with_error('low')
        delta_qs_extr, delta_dqs_extr = inv.get_qstar_low()
        
        self.assertEqual(qs_extr, _qstar+delta_qs_extr)
        self.assertEqual(dqs_extr, math.sqrt(dqstar*dqstar + delta_dqs_extr*delta_dqs_extr))
        
        # We don't expect the extrapolated invariant to be very far from the
        # result without extrapolation. Let's test for a result within 10%.
        self.assertTrue(math.fabs(qs_extr-qstar)/qstar<0.1)
        
        # Check that the two results are consistent within errors
        # Note that the error on the extrapolated value takes into account
        # a systematic error for the fact that we may not know the shape of I(q) at low Q.
        self.assertTrue(math.fabs(qs_extr-qstar)<dqs_extr)
        
    def test_qstar_low_q_power_law(self):
        """
            Test low-q extrapolation with a power law
        """
        inv = invariant.InvariantCalculator(self.data)
        
        # Basic sanity check
        _qstar = inv.get_qstar()
        qstar, dqstar = inv.get_qstar_with_error()
        self.assertEqual(qstar, _qstar)
        
        # Low-Q Extrapolation
        # Check that the returned invariant is what we expect given
        inv.set_extrapolation('low', npts=10, function='power_law')
        qs_extr, dqs_extr = inv.get_qstar_with_error('low')
        delta_qs_extr, delta_dqs_extr = inv.get_qstar_low()
        
        # A fit using SasView gives 0.0655 for the value of the exponent
        self.assertAlmostEqual(inv._low_extrapolation_function.power, 0.0655, 3)
        
        if False:
            npts = len(inv._data.x)-1
            import matplotlib.pyplot as plt
            plt.loglog(inv._data.x[:npts], inv._data.y[:npts], 'o', label='Original data', markersize=10)
            plt.loglog(inv._data.x[:npts], inv._low_extrapolation_function.evaluate_model(inv._data.x[:npts]), 'r', label='Fitted line')
            plt.legend()
            plt.show()        
        
        self.assertEqual(qs_extr, _qstar+delta_qs_extr)
        self.assertAlmostEqual(dqs_extr, math.sqrt(dqstar*dqstar + delta_dqs_extr*delta_dqs_extr), 15)
        
        # We don't expect the extrapolated invariant to be very far from the
        # result without extrapolation. Let's test for a result within 10%.
        self.assertTrue(math.fabs(qs_extr-qstar)/qstar<0.1)
        
        # Check that the two results are consistent within errors
        # Note that the error on the extrapolated value takes into account
        # a systematic error for the fact that we may not know the shape of I(q) at low Q.
        self.assertTrue(math.fabs(qs_extr-qstar)<dqs_extr)
        
    def test_qstar_high_q(self):
        """
            Test high-q extrapolation
        """
        inv = invariant.InvariantCalculator(self.data)
        
        # Basic sanity check
        _qstar = inv.get_qstar()
        qstar, dqstar = inv.get_qstar_with_error()
        self.assertEqual(qstar, _qstar)
        
        # High-Q Extrapolation
        # Check that the returned invariant is what we expect given
        # the result we got without extrapolation
        inv.set_extrapolation('high', npts=20, function='power_law')
        qs_extr, dqs_extr = inv.get_qstar_with_error('high')
        delta_qs_extr, delta_dqs_extr = inv.get_qstar_high()
        
        # From previous analysis using SasView, we expect an exponent of about 3 
        self.assertTrue(math.fabs(inv._high_extrapolation_function.power-3)<0.1)
        
        self.assertEqual(qs_extr, _qstar+delta_qs_extr)
        self.assertAlmostEqual(dqs_extr, math.sqrt(dqstar*dqstar + delta_dqs_extr*delta_dqs_extr), 10)
        
        # We don't expect the extrapolated invariant to be very far from the
        # result without extrapolation. Let's test for a result within 10%.
        #TODO: verify whether this test really makes sense
        #self.assertTrue(math.fabs(qs_extr-qstar)/qstar<0.1)
        
        # Check that the two results are consistent within errors
        self.assertTrue(math.fabs(qs_extr-qstar)<dqs_extr)
                
    def test_qstar_full_q(self):
        """
            Test high-q extrapolation
        """
        inv = invariant.InvariantCalculator(self.data)
        
        # Basic sanity check
        _qstar = inv.get_qstar()
        qstar, dqstar = inv.get_qstar_with_error()
        self.assertEqual(qstar, _qstar)
        
        # High-Q Extrapolation
        # Check that the returned invariant is what we expect given
        # the result we got without extrapolation
        inv.set_extrapolation('low',  npts=10, function='guinier')
        inv.set_extrapolation('high', npts=20, function='power_law')
        qs_extr, dqs_extr = inv.get_qstar_with_error('both')
        delta_qs_low, delta_dqs_low = inv.get_qstar_low()
        delta_qs_hi,  delta_dqs_hi = inv.get_qstar_high()
        
        self.assertAlmostEqual(qs_extr, _qstar+delta_qs_low+delta_qs_hi, 8)
        self.assertAlmostEqual(dqs_extr, math.sqrt(dqstar*dqstar + delta_dqs_low*delta_dqs_low \
                                             + delta_dqs_hi*delta_dqs_hi), 8)
        
        # We don't expect the extrapolated invariant to be very far from the
        # result without extrapolation. Let's test for a result within 10%.
        #TODO: verify whether this test really makes sense
        #self.assertTrue(math.fabs(qs_extr-qstar)/qstar<0.1)
        
        # Check that the two results are consistent within errors
        self.assertTrue(math.fabs(qs_extr-qstar)<dqs_extr)
        
        def _check_values(to_check, reference, tolerance=0.05):
            self.assertTrue( math.fabs(to_check-reference)/reference < tolerance, msg="Tested value = "+str(to_check) )
            
        # The following values should be replaced by values pulled from IGOR
        # Volume Fraction:
        v, dv = inv.get_volume_fraction_with_error(1, None)
        _check_values(v, 1.88737914186e-15)

        v_l, dv_l = inv.get_volume_fraction_with_error(1, 'low')
        _check_values(v_l, 1.94289029309e-15)

        v_h, dv_h = inv.get_volume_fraction_with_error(1, 'high')
        _check_values(v_h, 6.99440505514e-15)
        
        v_b, dv_b = inv.get_volume_fraction_with_error(1, 'both')
        _check_values(v_b, 6.99440505514e-15)
        
        # Specific Surface:
        s, ds = inv.get_surface_with_error(1, 1, None)
        _check_values(s, 3.1603095786e-09)

        s_l, ds_l = inv.get_surface_with_error(1, 1, 'low')
        _check_values(s_l, 3.1603095786e-09)

        s_h, ds_h = inv.get_surface_with_error(1, 1, 'high')
        _check_values(s_h, 3.1603095786e-09)
        
        s_b, ds_b = inv.get_surface_with_error(1, 1, 'both')
        _check_values(s_b, 3.1603095786e-09)
        
        
    def test_bad_parameter_name(self):
        """
            The set_extrapolation method checks that the name of the extrapolation
            function and the name of the q-range to extrapolate (high/low) is 
            recognized.
        """
        inv = invariant.InvariantCalculator(self.data)
        self.assertRaises(ValueError, inv.set_extrapolation, 'low', npts=4, function='not_a_name')
        self.assertRaises(ValueError, inv.set_extrapolation, 'not_a_range', npts=4, function='guinier')
        self.assertRaises(ValueError, inv.set_extrapolation, 'high', npts=4, function='guinier')
    
    
class TestGuinierExtrapolation(unittest.TestCase):
    """
        Generate a Guinier distribution and verify that the extrapolation
        produce the correct ditribution.
    """
    
    def setUp(self):
        """
            Generate a Guinier distribution. After extrapolating, we will
            verify that we obtain the scale and rg parameters
        """
        self.scale = 1.5
        self.rg = 30.0
        x = np.arange(0.0001, 0.1, 0.0001)
        y = np.asarray([self.scale * math.exp( -(q*self.rg)**2 / 3.0 ) for q in x])
        dy = y*.1
        self.data = Data1D(x=x, y=y, dy=dy)
        
    def test_low_q(self):
        """
            Invariant with low-Q extrapolation
        """
        # Create invariant object. Background and scale left as defaults.
        inv = invariant.InvariantCalculator(data=self.data)
        # Set the extrapolation parameters for the low-Q range
        inv.set_extrapolation(range='low', npts=20, function='guinier')
        
        self.assertEqual(inv._low_extrapolation_npts, 20)
        self.assertEqual(inv._low_extrapolation_function.__class__, invariant.Guinier)
        
        # Data boundaries for fiiting
        qmin = inv._data.x[0]
        qmax = inv._data.x[inv._low_extrapolation_npts - 1]
        
        # Extrapolate the low-Q data
        inv._fit(model=inv._low_extrapolation_function,
                          qmin=qmin,
                          qmax=qmax,
                          power=inv._low_extrapolation_power)
        self.assertAlmostEqual(self.scale, inv._low_extrapolation_function.scale, 6)
        self.assertAlmostEqual(self.rg, inv._low_extrapolation_function.radius, 6)
    

class TestPowerLawExtrapolation(unittest.TestCase):
    """
        Generate a power law distribution and verify that the extrapolation
        produce the correct ditribution.
    """
    
    def setUp(self):
        """
            Generate a power law distribution. After extrapolating, we will
            verify that we obtain the scale and m parameters
        """
        self.scale = 1.5
        self.m = 3.0
        x = np.arange(0.0001, 0.1, 0.0001)
        y = np.asarray([self.scale * math.pow(q ,-1.0*self.m) for q in x])
        dy = y*.1
        self.data = Data1D(x=x, y=y, dy=dy)
        
    def test_low_q(self):
        """
            Invariant with low-Q extrapolation
        """
        # Create invariant object. Background and scale left as defaults.
        inv = invariant.InvariantCalculator(data=self.data)
        # Set the extrapolation parameters for the low-Q range
        inv.set_extrapolation(range='low', npts=20, function='power_law')
        
        self.assertEqual(inv._low_extrapolation_npts, 20)
        self.assertEqual(inv._low_extrapolation_function.__class__, invariant.PowerLaw)
        
        # Data boundaries for fitting
        qmin = inv._data.x[0]
        qmax = inv._data.x[inv._low_extrapolation_npts - 1]
        
        # Extrapolate the low-Q data
        inv._fit(model=inv._low_extrapolation_function,
                          qmin=qmin,
                          qmax=qmax,
                          power=inv._low_extrapolation_power)
        
        self.assertAlmostEqual(self.scale, inv._low_extrapolation_function.scale, 6)
        self.assertAlmostEqual(self.m, inv._low_extrapolation_function.power, 6)
        
class TestLinearization(unittest.TestCase):
    
    def test_guinier_incompatible_length(self):
        g = invariant.Guinier()
        data_in = Data1D(x=[1], y=[1,2], dy=None)
        self.assertRaises(AssertionError, g.linearize_data, data_in)
        data_in = Data1D(x=[1,1], y=[1,2], dy=[1])
        self.assertRaises(AssertionError, g.linearize_data, data_in)
    
    def test_linearization(self):
        """
            Check that the linearization process filters out points
            that can't be transformed
        """
        x = np.asarray(np.asarray([0,1,2,3]))
        y = np.asarray(np.asarray([1,1,1,1]))
        g = invariant.Guinier()
        data_in = Data1D(x=x, y=y)
        data_out = g.linearize_data(data_in)
        x_out, y_out, dy_out = data_out.x, data_out.y, data_out.dy
        self.assertEqual(len(x_out), 3)
        self.assertEqual(len(y_out), 3)
        self.assertEqual(len(dy_out), 3)
        
    def test_allowed_bins(self):
        x = np.asarray(np.asarray([0,1,2,3]))
        y = np.asarray(np.asarray([1,1,1,1]))
        dy = np.asarray(np.asarray([1,1,1,1]))
        g = invariant.Guinier()
        data = Data1D(x=x, y=y, dy=dy)
        self.assertEqual(g.get_allowed_bins(data), [False, True, True, True])

        data = Data1D(x=y, y=x, dy=dy)
        self.assertEqual(g.get_allowed_bins(data), [False, True, True, True])

        data = Data1D(x=dy, y=y, dy=x)
        self.assertEqual(g.get_allowed_bins(data), [False, True, True, True])
    
class TestDataExtraLow(unittest.TestCase):
    """
        Generate a Guinier distribution and verify that the extrapolation
        produce the correct ditribution. Tested if the data generated by the 
        invariant calculator is correct
    """
    
    def setUp(self):
        """
            Generate a Guinier distribution. After extrapolating, we will
            verify that we obtain the scale and rg parameters
        """
        self.scale = 1.5
        self.rg = 30.0
        x = np.arange(0.0001, 0.1, 0.0001)
        y = np.asarray([self.scale * math.exp( -(q*self.rg)**2 / 3.0 ) for q in x])
        dy = y*.1
        self.data = Data1D(x=x, y=y, dy=dy)
        
    def test_low_q(self):
        """
            Invariant with low-Q extrapolation with no slit smear
        """
        # Create invariant object. Background and scale left as defaults.
        inv = invariant.InvariantCalculator(data=self.data)
        # Set the extrapolation parameters for the low-Q range
        inv.set_extrapolation(range='low', npts=10, function='guinier')
        
        self.assertEqual(inv._low_extrapolation_npts, 10)
        self.assertEqual(inv._low_extrapolation_function.__class__, invariant.Guinier)
        
        # Data boundaries for fiiting
        qmin = inv._data.x[0]
        qmax = inv._data.x[inv._low_extrapolation_npts - 1]
        
        # Extrapolate the low-Q data
        inv._fit(model=inv._low_extrapolation_function,
                          qmin=qmin,
                          qmax=qmax,
                          power=inv._low_extrapolation_power)
        self.assertAlmostEqual(self.scale, inv._low_extrapolation_function.scale, 6)
        self.assertAlmostEqual(self.rg, inv._low_extrapolation_function.radius, 6)
        
        qstar = inv.get_qstar(extrapolation='low')
        test_y = inv._low_extrapolation_function.evaluate_model(x=self.data.x)
        for i in range(len(self.data.x)):
            value  = math.fabs(test_y[i]-self.data.y[i])/self.data.y[i]
            self.assert_(value < 0.001)
            
class TestDataExtraLowSlitGuinier(unittest.TestCase):
    """
        for a smear data, test that the fitting go through 
        real data for atleast the 2 first points
    """
    
    def setUp(self):
        """
            Generate a Guinier distribution. After extrapolating, we will
            verify that we obtain the scale and rg parameters
        """
        self.scale = 1.5
        self.rg = 30.0
        x = np.arange(0.0001, 0.1, 0.0001)
        y = np.asarray([self.scale * math.exp( -(q*self.rg)**2 / 3.0 ) for q in x])
        dy = y*.1
        self.data = Data1D(x=x, y=y, dy=dy)
        self.npts = len(x)-10
        
    def test_low_q(self):
        """
            Invariant with low-Q extrapolation with slit smear
        """
        # Create invariant object. Background and scale left as defaults.
        inv = invariant.InvariantCalculator(data=self.data)
        # Set the extrapolation parameters for the low-Q range
        inv.set_extrapolation(range='low', npts=self.npts, function='guinier')
        
        self.assertEqual(inv._low_extrapolation_npts, self.npts)
        self.assertEqual(inv._low_extrapolation_function.__class__, invariant.Guinier)
        
        # Data boundaries for fiiting
        qmin = inv._data.x[0]
        qmax = inv._data.x[inv._low_extrapolation_npts - 1]
        
        # Extrapolate the low-Q data
        inv._fit(model=inv._low_extrapolation_function,
                          qmin=qmin,
                          qmax=qmax,
                          power=inv._low_extrapolation_power)
      
        
        qstar = inv.get_qstar(extrapolation='low')

        test_y = inv._low_extrapolation_function.evaluate_model(x=self.data.x[:inv._low_extrapolation_npts])
        self.assert_(len(test_y) == len(self.data.y[:inv._low_extrapolation_npts]))
        
        for i in range(inv._low_extrapolation_npts):
            value  = math.fabs(test_y[i]-self.data.y[i])/self.data.y[i]
            self.assert_(value < 0.001)
            
    def test_low_data(self):
        """
            Invariant with low-Q extrapolation with slit smear
        """
        # Create invariant object. Background and scale left as defaults.
        inv = invariant.InvariantCalculator(data=self.data)
        # Set the extrapolation parameters for the low-Q range
        inv.set_extrapolation(range='low', npts=self.npts, function='guinier')
        
        self.assertEqual(inv._low_extrapolation_npts, self.npts)
        self.assertEqual(inv._low_extrapolation_function.__class__, invariant.Guinier)
        
        # Data boundaries for fiiting
        qmin = inv._data.x[0]
        qmax = inv._data.x[inv._low_extrapolation_npts - 1]
        
        # Extrapolate the low-Q data
        inv._fit(model=inv._low_extrapolation_function,
                          qmin=qmin,
                          qmax=qmax,
                          power=inv._low_extrapolation_power)
      
        
        qstar = inv.get_qstar(extrapolation='low')
        #Compution the y 's coming out of the invariant when computing extrapolated
        #low data . expect the fit engine to have been already called and the guinier
        # to have the radius and the scale fitted
        data_in_range = inv.get_extra_data_low(q_start=self.data.x[0], 
                                               npts = inv._low_extrapolation_npts) 
        test_y = data_in_range.y
        self.assert_(len(test_y) == len(self.data.y[:inv._low_extrapolation_npts]))
        for i in range(inv._low_extrapolation_npts):
            value  = math.fabs(test_y[i]-self.data.y[i])/self.data.y[i]
            self.assert_(value < 0.001)    
       
            
class TestDataExtraHighSlitPowerLaw(unittest.TestCase):
    """
        for a smear data, test that the fitting go through 
        real data for atleast the 2 first points
    """
    
    def setUp(self):
        """
            Generate a Guinier distribution. After extrapolating, we will
            verify that we obtain the scale and rg parameters
        """
        self.scale = 1.5
        self.m = 3.0
        x = np.arange(0.0001, 0.1, 0.0001)
        y = np.asarray([self.scale * math.pow(q ,-1.0*self.m) for q in x])
        dy = y*.1
        self.data = Data1D(x=x, y=y, dy=dy)
        self.npts = 20
        
    def test_high_q(self):
        """
            Invariant with high-Q extrapolation with slit smear
        """
        # Create invariant object. Background and scale left as defaults.
        inv = invariant.InvariantCalculator(data=self.data)
        # Set the extrapolation parameters for the low-Q range
        inv.set_extrapolation(range='high', npts=self.npts, function='power_law')
        
        self.assertEqual(inv._high_extrapolation_npts, self.npts)
        self.assertEqual(inv._high_extrapolation_function.__class__, invariant.PowerLaw)
        
        # Data boundaries for fiiting
        xlen = len(self.data.x)
        start =  xlen - inv._high_extrapolation_npts
        qmin = inv._data.x[start]
        qmax = inv._data.x[xlen-1]
        
        # Extrapolate the high-Q data
        inv._fit(model=inv._high_extrapolation_function,
                          qmin=qmin,
                          qmax=qmax,
                          power=inv._high_extrapolation_power)
      
        
        qstar = inv.get_qstar(extrapolation='high')
        
        test_y = inv._high_extrapolation_function.evaluate_model(x=self.data.x[start: ])
        self.assert_(len(test_y) == len(self.data.y[start:]))
        
        for i in range(len(self.data.x[start:])):
            value  = math.fabs(test_y[i]-self.data.y[start+i])/self.data.y[start+i]
            self.assert_(value < 0.001)
            
    def test_high_data(self):
        """
            Invariant with low-Q extrapolation with slit smear
        """
        # Create invariant object. Background and scale left as defaults.
        inv = invariant.InvariantCalculator(data=self.data)
        # Set the extrapolation parameters for the low-Q range
        inv.set_extrapolation(range='high', npts=self.npts, function='power_law')
        
        self.assertEqual(inv._high_extrapolation_npts, self.npts)
        self.assertEqual(inv._high_extrapolation_function.__class__, invariant.PowerLaw)
        
        # Data boundaries for fiiting
        xlen = len(self.data.x)
        start =  xlen - inv._high_extrapolation_npts
        qmin = inv._data.x[start]
        qmax = inv._data.x[xlen-1]
        
        # Extrapolate the high-Q data
        inv._fit(model=inv._high_extrapolation_function,
                          qmin=qmin,
                          qmax=qmax,
                          power=inv._high_extrapolation_power)
      
        qstar = inv.get_qstar(extrapolation='high')
       
        data_in_range= inv.get_extra_data_high(q_end = max(self.data.x),
                                               npts = inv._high_extrapolation_npts) 
        test_y = data_in_range.y
        self.assert_(len(test_y) == len(self.data.y[start:]))
        temp = self.data.y[start:]
        
        for i in range(len(self.data.x[start:])):
            value  = math.fabs(test_y[i]- temp[i])/temp[i]
            self.assert_(value < 0.001)                
                      