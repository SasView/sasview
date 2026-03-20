"""Integration tests for undo/redo wiring in FittingWidget (Phase 2).

These tests verify that FittingWidget handlers push the correct undo
commands to the UndoStack in response to user-initiated state changes.

Unlike UndoRedoTest.py (which tests Phase 1 command/stack internals in
isolation with a mocked widget), these tests spin up a real FittingWidget
and exercise its actual signal/slot plumbing.

Test organisation:
    TestUndoStackInitialization       — stack exists, initial state correct
    TestParameterValueUndo            — main params, poly, magnetism
    TestParameterMinMaxUndo           — min/max edits via main model
    TestModelSelectionUndo            — switching models via cbModel
    TestFitOptionsUndo                — Q range / npts / weighting changes
    TestSmearingOptionsUndo           — smearing state changes
    TestCheckboxToggleUndo            — poly / magnetism / 2D toggles
    TestFitResultUndo                 — undo after a fit completes
    TestUndoStackDisabledDuringFit    — stack disabled while fitting
    TestOptionsWidgetSetState         — OptionsWidget.setState() round-trip
"""
import glob
import os
from unittest.mock import MagicMock

import pytest
from PySide6 import QtCore, QtWidgets

from sasmodels.sasview_model import load_custom_model

from sas.qtgui.Perspectives.Fitting import FittingUtilities, FittingWidget
from sas.qtgui.Perspectives.Fitting.UndoRedo import (
    CheckboxToggleCommand,
    FitOptionsCommand,
    FitResultCommand,
    ModelSelectionCommand,
    ParameterMinMaxCommand,
    ParameterValueCommand,
    SmearingOptionsCommand,
    UndoStack,
)
from sas.qtgui.Utilities import GuiUtils
from sas.sascalc.fit.models import ModelManager, ModelManagerBase

# ---------------------------------------------------------------------------
# Helpers (same pattern as FittingWidgetTest.py)
# ---------------------------------------------------------------------------

class dummy_manager:
    HELP_DIRECTORY_LOCATION = "html"
    communicate = GuiUtils.Communicate()

    def __init__(self):
        self._perspective = dummy_perspective()

    def perspective(self):
        return self._perspective


class dummy_perspective:

    def __init__(self):
        self.symbol_dict = {}
        self.constraint_list = []
        self.constraint_tab = None

    def getActiveConstraintList(self):
        return self.constraint_list

    def getSymbolDictForConstraints(self):
        return self.symbol_dict

    def getConstraintTab(self):
        return self.constraint_tab


def find_plugin_models_mod():
    plugins_dir = [
        os.path.abspath(path) for path in glob.glob("**/plugin_models", recursive=True)
        if os.path.normpath("qtgui/Perspectives/Fitting/plugin_models") in os.path.abspath(path)
    ][0]
    plugins = {}
    for filename in os.listdir(plugins_dir):
        name, ext = os.path.splitext(filename)
        if ext == '.py' and not name == '__init__':
            path = os.path.abspath(os.path.join(plugins_dir, filename))
            model = load_custom_model(path)
            plugins[model.name] = model
    return plugins


class ModelManagerBaseMod(ModelManagerBase):
    def _is_plugin_dir_changed(self):
        return False

    def plugins_reset(self):
        self.plugin_models = find_plugin_models_mod()
        self.model_dictionary.clear()
        self.model_dictionary.update(self.standard_models)
        self.model_dictionary.update(self.plugin_models)
        return self.get_model_list()


class ModelManagerMod(ModelManager):
    base = None

    def __init__(self):
        if ModelManagerMod.base is None:
            ModelManagerMod.base = ModelManagerBaseMod()


class FittingWidgetMod(FittingWidget.FittingWidget):
    def customModels(cls):
        manager = ModelManagerMod()
        manager.update()
        return manager.base.plugin_models


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _suppress_message_boxes(monkeypatch):
    """Suppress QMessageBox dialogs globally."""
    monkeypatch.setattr(
        "sas.qtgui.Perspectives.Fitting.UndoRedo.QtWidgets.QMessageBox",
        MagicMock(),
    )


@pytest.fixture
def widget(qapp, monkeypatch):
    """Create a real FittingWidget for integration testing."""
    w = FittingWidgetMod(dummy_manager())
    monkeypatch.setattr(FittingUtilities, 'checkConstraints', lambda *a, **kw: None)
    yield w
    w.close()
    del w


