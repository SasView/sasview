"""
FittingState - Shared state object for fitting widgets.

This dataclass encapsulates the shared state between FittingWidget and its tab widgets,
reducing tight coupling and making widgets more independent.
"""
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class FittingState:
    """
    Shared state for fitting widgets.

    This object is passed to tab widgets instead of direct parent references,
    allowing widgets to access shared state without tight coupling to FittingWidget.
    """
    # Data state
    is2D: bool = False
    is_batch_fitting: bool = False
    is_chain_fitting: bool = False
    data_is_loaded: bool = False
    model_is_loaded: bool = False
    data_index: int = 0

    # Fitting state
    fit_started: bool = False
    chi2: float | None = None
    fitResults: bool = False

    # Model state
    has_error_column: bool = False
    has_poly_error_column: bool = False
    has_magnet_error_column: bool = False

    # Q range and options
    q_range_min: float = 0.0
    q_range_max: float = 1.0
    npts: int = 50
    log_points: bool = False
    weighting: int = 0

    # Tab enablement
    poly_enabled: bool = False
    magnetism_enabled: bool = False

    # Callbacks for widgets to trigger actions
    on_fit_ready_changed: Callable[[bool], None] | None = None
    on_data_changed: Callable[[], None] | None = None
    on_model_changed: Callable[[], None] | None = None

    # Signal emitter for status updates
    communicator: Any | None = None

    def canHaveMagnetism(self, kernel_module: Any = None) -> bool:
        """
        Checks if the current model has magnetic scattering implemented.
        """
        has_mag_params = False
        if kernel_module:
            has_mag_params = len(kernel_module.magnetic_params) > 0
        return self.is2D and has_mag_params

    def updateFitReadyState(self, can_fit: bool) -> None:
        """
        Update the fit-ready state and notify listeners.
        """
        if self.on_fit_ready_changed:
            self.on_fit_ready_changed(can_fit)

    def notifyDataChanged(self) -> None:
        """
        Notify that data has changed.
        """
        if self.on_data_changed:
            self.on_data_changed()

    def notifyModelChanged(self) -> None:
        """
        Notify that model has changed.
        """
        if self.on_model_changed:
            self.on_model_changed()
