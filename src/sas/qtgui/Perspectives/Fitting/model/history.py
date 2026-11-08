"""
Qt-free undo/redo history (FW-MVC-DESIGN.md §3.7).

``History`` holds the undo and redo stacks, coalescing, the depth limit,
suppression, the replay guard and the recovery snapshot. It knows nothing
about widgets: the target it replays commands on, and the hooks for the
recovery snapshot and the view refresh, are passed in.

``sas.qtgui.Perspectives.UndoRedo.UndoStack`` is the Qt wrapper used by
every perspective: a ``QObject`` that is also a ``History``, adding the
``stackChanged`` signal and the failure dialog.
"""
from __future__ import annotations

import contextlib
import copy
import logging
import time
import traceback
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class UndoCommand:
    """Abstract base for all undoable actions.

    Subclasses must implement ``undo(target)`` and ``redo(target)``.
    ``description`` is shown in UI tooltips and the failure dialog.
    """

    def __init__(self, description: str) -> None:
        self.description: str = description
        self.timestamp: float = time.monotonic()

    def undo(self, target) -> None:
        """Apply the reverse change to *target*."""
        raise NotImplementedError(f"{type(self).__name__}.undo() not implemented")

    def redo(self, target) -> None:
        """Apply (or re-apply) the forward change to *target*."""
        raise NotImplementedError(f"{type(self).__name__}.redo() not implemented")

    def can_merge(self, other: UndoCommand) -> bool:
        """Return True if *other* may be merged into this command. Default: no merging."""
        return False

    def merge(self, other: UndoCommand) -> UndoCommand:
        """Return a single command combining *self* (earlier) with *other* (later)."""
        raise NotImplementedError(f"{type(self).__name__}.merge() not implemented")

    def __repr__(self) -> str:
        return f"<{type(self).__name__}: {self.description!r}>"


class CompoundCommand(UndoCommand):
    """Groups commands into one atomic entry: undo runs them in reverse order, redo in order."""

    def __init__(self, commands: list[UndoCommand], description: str = "") -> None:
        super().__init__(description or (commands[0].description if commands else "Compound action"))
        self._commands: list[UndoCommand] = list(commands)

    @property
    def commands(self) -> list[UndoCommand]:
        """A copy of the contained command list."""
        return list(self._commands)

    def undo(self, target) -> None:
        for cmd in reversed(self._commands):
            cmd.undo(target)

    def redo(self, target) -> None:
        for cmd in self._commands:
            cmd.redo(target)


class ReplayError(RuntimeError):
    """``History.execute`` was called while a command was being replayed (a programming error)."""