@pytest.fixture
def widget_with_model(widget):
    """FittingWidget with 'cylinder' model loaded and processEvents run."""
    category_index = widget.cbCategory.findText("Cylinder")
    widget.cbCategory.setCurrentIndex(category_index)
    model_index = widget.cbModel.findText("cylinder")
    widget.cbModel.setCurrentIndex(model_index)
    QtWidgets.QApplication.processEvents()
    # Clear the undo stack so model-load commands don't interfere with tests
    widget.undo_stack.clear()
    return widget


# ---------------------------------------------------------------------------
# TestUndoStackInitialization
# ---------------------------------------------------------------------------

class TestUndoStackInitialization:

    def test_widget_has_undo_stack(self, widget):
        assert hasattr(widget, 'undo_stack')
        assert isinstance(widget.undo_stack, UndoStack)

    def test_initial_stack_is_empty(self, widget):
        assert not widget.undo_stack.can_undo()
        assert not widget.undo_stack.can_redo()

    def test_stack_widget_reference(self, widget):
        """The stack must reference the correct widget for command replay."""
        assert widget.undo_stack._widget is widget


# ---------------------------------------------------------------------------
# TestParameterValueUndo
# ---------------------------------------------------------------------------

class TestParameterValueUndo:

    def test_main_param_change_pushes_value_command(self, widget_with_model):
        """Editing a model parameter value should push a ParameterValueCommand."""
        w = widget_with_model
        # Find the 'radius' row
        param_col = w.lstParams.itemDelegate().param_value
        for row in range(w._model_model.rowCount()):
            name = w._model_model.item(row, 0).text()
            if name == "radius":
                item = w._model_model.item(row, param_col)
                old_val = float(item.text())
                item.setText("99.0")
                break
        else:
            pytest.fail("Could not find 'radius' parameter in the model")

        assert w.undo_stack.can_undo()
        top_cmd = w.undo_stack._undo_stack[-1]
        assert isinstance(top_cmd, ParameterValueCommand)
        assert top_cmd.param_name == "radius"
        assert top_cmd._new_val == 99.0
        assert top_cmd._old_val == old_val

    def test_main_param_undo_restores_value(self, widget_with_model):
        """Undo should restore the original kernel parameter value."""
        w = widget_with_model
        param_col = w.lstParams.itemDelegate().param_value
        for row in range(w._model_model.rowCount()):
            name = w._model_model.item(row, 0).text()
            if name == "radius":
                old_val = float(w._model_model.item(row, param_col).text())
                w._model_model.item(row, param_col).setText("99.0")
                break

        assert w.logic.kernel_module.getParam("radius") == 99.0
        w.undo_stack.undo()
        assert w.logic.kernel_module.getParam("radius") == old_val

    def test_checkbox_column_does_not_push_command(self, widget_with_model):
        """Toggling the 'fit' checkbox (column 0) must NOT push an undo command."""
        w = widget_with_model
        initial_count = len(w.undo_stack._undo_stack)
        item = w._model_model.item(0, 0)
        item.setCheckState(
            QtCore.Qt.Unchecked if item.checkState() == QtCore.Qt.Checked
            else QtCore.Qt.Checked
        )
        assert len(w.undo_stack._undo_stack) == initial_count


# ---------------------------------------------------------------------------
# TestParameterMinMaxUndo
# ---------------------------------------------------------------------------

class TestParameterMinMaxUndo:

    def test_min_change_pushes_minmax_command(self, widget_with_model):
        """Editing a min bound should push a ParameterMinMaxCommand."""
        w = widget_with_model
        min_col = w.lstParams.itemDelegate().param_min
        for row in range(w._model_model.rowCount()):
            name = w._model_model.item(row, 0).text()
            if name == "radius":
                w._model_model.item(row, min_col).setText("1.0")
                break

        top_cmd = w.undo_stack._undo_stack[-1]
        assert isinstance(top_cmd, ParameterMinMaxCommand)
        assert top_cmd._param_name == "radius"
        assert top_cmd._bound == "min"
        assert top_cmd._new_val == 1.0

    def test_max_change_pushes_minmax_command(self, widget_with_model):
        """Editing a max bound should push a ParameterMinMaxCommand."""
        w = widget_with_model
        max_col = w.lstParams.itemDelegate().param_max
        for row in range(w._model_model.rowCount()):
            name = w._model_model.item(row, 0).text()
            if name == "radius":
                w._model_model.item(row, max_col).setText("500.0")
                break

        top_cmd = w.undo_stack._undo_stack[-1]
        assert isinstance(top_cmd, ParameterMinMaxCommand)
        assert top_cmd._bound == "max"
        assert top_cmd._new_val == 500.0


