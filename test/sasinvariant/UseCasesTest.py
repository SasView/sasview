"""Implementation of the use-case from a usage perspective."""

import os.path

import pytest

from sasdata.dataloader.loader import Loader

from sas.sascalc.invariant import invariant


def find(filename):
    return os.path.join(os.path.dirname(__file__), "data", filename)


class TestLineFit:
    """Test Line fit."""

    def setup_method(self):
        self.data_list = Loader().load(find("linefittest.txt"))
        self.data = self.data_list[0]

    def test_fit_line_data(self):
        """
        Bx^A becomes logB + A logX = ax+b in log-log space.
        For the extrapolation a can be fixed (usually to -4) or floating.
        Here we test letting it float.
        """
        fit = invariant.Extrapolator(data=self.data)

        # Let the power float (not fixed)
        p, _ = fit.fit(power=None)

        assert p[0] == pytest.approx(2.3983, abs=5e-4)
        assert p[1] == pytest.approx(0.87833, abs=5e-4)

    def test_fit_line_data_fixed(self):
        """Test fit for fixed power, in this case -4"""
        fit = invariant.Extrapolator(data=self.data)

        # Fixing  a = -power =4
        p, _ = fit.fit(power=-4)

        assert p[0] == pytest.approx(4)
        assert p[1] == pytest.approx(-4.0676, abs=5e-4)


class TestLineFitNoweight:
    """Test Line fit without weighting by the uncertainties in I."""

    def setup_method(self):
        self.data_list = Loader().load(find("linefittest_no_weight.txt"))
        self.data = self.data_list[0]

    def skip_test_fit_line_data_no_weight(self):
        """Tests linear fit, ax+b, without fixing the power a"""
        fit = invariant.Extrapolator(data=self.data)

        # Let the power float (not fixed)
        p, _ = fit.fit(power=None)

        assert p[0] == pytest.approx(2.4727, abs=5e-4)
        assert p[1] == pytest.approx(0.6, abs=5e-4)

    def test_fit_line_data_fixed_no_weight(self):
        """Tests linear fit, ax+b, with 'a' fixed"""
        fit = invariant.Extrapolator(data=self.data)

        # Fixing  a = -power =4
        p, _ = fit.fit(power=-4)

        assert p[0] == pytest.approx(4)
        assert p[1] == pytest.approx(-7.8, abs=5e-4)


class TestInvNoResolution:
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
    Background was set to 0.

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

    def setup_method(self):
        self.data_list = Loader().load(find("100nmSpheresNodQ.txt"))
        self.data = self.data_list[0]

    def test_no_extrapolation(self):
        """Test the Invariant without extrapolation."""

        # Background of zero as that is how the data was created.
        # A different background could cause negative intensities. Leave scale as defaults.
        inv = invariant.InvariantCalculator(data=self.data, background=0)

        qstar1 = inv.get_qstar()
        qstar, _ = inv.get_qstar_with_error()

        v, _ = inv.get_volume_fraction_with_error(contrast=2.2e-6)
        s, _ = inv.get_surface_with_error(contrast=2.2e-6, porod_const=1.825e-7)

        assert qstar1 == pytest.approx(qstar, abs=1e-6)
        assert qstar == pytest.approx(9.458239e-5, abs=1e-6)
        assert v == pytest.approx(0.01000, abs=1e-4)
        assert s == pytest.approx(6.000e-5, abs=5e-8)

    def test_low_q_guinier(self):
        """Test the Invariant with the low-Q Guinier extrapolation."""

        # Background of zero as that is how the data was created.
        # A different background could cause negative intensities. Leave scale as defaults.
        inv = invariant.InvariantCalculator(data=self.data, background=0)

        inv.set_extrapolation(range="low", npts=10, function="guinier")

        qstar1 = inv.get_qstar(extrapolation="low")
        qstar, _ = inv.get_qstar_with_error(extrapolation="low")

        v, _ = inv.get_volume_fraction_with_error(contrast=2.2e-6)
        s, _ = inv.get_surface_with_error(contrast=2.2e-6, porod_const=1.825e-7)

        assert qstar1 == pytest.approx(qstar, abs=1e-6)
        assert qstar == pytest.approx(9.458239e-5, abs=1e-6)
        assert v == pytest.approx(0.01000, abs=1e-4)
        assert s == pytest.approx(6.000e-5, abs=5e-8)

    def test_high_Q_power(self):
        """Test the Invariant with a Q^-4 high-Q extrapolation."""

        # Background of zero as that is how the data was created.
        # A different background could cause negative intensities. Leave scale as defaults.
        inv = invariant.InvariantCalculator(data=self.data, background=0)

        inv.set_extrapolation(range="high", npts=10, function="power_law", power=4)

        qstar1 = inv.get_qstar(extrapolation="high")
        qstar, _ = inv.get_qstar_with_error(extrapolation="high")

        v, _ = inv.get_volume_fraction_with_error(contrast=2.2e-6)
        s, _ = inv.get_surface_with_error(contrast=2.2e-6, porod_const=1.825e-7)

        # Test results
        assert qstar1 == pytest.approx(qstar, abs=1e-6)
        assert qstar == pytest.approx(9.458239e-5, abs=1e-6)
        assert v == pytest.approx(0.01000, abs=1e-4)
        assert s == pytest.approx(6.000e-5, abs=5e-8)

    def test_high_and_low_Q_extrapolation(self):
        """Test the Invariant with both a high- and low-Q extrapolation."""

        # Background of zero as that is how the data was created.
        # A different background could cause negative intensities. Leave scale as defaults.
        inv = invariant.InvariantCalculator(data=self.data, background=0)

        inv.set_extrapolation(range="low", npts=10, function="guinier")
        inv.set_extrapolation(range="high", npts=10, function="power_law", power=4)

        qstar1 = inv.get_qstar(extrapolation="both")
        qstar, _ = inv.get_qstar_with_error(extrapolation="both")

        v, _ = inv.get_volume_fraction_with_error(contrast=2.2e-6)
        s, _ = inv.get_surface_with_error(contrast=2.2e-6, porod_const=1.825e-7)

        # Test results
        assert qstar1 == qstar
        assert qstar == pytest.approx(9.458239e-5, abs=1e-6)
        assert v == pytest.approx(0.01000, abs=1e-4)
        assert s == pytest.approx(6.000e-5, abs=5e-8)


