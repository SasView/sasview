import pytest

from sas.sascalc.invariant import invariant


class TestPowerLawExtrapolation:
    """Generate a power law distribution and verify that the extrapolation produce the correct distribution."""

    @pytest.fixture(autouse=True)
    def setup(self, power_law_data):
        self.scale = 1.5
        self.m = 3.0
        self.data = power_law_data

    def test_low_q(self):
        """Tests that the power law fit parameters match the known synthetic data."""
        inv = invariant.InvariantCalculator(data=self.data)
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


class TestDataExtraLow:
    """Test Guinier low-Q extrapolation against known synthetic data."""

    @pytest.fixture(autouse=True)
    def setup(self, guinier_data):
        self.scale = 1.5
        self.rg = 30.0
        self.data = guinier_data

    def test_low_q(self):
        """Invariant with low-Q extrapolation with no slit smear."""
        inv = invariant.InvariantCalculator(data=self.data)
        inv.set_extrapolation(range="low", npts=10, function="guinier")

        assert inv._low_extrapolation_npts == 10
        assert inv._low_extrapolation_function.__class__ == invariant.Guinier

        # Data boundaries for fitting
        qmin = inv._data.x[0]
        qmax = inv._data.x[inv._low_extrapolation_npts - 1]

        # Extrapolate the low-Q data
        inv._fit(model=inv._low_extrapolation_function, qmin=qmin, qmax=qmax, power=inv._low_extrapolation_power)

        assert self.scale == pytest.approx(inv._low_extrapolation_function.scale, abs=1e-6)
        assert self.rg**2 == pytest.approx(inv._low_extrapolation_function.Rg_squared, abs=1e-6)

        test_y = inv._low_extrapolation_function.evaluate_model(x=self.data.x)

        assert self.data.y == pytest.approx(test_y, rel=1e-3)

    def test_low_data(self):
        """Test that get_extra_data_low returns values matching the Guinier model."""
        inv = invariant.InvariantCalculator(data=self.data)
        inv.set_extrapolation(range="low", npts=10, function="guinier")

        # Data boundaries for fitting
        qmin = inv._data.x[0]
        qmax = inv._data.x[inv._low_extrapolation_npts - 1]

        inv._fit(model=inv._low_extrapolation_function, qmin=qmin, qmax=qmax, power=inv._low_extrapolation_power)
        inv.get_qstar(extrapolation="low")

        data_in_range = inv.get_extra_data_low(q_start=self.data.x[0], npts=inv._low_extrapolation_npts)
        test_y = data_in_range.y

        assert len(test_y) == len(self.data.y[: inv._low_extrapolation_npts])
        assert self.data.y[: inv._low_extrapolation_npts] == pytest.approx(test_y, rel=1e-3)


class TestDataExtraHighSlitPowerLaw:
    """Test power law high-Q extrapolation against known synthetic data."""

    @pytest.fixture(autouse=True)
    def setup(self, power_law_data):
        self.data = power_law_data
        self.npts = 20

    def test_high_q(self):
        """Test that the power law fit parameters match the known synthetic data."""
        inv = invariant.InvariantCalculator(data=self.data)
        inv.set_extrapolation(range="high", npts=self.npts, function="power_law")

        assert inv._high_extrapolation_npts == self.npts
        assert inv._high_extrapolation_function.__class__ == invariant.PowerLaw

        # Data boundaries for fitting
        xlen = len(self.data.x)
        start = xlen - inv._high_extrapolation_npts
        qmin = inv._data.x[start]
        qmax = inv._data.x[xlen - 1]

        # Extrapolate the high-Q data
        inv._fit(model=inv._high_extrapolation_function, qmin=qmin, qmax=qmax, power=inv._high_extrapolation_power)
        test_y = inv._high_extrapolation_function.evaluate_model(x=self.data.x[start:])

        assert len(test_y) == len(self.data.y[start:])
        assert self.data.y[start:] == pytest.approx(test_y, rel=1e-3)

    def test_high_data(self):
        """Test that get_extra_data_high returns values matching the power law model."""
        inv = invariant.InvariantCalculator(data=self.data)
        inv.set_extrapolation(range="high", npts=self.npts, function="power_law")

        # Data boundaries for fitting
        xlen = len(self.data.x)
        start = xlen - inv._high_extrapolation_npts
        qmin = inv._data.x[start]
        qmax = inv._data.x[xlen - 1]

        # Extrapolate the high-Q data
        inv._fit(model=inv._high_extrapolation_function, qmin=qmin, qmax=qmax, power=inv._high_extrapolation_power)
        inv.get_qstar(extrapolation="high")

        data_in_range = inv.get_extra_data_high(q_end=max(self.data.x), npts=inv._high_extrapolation_npts)
        test_y = data_in_range.y
        temp = self.data.y[start:]

        assert len(test_y) == len(temp)
        assert temp == pytest.approx(test_y, rel=1e-3)