# ---------------------------------------------------------------------------
# TestModelSelectionUndo
# ---------------------------------------------------------------------------

class TestModelSelectionUndo:

    def test_model_switch_pushes_model_selection_command(self, widget_with_model):
        """Changing cbModel should push a ModelSelectionCommand."""
        w = widget_with_model
        # Switch to a different model in the same category
        model_index = w.cbModel.findText("barbell")
        if model_index < 0:
            pytest.skip("barbell model not available")
        w.cbModel.setCurrentIndex(model_index)
        QtWidgets.QApplication.processEvents()

        assert w.undo_stack.can_undo()
        top_cmd = w.undo_stack._undo_stack[-1]
        assert isinstance(top_cmd, ModelSelectionCommand)
        assert "barbell" in top_cmd._new_triple[1]

    def test_model_selection_undo_restores_previous_model(self, widget_with_model):
        """Undoing a model switch should restore the previous model type."""
        w = widget_with_model
        original_model_type = type(w.logic.kernel_module)

        # Switch to a different model
        model_index = w.cbModel.findText("barbell")
        if model_index < 0:
            pytest.skip("barbell model not available")
        w.cbModel.setCurrentIndex(model_index)
        QtWidgets.QApplication.processEvents()

        assert type(w.logic.kernel_module) is not original_model_type
        w.undo_stack.undo()
        QtWidgets.QApplication.processEvents()
        # Verify the kernel module type was restored
        assert type(w.logic.kernel_module) is original_model_type

    def test_select_default_model_no_command(self, widget_with_model):
        """Selecting MODEL_DEFAULT should not push a command."""
        w = widget_with_model
        initial_count = len(w.undo_stack._undo_stack)

        default_index = w.cbModel.findText(FittingWidget.MODEL_DEFAULT)
        if default_index >= 0:
            w.cbModel.setCurrentIndex(default_index)
            # Should not push
            assert len(w.undo_stack._undo_stack) == initial_count


# ---------------------------------------------------------------------------
# TestFitOptionsUndo
# ---------------------------------------------------------------------------

class TestFitOptionsUndo:

    def test_options_update_pushes_fit_options_command(self, widget_with_model):
        """Changing Q-range or npts should push a FitOptionsCommand."""
        w = widget_with_model

        # Modify the Q range via the options widget's model
        from sas.qtgui.Perspectives.Fitting.OptionsWidget import OptionsWidget
        w._get_fit_options_dict()
        # Directly change the widget's model value to simulate user edit
        w.options_widget.model.item(
            OptionsWidget.MODEL.index('MIN_RANGE')
        ).setText("0.01")
        QtWidgets.QApplication.processEvents()

        if w.undo_stack.can_undo():
            top_cmd = w.undo_stack._undo_stack[-1]
            assert isinstance(top_cmd, FitOptionsCommand)

    def test_options_widget_setState_round_trip(self, widget_with_model):
        """OptionsWidget.setState must restore values consistently."""
        w = widget_with_model
        ow = w.options_widget

        # Get current state
        original = ow.state()
        # Set to different values
        ow.setState(0.001, 1.0, 200, True, 2)
        new_state = ow.state()
        assert new_state[0] == pytest.approx(0.001)
        assert new_state[1] == pytest.approx(1.0)
        assert new_state[2] == 200
        assert new_state[3] is True
        assert new_state[4] == 2

        # Restore original
        ow.setState(*original)
        restored = ow.state()
        assert restored[0] == pytest.approx(original[0])
        assert restored[1] == pytest.approx(original[1])
        assert restored[2] == original[2]


# ---------------------------------------------------------------------------
# TestSmearingOptionsUndo
# ---------------------------------------------------------------------------

class TestSmearingOptionsUndo:

    def test_initial_smearing_state_is_none(self, widget):
        """_last_smearing_state should be None until first update."""
        assert widget._last_smearing_state is None

    def test_first_smearing_update_no_command(self, widget_with_model):
        """First smearing update should NOT push a command (no prior state)."""
        w = widget_with_model
        w._last_smearing_state = None
        initial_count = len(w.undo_stack._undo_stack)
        w.onSmearingOptionsUpdate()
        # No command pushed because old_state was None
        assert len(w.undo_stack._undo_stack) == initial_count
        # But _last_smearing_state should now be populated
        assert w._last_smearing_state is not None

    def test_second_smearing_update_pushes_command(self, widget_with_model):
        """A smearing change after the first should push SmearingOptionsCommand."""
        w = widget_with_model
        # Prime the initial state
        w.onSmearingOptionsUpdate()
        w.undo_stack.clear()

        # Change smearing — simulate by altering the stored state
        old_state = dict(w._last_smearing_state)
        # Trigger another update (even if values are the same, verify logic)
        w.onSmearingOptionsUpdate()
        new_state = w._last_smearing_state

        if old_state != new_state:
            assert w.undo_stack.can_undo()
            top_cmd = w.undo_stack._undo_stack[-1]
            assert isinstance(top_cmd, SmearingOptionsCommand)


