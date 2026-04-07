import math

import numpy as np
import pytest

from sasdata.dataloader.data_info import Data1D

from sas.sascalc.invariant import invariant


def _midpoint_widths(x):
    """Return midpoint-width trapezoidal bin widths used by invariant integration."""
    dx = np.empty_like(x)
    dx[0] = (x[1] - x[0]) / 2
    dx[1:-1] = (x[2:] - x[:-2]) / 2
    dx[-1] = (x[-1] - x[-2]) / 2
    return dx


class TestUncertaintyClosedForm:
    """Uncertainty checks against closed-form propagation formulas to test conformity."""

    def test_qstar_uncertainty_matches_closed_form(self):
        """Verify dq* from the explicit q* propagation equation."""
        x = np.asarray([0.001, 0.002, 0.003, 0.005, 0.008])
        y = np.asarray([120.0, 90.0, 70.0, 40.0, 20.0])
        dy = np.asarray([1.2, 0.9, 0.7, 0.4, 0.2])
        data = Data1D(x=x, y=y, dy=dy)

        inv = invariant.InvariantCalculator(data)
        _, dqstar = inv.get_qstar_with_error()

        x_calc = inv._data.x
        dy_calc = inv._data.dy
        dx = _midpoint_widths(x_calc)
        expected_dqstar = math.sqrt(np.sum((x_calc * x_calc * dy_calc * dx) ** 2))

        assert dqstar == pytest.approx(expected_dqstar, rel=1e-6)

    def test_volume_fraction_uncertainty_matches_closed_form(self, real_data):
        """Verify dV from the explicit volume-fraction propagation equation."""
        inv = invariant.InvariantCalculator(real_data)
        contrast = 2.2e-6
        contrast_err = 0.2e-6

        _, volume_err = inv.get_volume_fraction_with_error(contrast, contrast_err=contrast_err)

        q = inv._qstar * 1.0e-8
        q_err = inv._qstar_err * 1.0e-8
        k = q / (2 * (math.pi * abs(contrast)) ** 2)
        root = math.sqrt(1 - 4 * k)
        term_q = q_err / (2 * math.pi**2 * contrast**2 * root)
        term_contrast = q * contrast_err / (math.pi**2 * contrast**3 * root)
        expected_volume_err = math.sqrt(term_q**2 + term_contrast**2)

        assert volume_err == pytest.approx(expected_volume_err, rel=1e-6)

    def test_contrast_uncertainty_matches_closed_form(self, real_data):
        """Verify dContrast from the explicit contrast propagation equation."""
        inv = invariant.InvariantCalculator(real_data)
        volume = 0.01
        volume_err = 0.001

        contrast, contrast_err = inv.get_contrast_with_error(volume, volume_err=volume_err)

        k = volume * (1 - volume)
        k_err = abs((1 - 2 * volume) * volume_err)
        expected_contrast_err = contrast / 2.0 * math.sqrt((inv._qstar_err / inv._qstar) ** 2 + (k_err / k) ** 2)

        assert contrast_err == pytest.approx(expected_contrast_err, rel=1e-6)

    def test_surface_uncertainty_matches_closed_form(self, real_data):
        """Verify dS from the relative-error expression for surface."""
        inv = invariant.InvariantCalculator(real_data)
        contrast = 2.2e-6
        contrast_err = 0.11e-6
        porod_const = 1.825e-7
        porod_const_err = 0.1825e-7

        surface, surface_err = inv.get_surface_with_error(
            contrast=contrast,
            porod_const=porod_const,
            contrast_err=contrast_err,
            porod_const_err=porod_const_err,
        )

        expected_rel = math.sqrt((porod_const_err / porod_const) ** 2 + (2.0 * contrast_err / contrast) ** 2)
        expected_surface_err = abs(surface) * expected_rel

        assert surface_err == pytest.approx(expected_surface_err, rel=1e-6)

    def test_surface_uncertainty_defaults_to_zero(self, real_data):
        """Verify that omitted uncertainty inputs produce zero propagated uncertainty."""
        inv = invariant.InvariantCalculator(real_data)
        surface, surface_err = inv.get_surface_with_error(contrast=2.2e-6, porod_const=1.825e-7)

        assert surface > 0
        assert surface_err == pytest.approx(0.0, abs=0.0)

    def test_extrapolation_uncertainty_quadrature_decomposition(self, real_data):
        """Verify low/high/both extrapolation uncertainty combines in quadrature."""
        inv = invariant.InvariantCalculator(real_data)
        inv.set_extrapolation("low", npts=10, function="guinier")
        inv.set_extrapolation("high", npts=20, function="power_law")

        q_base, dq_base = inv.get_qstar_with_error()
        q_low, dq_low = inv.get_qstar_with_error("low")
        q_high, dq_high = inv.get_qstar_with_error("high")
        q_both, dq_both = inv.get_qstar_with_error("both")

        delta_q_low, delta_dq_low = inv.get_qstar_low()
        delta_q_high, delta_dq_high = inv.get_qstar_high()

        expected_q_low = q_base + delta_q_low
        expected_q_high = q_base + delta_q_high
        expected_q_both = q_base + delta_q_low + delta_q_high

        expected_dq_low = math.sqrt(dq_base**2 + delta_dq_low**2)
        expected_dq_high = math.sqrt(dq_base**2 + delta_dq_high**2)
        expected_dq_both = math.sqrt(dq_base**2 + delta_dq_low**2 + delta_dq_high**2)

        assert q_low == pytest.approx(expected_q_low, rel=1e-6)
        assert q_high == pytest.approx(expected_q_high, rel=1e-6)
        assert q_both == pytest.approx(expected_q_both, rel=1e-6)
        assert dq_low == pytest.approx(expected_dq_low, rel=1e-6)
        assert dq_high == pytest.approx(expected_dq_high, rel=1e-6)
        assert dq_both == pytest.approx(expected_dq_both, rel=1e-6)


