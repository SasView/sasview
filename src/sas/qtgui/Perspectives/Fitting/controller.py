"""
FitPageController: the intents of a fit page (FW-MVC-DESIGN.md §3.1, Phases 5 and 6).

Every user edit is an intent here: it writes the document first, and records an
undoable command (``model/commands.py``) where the change is undoable. The views,
the tables and the legacy kernel follow the document (``ParameterTableAdapter``,
``SettingsSync``, ``LegacyKernelSync``).

A layout change (model, S(Q), category, shell count, 2D view, a data load that changes
is2D) takes the new layout from ``KernelBuilder.layout``, carries the user's settings
over (§2.6) and records one ``SnapshotCommand``. Undo restores a snapshot, which carries
its own layout.

The page is the presenter: it computes theory, asks questions and shows messages.
"""
from __future__ import annotations

import contextlib
import copy
import dataclasses

from sas.qtgui.Perspectives.Fitting.FittingConstants import CATEGORY_CUSTOM, STRUCTURE_DEFAULT
from sas.qtgui.Perspectives.Fitting.model import retention, rules, serializer
from sas.qtgui.Perspectives.Fitting.model.commands import (
    ApplyFitResultCommand,
    SetFlagCommand,
    SetOptionsCommand,
    SetParameterCommand,
    SetSmearingCommand,
    SnapshotCommand,
)
from sas.qtgui.Perspectives.Fitting.model.events import Origin
from sas.qtgui.Perspectives.Fitting.model.parameters import ModelSelection

_APPLY_FLAG = {"polydispersity": "applyPolydispersity", "magnetism": "applyMagnetism", "chain_fit": "applyChainFit"}


