"""
   Implementation of the use-case from a usage perspective. 
   TODO: check the return values to perform actual unit testing.
"""
import unittest
from DataLoader.loader import  Loader
from sans.invariant import invariant


class TestInvPolySphere(unittest.TestCase):
    """
        Test unsmeared data for invariant computation
    """
    def setUp(self):
        self.data = Loader().load("PolySpheres.txt")
        
    def test_use_case_1(self):
        """
            Invariant without extrapolation
        """
        # Create invariant object. Background and scale left as defaults.
        inv = invariant.InvariantCalculator(data=self.data)
        
        # We have to be able to tell the InvariantCalculator whether we want the
        # extrapolation or not. By default, when the user doesn't specify, we
        # should compute Q* without extrapolation. That's what should be done in __init__.
        
        # We call get_qstar() with no argument, which signifies that we do NOT
        # want extrapolation.
        qstar = inv.get_qstar()
        
        # The volume fraction and surface use Q*. That means that the following 
        # methods should check that Q* has been computed. If not, it should 
        # compute it by calling get_qstare(), leaving the parameters as default.
        volume_fraction = inv.get_volume_fraction(contrast=1.0)
        surface         = inv.get_surface(contrast=1.0, porod_const=1.0)
        
    def test_use_case_2(self):
        """
            Invariant without extrapolation. Invariant, volume fraction and surface 
            are given with errors.
        """
        # Create invariant object. Background and scale left as defaults.
        inv = invariant.InvariantCalculator(data=self.data)
        
        # Get the invariant with errors
        qstar, qstar_err = inv.get_qstar_with_error()
        v, dv            = inv.get_volume_fraction_with_error(contrast=1.0)
        s, ds            = inv.get_surface_with_error(contrast=1.0, porod_const=1.0)
        
    def test_use_case_3(self):
        """
            Invariant with low-Q extrapolation
        """
        # Create invariant object. Background and scale left as defaults.
        inv = invariant.InvariantCalculator(data=self.data)
        
        # Set the extrapolation parameters for the low-Q range
        
        # The npts parameter should have a good default.
        # The range parameter should be 'high' or 'low'
        # The function parameter should default to None. If it is None,
        #    the method should pick a good default (Guinier at low-Q and 1/q^4 at high-Q).
        #    The method should also check for consistency of the extrapolate and function
        #    parameters. For instance, you might not want to allow 'high' and 'guinier'.
        # The power parameter (not shown below) should default to 4.
        inv.set_extraplotation(range='low', npts=5, function='guinier')
        
        # The version of the call without error
        # At this point, we could still compute Q* without extrapolation by calling
        # get_qstar with arguments, or with extrapolate=None.
        qstar = inv.get_qstar(extrapolate='low')
        
        # The version of the call with error
        qstar, qstar_err = inv.get_qstar_with_error(extrapolate='low')

        # Get the volume fraction and surface
        v, dv            = inv.get_volume_fraction_with_error(contrast=1.0)
        s, ds            = inv.get_surface_with_error(contrast=1.0, porod_const=1.0)
        
    def test_use_case_4(self):
        """
            Invariant with high-Q extrapolation
        """
        # Create invariant object. Background and scale left as defaults.
        inv = invariant.InvariantCalculator(data=self.data)
        

        # Set the extrapolation parameters for the high-Q range
        
        # The npts parameter should have a good default.
        # The range parameter should be 'high' or 'low'. Those should be stored separately.
        # The function parameter should default to None. If it is None,
        #    the method should pick a good default (Guinier at low-Q and 1/q^4 at high-Q).
        #    The method should also check for consistency of the extrapolate and function
        #    parameters. For instance, you might not want to allow 'high' and 'guinier'.
        # The power parameter should default to 4.
        inv.set_extraplotation(range='high', npts=5, function='power_law', power=4)
        
        
        # The version of the call without error
        # The function parameter defaults to None, then is picked to be 'power_law' for extrapolate='high'
        qstar = inv.get_qstar(extrapolate='high')
        
        # The version of the call with error
        qstar, qstar_err = inv.get_qstar_with_error(extrapolate='high')

        # Get the volume fraction and surface
        v, dv            = inv.get_volume_fraction_with_error(contrast=1.0)
        s, ds            = inv.get_surface_with_error(contrast=1.0, porod_const=1.0)
        
    def test_use_case_5(self):
        """
            Invariant with both high- and low-Q extrapolation
        """
        # Create invariant object. Background and scale left as defaults.
        inv = invariant.InvariantCalculator(data=self.data)
        
        # Set the extrapolation parameters for the low- and high-Q ranges
        inv.set_extraplotation(range='low', npts=5, function='guinier')
        inv.set_extraplotation(range='high', npts=5, function='power_law', power=4)
        
        # The version of the call without error
        # The function parameter defaults to None, then is picked to be 'power_law' for extrapolate='high'
        qstar = inv.get_qstar(extrapolate='both')
        
        # The version of the call with error
        qstar, qstar_err = inv.get_qstar_with_error(extrapolate='both')

        # Get the volume fraction and surface
        v, dv            = inv.get_volume_fraction_with_error(contrast=1.0)
        s, ds            = inv.get_surface_with_error(contrast=1.0, porod_const=1.0)
        
                