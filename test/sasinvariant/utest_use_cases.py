"""
   Implementation of the use-case from a usage perspective.

   TODO: The calculation of the uncertainties needs to be checked
   TODO: It woudl be good to add tests for the uncertainties

"""

import os.path
import unittest

from sasdata.dataloader.loader import Loader

from sas.sascalc.invariant import invariant


def find(filename):
    return os.path.join(os.path.dirname(__file__), 'data', filename)


class Data1D:
    pass


class TestLineFit(unittest.TestCase):
    """
        Test Line fit
    """
    def setUp(self):
        self.data_list = Loader().load(find("linefittest.txt"))
        self.data = self.data_list[0]

    def test_fit_line_data(self):
        """
            Fit_Test_1: test linear fit, ax +b. The power law is calculated
            on the log data so that B * x^A becomes logB + A logX = ax+b.
            For the extrapolation a can be fixed (usually to -4) or floating.
            Here we test letting it float.
        """

        # Create invariant object. Background and scale left as defaults.
        fit = invariant.Extrapolator(data=self.data)

        # Let the power float (not fixed)
        p, dp = fit.fit(power=None)

        # Test results
        self.assertAlmostEqual(p[0], 2.3983,3)
        self.assertAlmostEqual(p[1], 0.87833,3)

    def test_fit_line_data_fixed(self):
        """
            Fit_Test_2: test linear fit, ax +b, with 'a' fixed
        """

        # Create invariant object. Background and scale left as defaults.
        fit = invariant.Extrapolator(data=self.data)

        # Fixing  a = -power =4
        p, dp = fit.fit(power=-4)

        # Test results
        self.assertAlmostEqual(p[0], 4)
        self.assertAlmostEqual(p[1], -4.0676,3)


class TestLineFitNoweight(unittest.TestCase):
    """
        Test Line fit without weighting by the uncertainties in I
    """
    def setUp(self):
        self.data_list = Loader().load(find("linefittest_no_weight.txt"))
        self.data = self.data_list[0]

    def skip_test_fit_line_data_no_weight(self):
        """
            Fit_Test_1: test linear fit, ax +b, without fixing the power a
        """

        # Create invariant object. Background and scale left as defaults.
        fit = invariant.Extrapolator(data=self.data)

        # Let the power float (not fixed)
        p, dp = fit.fit(power=None)

        # Test results
        self.assertAlmostEqual(p[0], 2.4727,3)
        self.assertAlmostEqual(p[1], 0.6,3)

    def test_fit_line_data_fixed_no_weight(self):
        """
            Fit_Test_2: test linear fit, ax +b, with 'a' fixed
        """

        # Create invariant object. Background and scale left as defaults.
        fit = invariant.Extrapolator(data=self.data)

        # Fixing  a = -power =4
        p, dp = fit.fit(power=-4)

        # Test results
        self.assertAlmostEqual(p[0], 4)
        self.assertAlmostEqual(p[1], -7.8,3)


class TestInvNoResolution(unittest.TestCase):
    """
        Test unsmeared data ("perfect" pinhole) for invariant computation.
        The test data is simulated using the sphere form factor simulating
        a 1% solution of SiO2 sphere of 100nm in diameter in D2O with zero
        polydispersity.

        Moreover NO resolution smearing was included so that this would be for
        a perfect, infinitely small pinhole camera.

        The parameters then are:
        vol fraction (Phi) = 0.01
        SLD = 4.2e-6 1/A (silica SLD)
        Solvent SLD = 6.4e-6 1/A (D2O SLD)
        Backgroun was set to 0.

        From this we can calculate the Sv (3*Phi/R):
        Sv = N * Surface of one sphere/ V_T
        V_T = N * Vol of one sphere/Phi
        Sv = surface of one sphere * Phi/Vol of one sphere =
        4 Pi R^2 * Phi/({4/3) Pi R^3) =
        3 * Phi/R = 6e-5 1/A

        Then the Porod Constant = 2 * PI *(SLD_solv-SLD)^2 * Sv
        = 1.825E-7 cm^-1A^-4

        and Q* = 2 * Pi^2 * (SLD_solv-SLD)^2 * Phi * (1-Phi)
        = 9.458239e-13 A^-4 = 9.458239e-5

        ..NOTE: with zero resolution there are two problems due to the fact
        that the curves have many deep dips to zero but they do not get well
        captured with fininte number of points.  This means:
        *  It is almost impossible to get a good experimental value for the
           Porod constant
        *  It also means that the integration I*q^2 will be slightly high (of
           order <1% in this case)since many of the dips won't be completly
           captured.
    """
    def setUp(self):
        self.data_list = Loader().load(find("100nmSpheresNodQ.txt"))
        self.data = self.data_list[0]

