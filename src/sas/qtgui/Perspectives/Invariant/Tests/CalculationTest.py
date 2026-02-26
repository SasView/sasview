"""Unit tests for the Invariant Perspective, focusing on the calculation process and error handling."""

import PySide6.QtTest as QtTest
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from twisted.internet import threads
from twisted.python.failure import Failure

from sas.qtgui.Perspectives import Invariant


@pytest.mark.parametrize("window_class", ["real_data"], indirect=True)
@pytest.mark.usefixtures("window_class")
class TestInvariantCalculation:
    def test_on_calculate_emits_slot(self, mocker):
        """Ensure clicking the button triggers the connected slot."""
        mock_calculate = mocker.patch.object(self.window, "calculate_invariant")
        self.window.cmdCalculate.setEnabled(True)

        QtTest.QTest.mouseClick(self.window.cmdCalculate, Qt.LeftButton)
        QApplication.processEvents()

        mock_calculate.assert_called_once()

    @pytest.mark.parametrize(
        "low_q_enabled, high_q_enabled, expected_extrapolation",
        [
            (True, True, "both"),
            (True, False, "low"),
            (False, True, "high"),
            (False, False, None),
        ],
        ids=["both", "low_only", "high_only", "none"],
    )
    def test_calculate_invariant_starts_thread_and_attaches_callbacks(
        self, mocker, low_q_enabled, high_q_enabled, expected_extrapolation
    ):
        self.window._low_extrapolate = low_q_enabled
        self.window._high_extrapolate = high_q_enabled

        mock_enable = mocker.patch.object(self.window, "enable_calculation")
        mock_deferred = mocker.MagicMock()
        mock_defer = mocker.patch.object(threads, "deferToThread", return_value=mock_deferred)
        mock_calc_thread = mocker.patch.object(self.window, "calculate_thread")

        self.window.calculate_invariant()

        mock_enable.assert_called_once_with(enabled=False, display="Calculating...")
        mock_defer.assert_called_once_with(self.window.calculate_thread, expected_extrapolation)

        # calculate_thread should not be called synchronously but deferred to the thread
        mock_calc_thread.assert_not_called()

        mock_deferred.addCallback.assert_called_once_with(self.window.deferredPlot)
        mock_deferred.addErrback.assert_called_once_with(self.window.on_calculation_failed)

    def test_on_calculation_failed(self, mocker):
        """Test that the on_calculation_failed method logs the error and checks if the button can be reenabled."""
        mock_check = mocker.patch.object(self.window, "check_status")
        mock_logger = mocker.patch.object(Invariant.InvariantPerspective, "logger")

        failure = Failure(Exception("some error"))
        self.window.on_calculation_failed(failure)

        mock_logger.error.assert_called_once()

        # Check that the logged message contains the expected text
        logged_message = mock_logger.error.call_args[0][0]
        assert "calculation failed:" in logged_message
        assert "some error" in logged_message

        mock_check.assert_called_once_with()

    def test_deferred_plot(self, mocker):
        """Test that the deferredPlot method updates the plot and checks if the button can be reenabled."""
        mock_call = mocker.patch.object(Invariant.InvariantPerspective, "reactor").callFromThread

        mock_plot = mocker.patch.object(self.window, "plot_result")
        mock_check = mocker.patch.object(self.window, "check_status")

        mock_model = mocker.Mock()

        self.window.deferredPlot(mock_model)

        mock_call.assert_called_once()

        # Check that the first arg is plot_result and it is called with the model
        calledfunc = mock_call.call_args[0][0]
        # assert callable(calledfunc)
        calledfunc()
        mock_plot.assert_called_once_with(mock_model)

        mock_check.assert_called_once()

    @pytest.mark.parametrize(
        "extrapolation, extrapolate_checkbox, extrapolate_param, compute_func, expected",
        [
            ("low", "chkLowQ_ex", "_low_extrapolate", "compute_low", (0.0, 0.0, False)),
            ("high", "chkHighQ_ex", "_high_extrapolate", "compute_high", (0.0, 0.0, False)),
        ],
    )
    def test_no_extrapolation_early_return(
        self, mocker, extrapolation, extrapolate_checkbox, extrapolate_param, compute_func, expected
    ):
        checkbox = getattr(self.window, extrapolate_checkbox)
        func = getattr(self.window, compute_func)

        checkbox.setChecked(False)

        assert not getattr(self.window, extrapolate_param)

        assert func() == expected

    def test_low_q_guinier(self):
        pass