class FitPageController:

    def __init__(self, page) -> None:
        self._page = page
        self.document = page.document
        self._anchor = None          # the last state with a model: what a layout change retains from

    @property
    def history(self):
        return self._page.undo_stack

    @property
    def muted(self) -> bool:
        """The legacy stores are being written from the document: the edits they fire are not the user's."""
        return self._page.shadow.applying

    def _in_legacy_writer(self) -> bool:
        """A legacy writer is running: the shadow reads its whole change back when it ends, so an
        edit it fires is not written to the document on its own (that would publish a half-done state)."""
        return self._page.shadow.depth > 0

    def _status(self, message: str) -> None:
        self._page.communicator.statusBarUpdateSignal.emit(message)

    # -- for the commands -------------------------------------------------

    @contextlib.contextmanager
    def transaction(self, origin: Origin, recalculate: bool | str = False):
        """A document transaction; after an undo or redo of a value-bearing change, theory (R-1).
        *recalculate* "grid" also renews the theory grid (an options change)."""
        with self.document.transaction(origin) as tx:
            yield tx
        self._page.shadow.flush()
        if recalculate and origin in (Origin.UNDO, Origin.REDO):
            self.request_theory(grid=recalculate == "grid")

    def redo_origin(self) -> Origin:
        return Origin.REDO if self.history.replaying else Origin.USER

    def restore(self, snapshot, origin: Origin) -> None:
        """Bring the page to *snapshot*, layout included."""
        with self.transaction(origin, recalculate=True) as tx:
            tx.restore(snapshot)

    def request_theory(self, grid: bool = False) -> None:
        """As before: an options change renews the theory grid (recalculatePlotData), the rest do not."""
        if grid:
            self._page.recalculatePlotData()
        else:
            self._page.calculateQGridForModel()

    # -- parameters ---------------------------------------------------------

    def set_parameter(self, key: str, **fields) -> None:
        """Value, bounds or dispersion (with its fit flag) of one parameter: one undoable command."""
        if self.muted or self._in_legacy_writer():
            return
        p = self.document.parameters[key]
        new = {name: value for name, value in fields.items() if getattr(p, name) != value}
        if not new:
            return
        old = {name: getattr(p, name) for name in new}
        try:
            self.history.execute(SetParameterCommand(key, old, new))
        except ValueError as error:
            self._status(str(error))
            self._page.shadow.resync({key})

    def set_fit_flag(self, key: str, fit: bool) -> None:
        """Not undoable (MD/UNDO_PLAN_CLAUDE.md)."""
        if self.muted or self._in_legacy_writer() or self.document.parameters[key].fit == fit:
            return
        with self.transaction(Origin.USER) as tx:
            tx.set_parameter(key, fit=fit)

    def set_constraint(self, key: str, constraint, **fields) -> None:
        """Add, change or remove (None) a constraint, with the fields it implies. Not undoable."""
        if self.muted or self._in_legacy_writer():
            return
        with self.transaction(Origin.USER) as tx:
            tx.set_constraint(key, constraint)
            if fields:
                tx.set_parameter(key, **fields)

    def set_constraint_active(self, key: str, active: bool) -> None:
        """Activate or deactivate the constraint on *key* (the constraint tab, or a single-page fit)."""
        current = self.document.parameters[key].constraint
        if current is None or current.active == active:
            return
        constraint = copy.deepcopy(current)
        constraint.active = active
        self.set_constraint(key, constraint)

    def rename(self, mnemonic: str, old: str) -> None:
        """The page's new name, and every constraint expression of this page that used the old one.
        Not undoable, as before (the constraint tab checks the name)."""
        with self.transaction(Origin.SYSTEM) as tx:
            if mnemonic != self.document.identity.mnemonic:
                tx.set_mnemonic(mnemonic)
            self._replace_in_constraints(tx, old, mnemonic)

    def replace_page_name(self, old: str, new: str) -> None:
        """Another page was renamed: the constraint expressions that refer to it follow."""
        with self.transaction(Origin.SYSTEM) as tx:
            self._replace_in_constraints(tx, old, new)

    def _replace_in_constraints(self, tx, old: str, new: str) -> None:
        for p in self.document.constrained():
            if p.constraint.func and old in p.constraint.func:
                constraint = copy.deepcopy(p.constraint)
                constraint.func = constraint.func.replace(old, new)
                tx.set_constraint(p.key, constraint)

    # -- page settings --------------------------------------------------------

    def set_options(self, options) -> None:
        """Fit options; theory follows every options update, as before."""
        if self.muted:
            return
        if not self._in_legacy_writer():
            self._execute_if_changed(SetOptionsCommand, self.document.options, options)
        self.request_theory(grid=True)

    def set_smearing(self, smearing) -> None:
        if self.muted:
            return
        if not self._in_legacy_writer():
            self._execute_if_changed(SetSmearingCommand, self.document.smearing, smearing)
        self.request_theory()

    def set_flag(self, name: str, value: bool) -> None:
        """Polydispersity, magnetism or chain fit; the views apply the side effects."""
        if self.muted:
            return
        if self._in_legacy_writer():
            # Its read-back records the flag; the side effects are due now
            getattr(self._page, _APPLY_FLAG[name])(value)
            return
        old = getattr(self.document.flags, name)
        if old != value:
            self.history.execute(SetFlagCommand(name, old, value))

    def _execute_if_changed(self, command, old, new) -> None:
        if new == old:
            return
        try:
            self.history.execute(command(old, new))
        except ValueError as error:
            self._status(str(error))

    # -- layout changes (§2.6) ----------------------------------------------------

    def select_model(self, category: str, model: str = "", structure: str = "",
                     description: str = "Select model") -> None:
        """Category, model and structure factor, as the combo boxes give them ("" for none)."""
        structure = "" if structure == STRUCTURE_DEFAULT else structure
        self._change_layout(description, ModelSelection(category, model, structure, category == CATEGORY_CUSTOM))

    def set_multiplicity(self, shells: int) -> None:
        selection = dataclasses.replace(self.document.selection, multiplicity=shells)
        self._change_layout("Change the number of shells", selection)

    def set_view_2d(self, view_2d: bool) -> None:
        self._change_layout("Toggle 2D view", self.document.selection, view_2d)

    def relayout(self) -> None:
        """The data changed (a load clears the history): the layout follows is2D."""
        self._change_layout(None, self.document.selection)

    def _change_layout(self, description: str | None, selection: ModelSelection,
                       view_2d: bool | None = None) -> bool:
        """The layout of *selection*, with the user's settings carried over from the last state that
        had a model (so that a category switch, which empties the table, still retains them).
        Recorded as one undoable step if *description* is given."""
        if self.muted or self._in_legacy_writer():
            return False
        doc = self.document
        view_2d = doc.flags.view_2d if view_2d is None else view_2d
        try:
            layout = self._page.kernel_builder.layout(selection, rules.is_2d(doc, view_2d))
        except KeyError as error:
            self._status(f"Model {error} is not available.")
            return False
        shells = layout.multiplicity()
        selection = dataclasses.replace(selection, multiplicity=None if shells is None else int(shells.value))
        before = doc.snapshot()
        if len(before.parameters):
            self._anchor = before
        dropped = []
        if self._anchor is not None:
            symbols = set(doc.symbol_table(layout)) | self._page.otherSymbols()
            layout, dropped = retention.retain(self._anchor.parameters, layout, symbols)
        if (selection, view_2d) == (doc.selection, doc.flags.view_2d) and layout == doc.parameters:
            return False
        with self.transaction(Origin.USER) as tx:
            tx.set_selection(selection)
            if view_2d != doc.flags.view_2d:
                tx.set_flags(view_2d=view_2d)
            tx.set_parameters(layout)
        if dropped:
            self._status(f"Constraints on {', '.join(dropped)} removed: they refer to parameters that no longer exist.")
        if description is not None and self._anchor is not None and len(doc.parameters):
            new = doc.snapshot()
            if new != self._anchor:
                self.history.push_applied(SnapshotCommand(description, self._anchor, new))
        self._page.updateData()
        return True

    # -- fit results ----------------------------------------------------------------

    def apply_fit(self, param_dict: dict) -> None:
        """A single fit's values and errors ({key: (value, error)}): one undoable step (R-2)."""
        params = self.document.parameters
        after = {key: value for key, (value, _) in param_dict.items() if key in params}
        before = {key: params[key].value for key in after}
        with self.transaction(Origin.JOB) as tx:
            for p in params:
                if p.key in after:
                    tx.set_parameter(p.key, value=after[p.key], error=param_dict[p.key][1])
                elif p.error is not None:
                    tx.set_parameter(p.key, error=None)
        if before != after:
            self.history.push_applied(ApplyFitResultCommand(before, after))

    # -- paste and project load (§2.3) -------------------------------------------

    def paste(self, line_dict: dict) -> None:
        """Onto the current model, as one undoable step. The mismatch question is the view's."""
        before = self.document.snapshot()
        if self._apply_page(serializer.decode(line_dict)):
            new = self.document.snapshot()
            if new != before:
                self.history.push_applied(SnapshotCommand("Paste parameters", before, new))
            self.request_theory()

    def load_selection(self, line_dict: dict) -> None:
        """The model, S(Q) and category of a project page (before the view asks about a mismatch)."""
        payload = serializer.decode(line_dict)
        if payload.category:
            self._change_layout(None, ModelSelection(
                payload.category, payload.model or "",
                "" if payload.structure in (None, STRUCTURE_DEFAULT) else payload.structure,
                payload.category == CATEGORY_CUSTOM))

    def load_page(self, line_dict: dict, mnemonic: str | None = None) -> None:
        """A project page, onto the model selected for it (``load_selection``). Clears the history (R-8)."""
        if self._apply_page(serializer.decode(line_dict), mnemonic):
            self.request_theory()
        self.history.clear()

    def _apply_page(self, payload, mnemonic: str | None = None) -> bool:
        doc = self.document
        selection = doc.selection
        if selection.multiplicity is not None and payload.multiplicity is not None:
            selection = dataclasses.replace(selection, multiplicity=payload.multiplicity)
        view_2d = payload.flags.get("view_2d", doc.flags.view_2d)
        if selection != doc.selection or view_2d != doc.flags.view_2d:
            self._change_layout(None, selection, view_2d)
        try:
            with self.transaction(Origin.USER) as tx:
                serializer.apply_payload(tx, payload)
                if mnemonic is not None and mnemonic != doc.identity.mnemonic:
                    tx.set_mnemonic(mnemonic)
        except ValueError as error:
            self._status(f"The parameters could not be applied: {error}")
            return False
        return True
