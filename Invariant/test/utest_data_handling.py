"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

See the license text in license.txt

copyright 2010, University of Tennessee
"""
import unittest
import numpy, math
from DataLoader.loader import  Loader
from DataLoader.data_info import Data1D
from sans.invariant import invariant
from DataLoader.qsmearing import smear_selection
    
class TestLinearFit(unittest.TestCase):
    """
        Test Line fit 
    """
    def setUp(self):
        x = numpy.asarray([1.,2.,3.,4.,5.,6.,7.,8.,9.])
        y = numpy.asarray([1.,2.,3.,4.,5.,6.,7.,8.,9.])
        dy = y/10.0
        
        self.data = Data1D(x=x,y=y,dy=dy)
        
    def test_fit_linear_data(self):
        """ 
            Simple linear fit
        """
        
        # Create invariant object. Background and scale left as defaults.
        fit = invariant.Extrapolator(data=self.data)
        a,b = fit.fit()

        # Test results
        self.assertAlmostEquals(a, 1.0, 5)
        self.assertAlmostEquals(b, 0.0, 5)

    def test_fit_linear_data_with_noise(self):
        """ 
            Simple linear fit with noise
        """
        import random, math
        
        for i in range(len(self.data.y)):
            self.data.y[i] = self.data.y[i]+.1*random.random()
            
        # Create invariant object. Background and scale left as defaults.
        fit = invariant.Extrapolator(data=self.data)
        a,b = fit.fit()

        # Test results
        self.assertTrue(math.fabs(a-1.0)<0.05)
        self.assertTrue(math.fabs(b)<0.1)        
    
    
class TestInvariantCalculator(unittest.TestCase):
    """
        Test Line fit 
    """
    def setUp(self):
        self.data = Loader().load("latex_smeared.xml")[0]
        
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
        x = numpy.arange(0.0001, 0.1, 0.0001)
        y = numpy.asarray([self.scale * math.exp( -(q*self.rg)**2 / 3.0 ) for q in x])
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
        a, b = inv._fit(model=inv._low_extrapolation_function,
                          qmin=qmin,
                          qmax=qmax,
                          power=inv._low_extrapolation_power)
        self.assertAlmostEqual(self.scale, a, 6)
        self.assertAlmostEqual(self.rg, b, 6)
    

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
        x = numpy.arange(0.0001, 0.1, 0.0001)
        y = numpy.asarray([self.scale * math.pow(q ,-1.0*self.m) for q in x])                
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
        a, b = inv._fit(model=inv._low_extrapolation_function,
                          qmin=qmin,
                          qmax=qmax,
                          power=inv._low_extrapolation_power)
        
        self.assertAlmostEqual(self.scale, a, 6)
        self.assertAlmostEqual(self.m, b, 6)
        
class TestLinearization(unittest.TestCase):
    
    def test_guinier_incompatible_length(self):
        g = invariant.Guinier()
        self.assertRaises(AssertionError, g.linearize_data, [1],[1,2],None)
        self.assertRaises(AssertionError, g.linearize_data, [1,2],[1,2],[1])
    
    def test_linearization(self):
        """
            Check that the linearization process filters out points
            that can't be transformed
        """
        x = numpy.asarray(numpy.asarray([0,1,2,3]))
        y = numpy.asarray(numpy.asarray([1,1,1,1]))
        g = invariant.Guinier()
        x_out, y_out, dy_out = g.linearize_data(x,y,None)
        self.assertEqual(len(x_out), 3)
        self.assertEqual(len(y_out), 3)
        self.assertEqual(len(dy_out), 3)

    
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
        x = numpy.arange(0.0001, 0.1, 0.0001)
        y = numpy.asarray([self.scale * math.exp( -(q*self.rg)**2 / 3.0 ) for q in x])
        dy = y*.1
        self.data = Data1D(x=x, y=y, dy=dy)
        
    def test_low_q(self):
        """
            Invariant with low-Q extrapolation with no slit smear
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
        a, b = inv._fit(model=inv._low_extrapolation_function,
                          qmin=qmin,
                          qmax=qmax,
                          power=inv._low_extrapolation_power)
        self.assertAlmostEqual(self.scale, a, 6)
        self.assertAlmostEqual(self.rg, b, 6)
        
        qstar = inv.get_qstar(extrapolation='low')
        reel_y = self.data.y
        test_y = inv._low_extrapolation_function.evaluate_model(x=self.data.x)
        for i in range(len(self.data.x)):
            value  = math.fabs(test_y[i]-reel_y[i])/reel_y[i]
            self.assert_(value < 0.001)
            
class TestDataExtraLowSlit(unittest.TestCase):
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
        list = Loader().load("latex_smeared.xml")
        self.data = list[0]
        self.data.dxl = list[0].dxl
        self.data.dxw = list[0].dxw
        
    def test_low_q(self):
        """
            Invariant with low-Q extrapolation with slit smear
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
        a, b = inv._fit(model=inv._low_extrapolation_function,
                          qmin=qmin,
                          qmax=qmax,
                          power=inv._low_extrapolation_power)
      
        
        qstar = inv.get_qstar(extrapolation='low')
        reel_y = self.data.y
        #Compution the y 's coming out of the invariant when computing extrapolated
        #low data . expect the fit engine to have been already called and the guinier
        # to have the radius and the scale fitted
        
        test_y = numpy.zeros(len(self.data.x))
        smearer = smear_selection(self.data)
        first_bin, last_bin = smearer.get_bin_range(min(self.data.x),
                                                         max(self.data.x))
        test_y[first_bin:last_bin] = inv._low_extrapolation_function.evaluate_model(self.data.x[first_bin:last_bin])
        test_y = smearer(test_y, first_bin, last_bin) 
        
        for i in range(len(self.data.x)):
            value  = math.fabs(test_y[i]-reel_y[i])/reel_y[i]
            self.assert_(value < 0.001)
            
        # test data coming out of the invariant 
        test_y = inv._low_extrapolation_function.evaluate_model(x=self.data.x)
        for i in range(len(self.data.x)):
            value  = math.fabs(test_y[i]-reel_y[i])/reel_y[i]
            self.assert_(value < 0.001)
            
            
                    
            