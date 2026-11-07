"""
The fit page document: the single, Qt-free owner of a fit page's state (FW-MVC-DESIGN.md §2).

All mutation goes through ``with doc.transaction(origin) as tx:``. A
transaction validates its inputs, applies them, runs the derived rules,
commits (``revision += 1``) and then publishes one ``ChangeSet`` to the
subscribers. If anything raises before the commit, the document is left
exactly as it was.
"""
from __future__ import annotations

import contextlib
import copy
import logging
import math
import threading
from collections.abc import Callable, Iterator

from sas.qtgui.Perspectives.Fitting.model import rules
from sas.qtgui.Perspectives.Fitting.model.events import (
    PARAMETER_FIELDS,
    ChangeSet,
    ConstraintsChanged,
    DataChanged,
    Event,
    FlagsChanged,
    IdentityChanged,
    ModelChanged,
    OptionsChanged,
    Origin,
    ParametersChanged,
    ReentrancyError,
    SmearingChanged,
    merge_events,
)
from sas.qtgui.Perspectives.Fitting.model.parameters import (
    Constraint,
    DataRef,
    FitOptions,
    Flags,
    ModelSelection,
    PageIdentity,
    PageMode,
    ParameterSet,
    Smearing,
    Table,
    ValueKind,
)
from sas.qtgui.Perspectives.Fitting.model.snapshot import PageSnapshot

logger = logging.getLogger(__name__)

Subscriber = Callable[[ChangeSet], None]


class Subscription:
    """Handle returned by ``FitPageDocument.subscribe``; ``dispose()`` unsubscribes."""

    def __init__(self, doc: FitPageDocument, fn: Subscriber) -> None:
        self._doc = doc
        self.fn = fn

    def dispose(self) -> None:
        if self in self._doc._subscriptions:
            self._doc._subscriptions.remove(self)