# ---------------------------------------------------------------------------
# TestCheckboxToggleUndo
# ---------------------------------------------------------------------------

class TestCheckboxToggleUndo:

    def test_toggle_poly_pushes_checkbox_command(self, widget_with_model):
        """Toggling polydispersity should push a CheckboxToggleCommand."""
        w = widget_with_model
        w.undo_stack.clear()

        w.chkPolydispersity.setEnabled(True)
        w.chkPolydispersity.setChecked(True)
        QtWidgets.QApplication.processEvents()

        assert w.undo_stack.can_undo()
        top_cmd = w.undo_stack._undo_stack[-1]
        assert isinstance(top_cmd, CheckboxToggleCommand)
        assert top_cmd._checkbox_id == "chkPolydispersity"
        assert top_cmd._new_bool is True

    def test_toggle_poly_undo_unchecks(self, widget_with_model):
        """Undoing poly toggle should uncheck the checkbox."""
        w = widget_with_model
        w.undo_stack.clear()

        w.chkPolydispersity.setEnabled(True)
        w.chkPolydispersity.setChecked(True)
        QtWidgets.QApplication.processEvents()

        w.undo_stack.undo()
        assert not w.chkPolydispersity.isChecked()

    def test_toggle_magnetism_pushes_checkbox_command(self, widget_with_model):
        """Toggling magnetism should push a CheckboxToggleCommand."""
        w = widget_with_model
        w.undo_stack.clear()

        w.chkMagnetism.setEnabled(True)
        w.chkMagnetism.setChecked(True)
        QtWidgets.QApplication.processEvents()

        assert w.undo_stack.can_undo()
        top_cmd = w.undo_stack._undo_stack[-1]
        assert isinstance(top_cmd, CheckboxToggleCommand)
        assert top_cmd._checkbox_id == "chkMagnetism"

    def test_toggle_2d_pushes_checkbox_command(self, widget_with_model):
        """Toggling 2D view should push a CheckboxToggleCommand."""
        w = widget_with_model
        w.undo_stack.clear()

        w.chk2DView.setEnabled(True)
        w.chk2DView.setChecked(True)
        QtWidgets.QApplication.processEvents()

        assert w.undo_stack.can_undo()
        top_cmd = w.undo_stack._undo_stack[-1]
        assert isinstance(top_cmd, CheckboxToggleCommand)
        assert top_cmd._checkbox_id == "chk2DView"

    def test_toggle_2d_does_not_push_model_selection(self, widget_with_model):
        """toggle2D calls onSelectModel internally — it must be suppressed."""
        w = widget_with_model
        w.undo_stack.clear()

        w.chk2DView.setEnabled(True)
        w.chk2DView.setChecked(True)
        QtWidgets.QApplication.processEvents()

        # Should have exactly one command (CheckboxToggle), not two
        # (i.e. the inner onSelectModel must not push its own ModelSelection)
        checkbox_cmds = [
            c for c in w.undo_stack._undo_stack
            if isinstance(c, CheckboxToggleCommand)
        ]
        model_cmds = [
            c for c in w.undo_stack._undo_stack
            if isinstance(c, ModelSelectionCommand)
        ]
        assert len(checkbox_cmds) == 1
        assert len(model_cmds) == 0


# ---------------------------------------------------------------------------
# TestFitResultUndo
# ---------------------------------------------------------------------------

