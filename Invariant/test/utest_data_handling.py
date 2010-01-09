"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

See the license text in license.txt

copyright 2010, University of Tennessee
"""
import unittest
import numpy
from DataLoader.loader import  Loader
from DataLoader.data_info import Data1D
from sans.invariant import invariant
    
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
        fit = invariant.FitFunctor(data=self.data)
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
        fit = invariant.FitFunctor(data=self.data)
        a,b = fit.fit()

        # Test results
        self.assertTrue(math.fabs(a-1.0)<0.05)
        self.assertTrue(math.fabs(b)<0.05)        
    
    
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
    
    