"""
   Implementation of the use-case from a usage perspective. 
  
"""
#TODO: there's no test for smeared extrapolation
import unittest
from sas.sascalc.dataloader.loader import  Loader
from sas.sascalc.invariant import invariant


class Data1D:
    pass


class TestLineFit(unittest.TestCase):
    """
        Test Line fit 
    """
    def setUp(self):
        self.data_list = Loader().load("linefittest.txt")
        self.data = self.data_list[0]

    def test_fit_line_data(self):
        """ 
            Fit_Test_1: test linear fit, ax +b, without fixed
        """

        # Create invariant object. Background and scale left as defaults.
        fit = invariant.Extrapolator(data=self.data)
        
        # Without holding
        p, dp = fit.fit(power=None)

        # Test results
        self.assertAlmostEquals(p[0], 2.3983,3)
        self.assertAlmostEquals(p[1], 0.87833,3)

    def test_fit_line_data_fixed(self):
        """ 
            Fit_Test_2: test linear fit, ax +b, with 'a' fixed
        """

        # Create invariant object. Background and scale left as defaults.
        fit = invariant.Extrapolator(data=self.data)

        # With holding a = -power =4
        p, dp = fit.fit(power=-4)

        # Test results
        self.assertAlmostEquals(p[0], 4)
        self.assertAlmostEquals(p[1], -4.0676,3)


class TestLineFitNoweight(unittest.TestCase):
    """
        Test Line fit without weight(dy data)
    """
    def setUp(self):
        self.data_list = Loader().load("linefittest_no_weight.txt")
        self.data = self.data_list[0]

    def skip_test_fit_line_data_no_weight(self):
        """ 
            Fit_Test_1: test linear fit, ax +b, without fixed
        """

        # Create invariant object. Background and scale left as defaults.
        fit = invariant.Extrapolator(data=self.data)

        # Without holding
        p, dp = fit.fit(power=None)

        # Test results
        self.assertAlmostEquals(p[0], 2.4727,3)
        self.assertAlmostEquals(p[1], 0.6,3)

    def test_fit_line_data_fixed_no_weight(self):
        """ 
            Fit_Test_2: test linear fit, ax +b, with 'a' fixed
        """

        # Create invariant object. Background and scale left as defaults.
        fit = invariant.Extrapolator(data=self.data)

        #With holding a = -power =4
        p, dp = fit.fit(power=-4)

        # Test results
        self.assertAlmostEquals(p[0], 4)
        self.assertAlmostEquals(p[1], -7.8,3)