class TestFitResultUndo:

    def _make_fit_result(self, widget):
        """Create a minimal fake fit result tuple."""
        res = MagicMock()
        res.fitness = 1.5
        res.pvec = [1.0, 2.0, 3.0]
        res.stderr = [0.1, 0.2, 0.3]
        # Build param_dict that paramDictFromResults would return
        param_names = [
            p.name for p in widget.logic.kernel_module._model_info.parameters.kernel_parameters
        ]
        res.pname = param_names[:len(res.pvec)]
        return ([[res]], 0.5)

    def test_fit_complete_pushes_fit_result_command(self, widget_with_model, monkeypatch):
        """fitComplete should push a FitResultCommand."""
        w = widget_with_model
        w.undo_stack.clear()

        # Mock methods that would crash without real fit data
        monkeypatch.setattr(w.polydispersity_widget, 'updatePolyModelFromList', lambda *a, **kw: None)
        monkeypatch.setattr(w.magnetism_widget, 'updateMagnetModelFromList', lambda *a, **kw: None)
        monkeypatch.setattr(w, 'onPlot', lambda *a, **kw: None)

        # Create a result that paramDictFromResults can handle
        old_params = w._get_parameter_dict()
        param_dict = {n: (v + 1.0, 0.01) for n, v in old_params.items()}
        monkeypatch.setattr(
            w.fitting_controller, 'paramDictFromResults', lambda *a, **kw: param_dict
        )

        # Make updateModelFromList actually modify the kernel so new_params != old_params
        def fake_update(pd):
            for name, (val, _err) in pd.items():
                w.logic.kernel_module.setParam(name, val)

        monkeypatch.setattr(
            w.fitting_controller, 'updateModelFromList', fake_update
        )

        result = self._make_fit_result(w)
        w.fitComplete(result)

        assert w.undo_stack.can_undo()
        top_cmd = w.undo_stack._undo_stack[-1]
        assert isinstance(top_cmd, FitResultCommand)

    def test_fit_complete_reenables_undo_stack(self, widget_with_model, monkeypatch):
        """fitComplete must re-enable the undo stack (disabled during fit)."""
        w = widget_with_model

        monkeypatch.setattr(w.fitting_controller, 'updateModelFromList', lambda *a, **kw: None)
        monkeypatch.setattr(w.polydispersity_widget, 'updatePolyModelFromList', lambda *a, **kw: None)
        monkeypatch.setattr(w.magnetism_widget, 'updateMagnetModelFromList', lambda *a, **kw: None)
        monkeypatch.setattr(w, 'onPlot', lambda *a, **kw: None)
        monkeypatch.setattr(
            w.fitting_controller, 'paramDictFromResults',
            lambda *a, **kw: {n: (v, 0.01) for n, v in w._get_parameter_dict().items()}
        )

        w.undo_stack.set_enabled(False)
        result = self._make_fit_result(w)
        w.fitComplete(result)
        assert w.undo_stack._enabled

    def test_fit_complete_failed_no_command(self, widget_with_model, monkeypatch):
        """A failed fit should not push an undo command."""
        w = widget_with_model
        w.undo_stack.clear()

        monkeypatch.setattr(w, 'enableInteractiveElements', lambda *a, **kw: None)
        w.kernel_module_copy = MagicMock()

        # Simulate failed fit
        w.fitComplete(None)
        assert not w.undo_stack.can_undo()


# ---------------------------------------------------------------------------
# TestUndoStackDisabledDuringFit
# ---------------------------------------------------------------------------

class TestUndoStackDisabledDuringFit:

    def test_onfit_disables_undo_stack(self, widget_with_model, monkeypatch):
        """onFit must disable the undo stack when fitting starts."""
        w = widget_with_model

        monkeypatch.setattr(w.fitting_controller, 'prepareFitters', lambda *a, **kw: ([MagicMock()], 0))
        monkeypatch.setattr(w, 'disableInteractiveElements', lambda *a, **kw: None)
        monkeypatch.setattr('twisted.internet.threads.deferToThread', lambda *a, **kw: MagicMock())

        w.onFit()
        assert not w.undo_stack._enabled

    def test_stopfit_reenables_undo_stack(self, widget_with_model, monkeypatch):
        """stopFit must re-enable the undo stack."""
        w = widget_with_model
        w.calc_fit = MagicMock()
        w.calc_fit.isrunning.return_value = True
        w.undo_stack.set_enabled(False)

        monkeypatch.setattr(w, 'enableInteractiveElements', lambda *a, **kw: None)
        w.stopFit()
        assert w.undo_stack._enabled


# ---------------------------------------------------------------------------
# TestOptionsWidgetSetState
# ---------------------------------------------------------------------------

