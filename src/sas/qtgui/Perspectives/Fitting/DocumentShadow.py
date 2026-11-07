"""
Phase 2 shadow: keeps ``FittingWidget.document`` in step with the legacy stores (FW-MVC-DESIGN.md §6).

The legacy stores (item models, kernel, widget fields) stay authoritative.
Every legacy writer runs inside ``shadow.operation(*sections)``, usually via
the ``@mirrors`` decorator. When the outermost operation ends, the named
sections are read back from the legacy stores into the document, in one
transaction:

- ``layout``: the selection or the tables were rebuilt. The document gets a
  fresh ``KernelBuilder.layout`` (only if it differs) and every other section.
- ``parameters``: values, bounds, fit flags, errors, dispersions, constraints.
- ``data``, ``options``, ``smearing``, ``flags``, ``identity``.

Only fields that differ are written, so each ChangeSet names what changed.
If the legacy stores cannot be read back, the error is logged (debug) and kept in
``shadow.errors`` (the tests assert it stays empty); the application goes on.

Temporary: removed in Phase 5, when the writers become controller intents.
"""
from __future__ import annotations

import contextlib
import copy
import functools
import inspect
import logging

from PySide6 import QtCore, QtWidgets

from sas.qtgui.Perspectives.Fitting.FittingConstants import CATEGORY_CUSTOM, STRUCTURE_DEFAULT
from sas.qtgui.Perspectives.Fitting.model.events import Origin
from sas.qtgui.Perspectives.Fitting.model.parameters import (
    ArrayDistribution,
    DataRef,
    Dispersion,
    FitOptions,
    ModelSelection,
    PageMode,
    RowKind,
    Smearing,
    Table,
    ValueKind,
    constraint_state,
)
from sas.qtgui.Utilities import GuiUtils

logger = logging.getLogger(__name__)

SECTIONS = ("data", "flags", "options", "layout", "parameters", "smearing", "identity")


class ShadowError(RuntimeError):
    """The legacy stores do not match the document's layout."""


def mirrors(*sections: str):
    """Decorator for legacy writers: mirror *sections* into the page's document when the call ends.

    Works on FittingWidget methods and on its tab widgets (through ``_fitting_widget`` or ``parent``).
    """
    def decorator(method):
        # Qt passes a slot only the signal arguments it accepts; a *args wrapper would get them all.
        parameters = inspect.signature(method).parameters.values()
        accepts_any = any(p.kind is p.VAR_POSITIONAL for p in parameters)
        positional = sum(p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD) for p in parameters) - 1

        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            if not accepts_any:
                args = args[:positional]
            shadow = _shadow_of(self)
            if shadow is None:
                return method(self, *args, **kwargs)
            with shadow.operation(*sections):
                return method(self, *args, **kwargs)
        return wrapper
    return decorator


def _shadow_of(widget):
    """The DocumentShadow of the page that *widget* is, or belongs to; None outside a page."""
    for owner in (widget, getattr(widget, "_fitting_widget", None), getattr(widget, "parent", None)):
        shadow = getattr(owner, "shadow", None)
        if isinstance(shadow, DocumentShadow):
            return shadow
    return None


def _number(text) -> float | None:
    """A cell's number, or None if the text is not one (the legacy code then ignores the edit too)."""
    try:
        return float(text)
    except (TypeError, ValueError):
        pass
    try:
        return GuiUtils.toDouble(text)
    except TypeError:
        return None


