"""
FitPageController: the intents of a fit page (FW-MVC-DESIGN.md §3.1, Phases 5 to 7).

Every user edit is an intent here: it writes the document first, and records an
undoable command (``model/commands.py``) where the change is undoable. The views
follow the document: they subscribe through ``subscribe_view``, and while they write
their widgets the edits those writes fire are ignored (``muted``).

A layout change (model, S(Q), category, shell count, 2D view, a data load that changes
is2D) takes the new layout from ``KernelBuilder.layout``, carries the user's settings
over (§2.6) and records one ``SnapshotCommand``. Undo restores a snapshot, which carries
its own layout.

Data: ``set_datasets`` (a load), ``set_active_dataset`` (the batch file combo box),
``data_masked`` and ``ensure_default_dataset`` (the theory grid of a page without data).

Jobs (§3.3): a theory or fit request is built from the document when it is launched,
and its completion is accepted only if it is still the page's latest request and the
layout it was computed for is still the page's. A theory result remembers the inputs it
was computed from: one computed from older inputs is still shown, but ``current_result``
does not return it. ``close`` cancels every request.

The page is the presenter: it shows plots, asks questions and shows messages.
"""
from __future__ import annotations

import contextlib
import copy
import dataclasses

from sas.qtgui.Perspectives.Fitting import FittingUtilities
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
from sas.qtgui.Perspectives.Fitting.model.events import PARAMETER_FIELDS, ChangeSet, Origin, ParametersChanged
from sas.qtgui.Perspectives.Fitting.model.parameters import DataRef, ModelSelection, PageMode
from sas.qtgui.Perspectives.Fitting.model.results import JobState, Provenance, Results
from sas.qtgui.Perspectives.Fitting.services import constraints as constraint_service
from sas.qtgui.Perspectives.Fitting.services import plots
from sas.qtgui.Perspectives.Fitting.services.requests import FitRequest
from sas.qtgui.Perspectives.Fitting.services.theory import TheoryService, resolution_of


def data_id(data, index: int) -> str:
    """The id of a dataset, or a positional one for data without an id (as in some tests)."""
    return str(data.id) if getattr(data, "id", None) else f"#{index}"


def data_ref(data, index: int = 0, synthetic: bool = False) -> DataRef:
    return DataRef(data_id(data, index), str(data.name), data, synthetic=synthetic,
                   resolution=None if synthetic else resolution_of(data))


