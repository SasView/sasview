"""Unit tests for UndoRedo.py — UndoCommand subclasses and UndoStack.

Tests focus on single-tab fitting scenarios.  The FittingWidget dependency
is fully mocked; no real fitting window is opened.

Test organisation:
    TestUndoCommand              — abstract base behaviour
    TestParameterValueCommand    — value change, coalescing
    TestParameterMinMaxCommand   — bound change
    TestModelSelectionCommand    — model triple + param restore
    TestFitOptionsCommand        — options dict round-trip
    TestSmearingOptionsCommand   — smearing state round-trip
    TestCheckboxToggleCommand    — checkbox flip
    TestFitResultCommand         — pre/post fit snapshot
    TestCompoundCommand          — atomic group, ordering
    TestUndoStack                — push / undo / redo / depth / suppression
    TestUndoStackFailure         — failure dialog, reset_to_last_good
"""
import logging
import time
from unittest.mock import MagicMock

import pytest

from sas.qtgui.Perspectives.Fitting.UndoRedo import (
    CheckboxToggleCommand,
    CompoundCommand,
    FitOptionsCommand,
    FitResultCommand,
    ModelSelectionCommand,
    ParameterMinMaxCommand,
    ParameterValueCommand,
    SmearingOptionsCommand,
    UndoCommand,
    UndoStack,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def mock_message_box(mocker):
    """Suppress all QMessageBox dialogs for the entire test module."""
    return mocker.patch("PySide6.QtWidgets.QMessageBox")


@pytest.fixture
def widget():
    """Minimal mock that satisfies the widget protocol used by commands."""
    w = MagicMock()
    # kernel_module.details must support real dict operations for MinMax tests
    w.logic.kernel_module.details = {}
    return w


@pytest.fixture
def stack(widget, qapp):
    """An UndoStack wired to a mock widget."""
    return UndoStack(widget)


# ---------------------------------------------------------------------------
# UndoCommand — abstract base
# ---------------------------------------------------------------------------

class TestUndoCommand:

    def test_undo_raises_not_implemented(self):
        cmd = UndoCommand("test")
        with pytest.raises(NotImplementedError):
            cmd.undo(None)

    def test_redo_raises_not_implemented(self):
        cmd = UndoCommand("test")
        with pytest.raises(NotImplementedError):
            cmd.redo(None)

    def test_can_merge_false_by_default(self):
        cmd = UndoCommand("test")
        assert cmd.can_merge(UndoCommand("other")) is False

    def test_merge_raises_not_implemented(self):
        cmd = UndoCommand("test")
        with pytest.raises(NotImplementedError):
            cmd.merge(UndoCommand("other"))

    def test_description_stored(self):
        cmd = UndoCommand("my action")
        assert cmd.description == "my action"

    def test_timestamp_is_recent(self):
        t_before = time.monotonic()
        cmd = UndoCommand("t")
        t_after = time.monotonic()
        assert t_before <= cmd.timestamp <= t_after

    def test_repr_contains_class_and_description(self):
        cmd = UndoCommand("hello")
        assert "UndoCommand" in repr(cmd)
        assert "hello" in repr(cmd)


# ---------------------------------------------------------------------------
# ParameterValueCommand
# ---------------------------------------------------------------------------

class TestParameterValueCommand:

    def test_undo_sets_old_value(self, widget):
        cmd = ParameterValueCommand("radius", 5.0, 10.0)
        cmd.undo(widget)
        widget.logic.kernel_module.setParam.assert_called_once_with("radius", 5.0)
        widget._update_model_param_value.assert_called_once_with("radius", 5.0)

    def test_redo_sets_new_value(self, widget):
        cmd = ParameterValueCommand("radius", 5.0, 10.0)
        cmd.redo(widget)
        widget.logic.kernel_module.setParam.assert_called_once_with("radius", 10.0)
        widget._update_model_param_value.assert_called_once_with("radius", 10.0)

    def test_can_merge_same_param(self):
        cmd1 = ParameterValueCommand("radius", 1.0, 2.0)
        cmd2 = ParameterValueCommand("radius", 2.0, 3.0)
        assert cmd1.can_merge(cmd2) is True

    def test_cannot_merge_different_param(self):
        cmd1 = ParameterValueCommand("radius", 1.0, 2.0)
        cmd2 = ParameterValueCommand("length", 1.0, 2.0)
        assert cmd1.can_merge(cmd2) is False

    def test_cannot_merge_different_type(self):
        cmd1 = ParameterValueCommand("radius", 1.0, 2.0)
        assert cmd1.can_merge(UndoCommand("other")) is False

    def test_merge_spans_full_range(self):
        cmd1 = ParameterValueCommand("radius", 1.0, 2.0)
        cmd2 = ParameterValueCommand("radius", 2.0, 3.0)
        merged = cmd1.merge(cmd2)
        assert merged._old_val == 1.0
        assert merged._new_val == 3.0
        assert merged.param_name == "radius"

    def test_merge_preserves_earlier_timestamp(self):
        cmd1 = ParameterValueCommand("r", 1.0, 2.0)
        cmd2 = ParameterValueCommand("r", 2.0, 3.0)
        merged = cmd1.merge(cmd2)
        assert merged.timestamp == cmd1.timestamp

    def test_param_name_property(self):
        cmd = ParameterValueCommand("scale", 1.0, 2.0)
        assert cmd.param_name == "scale"

    def test_cannot_merge_stale_same_param_command(self):
        """Edits to the same parameter outside the coalescing window must not merge."""
        cmd1 = ParameterValueCommand("radius", 1.0, 2.0)
        cmd2 = ParameterValueCommand("radius", 2.0, 3.0)
        # Backdate cmd1 so the gap exceeds the coalescing window
        cmd1.timestamp = (
            cmd2.timestamp - ParameterValueCommand._COALESCE_WINDOW_SECONDS - 1.0
        )
        assert cmd1.can_merge(cmd2) is False


# ---------------------------------------------------------------------------
# ParameterMinMaxCommand
# ---------------------------------------------------------------------------

class TestParameterMinMaxCommand:

    def test_undo_restores_min(self, widget):
        widget.logic.kernel_module.details = {"radius": [None, 0.0, 100.0]}
        cmd = ParameterMinMaxCommand("radius", "min", 0.0, 5.0)
        cmd.undo(widget)
        assert widget.logic.kernel_module.details["radius"][1] == 0.0
        widget._update_model_param_limit.assert_called_once_with(
            "radius", "min", 0.0
        )

    def test_redo_applies_new_min(self, widget):
        widget.logic.kernel_module.details = {"radius": [None, 0.0, 100.0]}
        cmd = ParameterMinMaxCommand("radius", "min", 0.0, 5.0)
        cmd.redo(widget)
        assert widget.logic.kernel_module.details["radius"][1] == 5.0
        widget._update_model_param_limit.assert_called_once_with(
            "radius", "min", 5.0
        )

    def test_undo_restores_max(self, widget):
        widget.logic.kernel_module.details = {"length": [None, 0.0, 100.0]}
        cmd = ParameterMinMaxCommand("length", "max", 100.0, 200.0)
        cmd.undo(widget)
        assert widget.logic.kernel_module.details["length"][2] == 100.0

    def test_redo_applies_new_max(self, widget):
        widget.logic.kernel_module.details = {"length": [None, 0.0, 100.0]}
        cmd = ParameterMinMaxCommand("length", "max", 100.0, 200.0)
        cmd.redo(widget)
        assert widget.logic.kernel_module.details["length"][2] == 200.0

    def test_invalid_bound_raises(self):
        with pytest.raises(AssertionError):
            ParameterMinMaxCommand("r", "middle", 1.0, 2.0)


# ---------------------------------------------------------------------------
# ModelSelectionCommand
# ---------------------------------------------------------------------------

class TestModelSelectionCommand:

    def test_undo_restores_old_triple_and_params(self, widget):
        old_triple = ("Shape", "sphere", "None")
        new_triple = ("Shape", "cylinder", "None")
        cmd = ModelSelectionCommand(
            old_triple, new_triple, {"radius": 1.0}, {"length": 5.0}
        )
        cmd.undo(widget)
        widget._restore_model_selection.assert_called_once_with(
            old_triple, {"radius": 1.0}
        )

    def test_redo_restores_new_triple_and_params(self, widget):
        old_triple = ("Shape", "sphere", "None")
        new_triple = ("Shape", "cylinder", "None")
        cmd = ModelSelectionCommand(
            old_triple, new_triple, {"radius": 1.0}, {"length": 5.0}
        )
        cmd.redo(widget)
        widget._restore_model_selection.assert_called_once_with(
            new_triple, {"length": 5.0}
        )

    def test_params_are_deep_copied(self):
        params = {"radius": 5.0}
        cmd = ModelSelectionCommand(
            ("A", "B", "C"), ("D", "E", "F"), params, {}
        )
        params["radius"] = 999.0  # mutate original
        assert cmd._old_params["radius"] == 5.0  # snapshot unchanged

    def test_description_includes_new_model_name(self):
        cmd = ModelSelectionCommand(
            ("A", "sphere", "C"), ("A", "cylinder", "C"), {}, {}
        )
        assert "cylinder" in cmd.description


# ---------------------------------------------------------------------------
# FitOptionsCommand
# ---------------------------------------------------------------------------

class TestFitOptionsCommand:

    def test_undo_applies_old_options(self, widget):
        old = {"q_min": 0.01, "q_max": 0.5}
        new = {"q_min": 0.05, "q_max": 1.0}
        cmd = FitOptionsCommand(old, new)
        cmd.undo(widget)
        widget._apply_fit_options.assert_called_once_with(old)

    def test_redo_applies_new_options(self, widget):
        old = {"q_min": 0.01, "q_max": 0.5}
        new = {"q_min": 0.05, "q_max": 1.0}
        cmd = FitOptionsCommand(old, new)
        cmd.redo(widget)
        widget._apply_fit_options.assert_called_once_with(new)

    def test_options_are_deep_copied(self):
        opts = {"q_min": 0.01}
        cmd = FitOptionsCommand(opts, {})
        opts["q_min"] = 999.0
        assert cmd._old_options["q_min"] == 0.01


# ---------------------------------------------------------------------------
# SmearingOptionsCommand
# ---------------------------------------------------------------------------

class TestSmearingOptionsCommand:

    def test_undo_applies_old_state(self, widget):
        cmd = SmearingOptionsCommand({"type": "none"}, {"type": "pinhole"})
        cmd.undo(widget)
        widget._apply_smearing_state.assert_called_once_with({"type": "none"})

    def test_redo_applies_new_state(self, widget):
        cmd = SmearingOptionsCommand({"type": "none"}, {"type": "pinhole"})
        cmd.redo(widget)
        widget._apply_smearing_state.assert_called_once_with({"type": "pinhole"})

    def test_state_is_deep_copied(self):
        state = {"type": "none"}
        cmd = SmearingOptionsCommand(state, {})
        state["type"] = "changed"
        assert cmd._old_state["type"] == "none"


# ---------------------------------------------------------------------------
# CheckboxToggleCommand
# ---------------------------------------------------------------------------

class TestCheckboxToggleCommand:

    def test_undo_sets_old_bool(self, widget):
        widget.chkPolydispersity = MagicMock()
        cmd = CheckboxToggleCommand("chkPolydispersity", False, True)
        cmd.undo(widget)
        widget.chkPolydispersity.setChecked.assert_called_once_with(False)

    def test_redo_sets_new_bool(self, widget):
        widget.chkPolydispersity = MagicMock()
        cmd = CheckboxToggleCommand("chkPolydispersity", False, True)
        cmd.redo(widget)
        widget.chkPolydispersity.setChecked.assert_called_once_with(True)

    def test_description_includes_checkbox_id(self):
        cmd = CheckboxToggleCommand("chkMagnetism", False, True)
        assert "chkMagnetism" in cmd.description


# ---------------------------------------------------------------------------
# FitResultCommand
# ---------------------------------------------------------------------------

class TestFitResultCommand:

    def test_undo_restores_pre_fit_params(self, widget):
        cmd = FitResultCommand({"radius": 1.0}, {"radius": 2.5})
        cmd.undo(widget)
        widget._restore_parameter_values.assert_called_once_with({"radius": 1.0})

    def test_redo_restores_post_fit_params(self, widget):
        cmd = FitResultCommand({"radius": 1.0}, {"radius": 2.5})
        cmd.redo(widget)
        widget._restore_parameter_values.assert_called_once_with({"radius": 2.5})

    def test_params_are_deep_copied(self):
        old = {"radius": 1.0}
        cmd = FitResultCommand(old, {})
        old["radius"] = 999.0
        assert cmd._old_params["radius"] == 1.0

    def test_description_is_fit_result(self):
        cmd = FitResultCommand({}, {})
        assert cmd.description == "Fit result"


# ---------------------------------------------------------------------------
# CompoundCommand
# ---------------------------------------------------------------------------

class TestCompoundCommand:

    def test_undo_executes_in_reverse_order(self, widget):
        order = []
        cmd1 = MagicMock(spec=UndoCommand)
        cmd1.undo.side_effect = lambda w: order.append("cmd1")
        cmd2 = MagicMock(spec=UndoCommand)
        cmd2.undo.side_effect = lambda w: order.append("cmd2")
        CompoundCommand([cmd1, cmd2], "c").undo(widget)
        assert order == ["cmd2", "cmd1"]

    def test_redo_executes_in_forward_order(self, widget):
        order = []
        cmd1 = MagicMock(spec=UndoCommand)
        cmd1.redo.side_effect = lambda w: order.append("cmd1")
        cmd2 = MagicMock(spec=UndoCommand)
        cmd2.redo.side_effect = lambda w: order.append("cmd2")
        CompoundCommand([cmd1, cmd2], "c").redo(widget)
        assert order == ["cmd1", "cmd2"]

    def test_commands_property_returns_copy(self):
        cmd1 = MagicMock(spec=UndoCommand)
        compound = CompoundCommand([cmd1], "c")
        copy = compound.commands
        copy.append(MagicMock())
        assert len(compound.commands) == 1  # original unaffected

    def test_description_falls_back_to_first_command(self):
        cmd1 = MagicMock(spec=UndoCommand)
        cmd1.description = "Select model"
        compound = CompoundCommand([cmd1])
        assert compound.description == "Select model"

    def test_explicit_description_takes_precedence(self):
        compound = CompoundCommand([], "Override")
        assert compound.description == "Override"


# ---------------------------------------------------------------------------
# UndoStack — normal operation
# ---------------------------------------------------------------------------

def _make_cmd(description: str = "cmd") -> MagicMock:
    """Return a MagicMock UndoCommand that disallows coalescing."""
    cmd = MagicMock(spec=UndoCommand)
    cmd.can_merge.return_value = False
    cmd.description = description
    return cmd


class TestUndoStack:

    def test_initial_state_empty(self, stack):
        assert not stack.can_undo()
        assert not stack.can_redo()
        assert stack.undo_text() == "Undo"
        assert stack.redo_text() == "Redo"

    def test_push_enables_undo(self, stack):
        stack.push(_make_cmd())
        assert stack.can_undo()
        assert not stack.can_redo()

    def test_undo_moves_to_redo(self, stack, widget):
        stack.push(_make_cmd())
        stack.undo()
        assert not stack.can_undo()
        assert stack.can_redo()

    def test_redo_moves_back_to_undo(self, stack, widget):
        stack.push(_make_cmd())
        stack.undo()
        stack.redo()
        assert stack.can_undo()
        assert not stack.can_redo()

    def test_push_after_undo_clears_redo(self, stack, widget):
        stack.push(_make_cmd("a"))
        stack.undo()
        assert stack.can_redo()
        stack.push(_make_cmd("b"))
        assert not stack.can_redo()

    def test_undo_calls_cmd_undo_with_widget(self, stack, widget):
        cmd = _make_cmd()
        stack.push(cmd)
        stack.undo()
        cmd.undo.assert_called_once_with(widget)

    def test_redo_calls_cmd_redo_with_widget(self, stack, widget):
        cmd = _make_cmd()
        stack.push(cmd)
        stack.undo()
        stack.redo()
        cmd.redo.assert_called_once_with(widget)

    def test_stackChanged_emitted_on_push(self, stack):
        received = []
        stack.stackChanged.connect(lambda: received.append(1))
        stack.push(_make_cmd())
        assert len(received) == 1

    def test_stackChanged_emitted_on_undo(self, stack):
        stack.push(_make_cmd())
        received = []
        stack.stackChanged.connect(lambda: received.append(1))
        stack.undo()
        assert len(received) == 1

    def test_stackChanged_emitted_on_redo(self, stack):
        stack.push(_make_cmd())
        stack.undo()
        received = []
        stack.stackChanged.connect(lambda: received.append(1))
        stack.redo()
        assert len(received) == 1

    def test_stackChanged_emitted_on_clear(self, stack):
        stack.push(_make_cmd())
        received = []
        stack.stackChanged.connect(lambda: received.append(1))
        stack.clear()
        assert len(received) == 1

    def test_max_depth_drops_oldest_entries(self, stack):
        stack._max_depth = 3
        cmds = [_make_cmd(f"c{i}") for i in range(5)]
        for cmd in cmds:
            stack.push(cmd)
        assert len(stack._undo_stack) == 3
        # Three newest survive
        assert cmds[2] in stack._undo_stack
        assert cmds[3] in stack._undo_stack
        assert cmds[4] in stack._undo_stack
        # Two oldest are gone
        assert cmds[0] not in stack._undo_stack
        assert cmds[1] not in stack._undo_stack

    def test_clear_empties_both_stacks(self, stack, widget):
        stack.push(_make_cmd())
        stack.undo()
        stack.clear()
        assert not stack.can_undo()
        assert not stack.can_redo()

    def test_suppressed_prevents_push(self, stack):
        with stack.suppressed():
            stack.push(_make_cmd())
        assert not stack.can_undo()

    def test_suppressed_restores_previous_enabled_state(self, stack):
        stack.set_enabled(True)
        with stack.suppressed():
            assert not stack._enabled
        assert stack._enabled

    def test_suppressed_restores_false_if_was_false(self, stack):
        stack.set_enabled(False)
        with stack.suppressed():
            pass
        assert not stack._enabled  # restored to False

    def test_set_enabled_false_prevents_push(self, stack):
        stack.set_enabled(False)
        stack.push(_make_cmd())
        assert not stack.can_undo()

    def test_disabled_prevents_undo(self, stack, widget):
        """A disabled stack must not execute undo."""
        stack.push(_make_cmd())
        stack.set_enabled(False)
        stack.undo()
        assert stack.can_undo()   # command must still be on the undo stack
        assert not stack.can_redo()

    def test_disabled_prevents_redo(self, stack, widget):
        """A disabled stack must not execute redo."""
        stack.push(_make_cmd())
        stack.undo()
        stack.set_enabled(False)
        stack.redo()
        assert not stack.can_undo()  # nothing moved back
        assert stack.can_redo()      # command must still be on the redo stack

    def test_replaying_prevents_recursive_push(self, stack):
        """Commands pushed during undo replay must be silently dropped."""
        inner = _make_cmd("inner")

        def undo_side_effect(w):
            stack.push(inner)  # simulate handler firing during replay

        outer = _make_cmd("outer")
        outer.undo.side_effect = undo_side_effect
        stack.push(outer)
        stack.undo()
        # outer moved to redo; inner was blocked → undo stack empty
        assert not stack.can_undo()
        inner.undo.assert_not_called()

    def test_coalescing_merges_same_param_commands(self, stack):
        cmd1 = ParameterValueCommand("radius", 1.0, 2.0)
        cmd2 = ParameterValueCommand("radius", 2.0, 3.0)
        stack.push(cmd1)
        stack.push(cmd2)
        assert len(stack._undo_stack) == 1
        merged = stack._undo_stack[0]
        assert merged._old_val == 1.0
        assert merged._new_val == 3.0

    def test_no_coalescing_for_different_params(self, stack):
        stack.push(ParameterValueCommand("radius", 1.0, 2.0))
        stack.push(ParameterValueCommand("length", 1.0, 2.0))
        assert len(stack._undo_stack) == 2

    def test_undo_text_includes_description(self, stack):
        stack.push(_make_cmd("Change radius"))
        assert stack.undo_text() == "Undo Change radius"

    def test_redo_text_includes_description(self, stack, widget):
        stack.push(_make_cmd("Change radius"))
        stack.undo()
        assert stack.redo_text() == "Redo Change radius"

    def test_undo_noop_when_empty(self, stack):
        stack.undo()  # must not raise

    def test_redo_noop_when_empty(self, stack):
        stack.redo()  # must not raise

    def test_max_depth_read_from_config(self, qapp):
        """UndoStack reads UNDO_STACK_MAX_DEPTH from the SasView config."""
        from sas import config as sas_config
        assert hasattr(sas_config, "UNDO_STACK_MAX_DEPTH")
        widget = MagicMock()
        s = UndoStack(widget)
        assert s._max_depth == sas_config.UNDO_STACK_MAX_DEPTH

    def test_successful_undo_auto_snapshots_widget_state(self, stack, widget):
        """A successful undo must save _last_good_state from the widget."""
        widget._get_parameter_dict.return_value = {"scale": 1.0}
        stack.push(_make_cmd())
        assert stack._last_good_state is None
        stack.undo()
        assert stack._last_good_state == {"scale": 1.0}

    def test_successful_redo_auto_snapshots_widget_state(self, stack, widget):
        """A successful redo must save _last_good_state from the widget."""
        stack.push(_make_cmd())
        stack.undo()
        stack._last_good_state = None  # reset so we can detect the auto-save
        widget._get_parameter_dict.return_value = {"scale": 2.0}
        stack.redo()
        assert stack._last_good_state == {"scale": 2.0}

    def test_auto_snapshot_silent_if_no_get_parameter_dict(self, stack, widget):
        """Missing _get_parameter_dict on the widget must not raise."""
        widget._get_parameter_dict.side_effect = AttributeError("no such method")
        stack.push(_make_cmd())
        stack.undo()  # must not raise
        assert stack._last_good_state is None


# ---------------------------------------------------------------------------
# UndoStack — failure resilience
# ---------------------------------------------------------------------------

class TestUndoStackFailure:

    @pytest.fixture
    def failing_undo_cmd(self):
        cmd = _make_cmd("failing command")
        cmd.undo.side_effect = RuntimeError("simulated undo failure")
        return cmd

    @pytest.fixture
    def failing_redo_cmd(self):
        cmd = _make_cmd("failing command")
        cmd.redo.side_effect = RuntimeError("simulated redo failure")
        return cmd

    def test_undo_failure_logs_warning(
        self, stack, failing_undo_cmd, caplog
    ):
        stack.push(failing_undo_cmd)
        with caplog.at_level(
            logging.WARNING,
            logger="sas.qtgui.Perspectives.Fitting.UndoRedo",
        ):
            stack.undo()
        assert any("undo failed" in m.lower() for m in caplog.messages)

    def test_redo_failure_logs_warning(
        self, stack, widget, failing_redo_cmd, caplog
    ):
        good = _make_cmd("good")
        stack.push(good)
        stack.undo()
        # Replace redo stack entry with a failing one
        stack._redo_stack[-1] = failing_redo_cmd
        with caplog.at_level(
            logging.WARNING,
            logger="sas.qtgui.Perspectives.Fitting.UndoRedo",
        ):
            stack.redo()
        assert any("redo failed" in m.lower() for m in caplog.messages)

    def test_failure_increments_consecutive_counter(
        self, stack, failing_undo_cmd
    ):
        stack.push(failing_undo_cmd)
        stack.undo()
        assert stack._consecutive_failures == 1

    def test_undo_failure_preserves_undo_stack(self, stack, failing_undo_cmd):
        """A failing undo must leave the command on the undo stack."""
        stack.push(failing_undo_cmd)
        stack.undo()
        assert stack.can_undo()   # command still in undo history
        assert not stack.can_redo()  # nothing moved to redo

    def test_redo_failure_preserves_redo_stack(self, stack, widget, failing_redo_cmd):
        """A failing redo must leave the command on the redo stack."""
        stack.push(_make_cmd("good"))
        stack.undo()
        stack._redo_stack[-1] = failing_redo_cmd
        stack.redo()
        assert not stack.can_undo()  # nothing moved to undo
        assert stack.can_redo()      # command still in redo history

    def test_success_resets_consecutive_counter(self, stack, widget):
        stack._consecutive_failures = 5
        stack.push(_make_cmd())
        stack.undo()
        assert stack._consecutive_failures == 0

    def test_failure_emits_stackChanged(self, stack, failing_undo_cmd):
        stack.push(failing_undo_cmd)
        received = []
        stack.stackChanged.connect(lambda: received.append(1))
        stack.undo()
        assert len(received) == 1  # stackChanged fired even on failure

    def test_save_and_reset_to_last_good_state(self, stack, widget):
        stack.save_last_good_state({"radius": 5.0})
        stack.reset_to_last_good()
        widget._restore_parameter_values.assert_called_once_with({"radius": 5.0})

    def test_reset_without_snapshot_logs_warning(self, stack, caplog):
        with caplog.at_level(
            logging.WARNING,
            logger="sas.qtgui.Perspectives.Fitting.UndoRedo",
        ):
            stack.reset_to_last_good()
        assert any("no snapshot" in m.lower() for m in caplog.messages)

    def test_save_last_good_state_copies_dict(self, stack):
        state = {"radius": 1.0}
        stack.save_last_good_state(state)
        state["radius"] = 999.0
        assert stack._last_good_state["radius"] == 1.0

    def test_failure_dialog_shown(self, stack, failing_undo_cmd, mock_message_box):
        stack.push(failing_undo_cmd)
        stack.undo()
        mock_message_box.assert_called_once()

    def test_repeated_failures_offer_reset_button(
        self, stack, widget, mock_message_box
    ):
        """After 2 consecutive failures with a snapshot, reset button appears."""
        stack.save_last_good_state({"radius": 1.0})
        stack._consecutive_failures = 1  # pre-seed counter

        failing = _make_cmd("fail again")
        failing.undo.side_effect = RuntimeError("boom")
        stack.push(failing)
        stack.undo()

        # addButton called with "Reset to Last Good State"
        instance = mock_message_box.return_value
        button_labels = [
            call.args[0]
            for call in instance.addButton.call_args_list
            if call.args
        ]
        assert any("Reset" in label for label in button_labels)