#    def test_wrong_data(self):
#        """ test receiving Data1D not of type loader"""
#        self.assertRaises(ValueError,invariant.InvariantCalculator, Data1D())
#
    def test_use_case_1(self):
        """
            Test the Invariant without extrapolation
        """
        # Create an invariant object with background of zero as that is how the
        # data was created. A different background could cause negative
        # intensities. Leave scale as defaults.
        inv = invariant.InvariantCalculator(data=self.data, background=0)

        # We have to be able to tell the InvariantCalculator whether we want the
        # extrapolation or not. By default, when the user doesn't specify, we
        # should compute Q* without extrapolation. That's what should be done
        # in __init__.

        # We call get_qstar() with no argument, which signifies that we do NOT
        # want extrapolation.

        # The version of the call without uncertainties. unlike the v and s
        # calculations the call to get_qstar_with_error runs the ge_qstar
        # method but does not read the return value so check that here.
        qstar1 = inv.get_qstar()

        # The version of the call including uncertainty
        qstar, qstar_err = inv.get_qstar_with_error()

        # The volume fraction and surface use Q*. That means that the following
        # methods should check that Q* has been computed. If not, it should
        # compute it by calling get_qstare(), leaving the parameters as default.
        v, dv = inv.get_volume_fraction_with_error(contrast=2.2e-6)
        s, ds = inv.get_surface_with_error(contrast=2.2e-6,
                                           porod_const=1.825e-7)

        # Test results
        self.assertEqual(qstar1, qstar)
        self.assertAlmostEqual(qstar, 9.458239e-5,delta=1e-6)
        self.assertAlmostEqual(v, 0.01000, delta=1e-4)
        self.assertAlmostEqual(s , 6.000e-5, 7)

    def test_use_case_2(self):
        """
            Test the Invariant with the low-Q Guinier extrapolation
        """
        # Create an invariant object with background of zero as that is how the
        # data was created. A different background could cause negative
        # intensities. Leave scale as defaults.
        inv = invariant.InvariantCalculator(data=self.data, background=0)

        # Now we do want to use the extrapoloation so first we need to set
        # the extrapolation parameters, in thsi case for the low-Q range

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

        # The version of the call without error again checks that the function
        # returns the same value as it calculates and passes to the verion of
        # the call with uncertainties.
        #
        # Note that at this point, we could still compute Q* without
        # extrapolation by calling get_qstar with no arguments, or with
        # extrapolation=None.
        # But of course we want to test the low Q Guinier extrapolation so...
        qstar1 = inv.get_qstar(extrapolation='low')

        # And again, using the version of the call which also retruns
        # the uncertainties.
        qstar, qstar_err = inv.get_qstar_with_error(extrapolation='low')

        # Get the volume fraction and surface
        v, dv = inv.get_volume_fraction_with_error(contrast=2.2e-6)
        s, ds = inv.get_surface_with_error(contrast=2.2e-6,
                                           porod_const=1.825e-7)

        # Test results
        self.assertEqual(qstar1, qstar)
        self.assertAlmostEqual(qstar, 9.458239e-5,delta=1e-6)
        self.assertAlmostEqual(v, 0.01000, delta=1e-4)
        self.assertAlmostEqual(s , 6.000e-5, 7)

    def test_use_case_3(self):
        """
            Test the Invariant with a Q^-4 high-Q extrapolation
        """
        # Create an invariant object with background of zero as that is how the
        # data was created. A different background could cause negative
        # intensities. Leave scale as defaults.
        inv = invariant.InvariantCalculator(data=self.data, background=0)

        # Now we set the extrapolation parameters to test the high-Q range
        # Note: that we are fixing the power law to 4 in this case, appropriate
        # for a solid sphere at high q.
        inv.set_extrapolation(range='high', npts=10, function='power_law',
                              power=4)

        # Again we start with the version of the call that does not return the
        # uncertainties to verify that it returns the same value as it passes
        # to the verion of the call with uncertainties.
        # Again by passing an extrapolation value, the values just set for
        # that extrapolation are used.
        qstar1 = inv.get_qstar(extrapolation='high')

        # Now the same call to the "full" version which also returns
        # uncertainties
        qstar, qstar_err = inv.get_qstar_with_error(extrapolation='high')

        # Get the volume fraction and surface
        v, dv = inv.get_volume_fraction_with_error(contrast=2.2e-6)
        s, ds = inv.get_surface_with_error(contrast=2.2e-6,
                                           porod_const=1.825e-7)

        # Test results
        self.assertEqual(qstar1, qstar)
        self.assertAlmostEqual(qstar, 9.458239e-5,delta=1e-6)
        self.assertAlmostEqual(v, 0.01000, delta=1e-4)
        self.assertAlmostEqual(s , 6.000e-5, 7)

    def test_use_case_4(self):
        """
            Test the Invariant with both a high- and low-Q extrapolation
        """
        # Create an invariant object with background of zero as that is how the
        # data was created. A different background could cause negative
        # intensities. Leave scale as defaults.
        inv = invariant.InvariantCalculator(data=self.data, background=0)


        # Finally set the extrapolation parameters to test both the low- and
        # high-Q extrapolotaions applied together.
        inv.set_extrapolation(range='low', npts=10, function='guinier')
        inv.set_extrapolation(range='high', npts=10, function='power_law',
                              power=4)

        # Again we start with the version of the call that does not return the
        # uncertainties to verify that it returns the same value as it passes
        # to the verion of the call with uncertainties.
        # Again by passing an extrapolation value, the values just set for
        # that extrapolation are used.
        qstar1 = inv.get_qstar(extrapolation='both')

        # The version of the call with error
        qstar, qstar_err = inv.get_qstar_with_error(extrapolation='both')

        # Get the volume fraction and surface
        v, dv = inv.get_volume_fraction_with_error(contrast=2.2e-6)
        s, ds = inv.get_surface_with_error(contrast=2.2e-6,
                                           porod_const=1.825e-7)

        # Test results
        self.assertEqual(qstar1, qstar)
        self.assertAlmostEqual(qstar, 9.458239e-5,delta=1e-6)
        self.assertAlmostEqual(v, 0.01000, delta=1e-4)
        self.assertAlmostEqual(s , 6.000e-5, 7)

    # Note - on March 21, 2020 PDB removed the low Q power law extrapolotion
    # tests. In the first place they are totally bogus based on assuming the
    # code was correct, looking at the values returned for a totally random
    # set of data and parameters and asserting them true. Moreover there is no
    # clear data set that could be used that would be reasonable here.  It is
    # not even clear that this is a valid extrapolation.