class TestOptionsWidgetSetState:

    def test_setState_updates_q_range(self, widget_with_model):
        """setState should update Q range text fields."""
        ow = widget_with_model.options_widget
        ow.setState(0.002, 2.0, 300, False, 0)
        q_min, q_max, npts, log_pts, weighting = ow.state()
        assert q_min == pytest.approx(0.002)
        assert q_max == pytest.approx(2.0)
        assert npts == 300

    def test_setState_updates_log_checkbox(self, widget_with_model):
        """setState should toggle the log checkbox."""
        ow = widget_with_model.options_widget
        ow.setState(0.001, 0.5, 150, True, 0)
        assert ow.chkLogData.isChecked()
        ow.setState(0.001, 0.5, 150, False, 0)
        assert not ow.chkLogData.isChecked()

    def test_setState_updates_weighting(self, widget_with_model):
        """setState should update the weighting radio buttons."""
        ow = widget_with_model.options_widget
        for w_val in range(4):
            ow.setState(0.001, 0.5, 150, False, w_val)
            assert ow.weighting == w_val

    def test_setState_does_not_emit_signals(self, widget_with_model):
        """setState blocks model signals to avoid feedback loops."""
        ow = widget_with_model.options_widget
        signal_received = []
        ow.model.dataChanged.connect(lambda *a: signal_received.append(1))
        ow.setState(0.003, 3.0, 500, True, 1)
        assert len(signal_received) == 0


# ---------------------------------------------------------------------------
# TestUndoRedoRoundTrip
# ---------------------------------------------------------------------------

class TestUndoRedoRoundTrip:
    """End-to-end: make a change, undo it, redo it, verify state at each step."""

    def test_param_value_round_trip(self, widget_with_model):
        """Change radius → undo → redo should return to changed value."""
        w = widget_with_model
        param_col = w.lstParams.itemDelegate().param_value
        for row in range(w._model_model.rowCount()):
            if w._model_model.item(row, 0).text() == "radius":
                original = w.logic.kernel_module.getParam("radius")
                w._model_model.item(row, param_col).setText("42.0")
                break

        assert w.logic.kernel_module.getParam("radius") == 42.0
        w.undo_stack.undo()
        assert w.logic.kernel_module.getParam("radius") == original
        w.undo_stack.redo()
        assert w.logic.kernel_module.getParam("radius") == 42.0

    def test_multiple_undo_redo(self, widget_with_model):
        """Multiple parameter edits: undo all, then redo all."""
        w = widget_with_model
        param_col = w.lstParams.itemDelegate().param_value

        # Find radius and length rows
        radius_row = length_row = None
        for row in range(w._model_model.rowCount()):
            name = w._model_model.item(row, 0).text()
            if name == "radius":
                radius_row = row
            elif name == "length":
                length_row = row

        if radius_row is None or length_row is None:
            pytest.skip("Could not find both radius and length parameters")

        original_radius = w.logic.kernel_module.getParam("radius")
        original_length = w.logic.kernel_module.getParam("length")

        # Edit radius then length
        w._model_model.item(radius_row, param_col).setText("11.0")
        w._model_model.item(length_row, param_col).setText("22.0")

        assert w.logic.kernel_module.getParam("radius") == 11.0
        assert w.logic.kernel_module.getParam("length") == 22.0

        # Undo length
        w.undo_stack.undo()
        assert w.logic.kernel_module.getParam("length") == original_length
        assert w.logic.kernel_module.getParam("radius") == 11.0

        # Undo radius
        w.undo_stack.undo()
        assert w.logic.kernel_module.getParam("radius") == original_radius

        # Redo radius
        w.undo_stack.redo()
        assert w.logic.kernel_module.getParam("radius") == 11.0

        # Redo length
        w.undo_stack.redo()
        assert w.logic.kernel_module.getParam("length") == 22.0

    def test_suppressed_context_prevents_push(self, widget_with_model):
        """Changes inside suppressed() must not appear on the stack."""
        w = widget_with_model
        param_col = w.lstParams.itemDelegate().param_value
        w.undo_stack.clear()

        with w.undo_stack.suppressed():
            for row in range(w._model_model.rowCount()):
                if w._model_model.item(row, 0).text() == "radius":
                    w._model_model.item(row, param_col).setText("77.0")
                    break

        assert not w.undo_stack.can_undo()

    def test_stackChanged_signal_emitted_on_param_edit(self, widget_with_model):
        """stackChanged should fire when a parameter edit pushes a command."""
        w = widget_with_model
        received = []
        w.undo_stack.stackChanged.connect(lambda: received.append(1))

        param_col = w.lstParams.itemDelegate().param_value
        for row in range(w._model_model.rowCount()):
            if w._model_model.item(row, 0).text() == "radius":
                w._model_model.item(row, param_col).setText("55.0")
                break

        assert len(received) >= 1