class TestUncertaintyHardcodedValues:
    """Checks with hard-coded values from a fixed data snapshot."""

    # test/sasinvariant/data/100nmSpheresNodQ.txt
    ORACLE_QSTAR = 9.43709052540011e-05
    ORACLE_DQSTAR = 1.3563537945777e-07

    ORACLE_VOLUME = 0.00997741220654419
    ORACLE_VOLUME_ERR = 0.0018326005068374975

    ORACLE_CONTRAST = 2.1975390071042192e-06
    ORACLE_CONTRAST_ERR = 1.08778546074455e-07

    ORACLE_SURFACE = 6.0011936186510115e-05
    ORACLE_SURFACE_ERR = 8.486969405923134e-06
    ORACLE_SURFACE_ERR_DEFAULT = 0.0

    ORACLE_Q_LOW = 9.519020393523791e-05
    ORACLE_DQ_LOW = 1.813164591741368e-07
    ORACLE_Q_HIGH = 9.463701884793585e-05
    ORACLE_DQ_HIGH = 1.7145636671288138e-07
    ORACLE_Q_BOTH = 9.545631752917265e-05
    ORACLE_DQ_BOTH = 2.0946595879324933e-07

    ORACLE_DELTA_Q_LOW = 8.192986812367958e-07
    ORACLE_DELTA_DQ_LOW = 1.2032747901785843e-07
    ORACLE_DELTA_Q_HIGH = 2.6611359393474845e-07
    ORACLE_DELTA_DQ_HIGH = 1.0488245575752317e-07

    ORACLE_SYNTHETIC_QSTAR = 5.785e-06
    ORACLE_SYNTHETIC_DQSTAR = 3.310985502837486e-08

    def test_qstar_uncertainty_hardcoded_values(self):
        """Verify q* and dq* against fixed hardcoded values for synthetic data."""
        x = np.asarray([0.001, 0.002, 0.003, 0.005, 0.008])
        y = np.asarray([120.0, 90.0, 70.0, 40.0, 20.0])
        dy = np.asarray([1.2, 0.9, 0.7, 0.4, 0.2])
        data = Data1D(x=x, y=y, dy=dy)

        inv = invariant.InvariantCalculator(data)
        qstar, dqstar = inv.get_qstar_with_error()

        assert qstar == pytest.approx(self.ORACLE_SYNTHETIC_QSTAR, rel=1e-6)
        assert dqstar == pytest.approx(self.ORACLE_SYNTHETIC_DQSTAR, rel=1e-6)

    def test_volume_fraction_uncertainty_hardcoded_values(self, real_data):
        """Verify volume and uncertainty against fixed hardcoded values."""
        inv = invariant.InvariantCalculator(real_data)
        volume, volume_err = inv.get_volume_fraction_with_error(2.2e-6, contrast_err=0.2e-6)

        assert volume == pytest.approx(self.ORACLE_VOLUME, rel=1e-6)
        assert volume_err == pytest.approx(self.ORACLE_VOLUME_ERR, rel=1e-6)

    def test_contrast_uncertainty_hardcoded_values(self, real_data):
        """Verify contrast and uncertainty against fixed hardcoded values."""
        inv = invariant.InvariantCalculator(real_data)
        contrast, contrast_err = inv.get_contrast_with_error(0.01, volume_err=0.001)

        assert contrast == pytest.approx(self.ORACLE_CONTRAST, rel=1e-6)
        assert contrast_err == pytest.approx(self.ORACLE_CONTRAST_ERR, rel=1e-6)

    def test_surface_uncertainty_hardcoded_values(self, real_data):
        """Verify surface and uncertainty against fixed hardcoded values."""
        inv = invariant.InvariantCalculator(real_data)
        surface, surface_err = inv.get_surface_with_error(
            contrast=2.2e-6,
            porod_const=1.825e-7,
            contrast_err=0.11e-6,
            porod_const_err=0.1825e-7,
        )

        assert surface == pytest.approx(self.ORACLE_SURFACE, rel=1e-6)
        assert surface_err == pytest.approx(self.ORACLE_SURFACE_ERR, rel=1e-6)

    def test_surface_uncertainty_defaults_to_zero_hardcoded_values(self, real_data):
        """Verify default uncertainty behavior against fixed hardcoded values."""
        inv = invariant.InvariantCalculator(real_data)
        surface, surface_err = inv.get_surface_with_error(contrast=2.2e-6, porod_const=1.825e-7)

        assert surface == pytest.approx(self.ORACLE_SURFACE, rel=1e-6)
        assert surface_err == pytest.approx(self.ORACLE_SURFACE_ERR_DEFAULT, abs=0.0)

    def test_extrapolation_uncertainty_hardcoded_values(self, real_data):
        """Verify low/high/both extrapolation values against fixed hardcoded values."""
        inv = invariant.InvariantCalculator(real_data)
        inv.set_extrapolation("low", npts=10, function="guinier")
        inv.set_extrapolation("high", npts=20, function="power_law")

        q_base, dq_base = inv.get_qstar_with_error()
        q_low, dq_low = inv.get_qstar_with_error("low")
        q_high, dq_high = inv.get_qstar_with_error("high")
        q_both, dq_both = inv.get_qstar_with_error("both")
        delta_q_low, delta_dq_low = inv.get_qstar_low()
        delta_q_high, delta_dq_high = inv.get_qstar_high()

        assert q_base == pytest.approx(self.ORACLE_QSTAR, rel=1e-6)
        assert dq_base == pytest.approx(self.ORACLE_DQSTAR, rel=1e-6)

        assert q_low == pytest.approx(self.ORACLE_Q_LOW, rel=1e-6)
        assert dq_low == pytest.approx(self.ORACLE_DQ_LOW, rel=1e-6)
        assert q_high == pytest.approx(self.ORACLE_Q_HIGH, rel=1e-6)
        assert dq_high == pytest.approx(self.ORACLE_DQ_HIGH, rel=1e-6)
        assert q_both == pytest.approx(self.ORACLE_Q_BOTH, rel=1e-6)
        assert dq_both == pytest.approx(self.ORACLE_DQ_BOTH, rel=1e-6)

        assert delta_q_low == pytest.approx(self.ORACLE_DELTA_Q_LOW, rel=1e-6)
        assert delta_dq_low == pytest.approx(self.ORACLE_DELTA_DQ_LOW, rel=1e-6)
        assert delta_q_high == pytest.approx(self.ORACLE_DELTA_Q_HIGH, rel=1e-6)
        assert delta_dq_high == pytest.approx(self.ORACLE_DELTA_DQ_HIGH, rel=1e-6)
