"""Shared undo/redo infrastructure for SasView perspectives.

The stacks themselves live in the Qt-free ``History`` core
(``Fitting/model/history.py``, FW-MVC-DESIGN.md §3.7). This module provides
the Qt side used by every perspective:

- ``UndoStack``: a ``QObject`` that is a ``History``, adding the
  ``stackChanged`` signal and the failure dialog, with hooks that call the
  widget's ``_get_parameter_dict`` / ``_restore_parameter_values``.
- ``DictSnapshotCommand``: bulk state snapshot for perspectives with an
  ``updateFromParameters()``-style restore.
- ``UndoCommand`` and ``CompoundCommand``, re-exported from the core.

The shared contract for any "undoable widget" is:
    1. ``self.undo_stack = UndoStack(self)``
    2. ``_get_parameter_dict() -> dict`` — capture current input state
    3. ``_restore_parameter_values(state: dict)`` — apply a state dict
"""
from __future__ import annotations

import logging

from PySide6 import QtCore, QtWidgets

from sas.qtgui.Perspectives.Fitting.model.history import CompoundCommand, History, UndoCommand

__all__ = ["CompoundCommand", "DictSnapshotCommand", "UndoCommand", "UndoStack"]

logger = logging.getLogger(__name__)


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

class UndoStack(QtCore.QObject, History):
    """Per-tab / per-page undo/redo history with Qt signalling.

    ``push`` records a command whose change has already been applied
    (``History.push_applied``). ``stackChanged`` is emitted whenever the
    stacks or the enabled state change, so that actionUndo / actionRedo
    enabled state and tooltip text can be refreshed. A failing undo or redo
    is logged and reported in a dialog that offers ``reset_to_last_good()``
    when failures repeat.

    The stack depth defaults to ``config.UNDO_STACK_MAX_DEPTH`` (200),
    per widget.

    Usage::

        self.undo_stack = UndoStack(self)
        self.undo_stack.push(DictSnapshotCommand(old, new, "Description"))
        with self.undo_stack.suppressed():
            self.loadFromProject(...)
    """

    stackChanged = QtCore.Signal()

    def __init__(self, widget, parent: QtCore.QObject | None = None, *, target=None,
                 snapshot_fn=None, restore_fn=None) -> None:
        """*widget* is the dialog parent. By default the commands replay on it, and the recovery
        snapshot is its ``_get_parameter_dict`` / ``_restore_parameter_values``. The fit page passes
        its controller as *target* and the document's snapshot and restore (FW-MVC-DESIGN.md §3.7)."""
        from sas import config as _sas_config
        # Cooperative initialisation: QObject passes the keywords on to History.
        super().__init__(
            parent,
            target=widget if target is None else target,
            max_depth=getattr(_sas_config, "UNDO_STACK_MAX_DEPTH", 200),
            snapshot_fn=snapshot_fn or self._widget_state,
            restore_fn=restore_fn or (lambda state: widget._restore_parameter_values(state)),
            refresh_fn=self._refresh_view,
        )
        self._widget = widget

    def push(self, cmd: UndoCommand) -> None:
        """Record *cmd*, whose change has already been applied (see ``History.push_applied``)."""
        self.push_applied(cmd)

    # -- History hooks ----------------------------------------------------

    def _changed(self) -> None:
        self.stackChanged.emit()

    def _replay_failed(self, cmd: UndoCommand, tb: str) -> None:
        """Show an error dialog; offer reset when failures repeat."""
        offer_reset = self._consecutive_failures >= 2 and self._last_good_state is not None
        parent = self._widget if isinstance(self._widget, QtWidgets.QWidget) else None
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
            msg_box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Close)
            msg_box.exec()

    def _widget_state(self) -> dict | None:
        """The widget's ``_get_parameter_dict()``, or None if it has none or it is not a dict."""
        try:
            state = self._widget._get_parameter_dict()
        except AttributeError:
            return None
        return dict(state) if isinstance(state, dict) else None

    def _refresh_view(self) -> None:
        """Force a viewport repaint after undo/redo (for QTreeView-based widgets)."""
        try:
            self._widget.lstParams.viewport().update()
        except AttributeError:
            pass
