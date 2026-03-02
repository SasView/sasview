"""Unit tests for the Invariant Perspective, focusing on the calculation process and error handling."""

import PySide6.QtTest as QtTest
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from twisted.internet import threads
from twisted.python.failure import Failure

from sas.qtgui.Perspectives import Invariant
from sas.qtgui.Perspectives.Invariant.InvariantUtils import WIDGETS
from sas.qtgui.Perspectives.Invariant.Tests.RealDataTest import UIHelpersMixin
from sas.qtgui.Plotting.PlotterData import Data1D


@pytest.mark.parametrize("window_class", ["real_data"], indirect=True)
@pytest.mark.usefixtures("window_class")
class TestInvariantCalculateThread(UIHelpersMixin):
    def test_calculate_thread(self, mocker):
        """Test that calculate_thread calls the appropriate compute methods and updates the model."""

        # Patch reactor and make scheduling synchronous for assertions
        mock_reactor = mocker.patch.object(Invariant.InvariantPerspective, "reactor")
        mock_reactor.callFromThread.side_effect = lambda fn, *a, **k: fn(*a, **k)

        mock_calculator = mocker.MagicMock()
        self.window._calculator = mock_calculator

        mock_update = mocker.patch.object(self.window, "update_model_from_thread")

        # wrap the real compute methods so they still execute but are trackable
        mock_compute_low = mocker.patch.object(self.window, "compute_low", wraps=self.window.compute_low)
        mock_compute_high = mocker.patch.object(self.window, "compute_high", wraps=self.window.compute_high)

        mock_enable = mocker.patch.object(self.window, "enable_calculation")

        self.window.calculate_thread(extrapolation=None)

        assert mock_compute_low.call_count == 1
        assert mock_compute_high.call_count == 1

        mock_calculator.get_qstar_with_error.assert_called()

        mock_update.assert_called()
        mock_enable.assert_called_once()

    @pytest.mark.parametrize(
        "setup_name,calc_method,other_method,expect_widget",
        [
            ("setup_contrast", "get_volume_fraction_with_error", "get_contrast_with_error", WIDGETS.W_VOLUME_FRACTION),
            (
                "setup_volume_fraction",
                "get_contrast_with_error",
                "get_volume_fraction_with_error",
                WIDGETS.W_CONTRAST_OUT,
            ),
        ],
        ids=["contrast_mode", "volume_fraction_mode"],
    )
    def test_calculate_thread_contrast_or_volfrac(self, mocker, setup_name, calc_method, other_method, expect_widget):
        """Test that calculate_thread updates the model with the correct volume fraction or contrast values."""

        # Patch reactor and make scheduling synchronous for assertions
        mock_reactor = mocker.patch.object(Invariant.InvariantPerspective, "reactor")
        mock_reactor.callFromThread.side_effect = lambda fn, *a, **k: fn(*a, **k)

        mock_calc = mocker.MagicMock()
        self.window._calculator = mock_calc

        returned = (0.321, 0.012)
        getattr(mock_calc, calc_method).return_value = returned
        mocker.patch.object(mock_calc, "get_qstar_with_error", return_value=(0.1, 0.01))

        mock_update = mocker.patch.object(self.window, "update_model_from_thread")
        mock_enable = mocker.patch.object(self.window, "enable_calculation")

        getattr(self, setup_name)()

        self.window.calculate_thread(extrapolation=None)

        getattr(mock_calc, calc_method).assert_called_once()
        getattr(mock_calc, other_method).assert_not_called()

        mock_update.assert_any_call(expect_widget, returned[0])
        err_widget = expect_widget + 1
        mock_update.assert_any_call(err_widget, returned[1])
        mock_enable.assert_called()

    @pytest.mark.parametrize(
        "setup_name,calc_method,other_method",
        [
            ("setup_contrast", "get_volume_fraction_with_error", "get_contrast_with_error"),
            ("setup_volume_fraction", "get_contrast_with_error", "get_volume_fraction_with_error"),
        ],
        ids=["volume_fraction_exception", "contrast_exception"],
    )
    def test_calculate_thread_exceptions(self, mocker, setup_name, calc_method, other_method):
        """Test that calculate_thread handles exceptions from the calculator and logs warnings."""

        # Patch reactor and make scheduling synchronous for assertions
        mock_reactor = mocker.patch.object(Invariant.InvariantPerspective, "reactor")
        mock_reactor.callFromThread.side_effect = lambda fn, *a, **k: fn(*a, **k)

        mock_logger = mocker.patch.object(Invariant.InvariantPerspective, "logger")

        mock_calc = mocker.MagicMock()
        self.window._calculator = mock_calc

        getattr(mock_calc, calc_method).side_effect = ValueError("calculation error")
        mocker.patch.object(mock_calc, "get_qstar_with_error", return_value=(0.1, 0.01))

        getattr(self, setup_name)()

        self.window.calculate_thread(extrapolation=None)

        getattr(mock_calc, calc_method).assert_called_once()
        getattr(mock_calc, other_method).assert_not_called()

        mock_logger.warning.assert_called_once()
        logged_message = mock_logger.warning.call_args[0][0]
        assert "Calculation failed:" in logged_message

    @pytest.mark.parametrize(
        "setup_name,calc_method",
        [
            ("setup_contrast", "get_volume_fraction_with_error"),
            ("setup_volume_fraction", "get_contrast_with_error"),
        ],
        ids=["contrast_mode", "volume_fraction_mode"],
    )
    def test_calculate_thread_with_porod(self, setup_name, calc_method, mocker):
        """
        Test that calculate_thread correctly updates the model with specific surface
        and q* when Porod constant is provided.
        """

        # Patch reactor and make scheduling synchronous for assertions
        mock_reactor = mocker.patch.object(Invariant.InvariantPerspective, "reactor")
        mock_reactor.callFromThread.side_effect = lambda fn, *a, **k: fn(*a, **k)

        mock_calc = mocker.MagicMock()
        self.window._calculator = mock_calc

        mocker.patch.object(mock_calc, calc_method, return_value=(0.321, 0.012))

        returned = (0.1, 0.01)
        mocker.patch.object(mock_calc, "get_surface_with_error", return_value=returned)
        mocker.patch.object(mock_calc, "get_qstar_with_error", return_value=(0.1, 0.01))

        mock_update = mocker.patch.object(self.window, "update_model_from_thread")
        mock_enable = mocker.patch.object(self.window, "enable_calculation")

        getattr(self, setup_name)()
        self.update_and_emit_line_edits(self.window.txtPorodCst, "1e-04")
        self.window.calculate_thread(extrapolation=None)

        mock_update.assert_any_call(WIDGETS.W_SPECIFIC_SURFACE, returned[0])
        err_widget = WIDGETS.W_SPECIFIC_SURFACE + 1
        mock_update.assert_any_call(err_widget, returned[1])
        mock_enable.assert_called()

    @pytest.mark.parametrize(
        "setup_name,calc_method",
        [
            ("setup_contrast", "get_volume_fraction_with_error"),
            ("setup_volume_fraction", "get_contrast_with_error"),
        ],
        ids=["contrast_mode", "volume_fraction_mode"],
    )
    def test_calculate_thread_with_porod_exception(self, setup_name, calc_method, mocker):
        """Test that calculate_thread handles exceptions in Porod constant calculation and logs a warning."""

        # Patch reactor and make scheduling synchronous for assertions
        mock_reactor = mocker.patch.object(Invariant.InvariantPerspective, "reactor")
        mock_reactor.callFromThread.side_effect = lambda fn, *a, **k: fn(*a, **k)

        mock_logger = mocker.patch.object(Invariant.InvariantPerspective, "logger")

        mock_calc = mocker.MagicMock()
        self.window._calculator = mock_calc

        mocker.patch.object(mock_calc, calc_method, return_value=(0.321, 0.012))

        mocker.patch.object(mock_calc, "get_surface_with_error", side_effect=ValueError("surface calculation error"))
        mocker.patch.object(mock_calc, "get_qstar_with_error", return_value=(0.1, 0.01))

        getattr(self, setup_name)()
        self.update_and_emit_line_edits(self.window.txtPorodCst, "1e-04")
        self.window.calculate_thread(extrapolation=None)

        mock_logger.warning.assert_called_once()
        logged_message = mock_logger.warning.call_args[0][0]
        assert "Calculation failed: Specific surface calculation failed:" in logged_message

    def set_extra_low(self, calc, mocker):
        extra_low = Data1D(x=[0.001, 0.002, 0.003], y=[0.0, 0.0, 0.0], dy=[0.0, 0.0, 0.0])
        extra_low.name = "low_extra"
        extra_low.filename = "low_extra.txt"
        calc.get_extra_data_low = mocker.MagicMock(return_value=extra_low)
        return extra_low

    def set_extra_high(self, calc, mocker):
        extra_high = Data1D(x=[0.1, 0.2, 0.3], y=[0.0, 0.0, 0.0], dy=[0.0, 0.0, 0.0])
        extra_high.name = "high_extra"
        extra_high.filename = "high_extra.txt"
        calc.get_extra_data_high = mocker.MagicMock(return_value=extra_high)
        return extra_high

    @pytest.mark.parametrize(
        "extrapolation, plots",
        [
            ("low", ["low_extrapolation_plot"]),
            ("high", ["high_extrapolation_plot"]),
            ("both", ["low_extrapolation_plot", "high_extrapolation_plot"]),
        ],
        ids=["low_extrapolation", "high_extrapolation", "both_extrapolations"],
    )
    def test_calculate_thread_with_extrapolation_success(self, extrapolation, plots, mocker):
        """Test that calculate_thread handles a successful low extrapolation and updates the model accordingly."""

        # Patch reactor and make scheduling synchronous for assertions
        mock_reactor = mocker.patch.object(Invariant.InvariantPerspective, "reactor")
        mock_reactor.callFromThread.side_effect = lambda fn, *a, **k: fn(*a, **k)

        mock_compute_low = mocker.patch.object(self.window, "compute_low")
        mock_compute_high = mocker.patch.object(self.window, "compute_high")
        mocker.patch.object(self.window, "update_model_from_thread")

        mock_calc = mocker.MagicMock()
        self.window._calculator = mock_calc

        npts = 10
        if extrapolation == "low":
            mock_compute_low.return_value = (0.1, 0.01, True)
            mock_compute_high.return_value = (0.0, 0.0, False)
            self.window._low_points = npts
            self.set_extra_low(mock_calc, mocker)
            get_methods = ["get_extra_data_low"]
            expected_titles = [f"Low-Q extrapolation [{self.window._data.name}]"]
        elif extrapolation == "high":
            mock_compute_low.return_value = (0.0, 0.0, False)
            mock_compute_high.return_value = (0.2, 0.02, True)
            self.window._high_points = npts
            self.set_extra_high(mock_calc, mocker)
            get_methods = ["get_extra_data_high"]
            expected_titles = [f"High-Q extrapolation [{self.window._data.name}]"]
        else:
            mock_compute_low.return_value = (0.1, 0.01, True)
            mock_compute_high.return_value = (0.2, 0.02, True)
            self.window._low_points = npts
            self.window._high_points = npts
            self.set_extra_low(mock_calc, mocker)
            self.set_extra_high(mock_calc, mocker)
            get_methods = ["get_extra_data_low", "get_extra_data_high"]
            expected_titles = [
                f"Low-Q extrapolation [{self.window._data.name}]",
                f"High-Q extrapolation [{self.window._data.name}]",
            ]

        self.setup_contrast()

        mocker.patch.object(mock_calc, "get_qstar_with_error", return_value=(0.5, 0.05))
        mocker.patch.object(mock_calc, "get_volume_fraction_with_error", return_value=(0.321, 0.012))
        mocker.patch.object(mock_calc, "get_extrapolation_power", return_value=4.0)

        self.window.calculate_thread(extrapolation=extrapolation)

        for get_method in get_methods:
            getattr(self.window._calculator, get_method).assert_called_once()

        if extrapolation == "both":
            assert self.window._calculator.get_extrapolation_power.call_count == 2
        else:
            self.window._calculator.get_extrapolation_power.assert_called_once_with(range=extrapolation)

        for i, plot in enumerate(plots):
            plot = getattr(self.window, plot)
            assert plot is not None

            assert getattr(plot, "name", None) == expected_titles[i]
            assert getattr(plot, "title", None) == expected_titles[i]
            assert getattr(plot, "symbol", None) == "Line"
            assert getattr(plot, "has_errors", None) is False

    def test_plot_result(self, mocker):
        """Test plot_result updates model item and emits plot request when extrapolation plots exist."""

        mock_close = mocker.patch.object(self.window._manager.filesWidget, "closePlotsForItem")
        mock_update_model_item_with_plot = mocker.patch.object(
            Invariant.InvariantPerspective.GuiUtils, "updateModelItemWithPlot"
        )
        emitted = []
        self.window.communicate.plotRequestedSignal.connect(lambda plots: emitted.append(plots))
        mock_details = mocker.patch.object(self.window, "update_details_widget")
        mock_progress = mocker.patch.object(self.window, "update_progress_bars")

        mock_calc = mocker.MagicMock()
        self.window._calculator = mock_calc
        extra_high = self.set_extra_high(mock_calc, mocker)
        extra_low = self.set_extra_low(mock_calc, mocker)

        self.window.high_extrapolation_plot = self.window._manager.createGuiData(extra_high)
        title = "High-Q extrapolation"
        self.window.high_extrapolation_plot.name = title
        self.window.high_extrapolation_plot.title = title

        self.window.low_extrapolation_plot = self.window._manager.createGuiData(extra_low)
        title = "Low-Q extrapolation"
        self.window.low_extrapolation_plot.name = title
        self.window.low_extrapolation_plot.title = title
        self.window.extrapolation_made = False

        mock_model = mocker.Mock()
        mock_model.name = "test_model"

        self.window.plot_result(mock_model)

        mock_close.assert_called_once_with(self.window._model_item)

        assert mock_update_model_item_with_plot.call_count == 2

        assert len(emitted) == 1
        emitted_arg = emitted[0]
        assert isinstance(emitted_arg, list)
        assert emitted_arg[0] is self.window._model_item

        assert getattr(self.window.high_extrapolation_plot, "symbol", None) == "Line"
        assert getattr(self.window.low_extrapolation_plot, "symbol", None) == "Line"

        mock_details.assert_called_once()
        mock_progress.assert_called_once()


