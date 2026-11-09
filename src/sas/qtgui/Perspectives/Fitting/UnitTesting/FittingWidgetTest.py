"""
The fit page as a view (FW-MVC-DESIGN.md §4.1, Phase 8): the wiring of its widgets to the
controller's intents, and the enablement that follows the document.

The tables are tested in ``ParameterTableAdapterTest``, and the document, the serializer and
the constraint service without Qt (``ModelDocumentTest``, ``ModelSerializerTest``,
``ModelKernelTest``).
"""
import time

import pytest
from PySide6 import QtCore, QtGui, QtTest, QtWidgets
from twisted.internet import threads

from sas import config
from sas.qtgui.Perspectives.Fitting import FittingWidget
from sas.qtgui.Perspectives.Fitting.Constraint import Constraint
from sas.qtgui.Perspectives.Fitting.model.results import DatasetResult, Provenance
from sas.qtgui.Perspectives.Fitting.ModelThread import Calc1D
from sas.qtgui.Perspectives.Fitting.services import constraints as constraint_service
from sas.qtgui.Perspectives.Fitting.UnitTesting import golden_support as g
from sas.qtgui.Perspectives.Fitting.UnitTesting.fitting_test_support import FittingWidgetMod, dummy_manager
from sas.qtgui.Perspectives.UndoRedo import UndoStack
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.UnitTesting.TestUtils import QtSignalSpy
from sas.qtgui.Utilities import GuiUtils


def _select(widget, category: str, model: str) -> None:
    """Select a model through the combo boxes, as the user does."""
    widget.cbCategory.setCurrentIndex(widget.cbCategory.findText(category))
    widget.cbModel.setCurrentIndex(widget.cbModel.findText(model))


@pytest.fixture
def widget(qapp, request, mocker):
    """A fit page in a perspective of its own (an inconsistent constraint is not shown in a dialog)."""
    mocker.patch.object(QtWidgets.QMessageBox, 'critical')
    w = FittingWidgetMod(dummy_manager())
    w.parent.perspective().fit_tabs.append(w)
    yield w
    w.shadow_checker.assert_ok(request)
    w.close()