class FitPageController:

    def __init__(self, page) -> None:
        self._page = page
        self.document = page.document
        self._anchor = None          # the last state with a model: what a layout change retains from
        self._views: list = []       # the view syncs (subscribe_view), for resync
        self._applying = 0           # a view sync is running
        self._last_request = 0
        self.inputs_revision = 0     # the revision of the last change that was not DERIVED
        self.jobs = JobState()
        self.results = Results()
        self.document.subscribe(self._track_inputs)

    @property
    def history(self):
        return self._page.undo_stack

    @property
    def muted(self) -> bool:
        """A view is writing its widgets from the document: the edits they fire are not the user's."""
        return self._applying > 0

    def subscribe_view(self, fn):
        """Subscribe a document-to-view sync *fn(change)*."""
        def subscriber(change) -> None:
            self._applying += 1
            try:
                fn(change)
            finally:
                self._applying -= 1
        self._views.append(subscriber)
        return self.document.subscribe(subscriber)

    def resync(self, keys: set[str]) -> None:
        """Show the parameters *keys* again (after a rejected edit)."""
        change = ChangeSet(Origin.SYSTEM, self.document.revision,
                           (ParametersChanged(frozenset(keys), PARAMETER_FIELDS),))
        for view in self._views:
            view(change)

    def _track_inputs(self, change) -> None:
        if change.origin is not Origin.DERIVED:
            self.inputs_revision = change.revision

    def _status(self, message: str) -> None:
        self._page.communicator.statusBarUpdateSignal.emit(message)

    # -- for the commands -------------------------------------------------

    @contextlib.contextmanager
    def transaction(self, origin: Origin, recalculate: bool | str = False):
        """A document transaction; after an undo or redo of a value-bearing change, theory (R-1).
        *recalculate* "grid" also renews the theory grid (an options change)."""
        with self.document.transaction(origin) as tx:
            yield tx
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
        if self.muted:
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
            self.resync({key})

    def set_fit_flag(self, key: str, fit: bool) -> None:
        """Not undoable (MD/UNDO_PLAN_CLAUDE.md)."""
        if self.muted or self.document.parameters[key].fit == fit:
            return
        with self.transaction(Origin.USER) as tx:
            tx.set_parameter(key, fit=fit)

    def set_constraint(self, key: str, constraint, **fields) -> None:
        """Add, change or remove (None) a constraint, with the fields it implies. Not undoable."""
        if self.muted:
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
        Not undoable, as before (``FitPerspectiveCoordinator.rename`` checks the name)."""
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

    def deactivate_dangling(self, mnemonic: str, symbols: dict[str, float]) -> list[str]:
        """Deactivate the active constraints that refer to page *mnemonic* and no longer evaluate
        with *symbols* (a parameter of that page went away, or the page closed). Returns their names."""
        doc = self.document
        prefix = doc.identity.mnemonic
        def dangles(p) -> bool:
            name = f"{prefix}.{p.key}"
            return bool(constraint_service.validate({**symbols, name: 0.0}, [(name, p.constraint.func)]))
        dangling = [p for p in doc.constrained() if p.constraint.active and p.constraint.func
                    and f"{mnemonic}." in p.constraint.func and dangles(p)]
        if dangling:
            with self.transaction(Origin.SYSTEM) as tx:
                for p in dangling:
                    constraint = copy.deepcopy(p.constraint)
                    constraint.active = False
                    tx.set_constraint(p.key, constraint)
        return [f"{prefix}.{doc.parameters.legacy_key(p.key)}" for p in dangling]

    # -- page settings --------------------------------------------------------

    def set_options(self, options) -> None:
        """Fit options; theory follows every options update, as before."""
        if self.muted:
            return
        self._execute_if_changed(SetOptionsCommand, self.document.options, options)
        self.request_theory(grid=True)

    def set_q_min(self, value) -> None:
        """The low-Q slider of a theory plot (to three digits, as the options tab shows it)."""
        self.set_options(dataclasses.replace(self.document.options, qmin=float(f"{float(value):.3}")))

    def set_q_max(self, value) -> None:
        """The high-Q slider of a theory plot."""
        self.set_options(dataclasses.replace(self.document.options, qmax=float(f"{float(value):.3}")))

    def set_smearing(self, smearing) -> None:
        if self.muted:
            return
        self._execute_if_changed(SetSmearingCommand, self.document.smearing, smearing)
        self.request_theory()

    def set_flag(self, name: str, value: bool) -> None:
        """Polydispersity, magnetism or chain fit; the views apply the side effects."""
        if self.muted:
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

    # -- data ---------------------------------------------------------------------

    def set_datasets(self, datasets: list, batch: bool, smearing) -> None:
        """A data load: the datasets (the first is active), the Q range and weighting of the active
        one, and the smearing the tab offers for it. Clears the history and the page's jobs."""
        doc = self.document
        refs = [data_ref(data, i) for i, data in enumerate(datasets)]
        self.history.clear()
        self.jobs.cancel()
        self.results = Results()
        with self.transaction(Origin.LOAD) as tx:
            mode = PageMode.BATCH if batch else PageMode.SINGLE
            if mode is not doc.mode:
                tx.set_mode(mode)
            tx.set_datasets(refs)
            tx.set_options(self._data_options(refs[0].data))
            if smearing != doc.smearing:
                tx.set_smearing(smearing)

    def _data_options(self, data, weighting: int | None = None):
        """The options with the Q range of *data*; the weighting is by dI if the data has errors."""
        qmin, qmax, npts = plots.data_range(data)
        if weighting is None:
            weighting = 1 if plots.has_errors(data) else 0
        return dataclasses.replace(self.document.options, qmin=float(qmin), qmax=float(qmax), npts=int(npts),
                                   theory_weighting=weighting, fit_weighting=weighting)

    def set_active_dataset(self, dataset_id: str) -> None:
        """Another dataset of a batch page is shown: its Q range, and its theory. Clears the history."""
        doc = self.document
        if dataset_id == doc.active_id:
            return
        self.history.clear()
        with self.transaction(Origin.LOAD) as tx:
            tx.set_active_dataset(dataset_id)
            tx.set_options(self._data_options(doc.datasets[dataset_id].data, doc.options.fit_weighting))
        self.request_theory(grid=True)

    def data_masked(self) -> None:
        """A mask was applied: the active dataset is new (its revision), the Q range follows it."""
        doc = self.document
        if doc.is_loaded():
            ref = doc.datasets[doc.active_id]
            with self.transaction(Origin.LOAD) as tx:
                tx.set_datasets([dataclasses.replace(r, revision=r.revision + 1) if r is ref else r
                                 for r in (doc.datasets[i] for i in doc.dataset_order)], ref.id)
                tx.set_options(self._data_options(ref.data, doc.options.fit_weighting))
        self._page.updateData()

    def ensure_default_dataset(self) -> None:
        """The theory grid of a page without data, for the current options and view."""
        def write() -> None:
            doc = self.document
            if doc.is_loaded():
                return
            data = plots.default_dataset(doc.options, doc.is2D(), doc.identity.tab_id)
            with self.transaction(Origin.DERIVED) as tx:
                tx.set_datasets([data_ref(data, synthetic=True)])
        self.document.after_publish(write)

    def set_chain_order(self, ids: list[str]) -> None:
        """The order of the datasets in a chain fit (the order tab)."""
        if ids != self.document.chain_order:
            with self.transaction(Origin.USER) as tx:
                tx.set_chain_order(ids)

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

    def relayout(self) -> bool:
        """The data changed (a load clears the history): the layout follows is2D."""
        return self._change_layout(None, self.document.selection)

    def _change_layout(self, description: str | None, selection: ModelSelection,
                       view_2d: bool | None = None) -> bool:
        """The layout of *selection*, with the user's settings carried over from the last state that
        had a model (so that a category switch, which empties the table, still retains them).
        Recorded as one undoable step if *description* is given."""
        if self.muted:
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

    # -- theory (§3.3) ------------------------------------------------------------

    def prepare_theory(self, dataset_id: str | None = None, kernel=None):
        """The request for *dataset_id* (the active one by default), with a new engine instance
        holding the document's effective state unless *kernel* is given."""
        doc = self.document
        ref = doc.datasets[dataset_id or doc.active_id]
        self._last_request += 1
        provenance = Provenance(self._last_request, self.inputs_revision, doc.parameters.layout_generation,
                                ref.id, ref.revision)
        return TheoryService.prepare(doc, provenance, kernel or self._page.kernel_builder.build(doc))

    def compute_theory(self, dataset_id: str | None = None, kernel=None, use_threads: bool = True) -> None:
        """Theory for a dataset; a newer request for it supersedes this one."""
        doc = self.document
        if not len(doc.parameters) or (dataset_id or doc.active_id) is None:
            return
        request = self.prepare_theory(dataset_id, kernel)
        self.jobs.theory[request.dataset_id] = request.request_id
        self._page.disableInteractiveElementsOnCalculate()
        self._page.theory_service.run(request, self.theory_done, use_threads)

    def theory_done(self, request, return_data) -> None:
        """A theory calculation completed (on the GUI thread)."""
        doc = self.document
        if self.jobs.theory.get(request.dataset_id) != request.request_id:
            return                      # superseded, or cancelled
        del self.jobs.theory[request.dataset_id]
        if not self.jobs.theory and self.jobs.fit is None:
            self._page.enableInteractiveElements()
        if (return_data is None or request.provenance.layout_generation != doc.parameters.layout_generation
                or request.dataset_id not in doc.datasets):
            return                      # failed, or computed for a layout or dataset the page no longer has
        result = TheoryService.outcome(doc, request, return_data)
        self.results.per_dataset[request.dataset_id] = result
        self._page.showTheory(result)
        if result.radius_effective is not None and self.current_result(request.dataset_id) is result:
            self._set_radius_effective(float(result.radius_effective))

    def current_result(self, dataset_id: str | None = None):
        """The theory result of a dataset (the active one by default), if computed from the current inputs."""
        return self.results.current(dataset_id or self.document.active_id, self.inputs_revision)

    def _set_radius_effective(self, value: float) -> None:
        """The effective radius sasmodels computed (radius_effective_mode > 0): a derived value,
        never recorded and never recalculating."""
        params = self.document.parameters
        if ("radius_effective" not in params or "radius_effective_mode" not in params
                or int(params["radius_effective_mode"].value) < 1 or params["radius_effective"].value == value):
            return
        def write() -> None:
            with self.transaction(Origin.DERIVED) as tx:
                tx.set_parameter("radius_effective", value=value)
        self.document.after_publish(write)

    # -- fitting (§3.4) ------------------------------------------------------------

    def prepare_fitters(self, fitter=None, fit_id: int = 0, weight_increase: int = 1):
        """The Fit objects of the page; *fitter* is the simultaneous fit's shared one (the
        constraint tab). A single fit asks about constraints on other pages (ValueError if cancelled)."""
        page = self._page
        if fitter is None:
            constraints = page.getConstraintsForFitting()
        else:
            constraints = constraint_service.complex_constraints(self.document)
        return page.fit_service.prepare(self.document, constraints, fitter, fit_id, weight_increase, page.page_id)

    def start_fit(self) -> FitRequest:
        """A fit of the page, prepared from the document now. ValueError if it cannot run."""
        fitters, _ = self.prepare_fitters()
        self._last_request += 1
        request = FitRequest(self._last_request, self.document.parameters.layout_generation,
                             self.document.mode is PageMode.BATCH, tuple(fitters))
        self.jobs.fit = request.request_id
        return request

    def fit_done(self, request: FitRequest | None) -> bool | None:
        """A fit completed: True if its outcome may be applied, False if it is discarded (the page
        no longer has the layout it was fitted for), None if it is dropped (a cancelled or superseded
        fit: the page shows nothing). *request* None: a fit the coordinator routed here."""
        if request is None:
            return True
        if self.jobs.fit != request.request_id:
            return None
        self.jobs.fit = None
        if request.layout_generation != self.document.parameters.layout_generation:
            self._status("The fit result was discarded: the model changed while fitting.")
            return False
        return True

    def fit_failed(self) -> None:
        self.jobs.fit = None

    def outcome(self, result) -> dict | None:
        """{parameter: (value, error)} of a fit result; None (and a message) if it did not converge."""
        param_dict = self._page.fit_service.outcome(result)
        if param_dict is None:
            self._status("Fitting did not converge!")
        return param_dict

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

    def apply_batch_fit(self, results: list) -> None:
        """A batch fit: not applied to the page and not recorded. Each dataset's theory is computed
        with its fitted values, and routed by its id (§9.2 B-4)."""
        doc = self.document
        self.results.batch = results
        order = doc.chain_order if doc.flags.chain_fit else doc.dataset_order
        for dataset_id, res_list in zip(order, results):
            param_dict = self.outcome(res_list[0])
            if param_dict is None:
                continue
            kernel = FittingUtilities.updateKernelWithResults(self._page.kernel_builder.build(doc), param_dict)
            self.compute_theory(dataset_id, kernel, use_threads=False)

    def close(self) -> None:
        """The page closes: every request is cancelled, so late completions are dropped."""
        self.jobs.cancel()

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
