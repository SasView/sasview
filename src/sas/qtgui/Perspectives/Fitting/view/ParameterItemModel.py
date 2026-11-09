"""
A parameter table over the page's document (FW-MVC-DESIGN.md §4.2, Phase 10).

``ParameterItemModel`` is a ``QAbstractItemModel`` that reads the document: it holds no copy of
a value, so nothing has to be kept in step with it. One instance serves each ``Table``:

- **Rows** come from the layout. The main table has its headings, the shell-count row, and for
  each polydisperse parameter a "Polydispersity" child with the width and the distribution
  (a grandchild row, for display). The polydispersity and magnetism tables are flat.
- **Columns** are named (``column``, ``column_name``); the error column is shown while the
  document has errors. The delegates ask the model for a column's name.
- **Edits** (``setData``) are controller intents. A rejected edit leaves the document as it
  was, and the view shows the document again.
- **Document changes** become model signals (through ``controller.subscribe_view``): a layout
  change resets the model, a parameter or constraint change is a ``dataChanged`` of its row,
  and errors that appear or disappear insert or remove the error column.
- **Index widgets** (the shell-count combo box and the SLD profile button, the fixed-choice and
  the distribution combo boxes) are set on the view after every reset, and follow the document.
"""
from __future__ import annotations

import dataclasses
import re

from PySide6 import QtCore, QtGui, QtWidgets

from sasmodels.weights import MODELS as DISTRIBUTIONS

from sas.qtgui.Perspectives.Fitting.FittingUtilities import parse_number
from sas.qtgui.Perspectives.Fitting.model.events import ConstraintsChanged, ModelChanged, ParametersChanged
from sas.qtgui.Perspectives.Fitting.model.parameters import RowKind, Table, ValueKind
from sas.qtgui.Perspectives.Fitting.model.serializer import format_number

Qt = QtCore.Qt

# The columns of each table (the error column, when shown, is inserted after the value),
# with their captions and header tooltips
_SELECT = ("Parameter", "Select parameter for fitting")
_BOUNDS = [("min", "Min", "Enter minimum value for parameter"), ("max", "Max", "Enter maximum value for parameter")]
COLUMNS = {
    Table.MAIN: [("name",) + _SELECT, ("value", "Value", "Enter parameter value"), *_BOUNDS,
                 ("units", "Units", "Unit of the parameter")],
    Table.POLY: [("name",) + _SELECT,
                 ("value", "PD[ratio]", "Enter polydispersity ratio (Std deviation/mean).\n"
                  "For angles this can be either std deviation or half width (for uniform distributions) in degrees"),
                 *_BOUNDS, ("npts", "Npts", "Enter number of points for parameter"),
                 ("nsigmas", "Nsigs", "Enter number of sigmas parameter"),
                 ("function", "Function", "Select distribution function"),
                 ("filename", "Filename", "Select filename with user-definable distribution")],
    Table.MAGNET: [("name",) + _SELECT, ("value", "Value", "Enter parameter value"), *_BOUNDS,
                   ("units", "Units", "Unit of the parameter")],
}
ERROR_COLUMN = ("error", "Error", "Error value for fitted parameter")

# Models with SLD parameters per shell offer the SLD profile
_SLD_SHELL = re.compile(r'^[\w]{0,3}sld.*[1-9]$')

# internalId of an index: 0 for a top-level row; for the children of top-level row r,
# 2 * (r + 1) (the "Polydispersity" row) and 2 * (r + 1) + 1 (its distribution row)
_SUB, _DISTRIBUTION = 0, 1


def _text(value) -> str:
    return "" if value is None else format_number(value)