class Transaction:
    """The mutations allowed inside ``FitPageDocument.transaction``. Each method validates first."""

    def __init__(self, doc: FitPageDocument, origin: Origin) -> None:
        self._doc = doc
        self.origin = origin
        self.events: list[Event] = []

    # -- parameters -----------------------------------------------------

    def set_parameter(self, key: str, **fields) -> None:
        """Set fields (value, min, max, fit, error, dispersion, fittable, editable) of parameter *key*."""
        params = self._doc.parameters
        if key not in params:
            raise KeyError(f"no parameter {key!r}")
        unknown = set(fields) - PARAMETER_FIELDS
        if unknown:
            raise ValueError(f"unknown parameter fields {sorted(unknown)}")
        p = params[key]
        if "value" in fields:
            fields["value"] = _checked_value(p, fields["value"])
        for bound in ("min", "max"):
            if fields.get(bound) is not None:
                fields[bound] = _checked_number(f"{key}.{bound}", fields[bound])
        low = fields.get("min", p.min)
        high = fields.get("max", p.max)
        if low is not None and high is not None and low > high:
            raise ValueError(f"{key}: min {low} is greater than max {high}")
        for name, value in fields.items():
            setattr(p, name, value)
        self.events.append(ParametersChanged(frozenset({key}), frozenset(fields)))

    def set_constraint(self, key: str, constraint: Constraint | None) -> None:
        params = self._doc.parameters
        if key not in params:
            raise KeyError(f"no parameter {key!r}")
        params[key].constraint = constraint
        self.events.append(ConstraintsChanged(frozenset({key})))

    def set_parameters(self, parameters: ParameterSet) -> None:
        """Replace the whole parameter set (a new layout, or a restored one)."""
        doc = self._doc
        layout_changed = not parameters.same_layout(doc.parameters)
        generation = doc.parameters.layout_generation + (1 if layout_changed else 0)
        doc.parameters = parameters
        parameters.layout_generation = generation
        if layout_changed:
            self.events.append(ModelChanged(generation))
        self.events.append(ParametersChanged(frozenset(parameters.keys()), PARAMETER_FIELDS))
        self.events.append(ConstraintsChanged(frozenset(parameters.keys())))

    # -- page settings --------------------------------------------------

    def set_selection(self, selection: ModelSelection) -> None:
        if selection != self._doc.selection:
            self._doc.selection = selection
            self.events.append(ModelChanged(self._doc.parameters.layout_generation))

    def set_options(self, options: FitOptions) -> None:
        if not options.qmin < options.qmax:
            raise ValueError(f"Q range: qmin {options.qmin} must be less than qmax {options.qmax}")
        if options.npts < 1:
            raise ValueError(f"npts must be positive, not {options.npts}")
        self._doc.options = copy.copy(options)
        self.events.append(OptionsChanged())

    def set_smearing(self, smearing: Smearing) -> None:
        self._doc.smearing = copy.copy(smearing)
        self.events.append(SmearingChanged())

    def set_flags(self, **flags: bool) -> None:
        current = self._doc.flags
        unknown = set(flags) - set(vars(current))
        if unknown:
            raise ValueError(f"unknown flags {sorted(unknown)}")
        self._doc.flags = Flags(**{**vars(current), **flags})
        self.events.append(FlagsChanged())

    def set_mnemonic(self, mnemonic: str) -> None:
        if not mnemonic:
            raise ValueError("the page name must not be empty")
        self._doc.identity.mnemonic = mnemonic
        self.events.append(IdentityChanged())

    # -- data -----------------------------------------------------------

    def set_mode(self, mode: PageMode) -> None:
        """Single or batch page: decided when the page receives its data."""
        self._doc.mode = mode
        self.events.append(DataChanged(frozenset(self._doc.datasets)))

    def set_datasets(self, datasets: list[DataRef], active_id: str | None = None) -> None:
        ids = [d.id for d in datasets]
        if len(set(ids)) != len(ids):
            raise ValueError(f"dataset ids must be unique: {ids}")
        if active_id is None and ids:
            active_id = ids[0]
        if active_id is not None and active_id not in ids:
            raise KeyError(f"no dataset {active_id!r}")
        doc = self._doc
        old_ids = set(doc.datasets)
        doc.datasets = {d.id: d for d in datasets}
        doc.dataset_order = ids
        doc.chain_order = list(ids)
        doc.active_id = active_id
        self.events.append(DataChanged(frozenset(old_ids | set(ids))))

    def set_active_dataset(self, dataset_id: str) -> None:
        if dataset_id not in self._doc.datasets:
            raise KeyError(f"no dataset {dataset_id!r}")
        self._doc.active_id = dataset_id
        self.events.append(DataChanged(frozenset({dataset_id})))

    def set_chain_order(self, ids: list[str]) -> None:
        if sorted(ids) != sorted(self._doc.dataset_order):
            raise ValueError("the chain order must be a permutation of the datasets")
        self._doc.chain_order = list(ids)
        self.events.append(DataChanged(frozenset(ids)))

    # -- snapshots ------------------------------------------------------

    def restore(self, snapshot: PageSnapshot) -> None:
        """Whole-value replacement of the undoable state (``restore_undo_state``)."""
        doc = self._doc
        self.set_parameters(snapshot.parameters.copy())
        self.set_selection(snapshot.selection)
        if snapshot.options != doc.options:
            self.set_options(snapshot.options)
        if snapshot.smearing != doc.smearing:
            self.set_smearing(snapshot.smearing)
        if snapshot.flags != doc.flags:
            self.set_flags(**vars(snapshot.flags))
        if snapshot.mnemonic != doc.identity.mnemonic:
            self.set_mnemonic(snapshot.mnemonic)


def _checked_number(name: str, value) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name}: {value!r} is not a number") from None
    if math.isnan(number):
        raise ValueError(f"{name}: NaN is not allowed")
    return number


def _checked_value(p, value) -> float | int:
    if p.kind is ValueKind.CHOICE:
        if not isinstance(value, int) or not 0 <= value < len(p.choices or ()):
            raise ValueError(f"{p.key}: {value!r} is not a choice index")
        return value
    number = _checked_number(p.key, value)
    if p.kind is ValueKind.INT:
        if not number.is_integer():
            raise ValueError(f"{p.key}: {value!r} is not an integer")
        return int(number)
    return number


