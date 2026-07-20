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
        rng = np.random.default_rng(0)
        self.data.y += 0.1 * (rng.random(len(self.data.y)) - 0.5)

        fit = invariant.Extrapolator(data=self.data)
        p, _ = fit.fit()

        assert p[0] == pytest.approx(1.0, abs=0.05)
        assert p[1] == pytest.approx(0.0, abs=0.1)

    def test_fit_with_fixed_parameter(self):
        """Linear fit for y = ax + b, where a is fixed."""
        fit = invariant.Extrapolator(data=self.data)
        p, _ = fit.fit(power=-1.0)

        assert p[0] == pytest.approx(1.0, abs=1e-5)
        assert p[1] == pytest.approx(0.0, abs=1e-5)

    def test_fit_linear_data_with_noise_and_fixed_par(self):
        """Test a simple linear fit with noise and a fixed parameter."""
        rng = np.random.default_rng(0)
        self.data.y += 0.1 * (rng.random(len(self.data.y)) - 0.5)

        fit = invariant.Extrapolator(data=self.data)
        p, _ = fit.fit(power=-1.0)

        assert p[0] == pytest.approx(1.0, abs=0.05)
        assert p[1] == pytest.approx(0.0, abs=0.1)

    def test_fit_covariance_fallback_on_linalg_failure(self, monkeypatch):
        """If covariance estimation fails, fit should return sentinel errors."""
        fit = invariant.Extrapolator(data=self.data)

        def _raise(_):
            raise RuntimeError("forced pinv failure")

        monkeypatch.setattr(invariant.np.linalg, "pinv", _raise)
        _, err = fit.fit()

        assert err == [-1.0, -1.0]


class TestLinearization:
    """Test the linearization process of the Guinier extrapolation."""

    @pytest.mark.parametrize("x, y, dy", [([1], [1, 2], None), ([1, 1], [1, 2], [1])])
    def test_guinier_incompatible_length(self, x, y, dy):
        """Check that the linearization process raises an error when the input data arrays have incompatible lengths."""
        g = invariant.Guinier()
        data_in = Data1D(x=x, y=y, dy=dy)
        with pytest.raises(ValueError):
            g.linearize_data(data_in)

    def test_linearization(self):
        """Check that the linearization process filters out points that can't be transformed."""
        g = invariant.Guinier()

        x = np.asarray(np.asarray([0, 1, 2, 3]))
        y = np.asarray(np.asarray([1, 1, 1, 1]))
        dy = np.asarray(np.asarray([1, 1, 1, 1]))
        data_in = Data1D(x=x, y=y, dy=dy)

        data_out = g.linearize_data(data_in)
        x_out, y_out, dy_out = data_out.x, data_out.y, data_out.dy

        assert len(x_out) == len(y_out) == len(dy_out) == 3
        assert x_out == pytest.approx([1, 4, 9], abs=1e-10)
        assert y_out == pytest.approx([0, 0, 0], abs=1e-10)
        assert dy_out == pytest.approx([1, 1, 1], abs=1e-10)

    def test_linearization_with_none_dy_uses_unity_uncertainty(self):
        """When dy is missing, linearization should default to ones."""
        g = invariant.Guinier()
        x = np.asarray([1.0, 2.0, 3.0])
        y = np.asarray([2.0, 2.0, 2.0])
        data_in = Data1D(x=x, y=y, dy=None)

        data_out = g.linearize_data(data_in)
        assert data_out.dy == pytest.approx([0.5, 0.5, 0.5], abs=1e-10)

    def test_linearization_all_points_filtered_raises(self):
        """If all points are invalid, linearization should fail clearly."""
        g = invariant.Guinier()
        data_in = Data1D(
            x=np.asarray([0.0, -1.0]),
            y=np.asarray([1.0, -1.0]),
            dy=np.asarray([1.0, 1.0]),
        )

        with pytest.raises(ValueError):
            g.linearize_data(data_in)

    @pytest.mark.parametrize(
        "px, py, pdy, expected_bins",
        [
            (0, 1, 2, [False, True, True, True]),
            (1, 0, 2, [False, True, True, True]),
            (2, 1, 0, [False, True, True, True]),
        ],
    )
    def test_allowed_bins(self, px, py, pdy, expected_bins):
        """Check that the allowed bins are correctly identified."""
        g = invariant.Guinier()
        x = np.asarray(np.asarray([0, 1, 2, 3]))
        y = np.asarray(np.asarray([1, 1, 1, 1]))
        dy = np.asarray(np.asarray([1, 1, 1, 1]))
        arr = [x, y, dy]

        data = Data1D(x=arr[px], y=arr[py], dy=arr[pdy])
        assert g.get_allowed_bins(data) == expected_bins


class TestTransformAbstractFallback:
    """Execute abstract base fallback returns for completeness."""

    def test_abstract_method_fallback_returns_not_implemented(self):
        assert invariant.Transform.linearize_q_value(object(), 1.0) is NotImplemented
        assert invariant.Transform.extract_model_parameters(object(), 0.0, 0.0) is NotImplemented
        assert invariant.Transform.evaluate_model(object(), np.asarray([1.0])) is NotImplemented
        assert invariant.Transform.evaluate_model_errors(object(), np.asarray([1.0])) is NotImplemented
