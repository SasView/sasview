"""
Undoable commands on the fit page document (FW-MVC-DESIGN.md §3.7, Appendix B).

Qt-free. The target of every command is the page's ``FitPageController``. A command
changes the document only through ``target.transaction(origin, recalculate)``, which
requests theory after an undo or redo of a value-bearing change (register R-1).
"""
from __future__ import annotations

import copy

from sas.qtgui.Perspectives.Fitting.model.events import Origin
from sas.qtgui.Perspectives.Fitting.model.history import UndoCommand
from sas.qtgui.Perspectives.Fitting.model.snapshot import PageSnapshot


class _SwapCommand(UndoCommand):
    """Applies ``old`` on undo and ``new`` on redo, each in one transaction."""

    recalculate: bool | str = True

    def __init__(self, description: str, old, new) -> None:
        super().__init__(description)
        self.old = copy.deepcopy(old)
        self.new = copy.deepcopy(new)

    def _apply(self, tx, value) -> None:
        raise NotImplementedError

    def undo(self, target) -> None:
        with target.transaction(Origin.UNDO, self.recalculate) as tx:
            self._apply(tx, self.old)

    def redo(self, target) -> None:
        with target.transaction(target.redo_origin(), self.recalculate) as tx:
            self._apply(tx, self.new)


class SetParameterCommand(_SwapCommand):
    """Fields of one parameter (value, a bound, a dispersion with its fit flag). A value edit
    coalesces with a later value edit of the same parameter, as the legacy value command did."""

    COALESCE_WINDOW_SECONDS = 5.0

    def __init__(self, key: str, old: dict, new: dict) -> None:
        super().__init__(f"Change {key}" + ("" if set(new) == {"value"} else " " + "/".join(sorted(new))), old, new)
        self.key = key

    def _apply(self, tx, fields: dict) -> None:
        tx.set_parameter(self.key, **fields)

    def can_merge(self, other: UndoCommand) -> bool:
        return (isinstance(other, SetParameterCommand) and other.key == self.key
                and set(other.new) == set(self.new) == {"value"}
                and other.timestamp - self.timestamp <= self.COALESCE_WINDOW_SECONDS)

    def merge(self, other: SetParameterCommand) -> SetParameterCommand:
        merged = SetParameterCommand(self.key, self.old, other.new)
        merged.timestamp = other.timestamp
        return merged


class SetOptionsCommand(_SwapCommand):
    recalculate = "grid"     # the theory grid follows the Q range

    def __init__(self, old, new) -> None:
        super().__init__("Change fit options", old, new)

    def _apply(self, tx, options) -> None:
        tx.set_options(options)


class SetSmearingCommand(_SwapCommand):
    def __init__(self, old, new) -> None:
        super().__init__("Change smearing options", old, new)

    def _apply(self, tx, smearing) -> None:
        tx.set_smearing(smearing)


class SetFlagCommand(_SwapCommand):
    """A page toggle. Its side effects, including theory for polydispersity (R-10), are the views'."""

    recalculate = False

    def __init__(self, flag: str, old: bool, new: bool) -> None:
        super().__init__(f"Toggle {flag}", old, new)
        self.flag = flag

    def _apply(self, tx, value: bool) -> None:
        tx.set_flags(**{self.flag: value})


class SnapshotCommand(UndoCommand):
    """Whole-state change: model, S(Q), shell count and 2D-view switches, and paste.

    Undo and redo restore a snapshot (``target.restore``), which carries its own layout.
    Fit flags and constraints are not recorded (they have no commands), so undo notes
    their current values by key and redo re-applies them on top of ``new`` (§3.7).
    """

    def __init__(self, description: str, old: PageSnapshot, new: PageSnapshot) -> None:
        super().__init__(description)
        self.old, self.new = old, new
        self._unrecorded: dict = {}

    def undo(self, target) -> None:
        self._unrecorded = {p.key: (p.fit, copy.deepcopy(p.constraint)) for p in target.document.parameters}
        target.restore(self.old, Origin.UNDO)

    def redo(self, target) -> None:
        new = self.new
        if self._unrecorded:
            new = copy.deepcopy(new)
            for key, (fit, constraint) in self._unrecorded.items():
                if key in new.parameters:
                    new.parameters[key].fit, new.parameters[key].constraint = fit, constraint
        target.restore(new, target.redo_origin())


class ApplyFitResultCommand(_SwapCommand):
    """The values of a single fit. Undo and redo both clear the errors (register R-2)."""

    def __init__(self, before: dict, after: dict) -> None:
        super().__init__("Fit result", before, after)

    def _apply(self, tx, values: dict) -> None:
        for key, value in values.items():
            tx.set_parameter(key, value=value)
        for p in tx.document.parameters:
            if p.error is not None:
                tx.set_parameter(p.key, error=None)