class FitPageDocument:
    """State of one fit page. Mutate only through ``transaction``; read freely."""

    def __init__(self, identity: PageIdentity, mode: PageMode = PageMode.SINGLE, *,
                 strict: bool = False) -> None:
        self.identity = identity
        self.mode = mode
        self.datasets: dict[str, DataRef] = {}
        self.dataset_order: list[str] = []
        self.active_id: str | None = None
        self.chain_order: list[str] = []
        self.selection = ModelSelection()
        self.parameters = ParameterSet()
        self.options = FitOptions()
        self.smearing = Smearing()
        self.flags = Flags()
        self.revision = 0
        self.strict = strict              # re-raise subscriber errors (tests)
        self._subscriptions: list[Subscription] = []
        self._in_transaction = False
        self._publishing = False
        self._owner = threading.get_ident()

    # -- mutation -------------------------------------------------------

    @contextlib.contextmanager
    def transaction(self, origin: Origin) -> Iterator[Transaction]:
        if threading.get_ident() != self._owner:
            raise RuntimeError("FitPageDocument may only be changed on its owner (GUI) thread")
        if self._publishing:
            raise ReentrancyError("a change subscriber tried to change the document")
        if self._in_transaction:
            raise ReentrancyError("transactions do not nest")
        saved = self._state()
        was_2d = rules.is_2d(self)
        tx = Transaction(self, origin)
        self._in_transaction = True
        try:
            yield tx
            changed = rules.apply_rules(self)
        except BaseException:
            self._restore_state(saved)
            raise
        finally:
            self._in_transaction = False
        if changed:
            tx.events.append(ParametersChanged(frozenset(changed), frozenset({"value", "fittable", "editable"})))
        if rules.is_2d(self) != was_2d:
            tx.events.append(ModelChanged(self.parameters.layout_generation))
        if tx.events:
            self.revision += 1
            self._publish(ChangeSet(origin, self.revision, merge_events(tx.events)))

    def restore_undo_state(self, snapshot: PageSnapshot, origin: Origin = Origin.UNDO) -> None:
        with self.transaction(origin) as tx:
            tx.restore(snapshot)

    def _state(self) -> tuple:
        return (self.parameters.copy(), self.selection, copy.copy(self.options), copy.copy(self.smearing),
                copy.copy(self.flags), self.identity.mnemonic, dict(self.datasets), list(self.dataset_order),
                self.active_id, list(self.chain_order), self.mode)

    def _restore_state(self, state: tuple) -> None:
        (self.parameters, self.selection, self.options, self.smearing, self.flags, self.identity.mnemonic,
         self.datasets, self.dataset_order, self.active_id, self.chain_order, self.mode) = state

    # -- subscription ---------------------------------------------------

    def subscribe(self, fn: Subscriber) -> Subscription:
        subscription = Subscription(self, fn)
        self._subscriptions.append(subscription)
        return subscription

    def dispose(self) -> None:
        """The page is closing: drop every subscription."""
        self._subscriptions.clear()

    def _publish(self, change: ChangeSet) -> None:
        self._publishing = True
        try:
            for subscription in list(self._subscriptions):
                try:
                    subscription.fn(change)
                except ReentrancyError:
                    raise
                except Exception:
                    if self.strict:
                        raise
                    logger.exception("FitPageDocument subscriber %r failed", subscription.fn)
        finally:
            self._publishing = False

    # -- queries --------------------------------------------------------

    def snapshot(self) -> PageSnapshot:
        """A detached copy of the undoable state. Emits nothing."""
        return PageSnapshot.capture(self)

    def data(self):
        """The active dataset's Data1D/Data2D, or None."""
        active = self.datasets.get(self.active_id) if self.active_id else None
        return active.data if active is not None else None

    def is_loaded(self) -> bool:
        return rules.is_loaded(self)

    def is2D(self) -> bool:
        return rules.is_2d(self)

    def can_fit(self) -> bool:
        return rules.can_fit(self)

    def can_have_magnetism(self) -> bool:
        return rules.can_have_magnetism(self)

    def symbol_table(self) -> dict[str, float]:
        """{f"{mnemonic}.{name}": value} for constraints: fittable main rows, plus poly widths when active."""
        prefix = self.identity.mnemonic
        symbols = {f"{prefix}.{p.label}": float(p.value)
                   for p in self.parameters.by_table(Table.MAIN) if p.fittable}
        if self.flags.polydispersity:
            symbols.update({f"{prefix}.{p.key}": float(p.value) for p in self.parameters.by_table(Table.POLY)})
        return symbols
