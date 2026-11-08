from unittest.mock import Mock

from sas.sascalc.invariant import invariant_mapper


class TestInvariantMapper:
    """Verify that invariant_mapper functions forward arguments correctly."""

    def test_get_qstar_forwards_arguments(self):
        inv = Mock()
        inv.get_qstar.return_value = 1.23

        result = invariant_mapper.get_qstar(inv, extrapolation="low")

        inv.get_qstar.assert_called_once_with("low")
        assert result == 1.23

    def test_get_qstar_with_error_forwards_arguments(self):
        inv = Mock()
        inv.get_qstar_with_error.return_value = (1.23, 0.01)

        result = invariant_mapper.get_qstar_with_error(inv, extrapolation="both")

        inv.get_qstar_with_error.assert_called_once_with("both")
        assert result == (1.23, 0.01)

    def test_get_volume_fraction_forwards_arguments(self):
        inv = Mock()
        inv.get_volume_fraction.return_value = 0.02

        result = invariant_mapper.get_volume_fraction(inv, contrast=2.2e-6, extrapolation="high")

        inv.get_volume_fraction.assert_called_once_with(2.2e-6, "high")
        assert result == 0.02

    def test_get_volume_fraction_with_error_forwards_arguments(self):
        inv = Mock()
        inv.get_volume_fraction_with_error.return_value = (0.02, 0.001)

        result = invariant_mapper.get_volume_fraction_with_error(inv, contrast=2.2e-6, extrapolation="low")

        inv.get_volume_fraction_with_error.assert_called_once_with(2.2e-6, "low")
        assert result == (0.02, 0.001)

    def test_get_surface_forwards_arguments(self):
        inv = Mock()
        inv.get_surface.return_value = 6.0e-5

        result = invariant_mapper.get_surface(inv, contrast=2.2e-6, porod_const=1.825e-7, extrapolation=None)

        inv.get_surface.assert_called_once_with(contrast=2.2e-6, porod_const=1.825e-7, extrapolation=None)
        assert result == 6.0e-5

    def test_get_surface_with_error_forwards_arguments(self):
        inv = Mock()
        inv.get_surface_with_error.return_value = (6.0e-5, 1.0e-6)

        result = invariant_mapper.get_surface_with_error(
            inv,
            contrast=2.2e-6,
            porod_const=1.825e-7,
            extrapolation="both",
        )

        inv.get_surface_with_error.assert_called_once_with(
            contrast=2.2e-6,
            porod_const=1.825e-7,
            extrapolation="both",
        )
        assert result == (6.0e-5, 1.0e-6)
