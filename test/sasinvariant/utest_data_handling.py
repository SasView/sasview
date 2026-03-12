"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation.

See the license text in license.txt

copyright 2010, University of Tennessee
"""

import math

import numpy as np
import pytest

from sasdata.dataloader.data_info import Data1D

from sas.sascalc.invariant import invariant


class TestLinearFit:
    """Test Line fitting of the invariant calculator."""

    @pytest.fixture(autouse=True)
    def setup(self, linear_data):
        self.data = linear_data

    def test_fit_linear_data(self):
        """Test a simple linear fit."""
        fit = invariant.Extrapolator(data=self.data)
        p, _ = fit.fit()

        assert p[0] == pytest.approx(1.0, abs=1e-5)
        assert p[1] == pytest.approx(0.0, abs=1e-5)

    def test_fit_linear_data_with_noise(self):
        """Test a simple linear fit with noise."""
        self.data.y += 0.1 * (np.random.random(len(self.data.y)) - 0.5)

        fit = invariant.Extrapolator(data=self.data)
        p, _ = fit.fit()

        assert math.fabs(p[0] - 1.0) < 0.05
        assert math.fabs(p[1]) < 0.1

    def test_fit_with_fixed_parameter(self):
        """Linear fit for y = ax + b, where a is fixed."""
        fit = invariant.Extrapolator(data=self.data)
        p, _ = fit.fit(power=-1.0)

        assert p[0] == pytest.approx(1.0, abs=1e-5)
        assert p[1] == pytest.approx(0.0, abs=1e-5)

    def test_fit_linear_data_with_noise_and_fixed_par(self):
        """Test a simple linear fit with noise and a fixed parameter."""
        self.data.y += 0.1 * (np.random.random(len(self.data.y)) - 0.5)

        fit = invariant.Extrapolator(data=self.data)
        p, _ = fit.fit(power=-1.0)

        assert math.fabs(p[0] - 1.0) < 0.05
        assert math.fabs(p[1]) < 0.1


class TestInvariantCalculator:
    """Test main functionality of the Invariant calculator."""

    @pytest.fixture(autouse=True)
    def setup(self, real_data):
        self.data = real_data

    def test_initial_data_processing(self):
        """
        Test whether the background and scale are handled properly
        when creating an InvariantCalculator object.
        """
        length = len(self.data.x)
        assert length == len(self.data.y)

        inv = invariant.InvariantCalculator(self.data)
        assert len(inv._data.x) == length
        assert inv._data.x == pytest.approx(self.data.x)

        # Now the same thing with a background value
        bck = 0.1
        inv = invariant.InvariantCalculator(self.data, background=bck)
        assert inv._background == bck
        assert len(inv._data.x) == length
        assert inv._data.y == pytest.approx(self.data.y - bck)

        # Now the same thing with a scale value
        scale = 0.1
        inv = invariant.InvariantCalculator(self.data, scale=scale)
        assert inv._scale == scale
        assert len(inv._data.x) == length
        assert inv._data.y == pytest.approx(self.data.y * scale)

    def test_incompatible_data_class(self):
        """Check that only classes that inherit from Data1D are allowed as data."""
        class Incompatible:
            pass

        with pytest.raises(ValueError):
            invariant.InvariantCalculator(Incompatible())

    @pytest.mark.parametrize("dy", [[], None, [0, 0, 0, 0]])
    def test_error_treatment(self, dy):
        """Check that the error array is properly set to 1.0 when not provided or when all values are zero."""
        x = np.asarray(np.asarray([0, 1, 2, 3]))
        y = np.asarray(np.asarray([1, 1, 1, 1]))
        data = Data1D(x=x, y=y, dy=dy)

        inv = invariant.InvariantCalculator(data)

        assert  len(inv._data.dy) == len(inv._data.x) == len(inv._data.y)
        assert inv._data.dy == pytest.approx([1, 1, 1, 1], abs=1e-10)

    def test_qstar_no_extrapolation(self):
        """Test the invariant calculation without extrapolation."""
        inv = invariant.InvariantCalculator(self.data)

        qstar = inv.get_qstar()
        qstar_with_error, dqstar = inv.get_qstar_with_error()

        assert qstar == pytest.approx(qstar_with_error, abs=1e-10)
        assert dqstar > 0.0

    def test_qstar_low_q_guinier(self):
        """Test low-q extrapolation with a Guinier function."""
        inv = invariant.InvariantCalculator(self.data)
        qstar, dqstar = inv.get_qstar_with_error()

        inv.set_extrapolation("low", npts=10, function="guinier")
        qs_extr, dqs_extr = inv.get_qstar_with_error("low")
        delta_qs_extr, delta_dqs_extr = inv.get_qstar_low()

        assert qs_extr == qstar + delta_qs_extr
        assert dqs_extr == math.sqrt(dqstar * dqstar + delta_dqs_extr * delta_dqs_extr)

    def test_qstar_high_q(self):
        """Test high-q extrapolation with a power law function."""
        inv = invariant.InvariantCalculator(self.data)
        qstar, dqstar = inv.get_qstar_with_error()

        inv.set_extrapolation("high", npts=95, function="power_law")
        qs_extr, dqs_extr = inv.get_qstar_with_error("high")
        delta_qs_extr, delta_dqs_extr = inv.get_qstar_high()

        # In principle the slope should be -4, but SasView estimates it to be around 3.92.
        assert inv._high_extrapolation_function.power == pytest.approx(4, abs=0.1)
        assert qs_extr == qstar + delta_qs_extr

        expected_dqs_extr = math.sqrt(dqstar * dqstar + delta_dqs_extr * delta_dqs_extr)
        assert dqs_extr == pytest.approx(expected_dqs_extr, abs=1e-10)

    @pytest.fixture
    def configured_inv(self):
        inv = invariant.InvariantCalculator(self.data)
        inv.set_extrapolation("low", npts=10, function="guinier")
        inv.set_extrapolation("high", npts=20, function="power_law")
        return inv

    def test_qstar_both_extrapolation(self, configured_inv):
        """Test that combined low-q and high-q extrapolation gives the correct qstar."""
        qstar, dqstar = configured_inv.get_qstar_with_error()
        qs_extr, dqs_extr = configured_inv.get_qstar_with_error("both")
        delta_qs_low, delta_dqs_low = configured_inv.get_qstar_low()
        delta_qs_hi, delta_dqs_hi = configured_inv.get_qstar_high()

        assert qs_extr == pytest.approx(qstar + delta_qs_low + delta_qs_hi, abs=1e-8)
        expected_dqs = math.sqrt(dqstar**2 + delta_dqs_low**2 + delta_dqs_hi**2)
        assert dqs_extr == pytest.approx(expected_dqs, abs=1e-8)

    @pytest.mark.parametrize("extrapolation", [None, "low", "high", "both"])
    def test_volume_fraction(self, configured_inv, extrapolation):
        """Test that volume fraction is ~1% regardless of extrapolation mode."""
        v, _ = configured_inv.get_volume_fraction_with_error(2.2e-6, extrapolation=extrapolation)
        assert v == pytest.approx(0.01, rel=0.05)

    @pytest.mark.parametrize("extrapolation", [None, "low", "high", "both"])
    def test_contrast(self, configured_inv, extrapolation):
        """Test that contrast is ~2.2e-6 regardless of extrapolation mode."""
        c, _ = configured_inv.get_contrast_with_error(0.01, extrapolation=extrapolation)
        assert c == pytest.approx(2.2e-6, rel=0.05)

    @pytest.mark.parametrize("extrapolation", [None, "low", "high", "both"])
    def test_specific_surface(self, configured_inv, extrapolation):
        """Test that specific surface area is ~6e-5 regardless of extrapolation mode."""
        s, _ = configured_inv.get_surface_with_error(2.2e-6, 1.825e-7, extrapolation=extrapolation)
        assert s == pytest.approx(6.00e-5, rel=0.05)

    @pytest.mark.parametrize("extrapolation, func",
        [("low", "not_a_name"),
         ("not_a_range", "guinier"),
         ("high", "guinier")]
    )
    def test_bad_parameter_name(self, extrapolation, func):
        """Test that invalid extrapolation range or function names raise ValueError."""
        inv = invariant.InvariantCalculator(self.data)
        with pytest.raises(ValueError):
            inv.set_extrapolation(extrapolation, npts=4, function=func)

    def test_volume_fraction_uncertainty_increases_with_contrast_err(self):
        """Checks if the uncertainty calculated for volume fraction scales with the uncertainty entered for contrast."""
        inv = invariant.InvariantCalculator(self.data)
        contrast = 2.2e-6
        _, dv_small = inv.get_volume_fraction_with_error(contrast, contrast_err=0.1 * contrast)
        _, dv_large = inv.get_volume_fraction_with_error(contrast, contrast_err=0.5 * contrast)
        assert dv_large > dv_small

    def test_contrast_uncertainty_increases_with_volume_err(self):
        """Checks if the uncertainty calculated for contrast scales with the uncertainty entered for volume fraction."""
        inv = invariant.InvariantCalculator(self.data)
        volume = 0.01
        _, dc_small = inv.get_contrast_with_error(volume, volume_err=0.001)
        _, dc_large = inv.get_contrast_with_error(volume, volume_err=0.01)
        assert dc_large > dc_small

    def test_surface_uncertainty_increases_with_input_err(self):
        """
        Checks if the uncertainty calculated for specific surface scales with the uncertainty entered for:
            - SLD contrast
            - Porod constant
        """
        inv = invariant.InvariantCalculator(self.data)
        contrast = 2.2e-6
        porod = 1.825e-7

        _, ds_small_contrast = inv.get_surface_with_error(contrast, porod, contrast_err=0.1 * contrast)
        _, ds_large_contrast = inv.get_surface_with_error(contrast, porod, contrast_err=0.5 * contrast)
        assert ds_large_contrast > ds_small_contrast

        _, ds_small_porod = inv.get_surface_with_error(contrast, porod, porod_const_err=0.1 * porod)
        _, ds_large_porod = inv.get_surface_with_error(contrast, porod, porod_const_err=0.5 * porod)
        assert ds_large_porod > ds_small_porod


class TestGuinierExtrapolation:
    """
    Generate a Guinier distribution and verifies that the extrapolation
    produces the correct ditribution.
    TODO:: on 3/23/2020 PDB says: this seems to be a subset of class
        TestDataExtraLow (or equivalantly class TestDataExtaLowSlitGuinier).
    DELETE this test?
    """

    @pytest.fixture(autouse=True)
    def setup(self, guinier_data):
        self.scale = 1.5
        self.rg = 30.0
        self.data = guinier_data

    def test_low_q(self):
        """
        Invariant with low-Q extrapolation
        """
        # Create invariant object. Background and scale left as defaults.
        inv = invariant.InvariantCalculator(data=self.data)
        # Set the extrapolation parameters for the low-Q range
        inv.set_extrapolation(range="low", npts=20, function="guinier")

        assert inv._low_extrapolation_npts == 20
        assert inv._low_extrapolation_function.__class__ == invariant.Guinier

        # Data boundaries for fiiting
        qmin = inv._data.x[0]
        qmax = inv._data.x[inv._low_extrapolation_npts - 1]

        # Extrapolate the low-Q data
        inv._fit(model=inv._low_extrapolation_function, qmin=qmin, qmax=qmax, power=inv._low_extrapolation_power)
        assert self.scale == pytest.approx(inv._low_extrapolation_function.scale, abs=1e-6)
        assert self.rg**2 == pytest.approx(inv._low_extrapolation_function.Rg_squared, abs=1e-6)


class TestPowerLawExtrapolation:
    """
    Generate a power law distribution and verify that the extrapolation
    produce the correct ditribution.
    TODO:: As of 3/23/2020 PDB says: this test should be removed if and
           when we stop allowing low q power law extrapolation.
    """

    @pytest.fixture(autouse=True)
    def setup(self, power_law_data):
        self.scale = 1.5
        self.m = 3.0
        self.data = power_law_data

    def test_low_q(self):
        """
        Invariant with low-Q extrapolation
        NOTE: as noted in the class docs, this should probalby be removed.
        But until we remove the option for low Q power law extrapolation
        will leave this.
        """
        # Create invariant object. Background and scale left as defaults.
        inv = invariant.InvariantCalculator(data=self.data)
        # Set the extrapolation parameters for the low-Q range
        inv.set_extrapolation(range="low", npts=20, function="power_law")

        assert inv._low_extrapolation_npts == 20
        assert inv._low_extrapolation_function.__class__ == invariant.PowerLaw

        # Data boundaries for fitting
        qmin = inv._data.x[0]
        qmax = inv._data.x[inv._low_extrapolation_npts - 1]

        # Extrapolate the low-Q data
        inv._fit(model=inv._low_extrapolation_function, qmin=qmin, qmax=qmax, power=inv._low_extrapolation_power)

        assert self.scale == pytest.approx(inv._low_extrapolation_function.scale, abs=1e-6)
        assert self.m == pytest.approx(inv._low_extrapolation_function.power, abs=1e-6)


class TestLinearization:
    def test_guinier_incompatible_length(self):
        g = invariant.Guinier()
        data_in = Data1D(x=[1], y=[1, 2], dy=None)
        with pytest.raises(ValueError):
            g.linearize_data(data_in)
        data_in = Data1D(x=[1, 1], y=[1, 2], dy=[1])
        with pytest.raises(ValueError):
            g.linearize_data(data_in)

    def test_linearization(self):
        """
        Check that the linearization process filters out points
        that can't be transformed
        """
        x = np.asarray(np.asarray([0, 1, 2, 3]))
        y = np.asarray(np.asarray([1, 1, 1, 1]))
        g = invariant.Guinier()
        data_in = Data1D(x=x, y=y)
        data_out = g.linearize_data(data_in)
        x_out, y_out, dy_out = data_out.x, data_out.y, data_out.dy
        assert len(x_out) == 3
        assert len(y_out) == 3
        assert len(dy_out) == 3

    def test_allowed_bins(self):
        x = np.asarray(np.asarray([0, 1, 2, 3]))
        y = np.asarray(np.asarray([1, 1, 1, 1]))
        dy = np.asarray(np.asarray([1, 1, 1, 1]))
        g = invariant.Guinier()
        data = Data1D(x=x, y=y, dy=dy)
        assert g.get_allowed_bins(data) == [False, True, True, True]

        data = Data1D(x=y, y=x, dy=dy)
        assert g.get_allowed_bins(data) == [False, True, True, True]

        data = Data1D(x=dy, y=y, dy=x)
        assert g.get_allowed_bins(data) == [False, True, True, True]


class TestDataExtraLow:
    """
    Generate a Guinier distribution and verify that the extrapolation
    produce the correct ditribution. Test if the data generated by the
    invariant calculator is correct
    TODO:: on 3/23/2020 PDB says: this seems to be exactly the same
           tests as class TestDataExtraLowSlitGunier (whih in fact
           has no smearing whatsoever) and is a superset of the class
           TestGunierExtrapolation?
    KEEP THIS ONE?
    """

    @pytest.fixture(autouse=True)
    def setup(self, guinier_data):
        self.scale = 1.5
        self.rg = 30.0
        self.data = guinier_data

    def test_low_q(self):
        """
        Invariant with low-Q extrapolation with no slit smear
        """
        # Create invariant object. Background and scale left as defaults.
        inv = invariant.InvariantCalculator(data=self.data)
        # Set the extrapolation parameters for the low-Q range
        inv.set_extrapolation(range="low", npts=10, function="guinier")

        assert inv._low_extrapolation_npts == 10
        assert inv._low_extrapolation_function.__class__ == invariant.Guinier

        # Data boundaries for fiiting
        qmin = inv._data.x[0]
        qmax = inv._data.x[inv._low_extrapolation_npts - 1]

        # Extrapolate the low-Q data
        inv._fit(model=inv._low_extrapolation_function, qmin=qmin, qmax=qmax, power=inv._low_extrapolation_power)
        assert self.scale == pytest.approx(inv._low_extrapolation_function.scale, abs=1e-6)
        assert self.rg**2 == pytest.approx(inv._low_extrapolation_function.Rg_squared, abs=1e-6)

        qstar = inv.get_qstar(extrapolation="low")
        test_y = inv._low_extrapolation_function.evaluate_model(x=self.data.x)
        for i in range(len(self.data.x)):
            value = math.fabs(test_y[i] - self.data.y[i]) / self.data.y[i]
            assert value < 0.001


class TestDataExtraLowSlitGuinier:
    """
    for a smear data, test that the fitting goes through
    real data for at least the 2 first points
    TODO:: on 3/23/2020 PDB says: a) there is no slit smear data here and
           b) this seems to be the exactly the same tests as in class
           TestDataExtraLow which iteself is a superset of the class
           TestGunierExtrapolation?
    DELETE

    """

    @pytest.fixture(autouse=True)
    def setup(self, guinier_data):
        self.scale = 1.5
        self.rg = 30.0
        self.data = guinier_data
        self.npts = len(guinier_data.x) - 10

    def test_low_q(self):
        """
        Invariant with low-Q extrapolation with slit smear
        TODO:: on 3/23/2020 PDB says: a) there is no slit smear data here
               and b) this seems to be the exactly the same tests as
               test_low_dat and of the whole class TestDataExtraLow which
               iteself is a superset of the class TestGunierExtrapolation?
        """
        # Create invariant object. Background and scale left as defaults.
        inv = invariant.InvariantCalculator(data=self.data)
        # Set the extrapolation parameters for the low-Q range
        inv.set_extrapolation(range="low", npts=self.npts, function="guinier")

        assert inv._low_extrapolation_npts == self.npts
        assert inv._low_extrapolation_function.__class__ == invariant.Guinier

        # Data boundaries for fiiting
        qmin = inv._data.x[0]
        qmax = inv._data.x[inv._low_extrapolation_npts - 1]

        # Extrapolate the low-Q data
        inv._fit(model=inv._low_extrapolation_function, qmin=qmin, qmax=qmax, power=inv._low_extrapolation_power)

        qstar = inv.get_qstar(extrapolation="low")

        test_y = inv._low_extrapolation_function.evaluate_model(x=self.data.x[: inv._low_extrapolation_npts])
        assert len(test_y) == len(self.data.y[: inv._low_extrapolation_npts])

        for i in range(inv._low_extrapolation_npts):
            value = math.fabs(test_y[i] - self.data.y[i]) / self.data.y[i]
            assert value < 0.001

    def test_low_data(self):
        """
        Invariant with low-Q extrapolation with slit smear
        TODO:: on 3/23/2020 PDB says: a) there is no slit smear data here
               and b) this seems to be the exactly the same tests as
               test_low_q and of the whole class TestDataExtraLow which
               iteself is a superset of the class TestGunierExtrapolation?
        """
        # Create invariant object. Background and scale left as defaults.
        inv = invariant.InvariantCalculator(data=self.data)
        # Set the extrapolation parameters for the low-Q range
        inv.set_extrapolation(range="low", npts=self.npts, function="guinier")

        assert inv._low_extrapolation_npts == self.npts
        assert inv._low_extrapolation_function.__class__ == invariant.Guinier

        # Data boundaries for fiiting
        qmin = inv._data.x[0]
        qmax = inv._data.x[inv._low_extrapolation_npts - 1]

        # Extrapolate the low-Q data
        inv._fit(model=inv._low_extrapolation_function, qmin=qmin, qmax=qmax, power=inv._low_extrapolation_power)

        qstar = inv.get_qstar(extrapolation="low")
        # Computing the ys coming out of the invariant when computing
        # extrapolated low data . expect the fit engine to have been already
        # called and the guinier to have the radius and the scale fitted
        data_in_range = inv.get_extra_data_low(q_start=self.data.x[0], npts=inv._low_extrapolation_npts)
        test_y = data_in_range.y
        assert len(test_y) == len(self.data.y[: inv._low_extrapolation_npts])
        for i in range(inv._low_extrapolation_npts):
            value = math.fabs(test_y[i] - self.data.y[i]) / self.data.y[i]
            assert value < 0.001


class TestDataExtraHighSlitPowerLaw:
    """
    for a smear data, test that the fitting goes through
    real data for atleast the 2 first points
    TODO:: As of 3/23/2020 by PDB - this data is NOT smeared as far as
           I can see. On the other hand it is the only high q extrapolation
           test? Need to double check then rewrite doc strings accordingly.
    """

    @pytest.fixture(autouse=True)
    def setup(self, power_law_data):
        self.data = power_law_data
        self.npts = 20

    def test_high_q(self):
        """
        Invariant with high-Q extrapolation with slit smear
        TODO:: As of 3/23/2020 by PDB - this data is NOT smeared as far as
            I can see. On the other hand it is the only high q
            extrapolation test? Need to double check then rewrite doc
            strings accordingly.
        """
        # Create invariant object. Background and scale left as defaults.
        inv = invariant.InvariantCalculator(data=self.data)
        # Set the extrapolation parameters for the low-Q range
        inv.set_extrapolation(range="high", npts=self.npts, function="power_law")

        assert inv._high_extrapolation_npts == self.npts
        assert inv._high_extrapolation_function.__class__ == invariant.PowerLaw

        # Data boundaries for fiiting
        xlen = len(self.data.x)
        start = xlen - inv._high_extrapolation_npts
        qmin = inv._data.x[start]
        qmax = inv._data.x[xlen - 1]

        # Extrapolate the high-Q data
        inv._fit(model=inv._high_extrapolation_function, qmin=qmin, qmax=qmax, power=inv._high_extrapolation_power)

        qstar = inv.get_qstar(extrapolation="high")

        test_y = inv._high_extrapolation_function.evaluate_model(x=self.data.x[start:])
        assert len(test_y) == len(self.data.y[start:])

        for i in range(len(self.data.x[start:])):
            value = math.fabs(test_y[i] - self.data.y[start + i]) / self.data.y[start + i]
            assert value < 0.001

    def test_high_data(self):
        """
        Invariant with low-Q extrapolation with slit smear
        TODO:: on 3/23/2020 PDB says: a) there is no slit smear data here
               and b) this seems to be the exactly the same tests as
               test_high_q.  It is NOT a low q extrapolation?
        DELETE?
        """
        # Create invariant object. Background and scale left as defaults.
        inv = invariant.InvariantCalculator(data=self.data)
        # Set the extrapolation parameters for the low-Q range
        inv.set_extrapolation(range="high", npts=self.npts, function="power_law")

        assert inv._high_extrapolation_npts == self.npts
        assert inv._high_extrapolation_function.__class__ == invariant.PowerLaw

        # Data boundaries for fiiting
        xlen = len(self.data.x)
        start = xlen - inv._high_extrapolation_npts
        qmin = inv._data.x[start]
        qmax = inv._data.x[xlen - 1]

        # Extrapolate the high-Q data
        inv._fit(model=inv._high_extrapolation_function, qmin=qmin, qmax=qmax, power=inv._high_extrapolation_power)

        qstar = inv.get_qstar(extrapolation="high")

        data_in_range = inv.get_extra_data_high(q_end=max(self.data.x), npts=inv._high_extrapolation_npts)
        test_y = data_in_range.y
        assert len(test_y) == len(self.data.y[start:])
        temp = self.data.y[start:]

        for i in range(len(self.data.x[start:])):
            value = math.fabs(test_y[i] - temp[i]) / temp[i]
            assert value < 0.001
