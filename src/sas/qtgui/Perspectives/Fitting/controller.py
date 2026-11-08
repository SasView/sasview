"""
FitPageController: the intents of a fit page (FW-MVC-DESIGN.md §3.1, Phase 5).

Every user edit is an intent here: it writes the document first, and records an
undoable command (``model/commands.py``) where the change is undoable. The views
and the legacy kernel follow through the reverse syncs (``DocumentShadow.subscribe_reverse``).

Until Phase 6 the legacy code still builds the tables, so a layout change (model,
S(Q), category, shell count, 2D view) is built by the legacy builders. The shadow
reads the new layout back, ``layout_changed`` then carries the user's settings over
(§2.6) and ``record`` stores a ``SnapshotCommand``. Undo restores a snapshot,
rebuilding the tables for its selection first.

The page is the presenter: it builds tables, computes theory and shows messages.
"""
from __future__ import annotations

import contextlib
import dataclasses
import functools

from sas.qtgui.Perspectives.Fitting.model import retention, serializer
from sas.qtgui.Perspectives.Fitting.model.commands import (
    SetFlagCommand,
    SetOptionsCommand,
    SetParameterCommand,
    SetSmearingCommand,
    SnapshotCommand,
)
from sas.qtgui.Perspectives.Fitting.model.events import Origin

_APPLY_FLAG = {"polydispersity": "applyPolydispersity", "magnetism": "applyMagnetism", "chain_fit": "applyChainFit"}


def structural(description: str):
    """Decorator for the page's layout slots (model, S(Q), category, shells, 2D view).

    When the user runs one, it is built by the legacy code with history suppressed,
    and the result is recorded as one ``SnapshotCommand``. Nested calls, rebuilds for
    undo or load, and calls before the page is set up just run.
    """
    def decorator(method):
        @functools.wraps(method)
        def wrapper(page, *args):
            controller = getattr(page, "controller", None)
            if controller is None or not controller.records_layout():
                return method(page, *args)
            controller.layout_seen = False
            with page.undo_stack.suppressed():
                result = method(page, *args)
            controller.record(description)
            return result
        return wrapper
    return decorator


class FitPageController:

    def __init__(self, page) -> None:
        self._page = page
        self.document = page.document
        self._rebuilding = False
        self._anchor = None          # the last state with a model: what a layout change retains from
        self.layout_seen = False     # a layout read-back happened in the current structural slot

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
        """Bring the page to *snapshot*: rebuild the tables if its layout differs, then restore it."""
        doc = self.document
        if snapshot.selection != doc.selection or snapshot.flags.view_2d != doc.flags.view_2d:
            with self.rebuilding():
                self._page.rebuildForSelection(snapshot.selection, snapshot.flags.view_2d)
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
            self._page.communicator.statusBarUpdateSignal.emit(str(error))
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
            self._page.communicator.statusBarUpdateSignal.emit(str(error))

    # -- layout changes, built by the legacy code -----------------------------

    @contextlib.contextmanager
    def rebuilding(self):
        """The legacy builders run for an undo, a load or a paste: no retention, nothing recorded."""
        was, self._rebuilding = self._rebuilding, True
        try:
            with self.history.suppressed():
                yield
        finally:
            self._rebuilding = was

    def records_layout(self) -> bool:
        shadow = self._page.shadow
        return shadow.active and not shadow.applying and shadow.depth == 0 and not self._rebuilding

    def layout_changed(self, before) -> None:
        """Called by the shadow after it read a rebuilt layout back: carry the settings over (§2.6).

        The source is the last state that had a model, so that a category switch (which empties
        the table until a model is chosen) still retains, as before.
        """
        self.layout_seen = True
        if self._rebuilding:
            return
        if len(before.parameters):
            self._anchor = before
        doc = self.document
        if self._anchor is None or not len(doc.parameters):
            return
        symbols = set(doc.symbol_table()) | self._page.otherSymbols()
        retained, dropped = retention.retain(self._anchor.parameters, doc.parameters.copy(), symbols)
        if retained != doc.parameters:
            with self.transaction(Origin.USER) as tx:
                tx.set_parameters(retained)
        if dropped:
            self._page.communicator.statusBarUpdateSignal.emit(
                f"Constraints on {', '.join(dropped)} removed: they refer to parameters that no longer exist.")

    def record(self, description: str) -> None:
        """After a structural slot: one undoable step from the state before it."""
        if not self.layout_seen or self._anchor is None or not len(self.document.parameters):
            return
        new = self.document.snapshot()
        if new != self._anchor:
            self.history.push_applied(SnapshotCommand(description, self._anchor, new))

    # -- paste and project load (§2.3) -------------------------------------------

    def paste(self, line_dict: dict) -> None:
        """Onto the current model, as one undoable step. The mismatch question is the view's."""
        before = self.document.snapshot()
        if self._apply_page(serializer.decode(line_dict)):
            new = self.document.snapshot()
            if new != before:
                self.history.push_applied(SnapshotCommand("Paste parameters", before, new))
            self.request_theory()

    def load_page(self, line_dict: dict, mnemonic: str | None = None) -> None:
        """A project page, onto the model the view has selected for it. Clears the history (R-8)."""
        if self._apply_page(serializer.decode(line_dict), mnemonic):
            self.request_theory()
        self.history.clear()

    def _apply_page(self, payload, mnemonic: str | None = None) -> bool:
        doc = self.document
        selection = doc.selection
        if selection.multiplicity is not None and payload.multiplicity is not None:
            selection = dataclasses.replace(selection, multiplicity=payload.multiplicity)
        view_2d = payload.flags.get("view_2d", doc.flags.view_2d)
        if selection != doc.selection or (view_2d != doc.flags.view_2d and not doc.is_loaded()):
            with self.rebuilding():
                self._page.rebuildForSelection(selection, view_2d)
        try:
            with self.transaction(Origin.USER) as tx:
                serializer.apply_payload(tx, payload)
                if mnemonic is not None and mnemonic != doc.identity.mnemonic:
                    tx.set_mnemonic(mnemonic)
        except ValueError as error:
            self._page.communicator.statusBarUpdateSignal.emit(f"The parameters could not be applied: {error}")
            return False
        return True
