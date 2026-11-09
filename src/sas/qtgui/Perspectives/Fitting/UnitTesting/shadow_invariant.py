"""
The page invariant (FW-MVC-DESIGN.md §6, Phases 2 to 7), test-only.

``check_shadow(page)`` asserts that the views show ``page.document``: the three item models
(row order, text, check state, checkability, editability, error column), as the table
adapters build and patch them.

(Until Phase 5 it also compared the legacy rows and readers with the document, and until
Phase 6 the live kernel; since Phase 7 there is no live kernel: every job builds its own.)

``ShadowChecker`` runs the check on every committed ChangeSet of a page and
collects failures, so that a failure inside a Qt slot is not lost; tests
call ``assert_ok()`` at teardown.
"""
from __future__ import annotations

import math

from PySide6 import QtCore, QtWidgets

from sas.qtgui.Perspectives.Fitting.FittingUtilities import header_error_caption
from sas.qtgui.Perspectives.Fitting.model.parameters import RowKind, Table, ValueKind


def _number(text):
    try:
        return float(text)
    except (TypeError, ValueError):
        return text


def _close(a, b) -> bool:
    if isinstance(a, str) or isinstance(b, str) or a is None or b is None:
        return a == b
    return a == b or math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-12)


def _expect(condition: bool, message: str) -> None:
    assert condition, message


def _check_table_errors(where: str, has_column: bool, doc, header_model) -> None:
    """A table with rows shows its error column when any parameter of the page carries an error."""
    if header_model.rowCount() == 0:
        return
    has_errors = any(p.error is not None for p in doc.parameters)
    _expect(has_column == has_errors, f"{where}: error column {has_column}, document errors {has_errors}")
    if has_column:
        _expect(header_model.headerData(2, QtCore.Qt.Horizontal) == header_error_caption,
                f"{where}: error header missing")


def check_projection(page) -> None:
    doc = page.document
    params = doc.parameters

    # Main table
    table = page._model_model
    _expect(table.rowCount() == len(params.rows), f"main: {table.rowCount()} rows, layout {len(params.rows)}")
    offset = 1 if page.has_error_column else 0
    _check_table_errors("main", page.has_error_column, doc, table)
    for row, entry in enumerate(params.rows):
        name = table.item(row, 0)
        if entry.kind is RowKind.HEADING:
            _expect((name.text(), name.isCheckable()) == (entry.name, False), f"main row {row}: heading")
            continue
        p = params[entry.name]
        where = f"main {p.key}"
        _expect(name.text() == p.label, f"{where}: label {name.text()!r}")
        _expect(name.isCheckable() == p.fittable, f"{where}: checkable {name.isCheckable()}, fittable {p.fittable}")
        # A disabled row keeps the user's fit choice (§2.5), but its checkbox is gone (unchecked)
        _expect((name.checkState() == QtCore.Qt.Checked) == (p.fit and p.fittable), f"{where}: check state, fit {p.fit}")
        value = table.item(row, 1)
        if entry.kind is RowKind.PARAMETER:
            expected = p.value if p.kind is ValueKind.CHOICE else float(p.value)
            _expect(_close(_number(value.text()), expected), f"{where}: value {value.text()!r}, document {p.value}")
            if p.kind is ValueKind.FLOAT:
                locked = p.constraint is not None and p.constraint.active
                _expect(value.isEditable() == (p.editable and not locked),
                        f"{where}: editable {value.isEditable()}, document {p.editable}, constrained {locked}")
        if offset:
            error = _number(table.item(row, 2).text())
            _expect(_close(error if error != "" else None, p.error), f"{where}: error {error!r}, document {p.error}")
        if p.min is not None:
            bounds = (_number(table.item(row, 2 + offset).text()), _number(table.item(row, 3 + offset).text()))
            _expect(_close(bounds[0], p.min) and _close(bounds[1], p.max), f"{where}: bounds {bounds}")

    # Polydispersity table
    widget = page.polydispersity_widget
    table = widget.poly_model
    expected = params.by_table(Table.POLY)
    _expect(table.rowCount() == len(expected), f"poly: {table.rowCount()} rows, layout {len(expected)}")
    offset = 1 if widget.has_poly_error_column else 0
    _check_table_errors("poly", widget.has_poly_error_column, doc, table)
    for row, p in enumerate(expected):
        where = f"poly {p.key}"
        _expect(table.item(row, 0).text() == p.label, f"{where}: label")
        _expect((table.item(row, 0).checkState() == QtCore.Qt.Checked) == p.fit, f"{where}: check state")
        _expect(_close(_number(table.item(row, 1).text()), p.value), f"{where}: value")
        _expect(_close(_number(table.item(row, 4 + offset).text()), p.dispersion.npts), f"{where}: npts")
        _expect(_close(_number(table.item(row, 5 + offset).text()), p.dispersion.nsigmas), f"{where}: nsigmas")
        combo = widget.lstPoly.indexWidget(table.index(row, 6 + offset))
        if isinstance(combo, QtWidgets.QComboBox):
            _expect(combo.currentText() == p.dispersion.type, f"{where}: function {combo.currentText()!r}")

    # Magnetism table
    widget = page.magnetism_widget
    table = widget._magnet_model
    expected = params.by_table(Table.MAGNET)
    _expect(table.rowCount() == len(expected), f"magnet: {table.rowCount()} rows, layout {len(expected)}")
    _check_table_errors("magnet", widget.has_magnet_error_column, doc, table)
    for row, p in enumerate(expected):
        where = f"magnet {p.key}"
        _expect(table.item(row, 0).text() == p.label, f"{where}: label")
        _expect((table.item(row, 0).checkState() == QtCore.Qt.Checked) == p.fit, f"{where}: check state")
        _expect(_close(_number(table.item(row, 1).text()), p.value), f"{where}: value")


def check_shadow(page) -> None:
    check_projection(page)


class ShadowChecker:
    """Checks the invariant after every committed transaction of *page*'s document, and on demand."""

    def __init__(self, page) -> None:
        self.page = page
        self.failures: list[str] = []
        page.document.strict = True
        page.document.subscribe(self._on_change)

    def _on_change(self, change) -> None:
        try:
            check_shadow(self.page)
        except AssertionError as error:
            self.failures.append(f"after revision {change.revision}: {error}")

    def assert_ok(self, request=None) -> None:
        """Teardown: no failure after any commit, and the final state agrees (catches unmirrored writes).

        Skipped for tests marked ``shadow_exempt(reason)``: tests that put the page into a state the
        application cannot reach (writers mocked out, slots called with arguments no signal sends).
        """
        if request is not None and request.node.get_closest_marker("shadow_exempt"):
            return
        assert not self.failures, self.failures[0]
        check_shadow(self.page)
