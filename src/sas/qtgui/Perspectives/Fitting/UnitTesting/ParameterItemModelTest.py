"""
The parameter tables (``view/ParameterItemModel.py``, FW-MVC-DESIGN.md §4.2, Phase 10), with the
page's real views and delegates: what the tables show, the notifications the models send when the
document changes (checked by pytest-qt's model tester too), and the edits the delegates
commit.
"""
import os

import pytest
from PySide6 import QtCore, QtWidgets

from sas.qtgui.Perspectives.Fitting.Constraint import Constraint
from sas.qtgui.Perspectives.Fitting.model.events import Origin
from sas.qtgui.Perspectives.Fitting.model.parameters import ArrayDistribution, Table
from sas.qtgui.Perspectives.Fitting.UnitTesting.fitting_test_support import FittingWidgetMod, dummy_manager
from sas.qtgui.UnitTesting.TestUtils import QtSignalSpy


def _select(widget, category: str, model: str) -> None:
    widget.cbCategory.setCurrentIndex(widget.cbCategory.findText(category))
    widget.cbModel.setCurrentIndex(widget.cbModel.findText(model))


def _poly_fitted(widget) -> list[str]:
    return [p.key for p in widget.document.parameters.by_table(Table.POLY) if p.fit]


@pytest.fixture
def widget(qapp, request):
    w = FittingWidgetMod(dummy_manager())
    yield w
    w.close()


@pytest.fixture
def cylinder(widget):
    widget.show()
    _select(widget, "Cylinder", "cylinder")
    return widget


def top_level(spy) -> list:
    """The calls of a rows/columns spy for the table itself, not for the children of an item."""
    return [call for call in spy.called().values() if not call["args"][0].isValid()]


def model_of(widget, table: Table = Table.MAIN):
    return widget.tables[table]


def tooltips(model) -> list[str]:
    return [model.headerData(c, QtCore.Qt.Horizontal, QtCore.Qt.ToolTipRole) for c in range(model.columnCount())]


class NotificationTest:
    """The model tells its view what changed: a row, the columns, or everything."""

    def testAValueChangeIsTheChangeOfItsRow(self, cylinder):
        model = cylinder._model_model
        row = model_of(cylinder).rows()["radius"]
        changed = QtSignalSpy(model, model.dataChanged)
        reset = QtSignalSpy(model, model.modelReset)
        with cylinder.document.transaction(Origin.USER) as tx:
            tx.set_parameter("radius", value=50.0)
        spans = [(c["args"][0].row(), c["args"][0].column(), c["args"][1].row(), c["args"][1].column())
                 for c in changed.called().values()]
        assert spans == [(row, 0, row, model.columnCount() - 1)]
        assert reset.count() == 0
        assert model.index(row, 1).data() == "50.0"

    def testAModelSwitchResetsTheTable(self, cylinder):
        model = cylinder._model_model
        reset = QtSignalSpy(model, model.modelReset)
        cylinder.cbModel.setCurrentIndex(cylinder.cbModel.findText("barbell"))
        assert reset.count() == 1
        assert model.rowCount() == len(cylinder.document.parameters.rows)
        assert cylinder.lstParams.model() is model

    @pytest.mark.parametrize("table", list(Table))
    def testTheModelTester(self, widget, qtmodeltester, table):
        """Every change of a scenario keeps the model consistent: rows, columns, parents, data
        and the signals that announce them (pytest-qt's model tester)."""
        qtmodeltester.check(widget.tables[table], force_py=True)
        widget.show()
        _select(widget, "Sphere", "core_multi_shell")
        widget.chkPolydispersity.setChecked(True)
        widget.controller.apply_fit({"radius": (21.0, 0.5), "sld_core": (2.0, 0.1)})
        widget.undo_stack.undo()
        model = widget._model_model
        widget.lstParams.indexWidget(model.index(model.shell_row, 1)).setCurrentIndex(2)
        _select(widget, "Cylinder", "cylinder")
        widget.controller.set_parameter("radius.width", value=0.1)

    def testErrorsInsertTheErrorColumnOnce(self, cylinder):
        model = cylinder._model_model
        inserted = QtSignalSpy(model, model.columnsInserted)
        removed = QtSignalSpy(model, model.columnsRemoved)
        cylinder.controller.apply_fit({"radius": (21.0, 0.5), "length": (401.0, 2.0)})
        assert [tuple(call["args"][1:]) for call in top_level(inserted)] == [(2, 2)]
        # The delegate takes the columns from the model
        assert [model.column(name) for name in ("value", "error", "min")] == [1, 2, 3]
        assert model.headerData(2, QtCore.Qt.Horizontal) == "Error"
        row = model_of(cylinder).rows()["radius"]
        assert (model.index(row, 1).data(), model.index(row, 2).data()) == ("21.0", "0.5")
        cylinder.undo_stack.undo()
        assert len(top_level(removed)) == 1
        assert [model.column(name) for name in ("value", "error", "min")] == [1, -1, 2]

    def testAConstraintLocksItsRow(self, cylinder):
        model = cylinder._model_model
        row = model_of(cylinder).rows()["length"]
        changed = QtSignalSpy(model, model.dataChanged)
        constraint = Constraint(param="length", func="2*M1.radius", value_ex="2*M1.radius")
        cylinder.controller.set_constraint("length", constraint, fit=True)
        assert changed.count() > 0
        assert not bool(model.flags(model.index(row, 1)) & QtCore.Qt.ItemIsEditable)
        assert model.index(row, 1).data(QtCore.Qt.FontRole).italic()
        cylinder.controller.remove_constraint("length")
        assert bool(model.flags(model.index(row, 1)) & QtCore.Qt.ItemIsEditable)
        assert model.index(row, 1).data(QtCore.Qt.FontRole) is None