class TestInvPolySphere(unittest.TestCase):
    """
        Test unsmeared data for invariant computation
    """
    def setUp(self):
        self.data_list = Loader().load("PolySpheres.txt")
        self.data = self.data_list[0]

    def test_wrong_data(self):
        """ test receiving Data1D not of type loader"""
        self.assertRaises(ValueError,invariant.InvariantCalculator, Data1D())

    def test_use_case_1(self):
        """
            Invariant without extrapolation
        """
        # Create invariant object. Background and scale left as defaults.
        inv = invariant.InvariantCalculator(data=self.data)

        # We have to be able to tell the InvariantCalculator whether we want the
        # extrapolation or not. By default, when the user doesn't specify, we
        # should compute Q* without extrapolation. That's what should be done
        # in __init__.

        # We call get_qstar() with no argument, which signifies that we do NOT
        # want extrapolation.
        qstar = inv.get_qstar()

        # The volume fraction and surface use Q*. That means that the following 
        # methods should check that Q* has been computed. If not, it should 
        # compute it by calling get_qstare(), leaving the parameters as default.
        v, dv = inv.get_volume_fraction_with_error(contrast=2.6e-6)
        s, ds = inv.get_surface_with_error(contrast=2.6e-6, porod_const=2)

        # Test results
        self.assertAlmostEquals(qstar, 7.48959e-5,2)
        self.assertAlmostEquals(v, 0.005644689, 4)
        self.assertAlmostEquals(s , 941.7452, 3)

    def test_use_case_2(self):
        """
        Invariant without extrapolation. Invariant, volume fraction and surface 
        are given with errors.
        """
        # Create invariant object. Background and scale left as defaults.
        inv = invariant.InvariantCalculator(data=self.data)

        # Get the invariant with errors
        qstar, qstar_err = inv.get_qstar_with_error()

        # The volume fraction and surface use Q*. That means that the following 
        # methods should check that Q* has been computed. If not, it should 
        # compute it by calling get_qstare(), leaving the parameters as default.
        v, dv = inv.get_volume_fraction_with_error(contrast=2.6e-6)
        s, ds = inv.get_surface_with_error(contrast=2.6e-6, porod_const=2)
        # Test results
        self.assertAlmostEquals(qstar, 7.48959e-5,2)
        self.assertAlmostEquals(v, 0.005644689, 1)
        self.assertAlmostEquals(s , 941.7452, 3)

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
        #    the method should pick a good default
        #    (Guinier at low-Q and 1/q^4 at high-Q).
        #    The method should also check for consistency of the extrapolation
        #    and function parameters. For instance, you might not want to allow
        #    'high' and 'guinier'.
        # The power parameter (not shown below) should default to 4.
        inv.set_extrapolation(range='low', npts=10, function='guinier')

        # The version of the call without error
        # At this point, we could still compute Q* without extrapolation by
        # calling get_qstar with arguments, or with extrapolation=None.
        qstar = inv.get_qstar(extrapolation='low')

        # The version of the call with error
        qstar, qstar_err = inv.get_qstar_with_error(extrapolation='low')

        # Get the volume fraction and surface
        v, dv = inv.get_volume_fraction_with_error(contrast=2.6e-6)
        s, ds = inv.get_surface_with_error(contrast=2.6e-6, porod_const=2)

        # Test results
        self.assertAlmostEquals(qstar, 7.49e-5, 1)
        self.assertAlmostEquals(v, 0.005648401, 4)
        self.assertAlmostEquals(s , 941.7452, 3)

    def test_use_case_4(self):
        """
            Invariant with high-Q extrapolation
        """
        # Create invariant object. Background and scale left as defaults.
        inv = invariant.InvariantCalculator(data=self.data)

        # Set the extrapolation parameters for the high-Q range
        inv.set_extrapolation(range='high', npts=10, function='power_law',
                              power=4)
        
        # The version of the call without error
        # The function parameter defaults to None, then is picked to be
        # 'power_law' for extrapolation='high'
        qstar = inv.get_qstar(extrapolation='high')

        # The version of the call with error
        qstar, qstar_err = inv.get_qstar_with_error(extrapolation='high')

        # Get the volume fraction and surface
        v, dv = inv.get_volume_fraction_with_error(contrast=2.6e-6)
        s, ds = inv.get_surface_with_error(contrast=2.6e-6, porod_const=2)

        # Test results
        self.assertAlmostEquals(qstar, 7.49e-5,2)
        self.assertAlmostEquals(v, 0.005952674, 3)
        self.assertAlmostEquals(s , 941.7452, 3)

    def test_use_case_5(self):
        """
            Invariant with both high- and low-Q extrapolation
        """
        # Create invariant object. Background and scale left as defaults.
        inv = invariant.InvariantCalculator(data=self.data)

        # Set the extrapolation parameters for the low- and high-Q ranges
        inv.set_extrapolation(range='low', npts=10, function='guinier')
        inv.set_extrapolation(range='high', npts=10, function='power_law',
                              power=4)

        # The version of the call without error
        # The function parameter defaults to None, then is picked to be
        # 'power_law' for extrapolation='high'
        qstar = inv.get_qstar(extrapolation='both')
        
        # The version of the call with error
        qstar, qstar_err = inv.get_qstar_with_error(extrapolation='both')

        # Get the volume fraction and surface
        v, dv = inv.get_volume_fraction_with_error(contrast=2.6e-6)
        s, ds = inv.get_surface_with_error(contrast=2.6e-6, porod_const=2)

        # Test results
        self.assertAlmostEquals(qstar, 7.88981e-5,2)
        self.assertAlmostEquals(v, 0.005952674, 3)
        self.assertAlmostEquals(s , 941.7452, 3)

    def test_use_case_6(self):
        """
            Invariant with high-Q extrapolation
        """
        # Create invariant object. Background and scale left as defaults.
        inv = invariant.InvariantCalculator(data=self.data)

        # Set the extrapolation parameters for the high-Q range
        inv.set_extrapolation(range='low', npts=10, function='power_law', power=4)

        # The version of the call without error
        # The function parameter defaults to None, then is picked to be 'power_law' for extrapolation='high'
        qstar = inv.get_qstar(extrapolation='low')

        # The version of the call with error
        qstar, qstar_err = inv.get_qstar_with_error(extrapolation='low')

        # Get the volume fraction and surface
        v, dv = inv.get_volume_fraction_with_error(contrast=2.6e-6)
        s, ds = inv.get_surface_with_error(contrast=2.6e-6, porod_const=2)

        # Test results
        self.assertAlmostEquals(qstar, 7.49e-5,2)
        self.assertAlmostEquals(v, 0.005952674, 3)
        self.assertAlmostEquals(s , 941.7452, 3)