class TestInvPinholeSmeared:
    """
    Test invariant with pinhole smeared data.
    ..NOTE:
         The invariant code does NOT include pinhole smearing. Thus the
         invariant and derived vol fraction will be higher as the smearing
         is worse. The test values are given assuming the invariant is
         NOT handling pinhole smearing. Invariant calculation that include
         pinhole smearing effects could probably be included. If that is done
         and implmented the value in these tests should be adjusted to be
         approriately.

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
    the Sv however depends only on the Porod Constant which is an input
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

    def setup_method(self):
        self.data_list = Loader().load(find("100nmPinholeSphere.txt"))
        self.data = self.data_list[0]

    def test_no_extrapolation(self):
        """Test the Invariant without extrapolation."""
        inv = invariant.InvariantCalculator(data=self.data, background=0)

        qstar1 = inv.get_qstar()
        qstar, _ = inv.get_qstar_with_error()

        v, _ = inv.get_volume_fraction_with_error(contrast=2.2e-6)
        s, _ = inv.get_surface_with_error(contrast=2.2e-6, porod_const=1.825e-7)

        assert qstar1 == pytest.approx(qstar, abs=1e-6)
        assert qstar == pytest.approx(1.088e-4, abs=1e-6)
        assert v == pytest.approx(0.01150, abs=1e-4)
        assert s == pytest.approx(6.000e-5, abs=5e-8)

    def test_low_q_guinier(self):
        """Test the Invariant with the low-Q Guinier extrapolation."""
        inv = invariant.InvariantCalculator(data=self.data, background=0)

        inv.set_extrapolation(range="low", npts=10, function="guinier")

        qstar1 = inv.get_qstar(extrapolation="low")

        qstar, _ = inv.get_qstar_with_error(extrapolation="low")

        v, _ = inv.get_volume_fraction_with_error(contrast=2.2e-6)
        s, _ = inv.get_surface_with_error(contrast=2.2e-6, porod_const=1.825e-7)

        assert qstar1 == pytest.approx(qstar, abs=1e-6)
        assert qstar == pytest.approx(1.088e-4, abs=1e-6)
        assert v == pytest.approx(0.01150, abs=1e-4)
        assert s == pytest.approx(6.000e-5, abs=5e-8)

    def test_high_q_power(self):
        """Test the Invariant with a Q^-4 high-Q extrapolation."""
        inv = invariant.InvariantCalculator(data=self.data, background=0)

        inv.set_extrapolation(range="high", npts=10, function="power_law", power=4)

        qstar1 = inv.get_qstar(extrapolation="high")
        qstar, _ = inv.get_qstar_with_error(extrapolation="high")

        v, _ = inv.get_volume_fraction_with_error(contrast=2.2e-6)
        s, _ = inv.get_surface_with_error(contrast=2.2e-6, porod_const=1.825e-7)

        assert qstar1 == pytest.approx(qstar, abs=1e-6)
        assert qstar == pytest.approx(1.088e-4, abs=1e-6)
        assert v == pytest.approx(0.01150, abs=1e-4)
        assert s == pytest.approx(6.000e-5, abs=5e-8)

    def test_high_and_low_q_extrapolation(self):
        """Test the Invariant with both a high- and low-Q extrapolation."""
        inv = invariant.InvariantCalculator(data=self.data, background=0)

        inv.set_extrapolation(range="low", npts=10, function="guinier")
        inv.set_extrapolation(range="high", npts=10, function="power_law", power=4)

        qstar1 = inv.get_qstar(extrapolation="both")
        qstar, _ = inv.get_qstar_with_error(extrapolation="both")

        v, _ = inv.get_volume_fraction_with_error(contrast=2.2e-6)
        s, _ = inv.get_surface_with_error(contrast=2.2e-6, porod_const=1.825e-7)

        assert qstar1 == pytest.approx(qstar, abs=1e-6)
        assert qstar == pytest.approx(1.088e-4, abs=1e-6)
        assert v == pytest.approx(0.01150, abs=1e-4)
        assert s == pytest.approx(6.000e-5, abs=5e-8)


class TestInvSlitSmear:
    """
    Test slit smeared data for invariant computation.
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

    def setup_method(self):
        """Provide data with smear info."""
        data_list = Loader().load(find("1umSlitSmearSphere.ABS"))
        self.data_q_smear = data_list[0]

    def test_no_extrapolation(self):
        """
        Test the Invariant without extrapolation.  Because the object is
        so large and in this case I is only multiplied by q rather than q^2,
        a significant part of the invariant (~6.5%)is not captured with
        most of that (~5%) being in the low Q region. Thus the valuefor the
        invariant here is being adjusted down by 6.5% As seen when both
        extrapolations are included the integration seems to be computing
        a percent or two high.
        """
        inv = invariant.InvariantCalculator(data=self.data_q_smear, background=0)

        qstar1 = inv.get_qstar()
        qstar, _ = inv.get_qstar_with_error()

        v, _ = inv.get_volume_fraction_with_error(contrast=2.2e-6)
        s, _ = inv.get_surface_with_error(contrast=2.2e-6, porod_const=1.825e-8)

        assert qstar1 == qstar
        assert qstar == pytest.approx(8.8434e-5, abs=1.5e-6)
        assert v == pytest.approx(0.00935, abs=1.5e-4)
        assert s == pytest.approx(6.000e-6, abs=5e-8)

    def test_low_q_guinier(self):
        """
        Test the Invariant with  the low-Q Guinier extrapolation. This
        should now capture 98.5% of the invariant so in principle the
        calculation should give a value that is 1.5% below the theoretical
        value.  This should be within tolerance so leave the invariant
        test value at the true theoretical value here.
        """
        inv = invariant.InvariantCalculator(data=self.data_q_smear, background=0)

        inv.set_extrapolation(range="low", npts=10, function="guinier")

        qstar1 = inv.get_qstar(extrapolation="low")
        qstar, _ = inv.get_qstar_with_error(extrapolation="low")

        v, _ = inv.get_volume_fraction_with_error(contrast=2.2e-6)
        s, _ = inv.get_surface_with_error(contrast=2.2e-6, porod_const=1.825e-8)

        # Test results
        assert qstar1 == qstar
        assert qstar == pytest.approx(9.458239e-5, abs=1.5e-6)
        assert v == pytest.approx(0.01, abs=15e-4)
        assert s == pytest.approx(6.000e-6, abs=5e-8)

    def test_high_q_power(self):
        """
        Test the Invariant with the high-Q -4 power law extrapolation.
        This should still only capture 95% of the true invariant so i
        principle the calculation should give a value that is 5% lower than
        the true theoretical value. Thus here again we adjust the test
        value for the invariant down, this time by 5%.
        """
        inv = invariant.InvariantCalculator(data=self.data_q_smear, background=0)

        inv.set_extrapolation(range="high", npts=10, function="power_law", power=4)

        qstar1 = inv.get_qstar(extrapolation="high")
        qstar, _ = inv.get_qstar_with_error(extrapolation="high")

        v, _ = inv.get_volume_fraction_with_error(contrast=2.2e-6)
        s, _ = inv.get_surface_with_error(contrast=2.2e-6, porod_const=1.825e-8)

        assert qstar1 == qstar
        assert qstar == pytest.approx(8.9853e-5, abs=1.5e-6)
        assert v == pytest.approx(0.0095, abs=1.5e-4)
        assert s == pytest.approx(6.000e-6, abs=5e-8)

    def test_high_and_low_q_extrapolation(self):
        """
        Test the Invariant with both the low Q Guinier and the high-Q -4
        power law extrapolations. This should now capture all the invariant
        so we now again give the true theoretical invariant as the test
        value to compare agains.
        """
        inv = invariant.InvariantCalculator(data=self.data_q_smear, background=0)

        inv.set_extrapolation(range="low", npts=10, function="guinier")
        inv.set_extrapolation(range="high", npts=10, function="power_law", power=4)

        qstar1 = inv.get_qstar(extrapolation="low")
        qstar, _ = inv.get_qstar_with_error(extrapolation="low")

        v, _ = inv.get_volume_fraction_with_error(contrast=2.2e-6)
        s, _ = inv.get_surface_with_error(contrast=2.2e-6, porod_const=1.825e-8)

        assert qstar1 == qstar
        assert qstar == pytest.approx(9.458239e-5, abs=1.5e-6)
        assert v == pytest.approx(0.01, abs=15e-4)
        assert s == pytest.approx(6.000e-6, abs=5e-8)