class FittingWidgetTest:
    """The widgets, their enablement and their intents."""

    def testDefaults(self, widget):
        """Test the GUI in its default state"""
        assert isinstance(widget, QtWidgets.QWidget)
        assert widget.windowTitle() == "Fitting"
        sp = widget.sizePolicy()
        assert sp.horizontalPolicy() == QtWidgets.QSizePolicy.Policy.MinimumExpanding
        assert sp.verticalPolicy() == QtWidgets.QSizePolicy.Policy.Ignored
        assert isinstance(widget.lstParams.model(), QtGui.QStandardItemModel)
        assert isinstance(widget.lstPoly.model(), QtGui.QStandardItemModel)
        assert isinstance(widget.lstMagnetic.model(), QtGui.QStandardItemModel)
        assert not widget.cbModel.isEnabled()
        assert not widget.cbStructureFactor.isEnabled()
        assert not widget.cmdFit.isEnabled()
        assert widget.acceptsData()
        assert not widget.data_is_loaded

    def testCategoriesComeFromTheCatalog(self, widget):
        for category in widget.catalog.categories:
            assert widget.cbCategory.findText(category) != -1
        assert widget.cbCategory.currentText() == FittingWidget.CATEGORY_DEFAULT

    def testNonExistentModels(self, widget):
        """Models listed in categories.json that sasmodels does not have are not offered."""
        widget.catalog.categories["Cylinder"].append(["capped_anything", True])
        widget.catalog.regenerate()
        widget.cbCategory.setCurrentIndex(widget.cbCategory.findText("Cylinder"))
        assert widget.cbModel.findText("capped_anything") < 0

    def testWidgetWithData(self, widget, mocker):
        data = Data1D(x=[1, 2], y=[1, 2])
        mocker.patch.object(GuiUtils, 'dataFromItem', return_value=data)
        widget_with_data = FittingWidgetMod(dummy_manager(), data=QtGui.QStandardItem("test"), tab_id=3)
        assert widget_with_data.data == data
        assert widget_with_data.data_is_loaded
        assert not widget_with_data.acceptsData()

    def testStructureFactorsCanBeLoaded(self, widget):
        """Structure factors, including plugins classified as one."""
        for name in ("stickyhardsphere", "hayter_msa", "squarewell", "hardsphere"):
            assert widget.cbStructureFactor.findText(name) != -1

    def testSelectCategory(self, widget):
        widget.show()
        assert widget._previous_category_index == 0
        assert widget.cbModel.count() == 0
        category_index = widget.cbCategory.findText("Shape Independent")
        widget.cbCategory.setCurrentIndex(category_index)
        widget.cbModel.setCurrentIndex(widget.cbModel.findText("be_polyelectrolyte"))
        assert widget.cbModel.count() == 30
        # Back to the default category: it bounces back to the previous one
        widget.cbCategory.setCurrentIndex(0)
        assert widget.cbCategory.currentIndex() == category_index
        assert widget.cbModel.count() == 30
        # The structure factors: the model combo box is disabled
        widget.cbCategory.setCurrentIndex(widget.cbCategory.findText(FittingWidget.CATEGORY_STRUCTURE))
        assert not widget.cbModel.isEnabled()
        assert widget.cbStructureFactor.isEnabled()

    def testSelectModelIsAnIntent(self, widget, mocker):
        widget.show()
        widget.cbCategory.setCurrentIndex(widget.cbCategory.findText("Shape Independent"))
        widget.cbModel.setCurrentIndex(widget.cbModel.findText("be_polyelectrolyte"))
        assert widget.cbModel.isEnabled()
        assert not widget.cbStructureFactor.isEnabled()
        mocker.patch.object(widget.controller, 'ensure_default_dataset')
        mocker.patch.object(widget.controller, 'compute_theory')
        widget.cbModel.setCurrentIndex(4)
        assert widget.cbModel.currentText() == 'dab'
        # No data: only the theory grid
        assert widget.controller.ensure_default_dataset.called
        assert widget.document.selection.model == 'dab'
        assert widget._model_model.rowCount() == len(widget.document.parameters.rows)
        assert not widget.controller.compute_theory.called
        # With data, the theory is computed
        widget.data_is_loaded = True
        widget.cbModel.setCurrentIndex(2)
        assert widget.cbModel.currentText() == 'broad_peak'
        assert widget.controller.compute_theory.called

    def testSelectFactor(self, widget, mocker):
        widget.show()
        # The theory runs in a thread that briefly disables the controls
        mocker.patch.object(widget.controller, 'compute_theory')
        _select(widget, "Cylinder", "cylinder")
        assert widget.cbStructureFactor.isEnabled()
        assert widget.cbStructureFactor.currentText() == FittingWidget.STRUCTURE_DEFAULT
        rowcount = widget._model_model.rowCount()
        widget.cbStructureFactor.setCurrentIndex(widget.cbStructureFactor.findText('squarewell'))
        # 3 more parameters (radius_effective is removed), and new headings
        assert widget._model_model.rowCount() == rowcount + 7
        # Switching models keeps the structure factor
        widget.cbModel.setCurrentIndex(0)
        assert widget.cbStructureFactor.currentText() == 'squarewell'
        # The structure factor category
        widget.cbCategory.setCurrentIndex(widget.cbCategory.findText(FittingWidget.CATEGORY_STRUCTURE))
        assert widget.cbStructureFactor.isEnabled()
        assert not widget.cbModel.isEnabled()
        assert widget._model_model.rowCount() == 0
        # hayter_msa: 6 parameters and the heading row
        widget.cbStructureFactor.setCurrentIndex(widget.cbStructureFactor.findText('hayter_msa'))
        assert widget._model_model.rowCount() == 7
        assert widget.cmdPlot.isEnabled()
        assert not widget.cmdFit.isEnabled()

    def testTheFitButtonFollowsTheFitFlags(self, widget):
        page = g.new_page(data=g.make_data1d("d1", "data1"))
        g.select_model(page, "Cylinder", "cylinder")
        assert not page.cmdFit.isEnabled()
        page.controller.set_fit_flag("radius", True)
        assert page.cmdFit.isEnabled()
        page.controller.set_fit_flag("radius", False)
        assert not page.cmdFit.isEnabled()
        page.close()

    def testATheoryResultIsPublished(self, widget):
        """A page without data: the theory goes to a new theory item."""
        spy = QtSignalSpy(widget._model_model, widget.communicator.updateTheoryFromPerspectiveSignal)
        widget.show()
        widget.cbCategory.setCurrentIndex(1)
        widget.plot_publisher.publish(DatasetResult(Provenance(1, 0, 0, "theory", 0), Data1D(x=[1, 2], y=[1, 2])))
        assert spy.count() == 1
        assert isinstance(spy.called()[0]['args'][0], QtGui.QStandardItem)

    def testComputeTheoryStartsTheCalculation(self, widget, mocker):
        if config.USING_TWISTED:
            mocker.patch.object(threads, 'deferToThread')
            _select(widget, "Cylinder", "cylinder")
            widget.controller.compute_theory()
            time.sleep(1)
            assert threads.deferToThread.called
            assert threads.deferToThread.call_args_list[0][0][0].__name__ == "compute"
        else:
            mocker.patch.object(Calc1D, 'queue')
            # On a theory page: the default 1D dataset
            _select(widget, "Cylinder", "cylinder")
            widget.controller.compute_theory()
            time.sleep(1)
            assert Calc1D.queue.called

    def testPlotTheory(self, widget):
        assert not widget.cmdPlot.isEnabled()
        assert widget.cmdPlot.text() == 'Compute/Plot'
        widget.show()
        _select(widget, "Sphere", "adsorbed_layer")
        assert widget.cmdPlot.isEnabled()
        assert widget.cmdPlot.text() == 'Calculate'
        spy = QtSignalSpy(widget, widget.communicator.plotRequestedSignal)
        QtTest.QTest.mouseClick(widget.cmdPlot, QtCore.Qt.LeftButton)
        assert widget.cmdPlot.text() == 'Compute/Plot'
        assert spy.count() == 0
        QtTest.QTest.mouseClick(widget.cmdPlot, QtCore.Qt.LeftButton)
        assert spy.count() == 0

    def testOnHelp(self, widget, mocker):
        """The help page of each tab"""
        mocker.patch.object(widget.parent, 'showHelp', create=True)
        for tab, page in enumerate(["fitting_help.html", "residuals_help.html", "resolution.html",
                                    "polydispersity.html", "magnetism.html"]):
            widget.tabFitting.setCurrentIndex(tab)
            widget.onHelp()
            assert widget.parent.showHelp.call_count == tab + 1
            assert page in str(widget.parent.showHelp.call_args[0][0].absolute())

    def testModelContextMenu(self, widget):
        _select(widget, "Cylinder", "cylinder")
        assert len(widget.modelContextMenu([]).actions()) == 0
        # select, deselect, a separator, and constrain (one or three rows) or constrain mutually (two)
        for rows in ([1], [1, 3], [1, 2, 3]):
            assert len(widget.modelContextMenu(rows).actions()) == 4

    def testOnParameterPaste(self, widget, mocker):
        mocker.patch.object(widget.controller, 'paste')
        mocker.patch.object(widget, '_confirmModelMismatch', return_value=True)
        mocker.patch.object(QtWidgets.QMessageBox, 'exec_')
        cb = QtWidgets.QApplication.clipboard()
        # A bad clipboard
        cb.setText("bad clipboard")
        widget.clipboard_paste()
        QtWidgets.QMessageBox.exec_.assert_called_once()
        widget.controller.paste.assert_not_called()
        # A good one
        cb.setText("sasview_parameter_values:model_name,core_shell_bicelle:scale,False,1.0,None,0.0,inf,()")
        widget.clipboard_paste()
        widget.controller.paste.assert_called_once()

    def testQRangeReset(self, widget, mocker):
        options = widget.options_widget
        assert (options.qmin, options.qmax, options.npts) == (options.QMIN_DEFAULT, options.QMAX_DEFAULT,
                                                              options.NPTS_DEFAULT)
        assert options.npts == options.npts_fit
        options.updateMinQ(0.01)
        options.updateMaxQ(0.02)
        assert (float(options.qmin), float(options.qmax)) == (0.01, 0.02)
        options.cmdReset.click()
        assert (options.qmin, options.qmax, options.npts) == (options.QMIN_DEFAULT, options.QMAX_DEFAULT,
                                                              options.NPTS_DEFAULT)
        # With data, the reset goes back to the data's range
        data = Data1D(x=[1, 2], y=[1, 2])
        mocker.patch.object(GuiUtils, 'dataFromItem', return_value=data)
        with_data = FittingWidget.FittingWidget(dummy_manager(), data=QtGui.QStandardItem("test"), tab_id=3)
        options = with_data.options_widget
        assert (options.qmin, options.qmax, options.npts) == (min(data.x), max(data.x), len(data.x))
        options.updateMinQ(0.01)
        options.updateMaxQ(0.02)
        options.cmdReset.click()
        assert (options.qmin, options.qmax, options.npts) == (min(data.x), max(data.x), len(data.x))


