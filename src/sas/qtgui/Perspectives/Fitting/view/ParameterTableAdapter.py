"""
Document to item model, for one parameter table (FW-MVC-DESIGN.md §4.2, Phases 4 and 6).

- **Builds** the table from the document's layout on ``ModelChanged``: heading rows,
  parameter rows with the polydispersity sub-rows of the main table, the shell-count
  row with its combo box and the "Show SLD Profile" button, fixed-choice combo boxes,
  the distribution combo boxes of the polydispersity table, headers and the error column.
- **Patches** the cells of the parameters a change names: value, bounds, fit flag, error,
  dispersion, and the row's look (constrained, disabled, array distribution). A cell that
  already shows the value keeps its spelling.
- **Forwards** the user's edits to the controller (value, bound, npts, nsigmas, fit flag).

Document changes reach it through ``controller.subscribe_view``: the edits its own writes
fire are ignored (``controller.muted``).
"""
from __future__ import annotations

import copy
import dataclasses
import re

from PySide6 import QtCore, QtGui, QtWidgets

from sasmodels.weights import MODELS as DISTRIBUTIONS

from sas.qtgui.Perspectives.Fitting import FittingUtilities
from sas.qtgui.Perspectives.Fitting.AssociatedComboBox import AssociatedComboBox
from sas.qtgui.Perspectives.Fitting.model.events import ConstraintsChanged, ModelChanged, ParametersChanged
from sas.qtgui.Perspectives.Fitting.model.parameters import RowKind, Table, ValueKind
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

# Models with SLD parameters per shell offer the SLD profile (addExtraShells)
_SLD_SHELL = re.compile(r'^[\w]{0,3}sld.*[1-9]$')


def _number(text: str) -> float | None:
    try:
        return float(text)
    except ValueError:
        return None


def _text(value) -> str:
    return "" if value is None else format_number(value)


def _item(text: str = "", editable: bool = True) -> QtGui.QStandardItem:
    item = QtGui.QStandardItem(text)
    item.setEditable(editable)
    return item