@pytest.mark.parametrize("window_class", ["real_data"], indirect=True)
@pytest.mark.usefixtures("window_class")
class TestInvariantCalculateHelpers(UIHelpersMixin):
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
        """Test that calculate_invariant starts the calculation thread with correct extrapolation and attaches callbacks."""

        self.window._low_extrapolate = low_q_enabled
        self.window._high_extrapolate = high_q_enabled

        mock_deferred = mocker.MagicMock()
        mock_defer = mocker.patch.object(threads, "deferToThread", return_value=mock_deferred)
        mock_calc_thread = mocker.patch.object(self.window, "calculate_thread")
        mock_enable = mocker.patch.object(self.window, "enable_calculation")

        self.window.calculate_invariant()

        mock_enable.assert_called_once_with(enabled=False, display="Calculating...")
        mock_defer.assert_called_once_with(self.window.calculate_thread, expected_extrapolation)

        # calculate_thread should not be called synchronously but deferred to the thread
        mock_calc_thread.assert_not_called()

        mock_deferred.addCallback.assert_called()
        callback = mock_deferred.addCallback.call_args[0][0]
        mock_deferred_plot = mocker.patch.object(self.window, "deferredPlot")
        mock_model = mocker.Mock()
        callback(mock_model)
        mock_deferred_plot.assert_called_once_with(mock_model, expected_extrapolation)

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

    @pytest.mark.parametrize("extrapolation", ["low", "high"], ids=["low", "high"])
    def test_deferredPlot(self, mocker, extrapolation):
        """Test that the deferredPlot method updates the plot and checks if the button can be reenabled."""

        # Patch reactor and make scheduling synchronous for assertions
        mock_reactor = mocker.patch.object(Invariant.InvariantPerspective, "reactor")
        mock_reactor.callFromThread.side_effect = lambda fn, *a, **k: fn(*a, **k)

        mock_plot = mocker.patch.object(self.window, "plot_result")

        mock_model = mocker.Mock()

        if extrapolation is None:
            self.window.extrapolation_made = True

        self.window.deferredPlot(mock_model, extrapolation=extrapolation)

        mock_reactor.callFromThread.assert_called_once()
        mock_plot.assert_called_once_with(mock_model)

    def test_deferredPlot_recreates_plot_when_no_extrapolation(self, mocker):
        """Test that deferredPlot creates a new plot when extrapolation is None and extrapolation_made is True."""

        # Patch reactor and make scheduling synchronous for assertions
        mock_reactor = mocker.patch.object(Invariant.InvariantPerspective, "reactor")
        mock_reactor.callFromThread.side_effect = lambda fn, *a, **k: fn(*a, **k)

        mock_plot = mocker.patch.object(self.window, "plot_result")
        mock_check = mocker.patch.object(self.window, "check_status")
        mock_newplot = mocker.patch.object(self.window._manager.filesWidget, "newPlot")

        mock_model = mocker.Mock()

        self.window.extrapolation_made = True

        self.window.deferredPlot(mock_model, extrapolation=None)

        assert mock_reactor.callFromThread.call_count == 2
        mock_plot.assert_called_once_with(mock_model)
        mock_check.assert_called_once()
        mock_newplot.assert_called_once()
        assert self.window.extrapolation_made is False

    @pytest.mark.parametrize(
        "extrapolate_checkbox, extrapolate_param, compute_func, expected",
        [
            ("chkLowQ_ex", "_low_extrapolate", "compute_low", (0.0, 0.0, False)),
            ("chkHighQ_ex", "_high_extrapolate", "compute_high", (0.0, 0.0, False)),
        ],
    )
    def test_no_extrapolation_early_return(self, extrapolate_checkbox, extrapolate_param, compute_func, expected):
        """Test that compute_low and compute_high return early with expected values when extrapolation is disabled."""
        checkbox = getattr(self.window, extrapolate_checkbox)
        func = getattr(self.window, compute_func)

        checkbox.setChecked(False)

        assert not getattr(self.window, extrapolate_param)

        assert func() == expected

    @pytest.mark.parametrize(
        "low_guinier, low_fit, low_fix, expected_function",
        [
            (True, False, False, "guinier"),
            (False, True, False, "power_law"),
            (False, False, True, "power_law"),
        ],
        ids=["guinier", "fit", "fix"],
    )
    def test_compute_low(self, mocker, low_guinier, low_fit, low_fix, expected_function):
        """Test that compute_low returns expected values when low extrapolation is enabled."""
        self.window._low_extrapolate = True
        self.window._low_guinier = low_guinier
        self.window._low_fit = low_fit
        self.window._low_fix = low_fix

        if low_fix:
            power = 4.0
            self.window.txtLowQPower_ex.setText(str(power))

        # mock_setter = mocker.patch.object(self.window, "set_low_q_extrapolation_upper_limit")
        mock_calculator = mocker.patch.object(self.window, "_calculator", autospec=True)
        mock_calculator.get_qstar_low.return_value = (1.0, 0.1)

        qstar, qstar_err, success = self.window.compute_low()

        # self.window.set_low_q_extrapolation_upper_limit.assert_called_once()

        mock_calculator.set_extrapolation.assert_called_once_with(
            range="low", npts=self.window._low_points, function=expected_function, power=power if low_fix else None
        )

        assert (qstar, qstar_err, success) == (1.0, 0.1, True)

    def test_compute_low_exception_handling(self, mocker):
        """Test that compute_low handles exceptions and returns expected values."""
        self.window._low_extrapolate = True
        self.window._low_guinier = True

        mock_calculator = mocker.patch.object(self.window, "_calculator", autospec=True)
        mock_calculator.get_qstar_low.side_effect = Exception("some error")
        mock_logger = mocker.patch.object(Invariant.InvariantPerspective, "logger")

        qstar, qstar_err, success = self.window.compute_low()

        assert (qstar, qstar_err, success) == ("ERROR", "ERROR", False)

        mock_logger.warning.assert_called_once()
        assert "Low-q calculation failed: some error" in mock_logger.warning.call_args[0][0]

    @pytest.mark.parametrize(
        "high_fit, high_fix",
        [
            (True, False),
            (False, True),
        ],
        ids=["fit", "fix"],
    )
    def test_compute_high(self, mocker, high_fit, high_fix):
        """Test that compute_high returns expected values when high extrapolation is enabled."""
        self.window._high_extrapolate = True
        self.window._high_fit = high_fit
        self.window._high_fix = high_fix

        if high_fix:
            power = 4.0
            self.window.txtHighQPower_ex.setText(str(power))

        # mock_setter = mocker.patch.object(self.window, "set_high_q_extrapolation_upper_limit")
        mock_calculator = mocker.patch.object(self.window, "_calculator", autospec=True)
        mock_calculator.get_qstar_high.return_value = (1.0, 0.1)

        qstar, qstar_err, success = self.window.compute_high()

        mock_calculator.set_extrapolation.assert_called_once_with(
            range="high", npts=self.window._high_points, function="power_law", power=power if high_fix else None
        )
        assert (qstar, qstar_err, success) == (1.0, 0.1, True)

    def test_compute_high_exception_handling(self, mocker):
        """Test that compute_high handles exceptions and returns expected values."""
        self.window._high_extrapolate = True
        self.window._high_guinier = True

        mock_calculator = mocker.patch.object(self.window, "_calculator", autospec=True)
        mock_calculator.get_qstar_high.side_effect = Exception("some error")
        mock_logger = mocker.patch.object(Invariant.InvariantPerspective, "logger")

        qstar, qstar_err, success = self.window.compute_high()

        assert (qstar, qstar_err, success) == ("ERROR", "ERROR", False)

        mock_logger.warning.assert_called_once()
        assert "High-q calculation failed: some error" in mock_logger.warning.call_args[0][0]
