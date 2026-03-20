"""Undo/Redo infrastructure for the SasView Fitting perspective.

Provides UndoCommand (abstract base), concrete subclasses for each kind of
undoable action, and UndoStack which manages per-tab history.


Design notes:
- Each command stores only old_value + new_value (delta, not snapshot).
- UndoStack is a QObject so it can emit stackChanged for UI wiring.
- Command capture is suppressed during programmatic updates via suppressed().
- ParameterValueCommand supports coalescing: consecutive edits to the same
  parameter are merged into one entry (Qt fires dataChanged on commit, not
  per keystroke, providing the natural coalescing boundary).
- Parameter 'fit' checkbox toggles are intentionally NOT tracked
"""
from __future__ import annotations

import contextlib
import logging
import time
import traceback
from typing import Any

from PySide6 import QtCore, QtWidgets

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Base command
# ---------------------------------------------------------------------------

class UndoCommand:
    """Abstract base for all undoable actions.

    Subclasses must implement ``undo(widget)`` and ``redo(widget)``.
    ``description`` is shown in UI tooltips and the failure dialog.
    """

    def __init__(self, description: str) -> None:
        self.description: str = description
        self.timestamp: float = time.monotonic()

    def undo(self, widget) -> None:
        """Apply the reverse change to *widget*."""
        raise NotImplementedError(f"{type(self).__name__}.undo() not implemented")

    def redo(self, widget) -> None:
        """Re-apply the forward change to *widget*."""
        raise NotImplementedError(f"{type(self).__name__}.redo() not implemented")

    def can_merge(self, other: UndoCommand) -> bool:
        """Return True if *other* may be merged into this command.

        Merging collapses consecutive edits (e.g. two value changes to the
        same parameter) into a single undo entry.  Default: no merging.
        """
        return False

    def merge(self, other: UndoCommand) -> UndoCommand:
        """Return a single command combining *self* (earlier) with *other* (later).

        Only called when ``can_merge(other)`` returns True.
        """
        raise NotImplementedError(f"{type(self).__name__}.merge() not implemented")

    def __repr__(self) -> str:
        return f"<{type(self).__name__}: {self.description!r}>"


# ---------------------------------------------------------------------------
# Concrete commands
# ---------------------------------------------------------------------------

class ParameterValueCommand(UndoCommand):
    """Single parameter value change.

    Applies via ``widget.logic.kernel_module.setParam()`` and
    ``widget._update_model_param_value()`` (added in Phase 2).

    Supports coalescing: two consecutive edits to the same parameter are
    merged into one entry whose undo reverts all the way to the first
    captured value.
    """

    def __init__(self, param_name: str, old_val: float, new_val: float) -> None:
        super().__init__(f"Change {param_name}")
        self._param_name = param_name
        self._old_val = old_val
        self._new_val = new_val

    @property
    def param_name(self) -> str:
        return self._param_name

    def undo(self, widget) -> None:
        widget.logic.kernel_module.setParam(self._param_name, self._old_val)
        widget._update_model_param_value(self._param_name, self._old_val)

    def redo(self, widget) -> None:
        widget.logic.kernel_module.setParam(self._param_name, self._new_val)
        widget._update_model_param_value(self._param_name, self._new_val)

    #: Maximum age difference (seconds) between two edits to the same parameter
    #: that may still be coalesced into a single undo entry.  Edits farther
    #: apart than this are treated as independent actions.
    _COALESCE_WINDOW_SECONDS: float = 5.0

    def can_merge(self, other: UndoCommand) -> bool:
        return (
            isinstance(other, ParameterValueCommand)
            and other._param_name == self._param_name
            and (other.timestamp - self.timestamp) <= self._COALESCE_WINDOW_SECONDS
        )

    def merge(self, other: ParameterValueCommand) -> ParameterValueCommand:
        """Merge *self* (earlier) with *other* (later).

        The merged command undoes all the way to *self*'s old value and
        redoes all the way to *other*'s new value.  The *self* timestamp
        (earlier edit) is preserved.
        """
        merged = ParameterValueCommand(self._param_name, self._old_val, other._new_val)
        merged.timestamp = self.timestamp
        return merged


