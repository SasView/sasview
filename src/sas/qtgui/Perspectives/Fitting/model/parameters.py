"""
Plain data types of the fit page document (FW-MVC-DESIGN.md §2.1).

Nothing here imports Qt. ``Constraint`` is the existing Qt-free class from
``Fitting/Constraint.py``.
"""
from __future__ import annotations

import copy
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import Enum
from typing import Any

from sas.qtgui.Perspectives.Fitting.Constraint import Constraint


class Table(Enum):
    """Which table shows the parameter."""
    MAIN = "main"
    POLY = "poly"
    MAGNET = "magnet"


class ValueKind(Enum):
    FLOAT = "float"
    INT = "int"
    CHOICE = "choice"      # value is the integer index, as the engine and the legacy rows use it


class RowKind(Enum):
    """Kinds of row in the main table layout."""
    HEADING = "heading"            # bold, non-interactive section title (model or S(Q) name)
    PARAMETER = "parameter"
    MULTIPLICITY = "multiplicity"  # the shell-count row with its combo box


@dataclass(frozen=True)
class Row:
    """One row of the main table: a heading text, or the key of the parameter it shows."""
    kind: RowKind
    name: str


@dataclass(frozen=True)
class ArrayDistribution:
    """A user-supplied distribution, stored so that undo never reopens a file dialog."""
    x: tuple[float, ...]
    w: tuple[float, ...]
    filename: str


@dataclass
class Dispersion:
    """Dispersion settings of a polydispersity width parameter (mirrors sasmodels ``dispersion``)."""
    npts: int
    nsigmas: float
    type: str = "gaussian"
    array: ArrayDistribution | None = None


@dataclass
class Parameter:
    key: str                    # canonical engine name, unique within the page: "radius", "radius.width"
    label: str                  # column-0 text; the legacy row key of a MAIN parameter
    table: Table
    section: str                # model name, structure-factor name, "product", "polydispersity", "magnetism"
    kind: ValueKind
    value: float | int
    min: float | None           # None where the row has no bound text (fixed-choice S(Q) rows)
    max: float | None
    units: str = ""
    fit: bool = False           # the user's choice
    fittable: bool = True       # the row has a checkbox
    editable: bool = True
    error: float | None = None
    choices: tuple[str, ...] | None = None
    dispersion: Dispersion | None = None
    constraint: Constraint | None = None


def constraint_state(constraint: Constraint | None) -> tuple | None:
    """A comparable value for a Constraint (which has identity equality)."""
    return None if constraint is None else tuple(sorted(vars(constraint).items()))


def _parameter_state(p: Parameter) -> tuple:
    return tuple(constraint_state(v) if name == "constraint" else v for name, v in vars(p).items())


@dataclass(frozen=True)
class Capabilities:
    """Immutable metadata of the selected model that the layout carries."""
    magnetic: bool = False           # the model has magnetic parameters
    structure_factor: bool = False   # the structure-factor combo is enabled for this selection


