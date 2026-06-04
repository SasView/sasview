"""Shared undo/redo infrastructure for SasView perspectives.

Provides UndoCommand (abstract base), CompoundCommand (atomic grouping),
UndoStack (history management), and DictSnapshotCommand (bulk state
snapshot for perspectives with updateFromParameters()-style restore).

Originally extracted from Fitting/UndoRedo.py per the UNDO_OTHER.md plan.

Design notes:
- UndoStack is a QObject so it can emit stackChanged for UI wiring.
- Each command stores old + new state and applies via widget callbacks.
- Command capture is suppressed during programmatic updates via suppressed().
- The shared contract for any "undoable widget" is:
    1. ``self.undo_stack = UndoStack(self)``
    2. ``_get_parameter_dict() -> dict`` — capture current input state
    3. ``_restore_parameter_values(state: dict)`` — apply a state dict
"""
from __future__ import annotations

import contextlib
import logging
import time
import traceback

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

        Merging collapses consecutive edits into a single undo entry.
        Default: no merging.
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
# Compound command (groups multiple commands atomically)
# ---------------------------------------------------------------------------

class CompoundCommand(UndoCommand):
    """Groups multiple commands into a single atomic undo/redo entry.

    ``undo()`` executes sub-commands in reverse order.
    ``redo()`` executes them in forward order.
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
# Dict snapshot command — generic bulk-state undo/redo
# ---------------------------------------------------------------------------

class DictSnapshotCommand(UndoCommand):
    """Re-applies a full state-dict snapshot for undo or redo.

    For perspectives that already have ``updateFromParameters()``-style
    bulk apply (Invariant, Inversion, later SizeDistribution/Corfunc).

    Calls ``widget._restore_parameter_values(state)`` — the same hook name
    ``UndoStack.reset_to_last_good()`` already uses, so the recovery path
    works without any stack changes.
    """

    def __init__(self, old_state: dict, new_state: dict, description: str = "Change") -> None:
        super().__init__(description)
        self._old: dict = dict(old_state)
        self._new: dict = dict(new_state)

    def undo(self, widget) -> None:
        widget._restore_parameter_values(self._old)

    def redo(self, widget) -> None:
        widget._restore_parameter_values(self._new)


# ---------------------------------------------------------------------------
# UndoStack
# ---------------------------------------------------------------------------

class UndoStack(QtCore.QObject):
    """Per-tab / per-page undo/redo history.

    Responsibilities:
    - Maintain undo and redo stacks of UndoCommand objects.
    - Coalesce consecutive commands when supported by the command type.
    - Emit ``stackChanged`` whenever state changes so that actionUndo /
      actionRedo enabled state and tooltip text can be refreshed.
    - Suppress command capture during programmatic updates via the
      ``suppressed()`` context manager or ``set_enabled(False)``.
    - Handle command execution failures: log at WARNING, show a dialog,
      and offer ``reset_to_last_good()`` when failures repeat.

    The stack depth defaults to ``config.UNDO_STACK_MAX_DEPTH`` (200).

    Usage::

        # In widget.__init__:
        self.undo_stack = UndoStack(self)

        # Pushing a command:
        self.undo_stack.push(DictSnapshotCommand(old, new, "Description"))

        # Suppressing during programmatic updates:
        with self.undo_stack.suppressed():
            self.loadFromProject(...)
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
        self._last_good_state: dict | None = None
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
        else:
            self._undo_stack.append(cmd)
            if len(self._undo_stack) > self._max_depth:
                dropped = self._undo_stack.pop(0)
                logger.debug(
                    "UndoStack: depth limit reached, dropped %r", dropped
                )

        self._redo_stack.clear()
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
        self.stackChanged.emit()

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable command capture and undo/redo execution.

        Emits ``stackChanged`` so that action enabled state is refreshed
        immediately (e.g. buttons grey out when a calculation starts).
        """
        self._enabled = enabled
        self.stackChanged.emit()

    @contextlib.contextmanager
    def suppressed(self):
        """Context manager: temporarily disable command capture.

        Use around programmatic updates to prevent spurious entries::

            with self.undo_stack.suppressed():
                self.loadState(...)
        """
        was_enabled = self._enabled
        self._enabled = False
        try:
            yield
        finally:
            self._enabled = was_enabled

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

    def save_last_good_state(self, state: dict) -> None:
        """Store *state* as the recovery snapshot."""
        self._last_good_state = dict(state)

    def reset_to_last_good(self) -> None:
        """Restore widget parameters from the most recent good snapshot.

        Invoked when the user clicks "Reset to Last Good State" in the
        failure dialog.  If no snapshot exists, logs a warning and returns.
        """
        if self._last_good_state is None:
            return
        try:
            self._widget._restore_parameter_values(self._last_good_state)
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
        when the method is absent or returns non-dict data.
        """
        try:
            state = self._widget._get_parameter_dict()
        except AttributeError:
            return
        if isinstance(state, dict):
            self._last_good_state = dict(state)

    def _refresh_view(self) -> None:
        """Force viewport repaint after undo/redo (for QTreeView-based widgets).

        Silently skips when the widget doesn't have a ``lstParams``.
        """
        try:
            self._widget.lstParams.viewport().update()
        except AttributeError:
            pass