class TestInvPinholeSmear(unittest.TestCase):
    """
        Test pinhole smeared data for invariant computation
    """
    def setUp(self):
        # data with smear info
        list = Loader().load("latex_smeared.xml")
        self.data_q_smear = list[0]

    def test_use_case_1(self):
        """
            Invariant without extrapolation
        """
        inv = invariant.InvariantCalculator(data=self.data_q_smear)
        qstar = inv.get_qstar()

        v = inv.get_volume_fraction(contrast=2.6e-6)
        s = inv.get_surface(contrast=2.6e-6, porod_const=2)
        # Test results
        self.assertAlmostEquals(qstar, 1.361677e-3, 4)
        self.assertAlmostEquals(v, 0.115352622, 2)
        self.assertAlmostEquals(s , 941.7452, 3 )

    def test_use_case_2(self):
        """
            Invariant without extrapolation. Invariant, volume fraction and surface 
            are given with errors.
        """
        # Create invariant object. Background and scale left as defaults.
        inv = invariant.InvariantCalculator(data=self.data_q_smear)

        # Get the invariant with errors
        qstar, qstar_err = inv.get_qstar_with_error()
        # Get the volume fraction and surface
        v, dv = inv.get_volume_fraction_with_error(contrast=2.6e-6)
        s, ds = inv.get_surface_with_error(contrast=2.6e-6, porod_const=2)
        # Test results
        self.assertAlmostEquals(qstar, 1.361677e-3, 4)
        self.assertAlmostEquals(v, 0.115352622, 2)
        self.assertAlmostEquals(s , 941.7452, 3 )

    def test_use_case_3(self):
        """
            Invariant with low-Q extrapolation
        """
        # Create invariant object. Background and scale left as defaults.
        inv = invariant.InvariantCalculator(data=self.data_q_smear)
        # Set the extrapolation parameters for the low-Q range
        inv.set_extrapolation(range='low', npts=20, function='guinier')
        # The version of the call without error
        qstar = inv.get_qstar(extrapolation='low')
        # The version of the call with error
        qstar, qstar_err = inv.get_qstar_with_error(extrapolation='low')
        # Get the volume fraction and surface
        v, dv = inv.get_volume_fraction_with_error(contrast=2.6e-6)
        s, ds = inv.get_surface_with_error(contrast=2.6e-6, porod_const=2)

        # Test results
        self.assertAlmostEquals(qstar, 0.00138756,2)
        self.assertAlmostEquals(v, 0.117226896,2)
        self.assertAlmostEquals(s ,941.7452, 3)

    def test_use_case_4(self):
        """
            Invariant with high-Q extrapolation
        """
        # Create invariant object. Background and scale left as defaults.
        inv = invariant.InvariantCalculator(data=self.data_q_smear)
        # Set the extrapolation parameters for the high-Q range
        inv.set_extrapolation(range='high', npts=10, function='power_law', power=4)
        # The version of the call without error
        qstar = inv.get_qstar(extrapolation='high')
        # The version of the call with error
        qstar, qstar_err = inv.get_qstar_with_error(extrapolation='high')

        # Test results
        self.assertAlmostEquals(qstar, 0.0045773,2)

    def test_use_case_5(self):
        """
            Invariant with both high- and low-Q extrapolation
        """
        # Create invariant object. Background and scale left as defaults.
        inv = invariant.InvariantCalculator(data=self.data_q_smear)
        # Set the extrapolation parameters for the low- and high-Q ranges
        inv.set_extrapolation(range='low', npts=10, function='guinier')
        inv.set_extrapolation(range='high', npts=10, function='power_law',
                              power=4)
        # The version of the call without error
        # The function parameter defaults to None, then is picked to be
        # 'power_law' for extrapolation='high'
        qstar = inv.get_qstar(extrapolation='both')
        # The version of the call with error
        qstar, qstar_err = inv.get_qstar_with_error(extrapolation='both')

        # Test results
        self.assertAlmostEquals(qstar, 0.00460319,3)
      
  
if __name__ == '__main__':
    unittest.main(testRunner=unittest.TextTestRunner(verbosity=2))
   