class ParameterItemModel(QtCore.QAbstractItemModel):

    def __init__(self, page, table: Table, view: QtWidgets.QAbstractItemView) -> None:
        super().__init__(view)
        self._page = page
        self.table = table
        self.view = view
        self._rows: list = []        # the layout's rows (main) or parameter keys (poly, magnet)
        self._row_of: dict[str, int] = {}
        self._errors = False
        self._load()
        view.setModel(self)
        self.subscription = page.controller.subscribe_view(self._on_change)

    # -- rows and columns ---------------------------------------------------

    @property
    def _params(self):
        return self._page.document.parameters

    def _load(self) -> None:
        params = self._params
        if self.table is Table.MAIN:
            self._rows = list(params.rows)
            self._row_of = {r.name: i for i, r in enumerate(self._rows) if r.kind is not RowKind.HEADING}
        else:
            self._rows = [p.key for p in params.by_table(self.table)]
            self._row_of = {key: i for i, key in enumerate(self._rows)}
        self._errors = self._document_has_errors()

    def _document_has_errors(self) -> bool:
        return bool(self._rows) and any(p.error is not None for p in self._params)

    @property
    def columns(self) -> list[tuple[str, str, str]]:
        columns = list(COLUMNS[self.table])
        if self._errors:
            columns.insert(2, ERROR_COLUMN)
        return columns

    @property
    def has_error_column(self) -> bool:
        return self._errors

    def column(self, name: str) -> int:
        """The column of *name* ('value', 'error', 'min', ...), or -1 if it is not shown."""
        return next((i for i, c in enumerate(self.columns) if c[0] == name), -1)

    def column_name(self, column: int) -> str | None:
        columns = self.columns
        return columns[column][0] if 0 <= column < len(columns) else None

    def rows(self) -> dict[str, int]:
        """{key: row} of the parameters (and the shell count) the table shows."""
        return dict(self._row_of)

    def key_at(self, row: int) -> str | None:
        """The key of the parameter in top-level *row*, or None (a heading, or no such row)."""
        if not 0 <= row < len(self._rows):
            return None
        entry = self._rows[row]
        if self.table is not Table.MAIN:
            return entry
        return None if entry.kind is RowKind.HEADING else entry.name

    @property
    def shell_row(self) -> int:
        """The row of the shell-count combo box, or -1."""
        return next((i for i, r in enumerate(self._rows)
                     if self.table is Table.MAIN and r.kind is RowKind.MULTIPLICITY), -1)

    def _width_key(self, row: int) -> str | None:
        """The polydispersity width shown under top-level *row* of the main table."""
        if self.table is not Table.MAIN or not 0 <= row < len(self._rows):
            return None
        entry = self._rows[row]
        width = f"{entry.name}.width"
        return width if entry.kind is RowKind.PARAMETER and width in self._params else None

    # -- QAbstractItemModel ---------------------------------------------------

    def index(self, row: int, column: int, parent=QtCore.QModelIndex()) -> QtCore.QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()
        if not parent.isValid():
            return self.createIndex(row, column, 0)
        if parent.internalId() == 0:
            return self.createIndex(row, column, 2 * (parent.row() + 1) + _SUB)
        return self.createIndex(row, column, parent.internalId() + 1)

    def parent(self, index: QtCore.QModelIndex = QtCore.QModelIndex()) -> QtCore.QModelIndex:
        if not index.isValid() or index.internalId() == 0:
            return QtCore.QModelIndex()
        top = index.internalId() // 2 - 1
        if index.internalId() % 2 == _SUB:
            return self.createIndex(top, 0, 0)
        return self.createIndex(0, 0, 2 * (top + 1) + _SUB)

    def rowCount(self, parent=QtCore.QModelIndex()) -> int:
        if not parent.isValid():
            return len(self._rows)
        if parent.column() != 0:
            return 0
        if parent.internalId() == 0:
            return 1 if self._width_key(parent.row()) is not None else 0
        return 1 if parent.internalId() % 2 == _SUB else 0

    def columnCount(self, parent=QtCore.QModelIndex()) -> int:
        return len(self.columns)

    def headerData(self, section: int, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and 0 <= section < len(self.columns):
            if role == Qt.DisplayRole:
                return self.columns[section][1]
            if role == Qt.ToolTipRole:
                return self.columns[section][2]
        return None

    def data(self, index: QtCore.QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        name = self.column_name(index.column())
        if index.internalId() != 0:
            return self._sub_data(index, name, role)
        if self.table is Table.MAIN:
            entry = self._rows[index.row()]
            if entry.kind is RowKind.HEADING:
                return self._heading_data(entry.name, name, role)
            if entry.kind is RowKind.MULTIPLICITY:
                return self._shell_data(self._params[entry.name], name, role)
        p = self._params[self.key_at(index.row())]
        if role in (Qt.DisplayRole, Qt.EditRole):
            return self._text(p, name)
        if role == Qt.CheckStateRole and name == "name" and p.fittable:
            return Qt.Checked if p.fit else Qt.Unchecked
        if role == Qt.UserRole and name == "name":
            return p.key
        locked = p.constraint is not None and p.constraint.active
        if role == Qt.FontRole and (locked or (name == "name" and self._disabled(p))):
            font = QtGui.QFont()
            font.setItalic(True)
            return font
        if role == Qt.ForegroundRole:
            if locked:
                return QtGui.QBrush(QtGui.QColor("blue"))
            if name == "name" and self._disabled(p):
                return QtGui.QBrush(QtGui.QColor(50, 50, 50))
        return None

    @staticmethod
    def _text(p, name: str) -> str:
        if name == "name":
            return p.label
        if name == "value":
            return str(int(p.value)) if p.kind is ValueKind.CHOICE else format_number(p.value)
        if name in ("min", "max", "error"):
            return _text(getattr(p, name))
        if name == "units":
            return p.units
        d = p.dispersion
        if name == "npts":
            return str(int(d.npts))
        if name == "nsigmas":
            return format_number(d.nsigmas)
        if name == "filename":
            return d.array.filename if d.array is not None else ""
        return ""                      # the distribution: its combo box

    @staticmethod
    def _heading_data(text: str, name: str, role):
        if role == Qt.DisplayRole and name == "name":
            return text
        if role == Qt.FontRole and name == "name":
            font = QtGui.QFont()
            font.setBold(True)
            return font
        return None

    @staticmethod
    def _shell_data(p, name: str, role):
        if role != Qt.DisplayRole:
            return None
        return {"name": p.label, "min": str(int(p.min)), "max": str(int(p.max))}.get(name, "")

    def _sub_data(self, index, name: str, role):
        """The "Polydispersity" row and, under it, the width and the distribution of a parameter."""
        if role != Qt.DisplayRole:
            return None
        if index.internalId() % 2 == _SUB:
            return "Polydispersity" if name == "name" else ""
        width = self._params[self._width_key(index.internalId() // 2 - 1)]
        return {"name": "Distribution", "value": f"{width.value:.3f}", "units": width.dispersion.type}.get(name, "")

    def _disabled(self, p) -> bool:
        """Disabled by the document's rules (main table only)."""
        return self.table is Table.MAIN and not p.editable

    def flags(self, index: QtCore.QModelIndex):
        if not index.isValid():
            return Qt.NoItemFlags
        if index.internalId() != 0:
            return Qt.ItemIsEnabled
        name = self.column_name(index.column())
        if self.table is Table.MAIN:
            kind = self._rows[index.row()].kind
            if kind is RowKind.HEADING:
                return Qt.ItemIsEnabled
            if kind is RowKind.MULTIPLICITY:
                return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        p = self._params[self.key_at(index.row())]
        locked = p.constraint is not None and p.constraint.active
        array = p.dispersion is not None and p.dispersion.array is not None
        flags = Qt.ItemIsSelectable
        if name == "name":
            if p.fittable:
                flags |= Qt.ItemIsUserCheckable
            if not (locked or array):
                flags |= Qt.ItemIsEnabled
            return flags
        if not array or name in ("function", "filename"):
            flags |= Qt.ItemIsEnabled
        if not locked and self._editable(p, name):
            flags |= Qt.ItemIsEditable
        return flags

    def _editable(self, p, name: str) -> bool:
        if self.table is Table.POLY:
            return name in ("value", "min", "max", "npts", "nsigmas", "filename")
        if self.table is Table.MAGNET:
            return name in ("value", "min", "max")
        if name == "value":
            return p.editable and p.kind is not ValueKind.INT
        return name in ("min", "max") and p.min is not None and p.kind is ValueKind.FLOAT

    def setData(self, index: QtCore.QModelIndex, value, role=Qt.EditRole) -> bool:
        """A cell the user changed: a controller intent."""
        page = self._page
        key = self.key_at(index.row()) if index.isValid() and index.internalId() == 0 else None
        if key is None or page.controller.muted:
            return False
        name = self.column_name(index.column())
        if role == Qt.CheckStateRole and name == "name":
            fit = Qt.CheckState(value) == Qt.Checked
            if self.table is Table.MAIN and index.row() in page.selectedParameters(self.table):
                page.setFitForSelection(fit, self.table)      # checking one of several selected rows
            else:
                page.controller.set_fit_flag(key, fit)
            return True
        p = self._params[key]
        number = parse_number(value)
        if role != Qt.EditRole or number is None or name not in ("value", "min", "max", "npts", "nsigmas"):
            return False
        owner = {Table.POLY: page.polydispersity_widget, Table.MAGNET: page.magnetism_widget}.get(self.table)
        if name in ("npts", "nsigmas"):
            number = int(number) if name == "npts" else number
            page.controller.set_parameter(key, dispersion=dataclasses.replace(p.dispersion, **{name: number}))
        else:
            if self.table is Table.POLY and name == "value" and p.value != 0.0 and number == 0.0:
                # The polydispersity plot of this parameter is no longer meaningful
                owner.deletePlotSignal.emit(key[:-len(".width")])
            page.controller.set_parameter(key, **{name: int(number) if p.kind is ValueKind.CHOICE else number})
        if owner is not None and name in ("value", "npts", "nsigmas"):
            # Poly and magnet edits update the plot, as before
            owner.updateDataSignal.emit()
        return True

    # -- document changes -------------------------------------------------------

    def _on_change(self, change) -> None:
        if change.get(ModelChanged) is not None:
            self.beginResetModel()
            self._load()
            self.endResetModel()
            self._set_index_widgets()
            return
        parameters = change.get(ParametersChanged)
        constraints = change.get(ConstraintsChanged)
        if parameters is not None and "error" in parameters.fields:
            self._show_errors(self._document_has_errors())
        keys = set(parameters.keys if parameters is not None else ()) | set(constraints.keys if constraints else ())
        last = self.columnCount() - 1
        for key in keys:
            row = self._row_of.get(key)
            if row is not None:
                self.dataChanged.emit(self.index(row, 0), self.index(row, last))
                self._follow_widgets(key, row)
            elif self.table is Table.MAIN and key.endswith(".width") and key[:-len(".width")] in self._row_of:
                sub = self.index(0, 0, self.index(self._row_of[key[:-len(".width")]], 0))
                self.dataChanged.emit(self.index(0, 0, sub), self.index(0, last, sub))

    def _show_errors(self, shown: bool) -> None:
        """Insert or remove the error column."""
        if shown == self._errors:
            return
        if shown:
            self.beginInsertColumns(QtCore.QModelIndex(), 2, 2)
            self._errors = True
            self.endInsertColumns()
        else:
            self.beginRemoveColumns(QtCore.QModelIndex(), 2, 2)
            self._errors = False
            self.endRemoveColumns()

    # -- index widgets ----------------------------------------------------------------

    def _set_index_widgets(self) -> None:
        page, params = self._page, self._params
        for row in range(len(self._rows)):
            key = self.key_at(row)
            if key is None:
                continue
            p = params[key]
            if self.table is Table.MAIN and self._rows[row].kind is RowKind.MULTIPLICITY:
                combo = QtWidgets.QComboBox()
                combo.addItems([str(i) for i in range(int(p.min), int(p.max) + 1)])
                combo.setCurrentText(str(int(p.value)))
                combo.currentTextChanged.connect(page.modifyShellsInList)
                self.view.setIndexWidget(self.index(row, self.column("value")), combo)
                kernel = page.kernel()
                if kernel is not None and any(_SLD_SHELL.search(name) for name in kernel.params):
                    button = QtWidgets.QPushButton("Show SLD Profile")
                    button.clicked.connect(page.onShowSLDProfile)
                    self.view.setIndexWidget(self.index(row, self.column("units")), button)
            elif p.kind is ValueKind.CHOICE:
                combo = QtWidgets.QComboBox()
                combo.addItems(list(p.choices))
                combo.setCurrentIndex(int(p.value))
                combo.currentIndexChanged.connect(lambda i, k=key: page.controller.set_parameter(k, value=i))
                self.view.setIndexWidget(self.index(row, self.column("value")), combo)
            elif self.table is Table.POLY:
                combo = QtWidgets.QComboBox()
                combo.addItems([str(name) for name in DISTRIBUTIONS])
                combo.setCurrentIndex(combo.findText(p.dispersion.type))
                widget = page.polydispersity_widget
                combo.currentIndexChanged.connect(
                    lambda _, c=combo, r=row: widget.onPolyComboIndexChange(c.currentText(), r))
                self.view.setIndexWidget(self.index(row, self.column("function")), combo)

    def _follow_widgets(self, key: str, row: int) -> None:
        """A fixed choice or a distribution changed: its combo box shows it."""
        p = self._params[key]
        if p.kind is ValueKind.CHOICE:
            combo, index = self.view.indexWidget(self.index(row, self.column("value"))), int(p.value)
        elif self.table is Table.POLY:
            combo = self.view.indexWidget(self.index(row, self.column("function")))
            index = combo.findText(p.dispersion.type) if combo is not None else -1
        else:
            return
        if isinstance(combo, QtWidgets.QComboBox) and combo.currentIndex() != index:
            combo.blockSignals(True)
            combo.setCurrentIndex(index)
            combo.blockSignals(False)