class ParameterTableAdapter:

    def __init__(self, page, table: Table) -> None:
        self._page = page
        self.table = table
        owner, model, view, self._flag, self.model_key, self._headers, self._error_headers = _LEGACY[table]
        self._owner = lambda: owner(page)
        self._model_name, self._view_name = model, view
        self.subscription = page.controller.subscribe_view(self._on_change)
        self.item_model.dataChanged.connect(self._on_edit)

    # -- the table --------------------------------------------------------

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
        """The key of the parameter in *row*, or None (a heading)."""
        rows = self.rows()
        return next((key for key, r in (rows or {}).items() if r == row), None)

    # -- building -----------------------------------------------------------

    def build(self) -> None:
        """The whole table, from the document's layout."""
        model, params = self.item_model, self._page.document.parameters
        model.clear()
        setattr(self._owner(), self._flag, False)
        self.view.itemDelegate().removeErrorColumn()
        if self.table is Table.MAIN:
            for entry in params.rows:
                if entry.kind is RowKind.HEADING:
                    FittingUtilities.addHeadingRowToModel(model, entry.name)
                elif entry.kind is RowKind.MULTIPLICITY:
                    self._add_shell_row(params[entry.name])
                else:
                    self._add_row(params[entry.name], params)
        else:
            for p in params.by_table(self.table):
                self._add_row(p, params)
        self._headers(model)
        if any(p.error is not None for p in params):
            self.set_error_column(True)
            for key, row in (self.rows() or {}).items():
                model.item(row, 2).setText(_text(params[key].error))

    def _add_row(self, p, params) -> None:
        model = self.item_model
        name = _item(p.label, editable=False)
        name.setData(p.key, QtCore.Qt.UserRole)
        name.setCheckable(p.fittable)
        if p.kind is ValueKind.CHOICE:
            value = _item(str(int(p.value)))
        else:
            value = _item(format_number(p.value))
        items = [name, value, _item(_text(p.min)), _item(_text(p.max))]
        if self.table is Table.POLY:
            d = p.dispersion
            items += [_item(str(int(d.npts))), _item(format_number(d.nsigmas)), _item(),
                      _item(d.array.filename if d.array is not None else "")]
        else:
            items.append(_item(p.units, editable=False))
        width = f"{p.key}.width"
        if self.table is Table.MAIN and width in params:
            # The polydispersity sub-row: the width and the distribution, for display
            sub = QtGui.QStandardItem("Polydispersity")
            sub.setEditable(False)
            sub.setSelectable(False)
            cells = [QtGui.QStandardItem(t) for t in ("Distribution", self._caption(params[width]), "", "",
                                                      params[width].dispersion.type)]
            for cell in cells:
                cell.setEditable(False)
                cell.setSelectable(False)
            sub.appendRow(cells)
            name.appendRow([sub])
        if p.constraint is not None:
            child = QtGui.QStandardItem()
            child.setData(copy.deepcopy(p.constraint))
            value.setChild(0, child)
        model.appendRow(items)
        row = model.rowCount() - 1
        if p.kind is ValueKind.CHOICE:
            # The combo box writes the chosen index into the cell (AssociatedComboBox)
            combo = AssociatedComboBox(value, idx_as_value=True)
            combo.addItems(list(p.choices))
            combo.setCurrentIndex(int(p.value))
            self.view.setIndexWidget(value.index(), combo)
        if self.table is Table.POLY:
            combo = QtWidgets.QComboBox()
            combo.addItems([str(name) for name in DISTRIBUTIONS])
            combo.setCurrentIndex(combo.findText(p.dispersion.type))
            widget = self._owner()
            combo.currentIndexChanged.connect(lambda _, c=combo, r=row: widget.onPolyComboIndexChange(c.currentText(), r))
            self.view.setIndexWidget(model.index(row, 6), combo)
        self._style_row(p, row)

    def _add_shell_row(self, p) -> None:
        """The shell count: a combo box from the minimum to the maximum count, and the SLD profile button."""
        page, model = self._page, self.item_model
        items = [_item(p.label, editable=False), _item(), _item(str(int(p.min)), editable=False),
                 _item(str(int(p.max)), editable=False), _item(editable=False)]
        model.appendRow(items)
        page._n_shells_row = model.rowCount() - 1
        combo = QtWidgets.QComboBox()
        combo.addItems([str(i) for i in range(int(p.min), int(p.max) + 1)])
        combo.setCurrentText(str(int(p.value)))
        combo.currentTextChanged.connect(page.modifyShellsInList)
        self.view.setIndexWidget(items[1].index(), combo)
        kernel = page.kernel()
        if kernel is not None and any(_SLD_SHELL.search(name) for name in kernel.params):
            button = QtWidgets.QPushButton("Show SLD Profile")
            button.clicked.connect(page.onShowSLDProfile)
            self.view.setIndexWidget(items[4].index(), button)

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
        if change.get(ModelChanged) is not None:
            self.build()
            return
        parameters = change.get(ParametersChanged)
        constraints = change.get(ConstraintsChanged)
        if parameters is None and constraints is None:
            return
        doc = self._page.document
        if self.rows() is None:
            self.build()        # out of step (it cannot happen through the controller): start again
            return
        if parameters is not None and "error" in parameters.fields:
            self.set_error_column(any(p.error is not None for p in doc.parameters))
        rows = self.rows()
        fields = {key: set(parameters.fields) for key in parameters.keys} if parameters is not None else {}
        for key in constraints.keys if constraints is not None else ():
            fields.setdefault(key, set()).add("constraint")
        for key, names in fields.items():
            if key in rows:
                self._patch(doc.parameters[key], rows[key], names)
            elif self.table is Table.MAIN and key.endswith(".width") and key[:-len(".width")] in rows:
                self._set_caption(doc.parameters[key], rows[key[:-len(".width")]])

    def _patch(self, p, row: int, fields: set[str]) -> None:
        model = self.item_model
        offset = 1 if self.has_error_column else 0
        if "value" in fields and p.kind is not ValueKind.INT:
            self._set_value(p, row)
        if "error" in fields and offset:
            self._set_text(model.item(row, 2), _text(p.error))
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
            filename = model.item(row, 7 + offset)
            if filename is not None:
                self._set_text(filename, p.dispersion.array.filename if p.dispersion.array is not None else "")
        if "constraint" in fields:
            self._set_constraint(p, row)
        if fields & {"fit", "fittable", "editable", "constraint", "dispersion"}:
            self._style_row(p, row)

    def _set_value(self, p, row: int) -> None:
        if p.kind is ValueKind.CHOICE:
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
        """The constraint child item of the value cell (the constraint tab reads it)."""
        item = self.item_model.item(row, 1)
        if item.hasChildren():
            item.removeRow(0)
        if p.constraint is not None:
            child = QtGui.QStandardItem()
            child.setData(copy.deepcopy(p.constraint))
            item.setChild(0, child)

    @staticmethod
    def _caption(width) -> str:
        return f"{width.value:.3f}"

    def _set_caption(self, width, row: int) -> None:
        """The width and distribution in a main row's polydispersity sub-row."""
        name = self.item_model.item(row, 0)
        sub = name.child(0) if name.hasChildren() else None
        if sub is None or not sub.hasChildren():
            return
        offset = 1 if self.has_error_column else 0
        sub.child(0, 1).setText(self._caption(width))
        sub.child(0, 4 + offset).setText(width.dispersion.type)

    def _style_row(self, p, row: int) -> None:
        """The row's look and editability: constrained (italic, blue, locked and fitted), disabled by the
        derived rules (italic, grey, no checkbox), or an array distribution (the row is disabled)."""
        model = self.item_model
        locked = p.constraint is not None and p.constraint.active
        disabled = self.table is Table.MAIN and not p.editable
        array = p.dispersion is not None and p.dispersion.array is not None
        font, brush = QtGui.QFont(), QtGui.QBrush()
        if locked:
            font.setItalic(True)
            brush = QtGui.QBrush(QtGui.QColor("blue"))
        last_enabled = 6 if self.table is Table.POLY else model.columnCount()
        offset = 1 if self.has_error_column else 0
        for column in range(model.columnCount()):
            item = model.item(row, column)
            if item is None:
                continue
            item.setFont(font)
            item.setForeground(brush)
            item.setEditable(self._editable(p, column - (offset if column > 1 else 0), column) and not locked)
            if column < last_enabled + offset:
                item.setEnabled(not array)
        name = model.item(row, 0)
        if disabled and not locked:
            italic = QtGui.QFont()
            italic.setItalic(True)
            name.setFont(italic)
            name.setForeground(QtGui.QBrush(QtGui.QColor(50, 50, 50)))
        name.setCheckable(p.fittable)
        name.setEnabled(not locked and not array)
        # A disabled row keeps the user's fit choice in the document (§2.5), unchecked here
        state = QtCore.Qt.Checked if p.fit and p.fittable else QtCore.Qt.Unchecked
        if name.checkState() != state:
            name.setCheckState(state)

    def _editable(self, p, column: int, actual: int) -> bool:
        """Whether the cell of *column* (counted without the error column) may be edited."""
        if column == 0 or (self.has_error_column and actual == 2):
            return False
        if self.table is not Table.MAIN:
            return True
        if column == 1:
            return p.editable and p.kind is not ValueKind.INT
        if column in (2, 3):
            return p.min is not None and p.kind is ValueKind.FLOAT
        return False

    # -- edits --------------------------------------------------------------

    def _fields(self) -> dict[int, str]:
        delegate = self.view.itemDelegate()
        if self.table is Table.MAIN:
            return {delegate.param_value: "value", delegate.param_min: "min", delegate.param_max: "max"}
        if self.table is Table.POLY:
            return {delegate.poly_pd: "value", delegate.poly_min: "min", delegate.poly_max: "max",
                    delegate.poly_npts: "npts", delegate.poly_nsigs: "nsigmas"}
        return {delegate.mag_value: "value", delegate.mag_min: "min", delegate.mag_max: "max"}

    def _on_edit(self, top: QtCore.QModelIndex, bottom: QtCore.QModelIndex | None = None) -> None:
        """A cell the user changed: a controller intent."""
        page = self._page
        if page.controller.muted:
            return    # written from the document
        item = self.item_model.itemFromIndex(top)
        if item is None:
            return
        key = self.key_at(item.row())
        if key is None:
            return
        p = page.document.parameters[key]
        if item.column() == 0:
            if self.table is Table.MAIN:
                # Checking one of several selected rows checks them all
                page.setParameterSelection(item.checkState(), item=item, model_key=self.model_key)
            page.controller.set_fit_flag(key, item.checkState() == QtCore.Qt.Checked)
            return
        field = self._fields().get(item.column())
        value = FittingUtilities.parse_number(item.text())
        if field is None or value is None or p.kind is ValueKind.INT:
            return    # not a number, or the shell count (modifyShellsInList)
        if field in ("npts", "nsigmas"):
            value = int(value) if field == "npts" else value
            page.controller.set_parameter(key, dispersion=dataclasses.replace(p.dispersion, **{field: value}))
        else:
            if self.table is Table.POLY and field == "value" and p.value != 0.0 and value == 0.0:
                # The polydispersity plot of this parameter is no longer meaningful
                self._owner().deletePlotSignal.emit(key[:-len(".width")])
            page.controller.set_parameter(key, **{field: int(value) if p.kind is ValueKind.CHOICE else value})
        if self.table is not Table.MAIN and field in ("value", "npts", "nsigmas"):
            # Poly and magnet edits update the plot, as before
            self._owner().updateDataSignal.emit()