class TestInvPinholeSmeared(unittest.TestCase):
    """
        Test invariant with pinhole smeared data.
        ..NOTE:
             As of March 21, 2020 the invariant code does NOT include
             pinhole smearing. Thus the invariant and derived vol fraction
             will be high. Higher as the smearing is worse.  Note that an
             invariant calculation that incluede pinhole smearing effects
             could probably be included (need to either derive or find where
             it has been). If that is done and implmented the value in these
             tests should be adjusted to be approriately. The test values are
             given assuming the invariant is NOT handling pinhole smearing.

         ..NOTE2:
             The data supplied here is for the exact same system as above,
             so the result values should in principle be identical. However the
             model also assumed a 15% dQ/Q.  This is quite large but smooths
             all the wiggles out at high Q. This allows for a reasonable
             experimental determination of the porod constant (unlike in the
             previous case without resolution smearing) but means the integral
             will evaluate high and the vol fraction should thus be high.

        The fundamental theoretical values are the same as before (given the
        system is the same) but due to the 15% dQ/Q the invariant, and thus the
        volume fraction computed from that invariant, are roughly 15% high
        again because the invariant calculation is assuming a dQ/Q of 0%.
        the Sv however depends only on the Porod Constane which is an input
        parameter and so remains correct (the the extent the supplied constant
        is correct).  While the actual code here is in fact using the invariant
        in the computation of Sv it also uses Phi and so the errors cancel (as
        would be expected given in principle Sv does not depend on Q*).
        Ironically, the Porod Constant estimation from the experimental data
        will actually be much ore accurate using the smeared data.  Thus, the
        correct values for the test are:
        * Porod Constat = 1.825E-7 cm^-1A^-4
        * Sv = 6e-5 * 1.15 ~ 6.9e-5 1/A
        * Vol Fraction = 0.01 * 1.15 ~ 0.0115
        * Q* = 9.458239e-5 * 1.15 ~ 1.088e-4 cm^-1 A^-3



    """
    def setUp(self):
        self.data_list = Loader().load(find("100nmPinholeSphere.txt"))
        self.data = self.data_list[0]

    def test_wrong_data(self):
        """ test receiving Data1D not of type loader"""
        self.assertRaises(ValueError,invariant.InvariantCalculator, Data1D())

    def test_use_case_1(self):
        """
            Test the Invariant without extrapolation
        """
        # Create an invariant object with background of zero as that is how the
        # data was created. A different background could cause negative
        # intensities. Leave scale as defaults.
        inv = invariant.InvariantCalculator(data=self.data, background=0)

        # We have to be able to tell the InvariantCalculator whether we want the
        # extrapolation or not. By default, when the user doesn't specify, we
        # should compute Q* without extrapolation. That's what should be done
        # in __init__.

        # We call get_qstar() with no argument, which signifies that we do NOT
        # want extrapolation.

        # The version of the call without uncertainties. unlike the v and s
        # calculations the call to get_qstar_with_error runs the ge_qstar
        # method but does not read the return value so check that here.
        qstar1 = inv.get_qstar()

        # The version of the call including uncertainty
        qstar, qstar_err = inv.get_qstar_with_error()

        # The volume fraction and surface use Q*. That means that the following
        # methods should check that Q* has been computed. If not, it should
        # compute it by calling get_qstare(), leaving the parameters as default.
        v, dv = inv.get_volume_fraction_with_error(contrast=2.2e-6)
        s, ds = inv.get_surface_with_error(contrast=2.2e-6,
                                           porod_const=1.825e-7)

        # Test results
        self.assertEqual(qstar1, qstar)
        self.assertAlmostEqual(qstar, 1.088e-4,delta=1e-6)
        self.assertAlmostEqual(v, 0.01150, delta=1e-4)
        self.assertAlmostEqual(s , 6.000e-5, 7)

    def test_use_case_2(self):
        """
            Tes the Invariant with the low-Q Guinier extrapolation
        """
        # Create an invariant object with background of zero as that is how the
        # data was created. A different background could cause negative
        # intensities. Leave scale as defaults.
        inv = invariant.InvariantCalculator(data=self.data, background=0)

        # Now we do want to use the extrapoloation so first we need to set
        # the extrapolation parameters, in thsi case for the low-Q range

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

        # The version of the call without error again checks that the function
        # returns the same value as it calculates and passes to the verion of
        # the call with uncertainties.
        #
        # Note that at this point, we could still compute Q* without
        # extrapolation by calling get_qstar with no arguments, or with
        # extrapolation=None.
        # But of course we want to test the low Q Guinier extrapolation so...
        qstar1 = inv.get_qstar(extrapolation='low')

        # And again, using the version of the call which also retruns
        # the uncertainties.
        qstar, qstar_err = inv.get_qstar_with_error(extrapolation='low')

        # Get the volume fraction and surface
        v, dv = inv.get_volume_fraction_with_error(contrast=2.2e-6)
        s, ds = inv.get_surface_with_error(contrast=2.2e-6,
                                           porod_const=1.825e-7)

        # Test results
        self.assertEqual(qstar1, qstar)
        self.assertAlmostEqual(qstar, 1.088e-4,delta=1e-6)
        self.assertAlmostEqual(v, 0.01150, delta=1e-4)
        self.assertAlmostEqual(s , 6.000e-5, 7)

    def test_use_case_3(self):
        """
            Test the Invariant with a Q^-4 high-Q extrapolation
        """
        # Create an invariant object with background of zero as that is how the
        # data was created. A different background could cause negative
        # intensities. Leave scale as defaults.
        inv = invariant.InvariantCalculator(data=self.data, background=0)

        # Now we set the extrapolation parameters to test the high-Q range
        # Note: that we are fixing the power law to 4 in this case, appropriate
        # for a solid sphere at high q.
        inv.set_extrapolation(range='high', npts=10, function='power_law',
                              power=4)

        # Again we start with the version of the call that does not return the
        # uncertainties to verify that it returns the same value as it passes
        # to the verion of the call with uncertainties.
        # Again by passing an extrapolation value, the values just set for
        # that extrapolation are used.
        qstar1 = inv.get_qstar(extrapolation='high')

        # Now the same call to the "full" version which also returns
        # uncertainties
        qstar, qstar_err = inv.get_qstar_with_error(extrapolation='high')

        # Get the volume fraction and surface
        v, dv = inv.get_volume_fraction_with_error(contrast=2.2e-6)
        s, ds = inv.get_surface_with_error(contrast=2.2e-6,
                                           porod_const=1.825e-7)

        # Test results
        self.assertEqual(qstar1, qstar)
        self.assertAlmostEqual(qstar, 1.088e-4,delta=1e-6)
        self.assertAlmostEqual(v, 0.01150, delta=1e-4)
        self.assertAlmostEqual(s , 6.000e-5, 7)

    def test_use_case_4(self):
        """
            Test the Invariant with both a high- and low-Q extrapolation
        """
        # Create an invariant object with background of zero as that is how the
        # data was created. A different background could cause negative
        # intensities. Leave scale as defaults.
        inv = invariant.InvariantCalculator(data=self.data, background=0)


        # Finally set the extrapolation parameters to test both the low- and
        # high-Q extrapolotaions applied together.
        inv.set_extrapolation(range='low', npts=10, function='guinier')
        inv.set_extrapolation(range='high', npts=10, function='power_law',
                              power=4)

        # Again we start with the version of the call that does not return the
        # uncertainties to verify that it returns the same value as it passes
        # to the verion of the call with uncertainties.
        # Again by passing an extrapolation value, the values just set for
        # that extrapolation are used.
        qstar1 = inv.get_qstar(extrapolation='both')

        # The version of the call with error
        qstar, qstar_err = inv.get_qstar_with_error(extrapolation='both')

        # Get the volume fraction and surface
        v, dv = inv.get_volume_fraction_with_error(contrast=2.2e-6)
        s, ds = inv.get_surface_with_error(contrast=2.2e-6,
                                           porod_const=1.825e-7)

        # Test results
        self.assertEqual(qstar1, qstar)
        self.assertAlmostEqual(qstar, 1.088e-4,delta=1e-6)
        self.assertAlmostEqual(v, 0.01150, delta=1e-4)
        self.assertAlmostEqual(s , 6.000e-5, 7)

    # Note - on March 21, 2020 PDB removed the low Q power law extrapolotion
    # tests. In the first place they are totally bogus based on assuming the
    # code was correct, looking at the values returned for a totally random
    # set of data and parameters and asserting them true. Moreover there is no
    # clear data set that could be used that would be reasonable here.  It is
    # not even clear that this is a valid extrapolation.