class EditTest:
    """A value committed through the delegate's editor is an intent."""

    def _commit(self, widget, row, column, text):
        view, model = widget.lstParams, widget._model_model
        index = model.index(row, column)
        delegate = view.itemDelegate()
        editor = delegate.createEditor(view.viewport(), QtWidgets.QStyleOptionViewItem(), index)
        editor.setText(text)
        delegate.setModelData(editor, model, index)

    def testAValueEditIsUndoable(self, cylinder):
        cylinder.undo_stack.clear()
        row = model_of(cylinder).rows()["radius"]
        self._commit(cylinder, row, 1, "33.3")
        assert cylinder.document.parameters["radius"].value == 33.3
        assert cylinder.undo_stack.can_undo()
        cylinder.undo_stack.undo()
        assert cylinder._model_model.index(row, 1).data() == "20.0"

    def testARejectedBoundShowsTheDocumentAgain(self, cylinder):
        row = model_of(cylinder).rows()["radius"]
        cylinder.undo_stack.clear()
        self._commit(cylinder, row, 3, "-5")          # a maximum below the minimum
        assert cylinder.document.parameters["radius"].max == float("inf")
        assert cylinder._model_model.index(row, 3).data() == "inf"
        assert not cylinder.undo_stack.can_undo()


class MainTableTest:

    def testRowsAndKeys(self, cylinder):
        rows = model_of(cylinder).rows()
        assert (rows["scale"], rows["length"]) == (0, 6)
        assert model_of(cylinder).key_at(6) == "length"

    def testHeadersAndValues(self, cylinder):
        model = cylinder._model_model
        assert (model.rowCount(), model.columnCount()) == (7, 5)
        assert [model.headerData(c, QtCore.Qt.Horizontal, QtCore.Qt.ToolTipRole) for c in range(5)] == [
            'Select parameter for fitting', 'Enter parameter value', 'Enter minimum value for parameter',
            'Enter maximum value for parameter', 'Unit of the parameter']
        row = model_of(cylinder).rows()["length"]
        model.setData(model.index(row, 1), "333.0")
        assert cylinder.kernel().params["length"] == 333.0
        assert 333.0 not in cylinder.kernel().details["length"]

    def testValuesAreRetainedAcrossModels(self, cylinder):
        model = cylinder._model_model
        model.setData(model.index(model_of(cylinder).rows()["radius"], 1), "333.0")
        cylinder.cbModel.setCurrentIndex(cylinder.cbModel.findText("barbell"))
        assert float(model.index(model_of(cylinder).rows()["radius"], 1).data()) == 333
        _select(cylinder, "Sphere", "sphere")
        assert float(model.index(model_of(cylinder).rows()["radius"], 1).data()) == 333

    def testTheShellCountComboBox(self, widget):
        widget.show()
        _select(widget, "Sphere", "core_multi_shell")
        model = widget._model_model
        combo = widget.lstParams.indexWidget(model.index(model.shell_row, 1))
        assert isinstance(combo, QtWidgets.QComboBox)
        rows = model.rowCount()
        combo.setCurrentIndex(3)
        # n is 1 by default: two more shells, two parameters each
        assert model.rowCount() - rows == 4
        # The table, and its combo box, were rebuilt for the new layout
        widget.lstParams.indexWidget(model.index(model.shell_row, 1)).setCurrentIndex(0)
        assert model.rowCount() == rows - 2