class ConstraintDialogTest:
    """The page's own constraint actions: checked by the coordinator, kept in the document."""

    def testAConstraintIsCheckedAgainstEveryPage(self, widget):
        _select(widget, "Cylinder", "cylinder")
        assert widget.addConstraint(Constraint(param="radius", func="M1.length/20", value_ex="M1.length/20"))
        assert widget.document.parameters["radius"].constraint.func == "M1.length/20"
        assert widget.document.parameters["radius"].fit
        # An unknown symbol: reported, and not added
        assert not widget.addConstraint(Constraint(param="length", func="M9.radius", value_ex="M9.radius"))
        assert QtWidgets.QMessageBox.critical.call_args[0][1] == "Inconsistent constraint"
        assert widget.document.parameters["length"].constraint is None

    def testAPolydispersityConstraintIsOnTheWidth(self, widget):
        _select(widget, "Cylinder", "cylinder")
        # A width is a constraint symbol while polydispersity is on
        widget.chkPolydispersity.setChecked(True)
        constraint = Constraint(param="Distribution of radius", func="M1.length/1000")
        assert widget.addConstraint(constraint)
        assert constraint.param == "radius.width"
        assert widget.document.parameters["radius.width"].constraint is constraint

    def testSimpleConstraintsAndTheirRemoval(self, widget):
        _select(widget, "Cylinder", "cylinder")
        selection = widget.lstParams.selectionModel()
        for row in (1, 5):
            selection.select(widget._model_model.index(row, 0),
                             QtCore.QItemSelectionModel.Select | QtCore.QItemSelectionModel.Rows)
        widget.addSimpleConstraint()
        constraints = {p.key: p.constraint for p in widget.document.constrained()}
        assert list(constraints) == ["background", "radius"]
        assert not any(c.active for c in constraints.values())
        assert widget.getConstraintForRow(5).value == "20.0"
        widget.deleteConstraint()
        assert widget.document.constrained() == []
        assert (widget.document.parameters["radius"].min, widget.document.parameters["radius"].max) == (0.0, float("inf"))

    def testASingleFitAsksAboutConstraintsOnOtherPages(self, widget, mocker):
        _select(widget, "Cylinder", "cylinder")
        widget.controller.set_constraint("length", Constraint(param="length", func="M1.radius*2"), fit=True)
        widget.controller.set_constraint("scale", Constraint(param="scale", func="M2.background"), fit=True)
        mocker.patch.object(QtWidgets.QMessageBox, 'exec_', return_value=0)
        # Deactivate: only this page's constraint is fitted
        assert widget.getConstraintsForFitting() == [("length", "M1.radius*2")]
        assert QtWidgets.QMessageBox.exec_.called
        assert not widget.document.parameters["scale"].constraint.active
        # Cancel
        widget.controller.set_constraint_active("scale", True)
        QtWidgets.QMessageBox.exec_.return_value = QtWidgets.QMessageBox.RejectRole
        with pytest.raises(ValueError):
            widget.getConstraintsForFitting()
        assert ("scale", "M2.background") in constraint_service.complex_constraints(widget.document)


class FittingWidgetUndoRedoTest:
    """Undo and redo through the page."""

    def testWidgetHasUndoStack(self, widget):
        assert isinstance(widget.undo_stack, UndoStack)
        assert not widget.undo_stack.can_undo()
        assert not widget.undo_stack.can_redo()

    def testParamEditUndoRedo(self, widget):
        _select(widget, "Cylinder", "cylinder")
        widget.undo_stack.clear()
        row = widget.table_adapters[0].rows()["radius"]
        item = widget._model_model.item(row, widget.lstParams.itemDelegate().param_value)
        old_val = float(item.text())
        item.setText("99.0")
        assert widget.undo_stack.can_undo()
        widget.undo_stack.undo()
        assert widget.kernel().getParam("radius") == old_val
        assert widget.undo_stack.can_redo()
        widget.undo_stack.redo()
        assert widget.kernel().getParam("radius") == 99.0
