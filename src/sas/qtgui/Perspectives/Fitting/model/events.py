"""
Transaction origins and change events of the fit page document (FW-MVC-DESIGN.md §2.2).

One ``ChangeSet`` is published after each committed transaction. Events of
the same type within one transaction are merged.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# Every field of a Parameter that a ParametersChanged event can name.
PARAMETER_FIELDS = frozenset({"value", "min", "max", "fit", "fittable", "editable", "error", "dispersion"})


class Origin(Enum):
    USER = "user"
    UNDO = "undo"
    REDO = "redo"
    DERIVED = "derived"    # e.g. a computed effective radius; never triggers theory, never recorded
    LOAD = "load"
    JOB = "job"            # a background job's outcome
    SYSTEM = "system"      # cross-page changes made by the perspective coordinator


class ReentrancyError(RuntimeError):
    """A document was mutated from inside one of its own change subscribers (a programming error)."""


@dataclass(frozen=True)
class ModelChanged:
    """Selection, multiplicity, is2D or the parameter layout changed."""
    layout_generation: int


@dataclass(frozen=True)
class ParametersChanged:
    keys: frozenset[str]
    fields: frozenset[str]


@dataclass(frozen=True)
class ConstraintsChanged:
    keys: frozenset[str]


@dataclass(frozen=True)
class OptionsChanged:
    pass


@dataclass(frozen=True)
class SmearingChanged:
    pass


@dataclass(frozen=True)
class FlagsChanged:
    pass


@dataclass(frozen=True)
class DataChanged:
    ids: frozenset[str]


@dataclass(frozen=True)
class IdentityChanged:
    pass


Event = (ModelChanged | ParametersChanged | ConstraintsChanged | OptionsChanged
         | SmearingChanged | FlagsChanged | DataChanged | IdentityChanged)


@dataclass(frozen=True)
class ChangeSet:
    origin: Origin
    revision: int
    events: tuple[Event, ...]

    def get(self, event_type: type) -> Event | None:
        """The (merged) event of *event_type*, if the transaction produced one."""
        return next((e for e in self.events if isinstance(e, event_type)), None)


def merge_events(events: list[Event]) -> tuple[Event, ...]:
    """Merge events of the same type, keeping first-seen order. Key and field sets are united."""
    merged: dict[type, Event] = {}
    for event in events:
        previous = merged.get(type(event))
        if previous is None:
            merged[type(event)] = event
        elif isinstance(event, ParametersChanged):
            merged[ParametersChanged] = ParametersChanged(previous.keys | event.keys, previous.fields | event.fields)
        elif isinstance(event, ConstraintsChanged):
            merged[ConstraintsChanged] = ConstraintsChanged(previous.keys | event.keys)
        elif isinstance(event, DataChanged):
            merged[DataChanged] = DataChanged(previous.ids | event.ids)
        elif isinstance(event, ModelChanged):
            merged[ModelChanged] = event   # the latest layout generation wins
    return tuple(merged.values())
