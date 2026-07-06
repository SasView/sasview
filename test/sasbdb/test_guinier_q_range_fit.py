"""
Tests for SASBDB Guinier range linear fit (collect_guinier_from_q_range).
"""
import numpy as np
import pytest

from sas.qtgui.Utilities.SASBDB.sasbdb_data_collector import SASBDBDataCollector


class _Data1Dnm:
    """Minimal 1D curve: q in nm^-1, Guinier I = I0 exp(-Rg^2 q^2 / 3)."""

    def __init__(self, rg_nm: float = 2.0, i0: float = 1.0, n: int = 60):
        q = np.linspace(0.01, 0.12, n)
        self.x = q
        self.y = i0 * np.exp(-(rg_nm**2) * q**2 / 3.0)
        self.dy = self.y * 0.01

    def get_xaxis(self):
        return ("q", "nm^{-1}")


class _Data1DA:
    """Same physics with q in Å^-1 (Rg stored in nm in output)."""

    def __init__(self, rg_nm: float = 2.0, i0: float = 1.0, n: int = 60):
        q_nm = np.linspace(0.01, 0.12, n)
        q_a = q_nm / 10.0
        self.x = q_a
        self.y = i0 * np.exp(-((rg_nm * 10.0) ** 2) * q_a**2 / 3.0)
        self.dy = self.y * 0.01

    def get_xaxis(self):
        return ("q", "Å^{-1}")


@pytest.mark.parametrize("data_factory,atol", [(_Data1Dnm, 0.05), (_Data1DA, 0.08)])
def test_collect_guinier_from_q_range_recovers_rg_i0(data_factory, atol):
    data = data_factory(rg_nm=2.0, i0=1.0)
    collector = SASBDBDataCollector()
    q = np.asarray(data.x)
    q_lo = float(q[5])
    q_hi = float(q[40])
    guinier, fit_info = collector.collect_guinier_from_q_range(data, q_lo, q_hi)
    assert guinier is not None
    assert fit_info is not None
    assert fit_info["b"] < 0
    assert guinier.rg == pytest.approx(2.0, abs=atol)
    assert guinier.i0 == pytest.approx(1.0, abs=0.02)
    assert guinier.range_start == pytest.approx(min(q_lo, q_hi))
    assert guinier.range_end == pytest.approx(max(q_lo, q_hi))


def test_collect_guinier_from_q_range_too_few_points():
    data = _Data1Dnm()
    collector = SASBDBDataCollector()
    q = np.asarray(data.x)
    q0 = float(q[10])
    guinier, fit_info = collector.collect_guinier_from_q_range(data, q0, q0)
    assert guinier is None
    assert fit_info is None