class ParameterMinMaxCommand(UndoCommand):
    """Parameter min or max bound change.

    ``bound`` must be ``"min"`` or ``"max"``.
    Writes directly to ``kernel_module.details[param_name][1 or 2]`` and
    delegates UI item update to ``widget._update_model_param_limit()``
    (added in Phase 2).
    """

    _BOUND_INDEX: dict[str, int] = {"min": 1, "max": 2}

    def __init__(
        self, param_name: str, bound: str, old_val: float, new_val: float
    ) -> None:
        assert bound in ("min", "max"), (
            f"bound must be 'min' or 'max', got {bound!r}"
        )
        super().__init__(f"Change {param_name} {bound}")
        self._param_name = param_name
        self._bound = bound
        self._old_val = old_val
        self._new_val = new_val

    def _apply(self, widget, value: float) -> None:
        idx = self._BOUND_INDEX[self._bound]
        widget.logic.kernel_module.details[self._param_name][idx] = value
        widget._update_model_param_limit(self._param_name, self._bound, value)

    def undo(self, widget) -> None:
        self._apply(widget, self._old_val)

    def redo(self, widget) -> None:
        self._apply(widget, self._new_val)


class ModelSelectionCommand(UndoCommand):
    """Category / model / structure-factor triple change.

    ``old_triple`` / ``new_triple`` are ``(category, model, structure_factor)``.
    ``old_params`` / ``new_params`` are ``{param_name: value}`` dicts.

    On undo the old model triple is re-selected (triggering a param table
    rebuild) and old parameter *values* are re-applied.  UI micro-state
    (expanded rows, active editor) is NOT restored — values only.

    The entire replay must run inside ``undo_stack.suppressed()`` (handled
    in Phase 2) to prevent the internal rebuild from creating spurious
    stack entries.

    Delegates to ``widget._restore_model_selection(triple, params)``
    (added in Phase 2).
    """

    def __init__(
        self,
        old_triple: tuple[str, str, str],
        new_triple: tuple[str, str, str],
        old_params: dict[str, float],
        new_params: dict[str, float],
    ) -> None:
        super().__init__(f"Select model {new_triple[1]!r}")
        self._old_triple = old_triple
        self._new_triple = new_triple
        self._old_params = dict(old_params)
        self._new_params = dict(new_params)

    def undo(self, widget) -> None:
        widget._restore_model_selection(self._old_triple, self._old_params)

    def redo(self, widget) -> None:
        widget._restore_model_selection(self._new_triple, self._new_params)


class FitOptionsCommand(UndoCommand):
    """Q range, npts, log_points, weighting changes.

    Delegates to ``widget._apply_fit_options(options)`` (added in Phase 2).
    """

    def __init__(
        self, old_options: dict[str, Any], new_options: dict[str, Any]
    ) -> None:
        super().__init__("Change fit options")
        self._old_options = dict(old_options)
        self._new_options = dict(new_options)

    def undo(self, widget) -> None:
        widget._apply_fit_options(self._old_options)

    def redo(self, widget) -> None:
        widget._apply_fit_options(self._new_options)


class SmearingOptionsCommand(UndoCommand):
    """Smearing state change.

    Delegates to ``widget._apply_smearing_state(state)`` (added in Phase 2).
    """

    def __init__(
        self, old_state: dict[str, Any], new_state: dict[str, Any]
    ) -> None:
        super().__init__("Change smearing options")
        self._old_state = dict(old_state)
        self._new_state = dict(new_state)

    def undo(self, widget) -> None:
        widget._apply_smearing_state(self._old_state)

    def redo(self, widget) -> None:
        widget._apply_smearing_state(self._new_state)


