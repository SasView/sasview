"""
Parameter retention across layout changes (FW-MVC-DESIGN.md §2.6).

Model switch, S(Q) switch, multiplicity change or is2D change: the new
layout comes from ``KernelBuilder.layout``, and the user's settings are
carried over from the old parameter set by key.
"""
from __future__ import annotations

import copy
import re

from sas.qtgui.Perspectives.Fitting.model.parameters import Parameter, ParameterSet, ValueKind

# A constraint symbol: <mnemonic>.<parameter>, e.g. "M1.radius" or "M2.radius.width"
_SYMBOL = re.compile(r"\b([A-Za-z_]\w*)\.([A-Za-z_]\w*(?:\.width)?)\b")


def _value_fits(old: Parameter, new: Parameter) -> bool:
    if old.kind is not new.kind:
        return False
    if new.kind is ValueKind.CHOICE:
        return isinstance(old.value, int) and 0 <= old.value < len(new.choices or ())
    return True


def constraint_symbols(expression: str) -> set[str]:
    """The ``mnemonic.parameter`` symbols an expression refers to."""
    return {f"{m}.{p}" for m, p in _SYMBOL.findall(expression or "")}


def retain(old: ParameterSet, new: ParameterSet, symbols: set[str] | None = None) -> tuple[ParameterSet, list[str]]:
    """Carry the user's settings from *old* into the fresh layout *new* (which is modified and returned).

    Kept, by key: value (if the kind matches and a choice index is in range),
    min, max, fit and dispersion. Errors are cleared. Labels, sections, units,
    choices, editability and fittability come from the new layout. A
    constraint is kept only if every symbol it refers to is in *symbols*
    (the symbol set after the change; None keeps every constraint).

    Returns the new set and the keys whose constraints were dropped.
    """
    dropped = []
    for p in new:
        if p.key not in old:
            continue
        previous = old[p.key]
        if _value_fits(previous, p):
            p.value = previous.value
        if p.min is not None and previous.min is not None:
            p.min = previous.min
        if p.max is not None and previous.max is not None:
            p.max = previous.max
        p.fit = previous.fit
        if previous.dispersion is not None and p.dispersion is not None:
            p.dispersion = copy.deepcopy(previous.dispersion)
        p.error = None
        constraint = previous.constraint
        if constraint is not None:
            if symbols is None or constraint_symbols(constraint.func) <= symbols:
                p.constraint = copy.deepcopy(constraint)
            else:
                dropped.append(p.key)
    return new, dropped
