"""Undo/Redo commands specific to the SasView Fitting perspective.

The shared base classes (UndoCommand, CompoundCommand, UndoStack,
DictSnapshotCommand) live in ``sas.qtgui.Perspectives.UndoRedo``.

This module defines Fitting-specific subclasses:
- ParameterValueCommand
- ParameterMinMaxCommand
- ModelSelectionCommand
- FitOptionsCommand
- SmearingOptionsCommand
- CheckboxToggleCommand
- FitResultCommand

Design notes:
- Each command stores only old_value + new_value (delta, not snapshot).
- ParameterValueCommand supports coalescing: consecutive edits to the same
  parameter are merged into one entry.
- Parameter 'fit' checkbox toggles are intentionally NOT tracked
  (see UNDO_PLAN_CLAUDE.md, Decisions).
"""
from __future__ import annotations

import logging
from typing import Any

# Base class for Fitting-specific commands — imported from shared module
from sas.qtgui.Perspectives.UndoRedo import UndoCommand  # noqa: E402

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Concrete commands — Fitting-specific
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

    def _apply(self, widget, value: float) -> None:
        widget.logic.kernel_module.setParam(self._param_name, value)
        widget._update_model_param_value(self._param_name, value)
        # Recompute the theory so the plot reflects the restored input value.
        # The snapshot-based restore paths (_restore_parameter_values,
        # _apply_fit_options, _restore_fit_result_snapshot, ...) all end with a
        # recompute; without this an undo/redo updates the parameter table but
        # leaves the plotted curve stale, desyncing the view from the params.
        widget.calculateQGridForModel()

    def undo(self, widget) -> None:
        self._apply(widget, self._old_val)

    def redo(self, widget) -> None:
        self._apply(widget, self._new_val)

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
        redoes all the way to *other*'s new value.  The *other* timestamp
        (latest edit) is carried forward so that the coalescing window is
        measured from the most recent edit, not the first one in the group.
        """
        merged = ParameterValueCommand(self._param_name, self._old_val, other._new_val)
        merged.timestamp = other.timestamp
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
        # Keep the plotted theory in sync with the restored bound, matching the
        # snapshot-based restore paths (see ParameterValueCommand._apply).
        widget.calculateQGridForModel()

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
    See UNDO_PLAN_CLAUDE.md, Decisions for rationale.
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

    The snapshots are structured dicts of the form::

        {"main": {name: value}, "poly": {name.width: value}, "magnet": {name: value}}

    covering the main kernel parameters as well as the polydispersity-width
    and magnetism parameters that a fit can also modify.

    ``old_snapshot`` MUST be captured at the very start of ``fitComplete()``,
    before ``updateModelFromList()`` is called (see UNDO_PLAN_CLAUDE.md,
    Step 2.6 — Critical ordering).

    Delegates to ``widget._restore_fit_result_snapshot(snapshot)``
    (added in Phase 2).
    """

    def __init__(
        self, old_snapshot: dict[str, dict], new_snapshot: dict[str, dict]
    ) -> None:
        super().__init__("Fit result")
        self._old_snapshot = {key: dict(val) for key, val in old_snapshot.items()}
        self._new_snapshot = {key: dict(val) for key, val in new_snapshot.items()}

    def undo(self, widget) -> None:
        widget._restore_fit_result_snapshot(self._old_snapshot)

    def redo(self, widget) -> None:
        widget._restore_fit_result_snapshot(self._new_snapshot)
