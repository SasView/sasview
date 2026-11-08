"""
ConstraintService (FW-MVC-DESIGN.md §3.5): Qt-free validation of constraints and the
queries over a page document that the fit page, the fitter and the constraint tab use.

The dialogs that build constraints stay in the view (``FittingWidget``, ``ConstraintWidget``)
and hand the result to the controller.
"""
from __future__ import annotations

from collections.abc import Sequence

from sas.qtgui.Perspectives.Fitting.model.parameters import Table
from sas.sascalc.fit.expression import check_constraints

# The legacy model keys of the three tables
TABLES = {"standard": Table.MAIN, "poly": Table.POLY, "magnet": Table.MAGNET}


def validate(symbols: dict[str, float], constraints: Sequence[tuple[str, str]]) -> str | list:
    """The errors of *constraints* evaluated with *symbols*, as html, or an empty list.

    Unknown symbols, syntax errors and cyclic dependencies are tagged with <b> and the
    whole is wrapped in <div class = "error"> with a style header. Duplicate definitions:
    the last one wins (dict).
    """
    errors = "<br>".join(check_constraints(symbols, dict(constraints), html=True))
    if not errors:
        return []
    header = "<style type=\"text/css\"> div.error b { font-weight: normal; color:red;}</style>"
    return header + "<div class = \"error\">" + errors + "</div>"


def active(doc) -> list[tuple[str, str]]:
    """(legacy key, expression) of the active constraints (getConstraintsForAllModels)."""
    return [(doc.parameters.legacy_key(p.key), p.constraint.func) for p in doc.constrained() if p.constraint.active]


def complex_constraints(doc, table: Table | None = None) -> list[tuple[str, str]]:
    """(key, expression) of the active constraints that have an expression."""
    return [(p.key, p.constraint.func) for p in doc.constrained(table) if p.constraint.active and p.constraint.func]


def full_names(doc, table: Table) -> list[tuple[str, str]]:
    """(legacy key, expression) of every constraint of *table*, active or not."""
    return [(doc.parameters.legacy_key(p.key), p.constraint.func) for p in doc.constrained(table)]


def is_multimodel(doc, expression: str) -> bool:
    """The expression refers to another page (it does not contain this page's mnemonic)."""
    return doc.identity.mnemonic not in expression


def key_for(doc, name: str) -> str | None:
    """The key of a parameter shown as *name* (a main label, a poly "Distribution of x", a key)."""
    params = doc.parameters
    name = name.replace("Distribution of ", "") + ".width" if name.startswith("Distribution of ") else name
    if name in params:
        return name
    return params.key_for_legacy(name)