class CheckboxToggleCommand(UndoCommand):
    """Polydispersity / magnetism / 2D-view toggle.

    ``checkbox_id`` is the attribute name of the QCheckBox on *widget*
    (e.g. ``"chkPolydispersity"``).

    Note: parameter 'fit' checkbox toggles are intentionally NOT tracked.
    """

    def __init__(self, checkbox_id: str, old_bool: bool, new_bool: bool) -> None:
        super().__init__(f"Toggle {checkbox_id}")
        self._checkbox_id = checkbox_id
        self._old_bool = old_bool
        self._new_bool = new_bool

    def _apply(self, widget, value: bool) -> None:
        getattr(widget, self._checkbox_id).setChecked(value)

    def undo(self, widget) -> None:
        self._apply(widget, self._old_bool)

    def redo(self, widget) -> None:
        self._apply(widget, self._new_bool)


class FitResultCommand(UndoCommand):
    """Full parameter snapshot before and after a fit.

    ``old_params`` MUST be captured at the very start of ``fitComplete()``,
    before ``updateModelFromList()`` is called.

    Delegates to ``widget._restore_parameter_values(params)``
    (added in Phase 2).
    """

    def __init__(
        self, old_params: dict[str, float], new_params: dict[str, float]
    ) -> None:
        super().__init__("Fit result")
        self._old_params = dict(old_params)
        self._new_params = dict(new_params)

    def undo(self, widget) -> None:
        widget._restore_parameter_values(self._old_params)

    def redo(self, widget) -> None:
        widget._restore_parameter_values(self._new_params)


class CompoundCommand(UndoCommand):
    """Groups multiple commands into a single atomic undo/redo entry.

    ``undo()`` executes sub-commands in reverse order.
    ``redo()`` executes them in forward order.

    Used for model-selection changes, where the model switch and subsequent
    parameter-value restores must be treated as one logical action.
    """

    def __init__(
        self, commands: list[UndoCommand], description: str = ""
    ) -> None:
        desc = description or (
            commands[0].description if commands else "Compound action"
        )
        super().__init__(desc)
        self._commands: list[UndoCommand] = list(commands)

    @property
    def commands(self) -> list[UndoCommand]:
        """A copy of the contained command list."""
        return list(self._commands)

    def undo(self, widget) -> None:
        for cmd in reversed(self._commands):
            cmd.undo(widget)

    def redo(self, widget) -> None:
        for cmd in self._commands:
            cmd.redo(widget)


# ---------------------------------------------------------------------------
# UndoStack
# ---------------------------------------------------------------------------

