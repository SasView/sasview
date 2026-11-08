"""
Document to item model, for one parameter table (FW-MVC-DESIGN.md §4.2), in patch-only mode (Phase 4).

The legacy code still builds the three tables. The adapter patches the cells of
the parameters a document-first change names: value, bounds, fit flag, error,
editability, dispersion and the constraint child item. It inserts or removes the
error column when the page gains or loses errors. A table the legacy code has not
rebuilt for the document's layout yet is left alone.

It runs through ``DocumentShadow.subscribe_reverse``, so it never sees the shadow's
own read-backs, and the legacy edit slots its writes fire are muted (the
re-entrancy guard).
"""
from __future__ import annotations

import copy

from PySide6 import QtCore, QtGui, QtWidgets

from sas.qtgui.Perspectives.Fitting import FittingUtilities
from sas.qtgui.Perspectives.Fitting.model.events import ConstraintsChanged, ParametersChanged
from sas.qtgui.Perspectives.Fitting.model.parameters import RowKind, Table, ValueKind, constraint_state
from sas.qtgui.Perspectives.Fitting.model.serializer import format_number

# Per table: the widget holding the item model, the item model, its view, the error-column flag,
# the legacy model key, and the header functions without and with the error column.
_LEGACY = {
    Table.MAIN: (lambda page: page, "_model_model", "lstParams", "has_error_column", "standard",
                 FittingUtilities.addHeadersToModel, FittingUtilities.addErrorHeadersToModel),
    Table.POLY: (lambda page: page.polydispersity_widget, "poly_model", "lstPoly", "has_poly_error_column", "poly",
                 FittingUtilities.addPolyHeadersToModel, FittingUtilities.addErrorPolyHeadersToModel),
    Table.MAGNET: (lambda page: page.magnetism_widget, "_magnet_model", "lstMagnetic", "has_magnet_error_column",
                   "magnet", FittingUtilities.addHeadersToModel, FittingUtilities.addErrorHeadersToModel),
}

# The constraint hint of ConstraintManager.addConstraintToRow
_CONSTRAINED_FONT = QtGui.QFont()
_CONSTRAINED_FONT.setItalic(True)


def _number(text: str) -> float | None:
    try:
        return float(text)
    except ValueError:
        return None


