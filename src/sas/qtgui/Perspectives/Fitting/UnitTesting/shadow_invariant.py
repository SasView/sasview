"""
The shadow invariant (FW-MVC-DESIGN.md §6, Phases 2 and 3), test-only.

``check_shadow(page)`` asserts that ``page.document`` agrees with the legacy stores:

- rows: the serializer's legacy rows equal the legacy ``getFitPage() + getFitModel()``;
- projection: the document, as the Phase 4 adapters will show it, equals the
  three live item models (row order, text, check state, checkability,
  editability, error column);
- kernel: the document's effective engine inputs equal the legacy kernel's
  (``updateKernelModelWithExtraParams`` applied to a copy, as theory does);
- readers: every reader that answers from the document (``@reads``) gives the
  legacy reader's answer, and so does ``prepareFitters``' choice of parameters.

The legacy answers are read inside ``page.shadow.operation()``, where the
``@reads`` readers fall back to the legacy stores.

``ShadowChecker`` runs the check on every committed ChangeSet of a page and
collects failures, so that a failure inside a Qt slot is not lost; tests
call ``assert_ok()`` at teardown.
"""
from __future__ import annotations

import copy
import math

from PySide6 import QtCore, QtWidgets

from sas.qtgui.Perspectives.Fitting.FittingUtilities import header_error_caption
from sas.qtgui.Perspectives.Fitting.model import serializer
from sas.qtgui.Perspectives.Fitting.model.parameters import RowKind, Table, ValueKind
from sas.qtgui.Perspectives.Fitting.UnitTesting.document_fixtures import jsonable, same


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


def _register_r11(page) -> bool:
    """Register R-11: the legacy readers see parameters when the current FittingLogic has a kernel,
    the document when it has parameters. They disagree with a category but no model chosen (stale
    kernel) and on a batch page showing a dataset other than the first (no kernel)."""
    return (page.logic.kernel_module is None) != (not len(page.document.parameters))


def check_rows(page) -> None:
    with page.shadow.operation():
        legacy = jsonable(page.getFitPage() + page.getFitModel())
    rows = jsonable(serializer.legacy_rows(page.document))
    if _register_r11(page):
        # Only the page rows are compared
        legacy, rows = (r[next(i for i, row in enumerate(r) if row[0] == "is_data"):] for r in (legacy, rows))
    same(rows, legacy, "rows")


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
        _expect((name.checkState() == QtCore.Qt.Checked) == p.fit, f"{where}: check state, fit {p.fit}")
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


def check_kernel(page) -> None:
    """The document's effective engine state equals the legacy kernel's, as theory sees it."""
    kernel = page.logic.kernel_module
    doc = page.document
    if kernel is None or not len(doc.parameters):
        return
    effective = copy.deepcopy(kernel)
    page.updateKernelModelWithExtraParams(effective)
    _expect(effective.name == doc.identity.mnemonic, f"kernel name {effective.name!r}, mnemonic "
                                                     f"{doc.identity.mnemonic!r}")
    for p in doc.parameters.by_table(Table.MAIN):
        if p.kind is ValueKind.INT:
            continue
        where = f"kernel {p.key}"
        _expect(_close(float(effective.getParam(p.key)), float(p.value)),
                f"{where}: {effective.getParam(p.key)} != {p.value}")
        if p.min is not None and p.kind is ValueKind.FLOAT:
            _, low, high = effective.details[p.key]
            _expect(_close(float(low), p.min) and _close(float(high), p.max), f"{where}: bounds {low}, {high}")
    poly_on = doc.flags.polydispersity
    for p in doc.parameters.by_table(Table.POLY):
        name = p.key[:-len(".width")]
        _expect(_close(float(effective.getParam(p.key)), float(p.value) if poly_on else 0.0), f"kernel {p.key}")
        if p.dispersion.type != "array":
            _expect(_close(float(effective.getParam(name + ".npts")), p.dispersion.npts), f"kernel {name}.npts")
            _expect(_close(float(effective.getParam(name + ".nsigmas")), p.dispersion.nsigmas),
                    f"kernel {name}.nsigmas")
        _expect(effective.dispersion[name]["type"] == p.dispersion.type, f"kernel {name} type")
    magnet_on = doc.flags.magnetism
    for p in doc.parameters.by_table(Table.MAGNET):
        _expect(_close(float(effective.getParam(p.key)), float(p.value) if magnet_on else 0.0), f"kernel {p.key}")


READERS = ["haveParamsToFit", "getConstraintsForAllModels", "getComplexConstraintsForAllModels",
           "_report_parameters"]
KERNEL_READERS = ["canHaveMagnetism", "getSymbolDict"]          # R-11: the legacy ones need a kernel
MODEL_READERS = ["getComplexConstraintsForModel", "getFullConstraintNameListForModel"]


def check_readers(page) -> None:
    readers = READERS + ([] if _register_r11(page) else KERNEL_READERS)
    calls = [(name, ()) for name in readers]
    calls += [(name, (key,)) for name in MODEL_READERS for key in ("standard", "poly", "magnet")]
    with page.shadow.operation():
        legacy = [getattr(page, name)(*args) for name, args in calls]
        legacy_fit = page.fitting_controller.legacy_fit_inputs()
    for (name, args), expected in zip(calls, legacy):
        same(jsonable(getattr(type(page), name).from_document(page, *args)), jsonable(expected), f"{name}{args}")
    if page.data_is_loaded:
        same(list(page.fitting_controller.document_fit_inputs()), list(legacy_fit), "prepareFitters inputs")


def check_shadow(page) -> None:
    check_rows(page)
    check_projection(page)
    check_kernel(page)
    check_readers(page)


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
        assert not self.page.shadow.errors, self.page.shadow.errors[0]
        assert not self.failures, self.failures[0]
        check_shadow(self.page)