class UndoStack(QtCore.QObject):
    """Per-tab undo/redo history for FittingWidget.

    Responsibilities:
    - Maintain undo and redo stacks of UndoCommand objects.
    - Coalesce consecutive commands when supported by the command type.
    - Emit ``stackChanged`` whenever state changes so that actionUndo /
      actionRedo enabled state and tooltip text can be refreshed.
    - Suppress command capture during programmatic updates (readFitPage,
      model rebuild, undo/redo replay) via the ``suppressed()`` context
      manager or ``set_enabled(False)``.
    - Handle command execution failures: log at WARNING, show a dialog,
      and offer ``reset_to_last_good()`` when failures repeat.

    The stack depth defaults to ``config.UNDO_STACK_MAX_DEPTH`` (200).

    Usage (Phase 2 integration)::

        # In FittingWidget.__init__:
        self.undo_stack = UndoStack(self)

        # Pushing a command:
        self.undo_stack.push(ParameterValueCommand(name, old, new))

        # Suppressing during programmatic updates:
        with self.undo_stack.suppressed():
            self.readFitPage(...)

        # Saving recovery state after a successful undo/redo:
        self.undo_stack.save_last_good_state(self.getParameterDict())
    """

    stackChanged = QtCore.Signal()

    def __init__(
        self, widget, parent: QtCore.QObject | None = None
    ) -> None:
        super().__init__(parent)
        self._widget = widget
        from sas import config as _sas_config
        self._max_depth: int = getattr(_sas_config, "UNDO_STACK_MAX_DEPTH", 200)
        self._undo_stack: list[UndoCommand] = []
        self._redo_stack: list[UndoCommand] = []
        self._enabled: bool = True
        self._replaying: bool = False
        self._last_good_state: dict[str, float] | None = None
        self._consecutive_failures: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def push(self, cmd: UndoCommand) -> None:
        """Push *cmd* onto the undo stack.

        - Dropped silently if the stack is disabled or a replay is active.
        - Coalesced with the stack top when ``top.can_merge(cmd)`` is True.
        - Clears the redo stack (new action invalidates forward history).
        - Trims the oldest entry when depth exceeds ``_max_depth``.
        """
        if not self._enabled or self._replaying:
            return

        if self._undo_stack and self._undo_stack[-1].can_merge(cmd):
            self._undo_stack[-1] = self._undo_stack[-1].merge(cmd)
            logger.debug("UndoStack: merged into %r", self._undo_stack[-1])
        else:
            self._undo_stack.append(cmd)
            if len(self._undo_stack) > self._max_depth:
                dropped = self._undo_stack.pop(0)
                logger.debug(
                    "UndoStack: depth limit reached, dropped %r", dropped
                )

        self._redo_stack.clear()
        logger.debug(
            "UndoStack: pushed %r (depth=%d)", cmd, len(self._undo_stack)
        )
        self.stackChanged.emit()

    def undo(self) -> None:
        """Undo the most recent command."""
        if not self._enabled or not self._undo_stack:
            return
        cmd = self._undo_stack[-1]  # peek — only removed from source on success
        self._replaying = True
        try:
            cmd.undo(self._widget)
            self._undo_stack.pop()
            self._redo_stack.append(cmd)
            self._consecutive_failures = 0
            self._auto_snapshot()
            self._refresh_view()
            logger.debug(
                "UndoStack: undo %r (undo=%d, redo=%d)",
                cmd, len(self._undo_stack), len(self._redo_stack),
            )
        except Exception:
            tb = traceback.format_exc()
            logger.warning("UndoStack: undo failed for %r:\n%s", cmd, tb)
            self._consecutive_failures += 1
            self._handle_failure(cmd, tb)
        finally:
            self._replaying = False
            self.stackChanged.emit()

    def redo(self) -> None:
        """Redo the most recently undone command."""
        if not self._enabled or not self._redo_stack:
            return
        cmd = self._redo_stack[-1]  # peek — only removed from source on success
        self._replaying = True
        try:
            cmd.redo(self._widget)
            self._redo_stack.pop()
            self._undo_stack.append(cmd)
            self._consecutive_failures = 0
            self._auto_snapshot()
            self._refresh_view()
            logger.debug(
                "UndoStack: redo %r (undo=%d, redo=%d)",
                cmd, len(self._undo_stack), len(self._redo_stack),
            )
        except Exception:
            tb = traceback.format_exc()
            logger.warning("UndoStack: redo failed for %r:\n%s", cmd, tb)
            self._consecutive_failures += 1
            self._handle_failure(cmd, tb)
        finally:
            self._replaying = False
            self.stackChanged.emit()

    def can_undo(self) -> bool:
        """Return True if undo is possible (enabled and stack non-empty)."""
        return self._enabled and bool(self._undo_stack)

    def can_redo(self) -> bool:
        """Return True if redo is possible (enabled and stack non-empty)."""
        return self._enabled and bool(self._redo_stack)

    def clear(self) -> None:
        """Clear both stacks and reset failure state."""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._last_good_state = None
        self._consecutive_failures = 0
        logger.debug("UndoStack: cleared")
        self.stackChanged.emit()

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable command capture and undo/redo execution.

        Emits ``stackChanged`` so that action enabled state is refreshed
        immediately (e.g. buttons grey out when a fit starts).
        """
        self._enabled = enabled
        logger.debug("UndoStack: set_enabled=%s", enabled)
        self.stackChanged.emit()

    @contextlib.contextmanager
    def suppressed(self):
        """Context manager: temporarily disable command capture.

        Use around programmatic model updates (readFitPage, model
        initialization, undo/redo replay) to prevent spurious entries::

            with self.undo_stack.suppressed():
                self.readFitPage(...)
        """
        was_enabled = self._enabled
        self._enabled = False
        logger.debug("UndoStack: suppression entered")
        try:
            yield
        finally:
            self._enabled = was_enabled
            logger.debug(
                "UndoStack: suppression lifted (enabled=%s)", self._enabled
            )

    def undo_text(self) -> str:
        """Human-readable label for Undo (suitable for tooltip)."""
        if self._undo_stack:
            return f"Undo {self._undo_stack[-1].description}"
        return "Undo"

    def redo_text(self) -> str:
        """Human-readable label for Redo (suitable for tooltip)."""
        if self._redo_stack:
            return f"Redo {self._redo_stack[-1].description}"
        return "Redo"

    def save_last_good_state(self, state: dict[str, float]) -> None:
        """Store *state* as the recovery snapshot.

        Call from FittingWidget after each successful undo/redo::

            self.undo_stack.undo()
            self.undo_stack.save_last_good_state(self.getParameterDict())
        """
        self._last_good_state = dict(state)
        logger.debug(
            "UndoStack: last_good_state saved (%d params)",
            len(self._last_good_state),
        )

    def reset_to_last_good(self) -> None:
        """Restore widget parameters from the most recent good snapshot.

        Invoked when the user clicks "Reset to Last Good State" in the
        failure dialog.  If no snapshot exists, logs a warning and returns.
        """
        if self._last_good_state is None:
            logger.warning(
                "UndoStack: reset_to_last_good called but no snapshot available"
            )
            return
        try:
            self._widget._restore_parameter_values(self._last_good_state)
            logger.info(
                "UndoStack: reset to last good state (%d params)",
                len(self._last_good_state),
            )
        except Exception:
            logger.warning(
                "UndoStack: reset_to_last_good failed:\n%s",
                traceback.format_exc(),
            )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _handle_failure(self, cmd: UndoCommand, tb: str) -> None:
        """Show an error dialog; offer reset when failures repeat."""
        offer_reset = (
            self._consecutive_failures >= 2
            and self._last_good_state is not None
        )
        parent = (
            self._widget
            if isinstance(self._widget, QtWidgets.QWidget)
            else None
        )
        msg_box = QtWidgets.QMessageBox(parent)
        msg_box.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        msg_box.setWindowTitle("Undo/Redo Error")
        msg_box.setText(
            f"An error occurred while replaying:\n\n"
            f"  {cmd.description}\n\n"
            f"The command has not been removed from history. The widget\n"
            f"state may be inconsistent — you may try again, or use\n"
            f"'Reset to Last Good State' to recover a known-good state."
        )
        msg_box.setDetailedText(tb)
        if offer_reset:
            reset_btn = msg_box.addButton(
                "Reset to Last Good State",
                QtWidgets.QMessageBox.ButtonRole.ResetRole,
            )
            msg_box.addButton(QtWidgets.QMessageBox.StandardButton.Close)
            msg_box.exec()
            if msg_box.clickedButton() is reset_btn:
                self.reset_to_last_good()
        else:
            msg_box.setStandardButtons(
                QtWidgets.QMessageBox.StandardButton.Close
            )
            msg_box.exec()

    def _auto_snapshot(self) -> None:
        """Record widget state as the recovery snapshot after a successful replay.

        Calls ``widget._get_parameter_dict()`` if available; silently skips
        when the method is absent (Phase 1 / mocks) or returns non-dict data.
        Phase 2 adds ``_get_parameter_dict()`` to FittingWidget, at which
        point every successful undo/redo automatically updates the snapshot
        without any integration-side calls.
        """
        try:
            state = self._widget._get_parameter_dict()
        except AttributeError:
            return
        if isinstance(state, dict):
            self._last_good_state = dict(state)
            logger.debug(
                "UndoStack: auto-saved last_good_state (%d params)",
                len(self._last_good_state),
            )

    def _refresh_view(self) -> None:
        """Force the parameter table viewport to repaint after undo/redo.

        PySide6 QTreeView may defer repainting when model items are changed
        programmatically (via QStandardItem.setText) rather than through
        user interaction.  This forces an immediate visual update.
        """
        try:
            self._widget.lstParams.viewport().update()
        except AttributeError:
            pass