class TestInvSlitSmear(unittest.TestCase):
    """
        Test slit smeared data for invariant computation
        ..NOTE:
           The Invariant caculation for an infinite slit smearing has been
           known for a long time and is included here.  Ironically this means
           that as of March 21, 2020, the invarian calucation on slit smeared
           data will provide more accurate results.

        The data provided for this test was again computed using the sphere
        form factor simulating a similar 1% solution of SiO2 sphere in D2O but
        this time with a 1micron diameter - again with zero polydispersity.

        This time however a slit smearing of was applied to simulate data from
        the NIST USANS instrument (dl=0.117 1/A).

        The parameters then are:
        vol fraction (Phi) = 0.01
        SLD = 4.2e-6 1/A (silica SLD)
        Solvent SLD = 6.4e-6 1/A (D2O SLD)
        Backgroun was set to 0.

        From this we can again calculate the Sv (3*Phi/R):
        Sv = N * Surface of one sphere/ V_T
        V_T = N * Vol of one sphere/Phi
        Sv = surface of one sphere * Phi/Vol of one sphere =
        4 Pi R^2 * Phi/({4/3) Pi R^3) =
        3 * Phi/R = 6e-6 1/A

        Then the Porod Constant = 2 * PI *(SLD_solv-SLD)^2 * Sv
        = 1.825E-8 cm^-1A^-4

        and Q* = 2 * Pi^2 * (SLD_solv-SLD)^2 * Phi * (1-Phi) remains the same,
        as it should by the very principle of the invariant at:
        = 9.458239e-13 A^-4 = 9.458239e-5

    """
    def setUp(self):
        # data with smear info
        list = Loader().load(find("1umSlitSmearSphere.ABS"))
        self.data_q_smear = list[0]

    def test_use_case_1(self):
        """
            Test the Invariant without extrapolation.  Because the object is
            so large and in this case I is only multiplied by q rather than q^2,
            a significant part of the invariant (~6.5%)is not captured with
            most of that (~5%) being in the low Q region. Thus the valuefor the
            invariant here is being adjusted down by 6.5% As seen when both
            extrapolations are included the integration seems to be computing
            a percent or two high.
        """
        # Create an invariant object with background of zero as that is how the
        # data was created. A different background could cause negative
        # intensities. Leave scale as defaults.
        inv = invariant.InvariantCalculator(data=self.data_q_smear,
                                            background=0)
        # again using calls to both for reasons described in previous test
        # classes above.
        qstar1 = inv.get_qstar()
        qstar, qstar_err = inv.get_qstar_with_error()

        # Get the volume fraction and surface
        v, dv = inv.get_volume_fraction_with_error(contrast=2.2e-6)
        s, ds = inv.get_surface_with_error(contrast=2.2e-6,
                                           porod_const=1.825e-8)
        # Test results
        self.assertEqual(qstar1, qstar)
        self.assertAlmostEqual(qstar, 8.8434e-5, delta=1.5e-6)
        self.assertAlmostEqual(v, 0.00935, delta=1.5e-4)
        self.assertAlmostEqual(s , 6.000e-6, 7 )

    def test_use_case_2(self):
        """
            Test the Invariant with  the low-Q Guinier extrapolation. This
            should now capture 98.5% of the invariant so in principle the
            calculation should give a value that is 1.5% below the theoretical
            value.  This should be within tolerance so leave the invariant
            test value at the true theoretical value here.
        """
        # Create an invariant object with the background set to zero
        inv = invariant.InvariantCalculator(data=self.data_q_smear,
                                            background=0)
        # Set the extrapolation parameters for the low-Q range
        inv.set_extrapolation(range='low', npts=10, function='guinier')
        # again using calls to both for reasons described in previous test
        # classes above.
        qstar1 = inv.get_qstar(extrapolation='low')
        qstar, qstar_err = inv.get_qstar_with_error(extrapolation='low')
        # Get the volume fraction and surface
        v, dv = inv.get_volume_fraction_with_error(contrast=2.2e-6)
        s, ds = inv.get_surface_with_error(contrast=2.2e-6,
                                           porod_const=1.825e-8)

        # Test results
        self.assertEqual(qstar1, qstar)
        self.assertAlmostEqual(qstar, 9.458239e-5, delta=1.5e-6)
        self.assertAlmostEqual(v, 0.01, delta=15e-4)
        self.assertAlmostEqual(s , 6.000e-6, 7 )

    def test_use_case_3(self):
        """
            Test the Invariant with the high-Q -4 power law extrapolation.
            This should still only capture 95% of the true invariant so i
            principle the calculation should give a value that is 5% lower than
            the true theoretical value. Thus here again we adjust the test
            value for the invariant down, this time by 5%.
        """
        # Create an invariant object with the background set to zero
        inv = invariant.InvariantCalculator(data=self.data_q_smear,
                                            background=0)
        # Set the extrapolation parameters for the high-Q range
        inv.set_extrapolation(range='high', npts=10,
                              function='power_law', power=4)
        # again using calls to both for reasons described in previous test
        # classes above.
        qstar1 = inv.get_qstar(extrapolation='high')
        qstar, qstar_err = inv.get_qstar_with_error(extrapolation='high')
        # Get the volume fraction and surface
        v, dv = inv.get_volume_fraction_with_error(contrast=2.2e-6)
        s, ds = inv.get_surface_with_error(contrast=2.2e-6,
                                           porod_const=1.825e-8)

        # Test results
        self.assertEqual(qstar1, qstar)
        self.assertAlmostEqual(qstar, 8.9853e-5, delta=1.5e-6)
        self.assertAlmostEqual(v, 0.0095, delta=1.5e-4)
        self.assertAlmostEqual(s , 6.000e-6, 7 )

    def test_use_case_4(self):
        """
            Test the Invariant with both the low Q Guinier and the high-Q -4
            power law extrapolations. This should now capture all the invariant
            so we now again give the true theoretical invariant as the test
            value to compare agains.
        """
        # Create an invariant object with the background set to zero
        inv = invariant.InvariantCalculator(data=self.data_q_smear,
                                            background=0)
        # Set the extrapolation parameters for the low- and high-Q ranges
        inv.set_extrapolation(range='low', npts=10, function='guinier')
        inv.set_extrapolation(range='high', npts=10, function='power_law',
                              power=4)
        # again using calls to both for reasons described in previous test
        # classes above.
        qstar1 = inv.get_qstar(extrapolation='low')
        qstar, qstar_err = inv.get_qstar_with_error(extrapolation='low')
        # Get the volume fraction and surface
        v, dv = inv.get_volume_fraction_with_error(contrast=2.2e-6)
        s, ds = inv.get_surface_with_error(contrast=2.2e-6,
                                           porod_const=1.825e-8)

        # Test results
        self.assertEqual(qstar1, qstar)
        self.assertAlmostEqual(qstar, 9.458239e-5, delta=1.5e-6)
        self.assertAlmostEqual(v, 0.01, delta=15e-4)
        self.assertAlmostEqual(s , 6.000e-6, 7 )


if __name__ == '__main__':
    unittest.main(testRunner=unittest.TextTestRunner(verbosity=2))

