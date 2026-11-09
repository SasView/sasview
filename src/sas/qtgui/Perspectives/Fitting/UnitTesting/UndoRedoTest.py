"""Unit tests for the undo/redo history and the fit page's document commands.

The document commands (``model/commands.py``) are tested on a Qt-free document;
the shared ``UndoStack`` on a mock widget.

Test organisation:
    TestUndoCommand              — abstract base behaviour
    TestSetParameterCommand      — value / bound / dispersion change, coalescing
    TestSettingCommands          — options, smearing, flags
    TestSnapshotCommand          — whole-state change, unrecorded fields carried over
    TestApplyFitResultCommand    — fit values, errors cleared (R-2)
    TestHistoryExecute           — apply-then-record
    TestCompoundCommand          — atomic group, ordering
    TestUndoStack                — push / undo / redo / depth / suppression
    TestUndoStackFailure         — failure dialog, reset_to_last_good
"""
import contextlib
import copy
import logging
import time
from unittest.mock import MagicMock

import pytest

from sas.qtgui.Perspectives.Fitting.Constraint import Constraint
from sas.qtgui.Perspectives.Fitting.model.commands import (
    ApplyFitResultCommand,
    SetFlagCommand,
    SetOptionsCommand,
    SetParameterCommand,
    SetSmearingCommand,
    SnapshotCommand,
)
from sas.qtgui.Perspectives.Fitting.model.events import Origin
from sas.qtgui.Perspectives.Fitting.model.history import History
from sas.qtgui.Perspectives.Fitting.model.parameters import Smearing
from sas.qtgui.Perspectives.Fitting.UnitTesting.document_fixtures import d1, edit, page
from sas.qtgui.Perspectives.UndoRedo import (
    CompoundCommand,
    UndoCommand,
    UndoStack,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def mock_message_box(monkeypatch):
    """Suppress all QMessageBox dialogs for the entire test module."""
    mock = MagicMock()
    monkeypatch.setattr(
        "sas.qtgui.Perspectives.UndoRedo.QtWidgets.QMessageBox", mock
    )
    return mock


@pytest.fixture
def widget():
    """Minimal mock that satisfies the widget protocol used by commands."""
    w = MagicMock()
    # the kernel's details must support real dict operations for MinMax tests
    w.kernel().details = {}
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
# Document commands (model/commands.py, Phase 5)
# ---------------------------------------------------------------------------

class _Target:
    """The part of FitPageController a command uses, over a Qt-free document."""

    def __init__(self, doc):
        self.document = doc
        self.replaying = False
        self.origins = []
        self.theory = 0
        self.restored = []

    @contextlib.contextmanager
    def transaction(self, origin, recalculate=False):
        self.origins.append(origin)
        with self.document.transaction(origin) as tx:
            yield tx
        self.theory += recalculate and origin in (Origin.UNDO, Origin.REDO)

    def redo_origin(self):
        return Origin.REDO if self.replaying else Origin.USER

    def restore(self, snapshot, origin):
        self.restored.append(origin)
        self.document.restore_undo_state(snapshot, origin)


@pytest.fixture
def target():
    return _Target(page("Cylinder", "cylinder", data=[d1()]))


class TestSetParameterCommand:

    def test_redo_applies_and_undo_restores(self, target):
        cmd = SetParameterCommand("radius", {"value": 20.0}, {"value": 33.0})
        cmd.redo(target)
        assert target.document.parameters["radius"].value == 33.0
        cmd.undo(target)
        assert target.document.parameters["radius"].value == 20.0
        assert target.origins == [Origin.USER, Origin.UNDO]

    def test_replayed_redo_has_the_redo_origin_and_recalculates(self, target):
        cmd = SetParameterCommand("radius", {"value": 20.0}, {"value": 33.0})
        cmd.redo(target)
        assert target.theory == 0          # a value edit does not recalculate (R-1)
        target.replaying = True
        cmd.undo(target)
        cmd.redo(target)
        assert target.origins[-1] is Origin.REDO and target.theory == 2

    def test_bounds_and_dispersion_with_fit(self, target):
        cmd = SetParameterCommand("radius", {"min": 0.0, "max": float("inf")}, {"min": 1.0, "max": 50.0})
        cmd.redo(target)
        p = target.document.parameters["radius"]
        assert (p.min, p.max) == (1.0, 50.0)
        cmd.undo(target)
        assert (p.min, p.max) == (0.0, float("inf"))

    def test_merges_later_edit_of_the_same_fields(self):
        first = SetParameterCommand("radius", {"value": 1.0}, {"value": 2.0})
        second = SetParameterCommand("radius", {"value": 2.0}, {"value": 3.0})
        assert first.can_merge(second)
        merged = first.merge(second)
        assert (merged.old, merged.new, merged.timestamp) == ({"value": 1.0}, {"value": 3.0}, second.timestamp)

    def test_does_not_merge_other_fields_keys_or_stale_edits(self):
        first = SetParameterCommand("radius", {"value": 1.0}, {"value": 2.0})
        assert not first.can_merge(SetParameterCommand("radius", {"min": 0.0}, {"min": 1.0}))
        assert not first.can_merge(SetParameterCommand("length", {"value": 1.0}, {"value": 2.0}))
        stale = SetParameterCommand("radius", {"value": 2.0}, {"value": 3.0})
        stale.timestamp = first.timestamp + SetParameterCommand.COALESCE_WINDOW_SECONDS + 1
        assert not first.can_merge(stale)

    def test_old_and_new_are_copies(self):
        new = {"value": 2.0}
        cmd = SetParameterCommand("radius", {"value": 1.0}, new)
        new["value"] = 9.0
        assert cmd.new == {"value": 2.0}


class TestSettingCommands:

    def test_options_round_trip_and_recalculate_on_undo(self, target):
        old = copy.copy(target.document.options)
        new = copy.copy(old)
        new.qmin = 0.01
        cmd = SetOptionsCommand(old, new)
        cmd.redo(target)
        assert target.document.options.qmin == 0.01
        cmd.undo(target)
        assert target.document.options == old and target.theory == 1

    def test_smearing_round_trip(self, target):
        old = copy.copy(target.document.smearing)
        cmd = SetSmearingCommand(old, Smearing("Custom Pinhole Smear", "Low", 1.0, 2.0))
        cmd.redo(target)
        assert target.document.smearing.d_up == 2.0
        cmd.undo(target)
        assert target.document.smearing == old

    def test_flag_round_trip_does_not_request_theory(self, target):
        cmd = SetFlagCommand("polydispersity", False, True)
        cmd.redo(target)
        assert target.document.flags.polydispersity
        cmd.undo(target)
        assert not target.document.flags.polydispersity and target.theory == 0
        assert cmd.description == "Toggle polydispersity"


class TestSnapshotCommand:

    def test_undo_and_redo_restore_the_snapshots(self, target):
        doc = target.document
        old = doc.snapshot()
        edit(doc, "radius", value=33.0)
        cmd = SnapshotCommand("Select model", old, doc.snapshot())
        cmd.undo(target)
        assert doc.parameters["radius"].value == 20.0
        cmd.redo(target)
        assert doc.parameters["radius"].value == 33.0
        assert target.restored == [Origin.UNDO, Origin.USER]

    def test_fit_flags_and_constraints_set_after_the_command_survive_undo_and_redo(self, target):
        """They have no commands, so redo re-applies them on top of the new state (§3.7)."""
        doc = target.document
        old = doc.snapshot()
        edit(doc, "radius", value=33.0)
        cmd = SnapshotCommand("Paste", old, doc.snapshot())
        with doc.transaction(Origin.USER) as tx:
            tx.set_parameter("length", fit=True)
            tx.set_constraint("length", Constraint(param="length", func="2*M1.radius"))
        cmd.undo(target)
        assert not doc.parameters["length"].fit
        cmd.redo(target)
        assert doc.parameters["length"].fit and doc.parameters["length"].constraint.func == "2*M1.radius"


class TestApplyFitResultCommand:

    def test_undo_and_redo_set_the_values_and_clear_the_errors(self, target):
        """Register R-2."""
        doc = target.document
        edit(doc, "radius", value=25.5, error=0.75)
        cmd = ApplyFitResultCommand({"radius": 20.0}, {"radius": 25.5})
        cmd.undo(target)
        assert (doc.parameters["radius"].value, doc.parameters["radius"].error) == (20.0, None)
        edit(doc, "radius", error=0.75)
        cmd.redo(target)
        assert (doc.parameters["radius"].value, doc.parameters["radius"].error) == (25.5, None)


class TestHistoryExecute:

    def test_execute_applies_then_records_once(self, target):
        history = History(target=target)
        history.execute(SetParameterCommand("radius", {"value": 20.0}, {"value": 33.0}))
        assert target.document.parameters["radius"].value == 33.0
        assert len(history._undo_stack) == 1
        history.undo()
        assert target.document.parameters["radius"].value == 20.0

    def test_execute_during_replay_raises(self, target):
        history = History(target=target)

        class Reentrant(UndoCommand):
            def undo(self, t):
                history.execute(SetParameterCommand("radius", {"value": 1.0}, {"value": 2.0}))

            def redo(self, t):
                pass

        history.push_applied(Reentrant("bad"))
        history.undo()          # the failure is reported, the command stays
        assert history.can_undo()


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

    def test_stackChanged_emitted_on_set_enabled(self, stack):
        """set_enabled must emit stackChanged so UI actions refresh."""
        received = []
        stack.stackChanged.connect(lambda: received.append(1))
        stack.set_enabled(False)
        assert len(received) == 1
        stack.set_enabled(True)
        assert len(received) == 2

    def test_can_undo_false_when_disabled(self, stack):
        """can_undo must return False when the stack is disabled."""
        stack.push(_make_cmd())
        assert stack.can_undo()
        stack.set_enabled(False)
        assert not stack.can_undo()
        # Re-enable: can_undo should return True again
        stack.set_enabled(True)
        assert stack.can_undo()

    def test_can_redo_false_when_disabled(self, stack, widget):
        """can_redo must return False when the stack is disabled."""
        stack.push(_make_cmd())
        stack.undo()
        assert stack.can_redo()
        stack.set_enabled(False)
        assert not stack.can_redo()
        stack.set_enabled(True)
        assert stack.can_redo()

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
        # Command still on internal stack, but can_undo() reports False while disabled
        assert len(stack._undo_stack) == 1
        assert not stack.can_undo()
        assert not stack.can_redo()

    def test_disabled_prevents_redo(self, stack, widget):
        """A disabled stack must not execute redo."""
        stack.push(_make_cmd())
        stack.undo()
        stack.set_enabled(False)
        stack.redo()
        # Command still on internal redo stack, but can_redo() reports False while disabled
        assert not stack.can_undo()
        assert not stack.can_redo()
        assert len(stack._redo_stack) == 1

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
        stack.push(SetParameterCommand("radius", {"value": 1.0}, {"value": 2.0}))
        stack.push(SetParameterCommand("radius", {"value": 2.0}, {"value": 3.0}))
        assert len(stack._undo_stack) == 1
        merged = stack._undo_stack[0]
        assert (merged.old, merged.new) == ({"value": 1.0}, {"value": 3.0})

    def test_no_coalescing_for_different_params(self, stack):
        stack.push(SetParameterCommand("radius", {"value": 1.0}, {"value": 2.0}))
        stack.push(SetParameterCommand("length", {"value": 1.0}, {"value": 2.0}))
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
            logger="sas.qtgui.Perspectives.UndoRedo",
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
            logger="sas.qtgui.Perspectives.UndoRedo",
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
            logger="sas.qtgui.Perspectives.UndoRedo",
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
