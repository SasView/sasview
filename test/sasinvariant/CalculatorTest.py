import math

import numpy as np
import pytest

from sasdata.dataloader.data_info import Data1D

from sas.sascalc.invariant import invariant


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

        assert len(inv._data.dy) == len(inv._data.x) == len(inv._data.y)
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

    @pytest.mark.parametrize(
        "extrapolation, func", [("low", "not_a_name"), ("not_a_range", "guinier"), ("high", "guinier")]
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

    @pytest.mark.parametrize("power", [0.0, -1.0])
    def test_power_law_raises_for_non_positive_power(self, power):
        """Power-law model should reject non-positive power values."""
        model = invariant.PowerLaw(scale=1.0, power=power)
        with pytest.raises(ValueError):
            model.evaluate_model(np.asarray([0.1, 0.2]))

    def test_power_law_raises_for_non_positive_scale(self):
        """Power-law model should reject non-positive scale values."""
        model = invariant.PowerLaw(scale=0.0, power=4.0)
        with pytest.raises(ValueError):
            model.evaluate_model(np.asarray([0.1, 0.2]))

    def test_get_qstar_invalid_extrapolation_raises(self):
        """Invalid extrapolation mode should raise ValueError."""
        inv = invariant.InvariantCalculator(self.data)
        with pytest.raises(ValueError):
            inv.get_qstar(extrapolation="invalid")

    def test_get_qstar_invalid_data_raises(self):
        """Invalid data should raise ValueError when calculating q*."""
        inv = invariant.InvariantCalculator(self.data)
        inv._data.x = np.asarray([])
        assert len(inv._data.x) == 0
        with pytest.raises(ValueError):
            inv.get_qstar()

        inv = invariant.InvariantCalculator(self.data)
        inv._data.y = np.asarray([1.0, 1.0])
        assert len(inv._data.x) != 0
        assert len(inv._data.x) != len(inv._data.y)
        with pytest.raises(ValueError):
            inv.get_qstar()

        inv = invariant.InvariantCalculator(self.data)
        inv._data.y = np.asarray([])
        assert len(inv._data.x) != 0
        assert len(inv._data.y) == 0
        with pytest.raises(ValueError):
            inv.get_qstar()

    @pytest.mark.parametrize("contrast", [0.0, -1.0])
    def test_get_volume_fraction_invalid_contrast_raises(self, contrast):
        """Volume fraction requires positive contrast."""
        inv = invariant.InvariantCalculator(self.data)
        with pytest.raises(ValueError):
            inv.get_volume_fraction(contrast)

    @pytest.mark.parametrize("volume", [0.0, 1.0, -0.1, 1.1])
    def test_get_contrast_invalid_volume_raises(self, volume):
        """Contrast requires volume strictly between 0 and 1."""
        inv = invariant.InvariantCalculator(self.data)
        with pytest.raises(ValueError):
            inv.get_contrast(volume)

    def test_get_surface_zero_contrast_raises(self):
        """Surface computation requires non-zero contrast."""
        inv = invariant.InvariantCalculator(self.data)
        with pytest.raises(ValueError):
            inv.get_surface(contrast=0.0, porod_const=1.0e-7)

    @pytest.mark.parametrize(
        "contrast_err, porod_err",
        [(-1.0, 0.0), (0.0, -1.0), (-1.0, -1.0)],
    )
    def test_surface_with_error_negative_uncertainties_raise(self, contrast_err, porod_err):
        """Negative uncertainty inputs are invalid."""
        inv = invariant.InvariantCalculator(self.data)
        with pytest.raises(ValueError):
            inv.get_surface_with_error(
                contrast=2.2e-6,
                porod_const=1.825e-7,
                contrast_err=contrast_err,
                porod_const_err=porod_err,
            )

    def test_get_extra_data_low_invalid_range_returns_empty(self):
        """Low-Q extra data returns empty arrays when q_start is outside range."""
        inv = invariant.InvariantCalculator(self.data)
        inv.set_extrapolation("low", npts=10, function="guinier")
        q_end = inv._data.x[9]
        x_out, y_out = inv.get_extra_data_low(q_start=q_end, npts=20)

        assert len(x_out) == 0
        assert len(y_out) == 0

    def test_get_extra_data_high_invalid_range_returns_empty(self):
        """High-Q extra data returns empty arrays when q_end is before q_start."""
        inv = invariant.InvariantCalculator(self.data)
        inv.set_extrapolation("high", npts=20, function="power_law")
        q_start = inv._data.x[len(inv._data.x) - 20]
        x_out, y_out = inv.get_extra_data_high(npts_in=20, q_end=q_start, npts=20)

        assert len(x_out) == 0
        assert len(y_out) == 0

    def test_background_and_scale_setters_invalidate_cached_qstar(self):
        """Changing background/scale should invalidate cached qstar."""
        inv = invariant.InvariantCalculator(self.data)
        _ = inv.get_qstar()
        assert inv._qstar is not None

        inv.background = inv.background
        assert inv._qstar is None

        _ = inv.get_qstar()
        inv.scale = inv.scale
        assert inv._qstar is None

    def test_set_data_invalidates_cached_qstar(self):
        """Setting new data should invalidate cached qstar."""
        inv = invariant.InvariantCalculator(self.data)
        _ = inv.get_qstar()
        assert inv._qstar is not None

        new_data = Data1D(x=np.asarray([0.1, 0.2]), y=np.asarray([1.0, 1.0]), dy=np.asarray([0.1, 0.1]))
        inv.set_data(new_data)
        assert inv._qstar is None

    def test_get_data_returns_internal_data(self):
        """get_data should return the currently stored data object."""
        inv = invariant.InvariantCalculator(self.data)
        assert inv.get_data() is inv._data

    def test_get_extrapolation_power_low_and_high(self):
        """get_extrapolation_power should return stored fitted values for both ranges."""
        inv = invariant.InvariantCalculator(self.data)
        inv.set_extrapolation("low", npts=10, function="guinier")
        inv.set_extrapolation("high", npts=20, function="power_law")
        _ = inv.get_qstar_with_error("both")

        low_power = inv.get_extrapolation_power("low")
        high_power = inv.get_extrapolation_power("high")
        assert low_power is not None
        assert high_power is not None

    def test_qstar_low_with_valid_custom_limit_branch(self):
        """A valid low_q_limit should use the explicit branch in get_qstar_low."""
        inv = invariant.InvariantCalculator(self.data)
        inv.set_extrapolation("low", npts=10, function="guinier")
        qmin = inv._data.x[0]
        qmax = inv._data.x[9]
        low_q_limit = (qmin + qmax) / 2.0

        qs, dqs = inv.get_qstar_low(low_q_limit=low_q_limit)
        assert qs >= 0
        assert dqs >= 0

    def test_qstar_high_with_valid_custom_limit_branch(self):
        """A valid high_q_limit should use the explicit branch in get_qstar_high."""
        inv = invariant.InvariantCalculator(self.data)
        inv.set_extrapolation("high", npts=20, function="power_law")
        x_len = len(inv._data.x) - 1
        qmin = inv._data.x[int(x_len - inv._high_extrapolation_npts)]
        qmax = inv._data.x[x_len]
        high_q_limit = qmax + (qmax - qmin)

        qs, dqs = inv.get_qstar_high(high_q_limit=high_q_limit)
        assert qs > 0
        assert dqs >= 0

    def test_get_extra_data_low_default_q_start_branch(self):
        """get_extra_data_low should use default _low_q_limit when q_start is None."""
        inv = invariant.InvariantCalculator(self.data)
        inv.set_extrapolation("low", npts=10, function="guinier")
        _ = inv.get_qstar_low()

        data_out = inv.get_extra_data_low()
        assert len(data_out.x) > 0
        assert len(data_out.y) > 0

    def test_qstar_uncertainty_invalid_lengths_raise(self):
        """_get_qstar_uncertainty should reject data with only one point."""
        inv = invariant.InvariantCalculator(self.data)
        bad_data = Data1D(x=np.asarray([0.1]), y=np.asarray([1.0]), dy=np.asarray([0.1]))
        with pytest.raises(ValueError):
            inv._get_qstar_uncertainty(bad_data)

    def test_qstar_uncertainty_none_dy_returns_none(self):
        """_get_qstar_uncertainty should return None when dy is missing."""
        inv = invariant.InvariantCalculator(self.data)
        data = Data1D(x=np.asarray([0.1, 0.2]), y=np.asarray([1.0, 2.0]), dy=None)
        assert inv._get_qstar_uncertainty(data) is None

    def test_volume_fraction_runtime_for_nonpositive_qstar(self, monkeypatch):
        """get_volume_fraction should raise RuntimeError when qstar is non-positive."""
        inv = invariant.InvariantCalculator(self.data)

        def _fake_get_qstar(_=None):
            inv._qstar = 0.0
            inv._qstar_err = 0.0
            return inv._qstar

        monkeypatch.setattr(inv, "get_qstar", _fake_get_qstar)
        with pytest.raises(RuntimeError):
            inv.get_volume_fraction(contrast=2.2e-6)

    def test_volume_fraction_runtime_for_negative_discriminant(self, monkeypatch):
        """get_volume_fraction should raise RuntimeError when discriminant is negative."""
        inv = invariant.InvariantCalculator(self.data)

        def _fake_get_qstar(_=None):
            inv._qstar = 1.0e-3
            inv._qstar_err = 0.0
            return inv._qstar

        monkeypatch.setattr(inv, "get_qstar", _fake_get_qstar)
        with pytest.raises(RuntimeError):
            inv.get_volume_fraction(contrast=1.0e-10)

    def test_volume_fraction_discriminant_zero_returns_half(self, monkeypatch):
        """get_volume_fraction should return 0.5 when discriminant is exactly zero."""
        inv = invariant.InvariantCalculator(self.data)
        contrast = 2.2e-6
        target_qstar = 0.5 * (math.pi * abs(contrast)) ** 2 * 1.0e8

        def _fake_get_qstar(_=None):
            inv._qstar = target_qstar
            inv._qstar_err = 0.0
            return inv._qstar

        monkeypatch.setattr(inv, "get_qstar", _fake_get_qstar)
        assert inv.get_volume_fraction(contrast=contrast) == pytest.approx(0.5, abs=1e-12)

    def test_volume_fraction_inconsistent_results_branch(self, monkeypatch):
        """NaN from sqrt should trigger the inconsistent-results RuntimeError branch."""
        inv = invariant.InvariantCalculator(self.data)

        def _fake_get_qstar(_=None):
            inv._qstar = 1.0e-5
            inv._qstar_err = 0.0
            return inv._qstar

        monkeypatch.setattr(inv, "get_qstar", _fake_get_qstar)

        real_sqrt = invariant.math.sqrt

        def _nan_sqrt(value):
            if value > 0:
                return float("nan")
            return real_sqrt(value)

        monkeypatch.setattr(invariant.math, "sqrt", _nan_sqrt)
        with pytest.raises(RuntimeError):
            inv.get_volume_fraction(contrast=2.2e-6)

    def test_contrast_runtime_for_nonpositive_qstar(self, monkeypatch):
        """get_contrast should raise RuntimeError when qstar is non-positive."""
        inv = invariant.InvariantCalculator(self.data)

        def _fake_get_qstar(_=None):
            inv._qstar = 0.0
            inv._qstar_err = 0.0
            return inv._qstar

        monkeypatch.setattr(inv, "get_qstar", _fake_get_qstar)
        with pytest.raises(RuntimeError):
            inv.get_contrast(volume=0.5)

    def test_contrast_runtime_from_sqrt_error_branch(self, monkeypatch):
        """ValueError in sqrt should be mapped to RuntimeError in get_contrast."""
        inv = invariant.InvariantCalculator(self.data)

        def _fake_get_qstar(_=None):
            inv._qstar = 1.0e-5
            inv._qstar_err = 0.0
            return inv._qstar

        monkeypatch.setattr(inv, "get_qstar", _fake_get_qstar)

        def _raise(_):
            raise ValueError("forced")

        monkeypatch.setattr(invariant.math, "sqrt", _raise)
        with pytest.raises(RuntimeError):
            inv.get_contrast(volume=0.5)

    def test_contrast_with_error_returns_minus_one_when_internal_ratio_invalid(self, monkeypatch):
        """Division-by-zero in uncertainty expression should return -1."""
        inv = invariant.InvariantCalculator(self.data)
        inv._qstar = 0.0
        inv._qstar_err = 1.0

        monkeypatch.setattr(inv, "get_contrast", lambda volume, extrapolation=None: 1.0)
        _, uncertainty = inv.get_contrast_with_error(volume=0.5, volume_err=0.0)
        assert uncertainty == -1

    def test_surface_with_error_returns_none_pair_when_surface_is_none(self, monkeypatch):
        """If get_surface returns None, get_surface_with_error should return (None, None)."""
        inv = invariant.InvariantCalculator(self.data)
        monkeypatch.setattr(inv, "get_surface", lambda **kwargs: None)
        assert inv.get_surface_with_error(contrast=2.2e-6, porod_const=1.825e-7) == (None, None)

    def test_surface_with_error_zero_division_returns_none_uncertainty(self):
        """Zero porod constant with nonzero uncertainty should return undefined surface uncertainty."""
        inv = invariant.InvariantCalculator(self.data)
        s, ds = inv.get_surface_with_error(contrast=2.2e-6, porod_const=0.0, porod_const_err=1.0)
        assert s == pytest.approx(0.0, abs=0.0)
        assert ds is None