class ParameterSet:
    """Ordered, key-addressed parameters plus the layout of the main table.

    ``rows`` is the main table, top to bottom, including headings and the
    multiplicity row. The poly and magnet tables are flat lists in insertion
    order. ``layout_generation`` changes whenever the keys or their order do.
    Equality compares the layout and every parameter field by field.
    """

    def __init__(self, parameters: Iterable[Parameter] = (), rows: Iterable[Row] = (),
                 layout_generation: int = 0, capabilities: Capabilities = Capabilities()) -> None:
        self._parameters: dict[str, Parameter] = {}
        for p in parameters:
            if p.key in self._parameters:
                raise ValueError(f"duplicate parameter key {p.key!r}")
            self._parameters[p.key] = p
        self.rows: tuple[Row, ...] = tuple(rows)
        self.layout_generation = layout_generation
        self.capabilities = capabilities
        missing = [r.name for r in self.rows if r.kind is not RowKind.HEADING and r.name not in self._parameters]
        if missing:
            raise ValueError(f"layout rows without parameters: {missing}")

    def __getitem__(self, key: str) -> Parameter:
        return self._parameters[key]

    def __contains__(self, key: object) -> bool:
        return key in self._parameters

    def __iter__(self) -> Iterator[Parameter]:
        return iter(self._parameters.values())

    def __len__(self) -> int:
        return len(self._parameters)

    def keys(self) -> list[str]:
        return list(self._parameters)

    def by_table(self, table: Table) -> list[Parameter]:
        """Parameters of *table* in display order."""
        if table is Table.MAIN:
            return [self._parameters[r.name] for r in self.rows if r.kind is not RowKind.HEADING]
        return [p for p in self._parameters.values() if p.table is table]

    def by_section(self, section: str) -> list[Parameter]:
        return [p for p in self._parameters.values() if p.section == section]

    def multiplicity(self) -> Parameter | None:
        """The shell-count parameter, if the model has one."""
        return next((self._parameters[r.name] for r in self.rows if r.kind is RowKind.MULTIPLICITY), None)

    def keys_to_fit(self, *, poly_active: bool, magnet_active: bool) -> list[str]:
        """Canonical keys of the parameters selected for fitting, in table order."""
        tables = [Table.MAIN] + [Table.POLY] * poly_active + [Table.MAGNET] * magnet_active
        return [p.key for t in tables for p in self.by_table(t) if p.fit and p.fittable]

    def legacy_key(self, key: str) -> str:
        """The legacy row key: the label for MAIN parameters, the key for POLY/MAGNET."""
        p = self._parameters[key]
        return p.label if p.table is Table.MAIN else p.key

    def key_for_legacy(self, legacy_key: str) -> str | None:
        """Inverse of ``legacy_key`` (labels are unique within the main table)."""
        for p in self._parameters.values():
            if self.legacy_key(p.key) == legacy_key:
                return p.key
        return None

    def copy(self) -> ParameterSet:
        """A deep copy: values, layout, dispersions and constraints are detached."""
        return copy.deepcopy(self)

    def same_layout(self, other: ParameterSet) -> bool:
        return self.rows == other.rows and self.keys() == other.keys()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ParameterSet):
            return NotImplemented
        return (self.same_layout(other) and self.capabilities == other.capabilities
                and all(_parameter_state(a) == _parameter_state(b) for a, b in zip(self, other)))

    __hash__ = None


@dataclass(frozen=True)
class ModelSelection:
    """What the three combo boxes and the shell count select. Frozen: a valid cache key."""
    category: str = ""
    model: str = ""              # form factor, or "" when only an S(Q) is selected
    structure: str = ""          # "" when absent
    is_plugin: bool = False
    multiplicity: int | None = None


@dataclass
class PageIdentity:
    page_id: int                 # stable, assigned by the perspective
    tab_id: int                  # the default mnemonic is f"M{tab_id}"
    mnemonic: str = ""           # the constraint-symbol prefix and the kernel name

    def __post_init__(self) -> None:
        if not self.mnemonic:
            self.mnemonic = f"M{self.tab_id}"


class PageMode(Enum):
    SINGLE = "single"
    BATCH = "batch"              # a batch page may hold a single dataset


@dataclass
class DataRef:
    """A dataset on the page. The document holds no QStandardItems; everything is addressed by id."""
    id: str
    name: str                    # names may repeat
    data: Any                    # Data1D | Data2D
    synthetic: bool = False      # the theory-only grid from createDefaultDataset
    revision: int = 0            # bumped on masking / external data updates
    resolution: str | None = None  # SmearingWidget.smear_type of the data: "Pinhole", "Slit", "Hankel Transform", ...


@dataclass
class FitOptions:
    qmin: float = 0.0005
    qmax: float = 0.5
    npts: int = 150              # theory grid points
    log_points: bool = True
    theory_weighting: int = 0    # FittingWidget.weighting, persisted as 'q_weighting'
    fit_weighting: int = 0       # OptionsWidget.weighting (radio index), persisted as 'weighting'


@dataclass
class Smearing:
    """The smearing tab: the chosen option and the two values in its text boxes.

    The meaning of ``d_down``/``d_up`` depends on ``mode`` (pinhole dQ/Q in %,
    slit width/length, dQ data). The combo index persisted as
    ``line_dict['smearing']`` is computed by the codec from ``mode`` and the
    options available for the active data (rules.smearing_options).
    """
    mode: str = "None"           # "None" | "Use dQ Data" | "Custom Pinhole Smear" | "Custom Slit Smear" | "Hankel Transform"
    accuracy: str = ""
    d_down: float | None = None  # txtSmearDown, persisted as 'smearing_min'
    d_up: float | None = None    # txtSmearUp, persisted as 'smearing_max'


@dataclass
class Flags:
    polydispersity: bool = False
    magnetism: bool = False
    chain_fit: bool = False
    view_2d: bool = False        # chk2DView; meaningful only when no real data is loaded