class DocumentShadow:

    def __init__(self, page) -> None:
        self._page = page
        self._depth = 0
        self._pending: set[str] = set()
        self.active = False
        self.errors: list[str] = []    # read-back failures; the tests assert there are none

    def start(self) -> None:
        """Called at the end of FittingWidget.__init__: seed the document from the finished page."""
        self.active = True
        self._sync(set(SECTIONS))

    @contextlib.contextmanager
    def operation(self, *sections: str):
        self._depth += 1
        self._pending.update(sections)
        try:
            yield
        finally:
            self._depth -= 1
            if self._depth == 0:
                pending, self._pending = self._pending, set()
                if self.active:
                    self._sync(pending)

    # ------------------------------------------------------------------

    def _sync(self, sections: set[str]) -> None:
        doc = self._page.document
        if "layout" in sections:
            sections = set(SECTIONS)
        try:
            with doc.transaction(Origin.USER) as tx:
                for section in SECTIONS:
                    if section in sections:
                        getattr(self, f"_sync_{section}")(doc, tx)
        except Exception as error:
            # Never raise: writers run in Qt slots, where an exception would be lost anyway.
            self.errors.append(f"{type(error).__name__}: {error} (sections {sorted(sections)})")
            # Debug level: nothing reads the document yet (Phase 3), and the tests check it.
            logger.debug("The fit page document is out of step with the page (sections %s)", sorted(sections),
                         exc_info=True)

    def _sync_data(self, doc, tx) -> None:
        page = self._page
        if page.data_is_loaded:
            datasets = [GuiUtils.dataFromItem(item) for item in page.all_data]
            refs = [DataRef(_data_id(d, i), str(d.name), d) for i, d in enumerate(datasets)]
            active = refs[page.data_index].id
        elif page.logic.data is not None:
            refs = [DataRef(_data_id(page.logic.data, 0), str(page.logic.data.name), page.logic.data, synthetic=True)]
            active = refs[0].id
        else:
            refs, active = [], None
        if refs:
            refs[[r.id for r in refs].index(active)].resolution = page.smearing_widget.smear_type
        mode = PageMode.BATCH if page.is_batch_fitting else PageMode.SINGLE
        if mode is not doc.mode:
            tx.set_mode(mode)
        current = [(r.id, r.name, r.data, r.synthetic, r.resolution) for r in doc.datasets.values()]
        if current != [(r.id, r.name, r.data, r.synthetic, r.resolution) for r in refs]:
            tx.set_datasets(refs, active)
        elif active != doc.active_id:
            tx.set_active_dataset(active)
        if page.is_chain_fitting and len(refs) > 1:
            order = [_data_id(GuiUtils.dataFromItem(item), page.all_data.index(item))
                     for item in page.order_widget.ordering()]
            if order != doc.chain_order:
                tx.set_chain_order(order)

    def _sync_flags(self, doc, tx) -> None:
        page = self._page
        flags = dict(polydispersity=page.chkPolydispersity.isChecked(), magnetism=page.chkMagnetism.isChecked(),
                     chain_fit=page.chkChainFit.isChecked(), view_2d=page.chk2DView.isChecked())
        if flags != vars(doc.flags):
            tx.set_flags(**flags)

    def _sync_options(self, doc, tx) -> None:
        page = self._page
        options = FitOptions(page.q_range_min, page.q_range_max, int(page.npts), bool(page.log_points),
                             int(page.weighting), int(page.options_widget.weighting))
        if options != doc.options:
            tx.set_options(options)

    def _sync_smearing(self, doc, tx) -> None:
        mode, accuracy, d_down, d_up = self._page.smearing_widget.state()
        smearing = Smearing(mode, accuracy, d_down, d_up)
        if smearing != doc.smearing:
            tx.set_smearing(smearing)

    def _sync_identity(self, doc, tx) -> None:
        kernel = self._page.logic.kernel_module
        if kernel is not None and kernel.name and kernel.name != doc.identity.mnemonic:
            tx.set_mnemonic(kernel.name)

    def _sync_layout(self, doc, tx) -> None:
        selection = self._selection()
        layout = self._page.kernel_builder.layout(selection, doc.is2D())
        tx.set_selection(selection)
        if not layout.same_layout(doc.parameters):
            tx.set_parameters(layout)

    def _selection(self) -> ModelSelection:
        page = self._page
        category = page.cbCategory.currentText()
        model = page.cbModel.currentText()
        structure = page.cbStructureFactor.currentText()
        structure = "" if structure in ("", STRUCTURE_DEFAULT) else structure
        kernel = page.logic.kernel_module
        shells = page.logic.current_shell_displayed if kernel is not None and kernel.is_multiplicity_model else None
        return ModelSelection(category, model, structure, category == CATEGORY_CUSTOM, shells)

    # -- parameters -----------------------------------------------------

    def _sync_parameters(self, doc, tx) -> None:
        params = doc.parameters
        self._read_main(params, tx)
        self._read_poly(params, tx)
        self._read_magnet(params, tx)

    def _read_main(self, params, tx) -> None:
        page = self._page
        table = page._model_model
        if table.rowCount() != len(params.rows):
            raise ShadowError(f"main table has {table.rowCount()} rows, the layout {len(params.rows)}")
        offset = 1 if page.has_error_column else 0
        for row, entry in enumerate(params.rows):
            if entry.kind is RowKind.HEADING:
                continue
            p = params[entry.name]
            cell = lambda column: table.item(row, column).text()  # noqa: E731
            if table.item(row, 0).text() != p.label:
                raise ShadowError(f"main row {row} is {table.item(row, 0).text()!r}, the layout has {p.label!r}")
            if entry.kind is RowKind.MULTIPLICITY:
                value = page.logic.current_shell_displayed
            elif p.kind is ValueKind.CHOICE:
                value = _number(cell(1))
                value = None if value is None else int(value)
            else:
                value = _number(cell(1))
            fields = dict(value=value, fit=table.item(row, 0).checkState() == QtCore.Qt.Checked,
                          error=_number(cell(2)) if offset else None)
            if p.min is not None:
                fields.update(min=_number(cell(2 + offset)), max=_number(cell(3 + offset)))
            self._update(tx, p, fields, page.getConstraintForRow(row, model_key="standard"))

    def _read_poly(self, params, tx) -> None:
        widget = self._page.polydispersity_widget
        table = widget.poly_model
        expected = params.by_table(Table.POLY)
        if table.rowCount() != len(expected):
            raise ShadowError(f"poly table has {table.rowCount()} rows, the layout {len(expected)}")
        offset = 1 if widget.has_poly_error_column else 0
        kernel = self._page.logic.kernel_module
        for row, p in enumerate(expected):
            cell = lambda column: table.item(row, column).text()  # noqa: E731
            # As gatherPolyParams reads them
            combo = widget.lstPoly.indexWidget(table.index(row, 6 + offset))
            function = combo.currentText() if isinstance(combo, QtWidgets.QComboBox) else cell(6 + offset).strip()
            npts, nsigmas = _number(cell(4 + offset)), _number(cell(5 + offset))
            array = None
            name = p.key[:-len(".width")]
            if function == "array" and kernel is not None and "values" in kernel.dispersion.get(name, {}):
                pars = kernel.dispersion[name]
                filename = table.item(row, 7 + offset)
                array = ArrayDistribution(tuple(map(float, pars["values"])), tuple(map(float, pars["weights"])),
                                          filename.text() if filename is not None else "")
            dispersion = Dispersion(int(npts) if npts is not None else p.dispersion.npts,
                                    nsigmas if nsigmas is not None else p.dispersion.nsigmas, function, array)
            fields = dict(value=_number(cell(1)), fit=table.item(row, 0).checkState() == QtCore.Qt.Checked,
                          error=_number(cell(2)) if offset else None, min=_number(cell(2 + offset)),
                          max=_number(cell(3 + offset)), dispersion=dispersion)
            self._update(tx, p, fields, None)

    def _read_magnet(self, params, tx) -> None:
        widget = self._page.magnetism_widget
        table = widget._magnet_model
        expected = params.by_table(Table.MAGNET)
        if table.rowCount() != len(expected):
            raise ShadowError(f"magnet table has {table.rowCount()} rows, the layout {len(expected)}")
        offset = 1 if widget.has_magnet_error_column else 0
        for row, p in enumerate(expected):
            cell = lambda column: table.item(row, column).text()  # noqa: E731
            fields = dict(value=_number(cell(1)), fit=table.item(row, 0).checkState() == QtCore.Qt.Checked,
                          error=_number(cell(2)) if offset else None, min=_number(cell(2 + offset)),
                          max=_number(cell(3 + offset)))
            self._update(tx, p, fields, None)

    @staticmethod
    def _update(tx, p, fields: dict, constraint) -> None:
        """Write the fields of *p* that differ. A number that does not parse keeps the document's value."""
        changed = {name: value for name, value in fields.items()
                   if (value is not None or name == "error") and getattr(p, name) != value}
        if changed:
            tx.set_parameter(p.key, **changed)
        if constraint_state(constraint) != constraint_state(p.constraint):
            tx.set_constraint(p.key, copy.deepcopy(constraint))


def _data_id(data, index: int) -> str:
    """The data's id, or a positional one for data without an id (as in some tests)."""
    return str(data.id) if getattr(data, "id", None) else f"#{index}"