class History:
    """Undo/redo stacks for one target.

    - ``execute(cmd)`` applies the command to the target, then records it.
    - ``push_applied(cmd)`` only records a command whose change has already
      been applied (the legacy behaviour of ``UndoStack.push``).

    The keyword-only constructor makes ``History`` usable as a cooperative
    base of a ``QObject`` (``UndoStack``).

    Subclasses may override ``_changed`` (called after every change of the
    stacks) and ``_replay_failed`` (called when undo or redo raises).
    """

    def __init__(
        self,
        *,
        target: Any = None,
        max_depth: int = 200,
        snapshot_fn: Callable[[], Any] | None = None,
        restore_fn: Callable[[Any], None] | None = None,
        refresh_fn: Callable[[], None] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._target = target
        self._max_depth: int = max_depth
        self._snapshot_fn = snapshot_fn
        self._restore_fn = restore_fn
        self._refresh_fn = refresh_fn
        self._undo_stack: list[UndoCommand] = []
        self._redo_stack: list[UndoCommand] = []
        self._enabled: bool = True
        self._replaying: bool = False
        self._last_good_state: Any = None
        self._consecutive_failures: int = 0

    # -- recording ------------------------------------------------------

    def execute(self, cmd: UndoCommand) -> None:
        """Apply *cmd* to the target, then record it (unless recording is suppressed)."""
        if self._replaying:
            raise ReplayError(f"execute({cmd!r}) called during undo/redo replay")
        cmd.redo(self._target)
        self.push_applied(cmd)

    def push_applied(self, cmd: UndoCommand) -> None:
        """Record *cmd*, whose change has already been applied.

        - Dropped silently if recording is disabled or a replay is active.
        - Coalesced with the stack top when ``top.can_merge(cmd)`` is True.
        - Clears the redo stack (a new action invalidates forward history).
        - Trims the oldest entry when depth exceeds the limit.
        """
        if not self._enabled or self._replaying:
            return
        if self._undo_stack and self._undo_stack[-1].can_merge(cmd):
            self._undo_stack[-1] = self._undo_stack[-1].merge(cmd)
        else:
            self._undo_stack.append(cmd)
            if len(self._undo_stack) > self._max_depth:
                dropped = self._undo_stack.pop(0)
                logger.debug("History: depth limit reached, dropped %r", dropped)
        self._redo_stack.clear()
        self._changed()

    # -- replay ---------------------------------------------------------

    def undo(self) -> None:
        """Undo the most recent command."""
        self._replay(self._undo_stack, self._redo_stack, "undo")

    def redo(self) -> None:
        """Redo the most recently undone command."""
        self._replay(self._redo_stack, self._undo_stack, "redo")

    def _replay(self, source: list[UndoCommand], destination: list[UndoCommand], action: str) -> None:
        if not self._enabled or not source:
            return
        cmd = source[-1]  # peek: only removed from the source on success
        self._replaying = True
        try:
            getattr(cmd, action)(self._target)
            source.pop()
            destination.append(cmd)
            self._consecutive_failures = 0
            self._auto_snapshot()
            if self._refresh_fn is not None:
                self._refresh_fn()
        except Exception:
            tb = traceback.format_exc()
            logger.warning("History: %s failed for %r:\n%s", action, cmd, tb)
            self._consecutive_failures += 1
            self._replay_failed(cmd, tb)
        finally:
            self._replaying = False
            self._changed()

    # -- state ----------------------------------------------------------

    @property
    def replaying(self) -> bool:
        """An undo or redo is being applied."""
        return self._replaying

    def can_undo(self) -> bool:
        """True if undo is possible (enabled and the stack is not empty)."""
        return self._enabled and bool(self._undo_stack)

    def can_redo(self) -> bool:
        """True if redo is possible (enabled and the stack is not empty)."""
        return self._enabled and bool(self._redo_stack)

    def clear(self) -> None:
        """Clear both stacks and reset failure state."""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._last_good_state = None
        self._consecutive_failures = 0
        self._changed()

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable recording and undo/redo execution."""
        self._enabled = enabled
        self._changed()

    @contextlib.contextmanager
    def suppressed(self):
        """Temporarily disable recording, e.g. around programmatic updates."""
        was_enabled = self._enabled
        self._enabled = False
        try:
            yield
        finally:
            self._enabled = was_enabled

    def undo_text(self) -> str:
        """Human-readable label for Undo (suitable for a tooltip)."""
        return f"Undo {self._undo_stack[-1].description}" if self._undo_stack else "Undo"

    def redo_text(self) -> str:
        """Human-readable label for Redo (suitable for a tooltip)."""
        return f"Redo {self._redo_stack[-1].description}" if self._redo_stack else "Redo"

    # -- recovery -------------------------------------------------------

    def save_last_good_state(self, state: Any) -> None:
        """Store a copy of *state* as the recovery snapshot."""
        self._last_good_state = copy.copy(state)

    def reset_to_last_good(self) -> None:
        """Restore the target from the most recent good snapshot, if there is one."""
        if self._last_good_state is None or self._restore_fn is None:
            logger.warning("History: reset_to_last_good called but no snapshot available")
            return
        try:
            self._restore_fn(self._last_good_state)
            logger.info("History: reset to last good state")
        except Exception:
            logger.warning("History: reset_to_last_good failed:\n%s", traceback.format_exc())

    def _auto_snapshot(self) -> None:
        """Record the target's state as the recovery snapshot after a successful replay."""
        if self._snapshot_fn is None:
            return
        state = self._snapshot_fn()
        if state is not None:
            self._last_good_state = state

    # -- hooks ----------------------------------------------------------

    def _changed(self) -> None:
        """Called after every change of the stacks or of the enabled state."""

    def _replay_failed(self, cmd: UndoCommand, tb: str) -> None:
        """Called when undo or redo of *cmd* raised; the command stays where it was."""