class ParameterTableAdapter:

    def __init__(self, page, table: Table) -> None:
        self._page = page
        self.table = table
        owner, model, view, self._flag, self.model_key, self._headers, self._error_headers = _LEGACY[table]
        self._owner = lambda: owner(page)
        self._model_name, self._view_name = model, view
        self.subscription = page.shadow.subscribe_reverse(self._on_change)

    # -- the legacy table -----------------------------------------------

    @property
    def item_model(self) -> QtGui.QStandardItemModel:
        return getattr(self._owner(), self._model_name)

    @property
    def view(self) -> QtWidgets.QTreeView:
        return getattr(self._owner(), self._view_name)

    @property
    def has_error_column(self) -> bool:
        return getattr(self._owner(), self._flag)

    def rows(self) -> dict[str, int] | None:
        """{key: row} of the parameters this table shows, or None if the table does not hold the layout."""
        params = self._page.document.parameters
        if self.table is Table.MAIN:
            rows = {r.name: i for i, r in enumerate(params.rows) if r.kind is not RowKind.HEADING}
            count = len(params.rows)
        else:
            rows = {p.key: i for i, p in enumerate(params.by_table(self.table))}
            count = len(rows)
        model = self.item_model
        if model.rowCount() != count or any(model.item(row, 0).text() != params[key].label
                                            for key, row in rows.items()):
            return None
        return rows

    def key_at(self, row: int) -> str | None:
        """The key of the parameter in *row*, or None (a heading, or a table being rebuilt)."""
        rows = self.rows()
        return next((key for key, r in (rows or {}).items() if r == row), None)

    # -- the error column -----------------------------------------------

    def set_error_column(self, shown: bool) -> None:
        """Insert or remove the error column (column 2), with its headers and the delegate's column table."""
        model = self.item_model
        if self.has_error_column == shown or (shown and model.rowCount() == 0):
            return
        delegate = self.view.itemDelegate()
        if shown:
            model.insertColumn(2, [QtGui.QStandardItem("") for _ in range(model.rowCount())])
            delegate.addErrorColumn()
            self._error_headers(model)
        else:
            model.removeColumn(2)
            delegate.removeErrorColumn()
            self._headers(model)
        if self.table is Table.MAIN:
            # The polydispersity sub-rows of the main table carry the column too
            for row in range(model.rowCount()):
                item = model.item(row, 0)
                sub = item.child(0) if item is not None and item.hasChildren() else None
                if sub is not None and sub.hasChildren():
                    if shown:
                        sub.insertColumn(2, [QtGui.QStandardItem("")])
                    else:
                        sub.removeColumn(2)
        setattr(self._owner(), self._flag, shown)

    # -- patching ---------------------------------------------------------

    def _on_change(self, change) -> None:
        parameters = change.get(ParametersChanged)
        constraints = change.get(ConstraintsChanged)
        if parameters is None and constraints is None:
            return
        doc = self._page.document
        if parameters is not None and "error" in parameters.fields:
            self.set_error_column(any(p.error is not None for p in doc.parameters))
        rows = self.rows()
        if rows is None:
            return
        fields = {key: set(parameters.fields) for key in parameters.keys} if parameters is not None else {}
        for key in constraints.keys if constraints is not None else ():
            fields.setdefault(key, set()).add("constraint")
        for key, names in fields.items():
            if key in rows:
                self._patch(doc.parameters[key], rows[key], names)
        if self.table is Table.POLY and parameters is not None:
            # The main table shows each width and function in a polydispersity sub-row
            self._page.iterateOverModel(self._page.updateFunctionCaption)

    def _patch(self, p, row: int, fields: set[str]) -> None:
        model = self.item_model
        offset = 1 if self.has_error_column else 0
        if "value" in fields and not (self.table is Table.MAIN and p.kind is ValueKind.INT):
            self._set_value(p, row)
        if "error" in fields and offset:
            self._set_text(model.item(row, 2), "" if p.error is None else format_number(p.error))
        if p.min is not None:
            if "min" in fields:
                self._set_number(model.item(row, 2 + offset), p.min)
            if "max" in fields:
                self._set_number(model.item(row, 3 + offset), p.max)
        if "dispersion" in fields and p.dispersion is not None:
            self._set_number(model.item(row, 4 + offset), p.dispersion.npts)
            self._set_number(model.item(row, 5 + offset), p.dispersion.nsigmas)
            combo = self.view.indexWidget(model.index(row, 6 + offset))
            if isinstance(combo, QtWidgets.QComboBox):
                combo.setCurrentIndex(combo.findText(p.dispersion.type))
            # An array distribution disables the row and names its file (onPolyComboIndexChange)
            array = p.dispersion.array
            for column in range(6 + offset):
                if model.item(row, column).isEnabled() != (array is None):
                    model.item(row, column).setEnabled(array is None)
            filename = model.item(row, 7 + offset)
            if filename is not None:
                self._set_text(filename, array.filename if array is not None else "")
        if "constraint" in fields:
            self._set_constraint(p, row)
        name = model.item(row, 0)
        if self.table is Table.MAIN and fields & {"editable", "fittable", "constraint"}:
            # Rows the derived rules enable and disable (fittable and editable together), as
            # processEffectiveRadius does; a constrained row keeps its constrained look
            locked = p.constraint is not None and p.constraint.active
            current = (name.isCheckable(), model.item(row, 1).isEditable())
            if p.fittable == p.editable and not locked and current != (p.fittable, p.editable):
                self._page.setParamEditableByRow(row, p.editable)
        if name.isCheckable() and fields & {"fit", "fittable", "editable", "constraint"}:
            state = QtCore.Qt.Checked if p.fit and p.fittable else QtCore.Qt.Unchecked
            if name.checkState() != state:
                name.setCheckState(state)

    def _set_value(self, p, row: int) -> None:
        if p.kind is ValueKind.CHOICE:
            # The fixed-choice combo writes the index into its cell (AssociatedComboBox)
            combo = self.view.indexWidget(self.item_model.index(row, 1))
            if isinstance(combo, QtWidgets.QComboBox):
                combo.setCurrentIndex(int(p.value))
                return
        self._set_number(self.item_model.item(row, 1), p.value)

    def _set_number(self, item: QtGui.QStandardItem, value) -> None:
        """Write *value* unless the cell already shows it (so typed spellings like '1.00' are kept)."""
        if _number(item.text()) != value:
            item.setText(format_number(value))

    @staticmethod
    def _set_text(item: QtGui.QStandardItem, text: str) -> None:
        if item.text() != text:
            item.setText(text)

    def _set_constraint(self, p, row: int) -> None:
        """The constraint child item of the value cell, and the row's constrained look."""
        page = self._page
        if constraint_state(page.getConstraintForRow(row, model_key=self.model_key)) == constraint_state(p.constraint):
            return
        item = self.item_model.item(row, 1)
        if item.hasChildren():
            item.removeRow(0)
        if p.constraint is not None:
            child = QtGui.QStandardItem()
            child.setData(copy.deepcopy(p.constraint))
            item.setChild(0, child)
        style = {}
        if p.constraint is not None and p.constraint.active:
            style = dict(font=_CONSTRAINED_FONT, brush=QtGui.QBrush(QtGui.QColor("blue")))
        page.modifyViewOnRow(row, model_key=self.model_key, **style)