class PolydispersityTableTest:

    def testRowsHeadersAndDelegate(self, widget):
        widget.show()
        _select(widget, "Shape Independent", "be_polyelectrolyte")
        model = widget.polydispersity_widget.poly_model
        assert model.rowCount() == 0
        _select(widget, "Cylinder", "cylinder")
        assert [model.index(r, 0).data() for r in range(model.rowCount())] == [
            "Distribution of radius", "Distribution of length"]
        assert model.columnCount() == 8 and widget.lstPoly.horizontalHeader().count() == 8
        assert tooltips(model)[1].startswith("Enter polydispersity ratio") and len(tooltips(model)) == 8
        for row in range(model.rowCount()):
            assert isinstance(widget.lstPoly.indexWidget(model.index(row, 6)), QtWidgets.QComboBox)
        delegate = widget.lstPoly.itemDelegate()
        assert len(delegate.POLYDISPERSE_FUNCTIONS) == 5
        assert delegate.EDITED == ("value", "min", "max", "npts", "nsigmas")
        assert model.column("function") == 6

    def testEdits(self, widget):
        widget.show()
        _select(widget, "Cylinder", "barbell")
        model = widget.polydispersity_widget.poly_model
        model.setData(model.index(0, 0), QtCore.Qt.Checked, QtCore.Qt.CheckStateRole)
        assert _poly_fitted(widget) == ['radius_bell.width']
        assert widget.document.parameters['radius_bell.width'].value == 0.0
        model.setData(model.index(2, 0), QtCore.Qt.Checked, QtCore.Qt.CheckStateRole)
        assert _poly_fitted(widget) == ['radius_bell.width', 'length.width']
        # Bounds of the width, not of the parameter
        model.setData(model.index(0, 2), "1.0")
        assert widget.kernel().details['radius_bell.width'][1] == 1.0
        assert widget.kernel().details['radius_bell'][1] == 0.0
        # Points and sigmas; text that is not a number changes nothing
        model.setData(model.index(0, 4), "22")
        assert widget.kernel().getParam('radius_bell.npts') == 22
        model.setData(model.index(0, 4), "butt")
        model.setData(model.index(0, 5), "222")
        model.setData(model.index(0, 4), "beer")
        assert (widget.document.parameters['radius_bell.width'].dispersion.npts,
                widget.document.parameters['radius_bell.width'].dispersion.nsigmas) == (22, 222)
        # The width: 0 in the kernel while polydispersity is off
        model.setData(model.index(0, 1), "0.8")
        assert widget.document.parameters['radius_bell.width'].value == pytest.approx(0.8)
        assert widget.kernel().getParam('radius_bell.width') == 0.0
        widget.chkPolydispersity.setChecked(True)
        assert widget.kernel().getParam('radius_bell.width') == pytest.approx(0.8)
        widget.chkPolydispersity.setChecked(False)
        assert widget.kernel().getParam('radius_bell.width') == 0.0

    def testDistributionFunctions(self, widget, mocker):
        widget.show()
        _select(widget, "Cylinder", "barbell")
        poly = widget.polydispersity_widget
        dispersion = lambda: widget.document.parameters['radius_bell.width'].dispersion  # noqa: E731
        poly.onPolyComboIndexChange('gaussian', 0)
        assert (dispersion().npts, dispersion().nsigmas) == (35, 3)
        poly.onPolyComboIndexChange('rectangle', 0)
        assert dispersion().npts == 35 and dispersion().nsigmas == pytest.approx(1.73205, abs=1e-5)
        for name in ('lognormal', 'schulz'):
            poly.onPolyComboIndexChange(name, 0)
            assert (dispersion().npts, dispersion().nsigmas) == (80, 8)
        mocker.patch.object(poly, 'loadPolydispArray',
                            return_value=ArrayDistribution((10.0, 20.0), (0.5, 0.5), "weights.txt"))
        poly.onPolyComboIndexChange('array', 0)
        poly.loadPolydispArray.assert_called()
        assert dispersion().array.filename == "weights.txt"
        assert not bool(poly.poly_model.flags(poly.poly_model.index(0, 1)) & QtCore.Qt.ItemIsEnabled)

    def testAnArrayFileThatDoesNotExist(self, widget, mocker):
        filename = os.path.join("UnitTesting", "testdata_noexist.txt")
        mocker.patch.object(QtWidgets.QFileDialog, 'getOpenFileName', return_value=(filename, ''))
        widget.show()
        _select(widget, "Cylinder", "barbell")
        widget.polydispersity_widget.onPolyComboIndexChange('array', 0)
        assert bool(widget.polydispersity_widget.poly_model.flags(widget.polydispersity_widget.poly_model.index(0, 1)) & QtCore.Qt.ItemIsEnabled)
        assert widget.document.parameters['radius_bell.width'].dispersion.array is None


class MagnetismTableTest:

    def testRowsHeadersAndDelegate(self, widget):
        widget.show()
        _select(widget, "Sphere", "core_shell_sphere")
        model = widget.magnetism_widget._magnet_model
        assert (model.rowCount(), model.columnCount()) == (13, 5)
        assert widget.lstMagnetic.horizontalHeader().count() == 5
        assert len(tooltips(model)) == 5
        assert all('_' in model.index(row, 0).data() for row in range(model.rowCount()))
        _select(widget, "Cylinder", "cylinder")
        assert [model.index(r, 0).data() for r in range(model.rowCount())] == [
            "up_frac_i", "up_frac_f", "up_theta", "up_phi", "sld_M0", "sld_mtheta", "sld_mphi",
            "sld_solvent_M0", "sld_solvent_mtheta", "sld_solvent_mphi"]
        assert widget.lstMagnetic.itemDelegate().EDITED == ("value", "min", "max")
