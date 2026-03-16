import pytest
from unittest.mock import MagicMock
from unittest.mock import patch

from sas.qtgui.MainWindow.GuiManager import GuiManager


def _make_manager():
    """Construct a lightweight GuiManager instance for unit testing internals."""
    manager = object.__new__(GuiManager)

    workspace = MagicMock()
    workspace.actionUndo = MagicMock()
    workspace.actionRedo = MagicMock()

    manager._workspace = workspace
    manager._current_perspective = None
    manager._connected_undo_stack = None
    manager._connected_tabbed_perspective = None

    return manager


class TestGuiManagerUndoRedoPhase3:

    def test_action_undo_dispatches_to_active_stack(self):
        manager = _make_manager()
        stack = MagicMock()
        perspective = MagicMock()
        perspective.undo_stack = stack
        manager._current_perspective = perspective

        manager.actionUndo()

        stack.undo.assert_called_once_with()

    def test_action_redo_dispatches_to_active_stack(self):
        manager = _make_manager()
        stack = MagicMock()
        perspective = MagicMock()
        perspective.undo_stack = stack
        manager._current_perspective = perspective

        manager.actionRedo()

        stack.redo.assert_called_once_with()

    def test_action_undo_no_stack_is_noop(self):
        manager = _make_manager()
        manager._current_perspective = MagicMock(undo_stack=None)

        # Should not raise and should not call undo on a missing stack.
        manager.actionUndo()

    def test_update_actions_disabled_when_no_active_stack(self):
        manager = _make_manager()
        manager._current_perspective = MagicMock(undo_stack=None)

        manager._update_undo_redo_actions()

        manager._workspace.actionUndo.setEnabled.assert_called_with(False)
        manager._workspace.actionRedo.setEnabled.assert_called_with(False)
        manager._workspace.actionUndo.setToolTip.assert_called_with("Undo")
        manager._workspace.actionRedo.setToolTip.assert_called_with("Redo")

    def test_update_actions_uses_stack_state_and_labels(self):
        manager = _make_manager()
        stack = MagicMock()
        stack.can_undo.return_value = True
        stack.can_redo.return_value = False
        stack.undo_text.return_value = "Undo Change radius"
        stack.redo_text.return_value = "Redo Change radius"
        manager._current_perspective = MagicMock(undo_stack=stack)

        manager._update_undo_redo_actions()

        manager._workspace.actionUndo.setEnabled.assert_called_with(True)
        manager._workspace.actionRedo.setEnabled.assert_called_with(False)
        manager._workspace.actionUndo.setToolTip.assert_called_with("Undo Change radius")
        manager._workspace.actionRedo.setToolTip.assert_called_with("Redo Change radius")

    def test_connect_hooks_binds_current_tab_and_stack_signals(self):
        manager = _make_manager()

        stack_signal = MagicMock()
        stack = MagicMock()
        stack.stackChanged = stack_signal

        tab_signal = MagicMock()
        perspective = MagicMock()
        perspective.currentChanged = tab_signal
        perspective.undo_stack = stack
        manager._current_perspective = perspective

        manager._connect_undo_redo_hooks()

        tab_signal.connect.assert_called_once()
        stack_signal.connect.assert_called_once()
        assert manager._connected_tabbed_perspective is perspective
        assert manager._connected_undo_stack is stack

    def test_disconnect_hooks_unbinds_connected_signals(self):
        manager = _make_manager()

        stack_signal = MagicMock()
        stack = MagicMock()
        stack.stackChanged = stack_signal

        tab_signal = MagicMock()
        perspective = MagicMock()
        perspective.currentChanged = tab_signal

        manager._connected_undo_stack = stack
        manager._connected_tabbed_perspective = perspective

        manager._disconnect_undo_redo_hooks()

        stack_signal.disconnect.assert_called_once()
        tab_signal.disconnect.assert_called_once()
        assert manager._connected_undo_stack is None
        assert manager._connected_tabbed_perspective is None

    def test_tab_changed_rewires_hooks(self):
        manager = _make_manager()
        with patch.object(manager, "_disconnect_undo_redo_hooks") as disconnect_spy, \
             patch.object(manager, "_connect_undo_redo_hooks") as connect_spy:

            manager._on_perspective_tab_changed(1)

            disconnect_spy.assert_called_once_with()
            connect_spy.assert_called_once_with()

    # -- Additional Phase 3 coverage --

    def test_action_redo_no_stack_is_noop(self):
        """actionRedo should not raise when no stack is available."""
        manager = _make_manager()
        manager._current_perspective = MagicMock(undo_stack=None)
        manager.actionRedo()  # must not raise

    def test_action_undo_no_perspective_is_noop(self):
        """actionUndo should be safe when no perspective is active."""
        manager = _make_manager()
        manager._current_perspective = None
        manager.actionUndo()  # must not raise

    def test_action_redo_no_perspective_is_noop(self):
        """actionRedo should be safe when no perspective is active."""
        manager = _make_manager()
        manager._current_perspective = None
        manager.actionRedo()  # must not raise

    def test_update_actions_disabled_when_no_perspective(self):
        """With no perspective active, both actions must be disabled."""
        manager = _make_manager()
        manager._current_perspective = None

        manager._update_undo_redo_actions()

        manager._workspace.actionUndo.setEnabled.assert_called_with(False)
        manager._workspace.actionRedo.setEnabled.assert_called_with(False)

    def test_connect_hooks_skips_tab_signal_for_non_tabbed_perspective(self):
        """Perspectives without currentChanged should only wire the stack signal."""
        manager = _make_manager()

        stack_signal = MagicMock()
        stack = MagicMock()
        stack.stackChanged = stack_signal

        perspective = MagicMock(spec=[])  # no attributes by default
        perspective.undo_stack = stack
        manager._current_perspective = perspective

        manager._connect_undo_redo_hooks()

        stack_signal.connect.assert_called_once()
        assert manager._connected_undo_stack is stack
        assert manager._connected_tabbed_perspective is None

    def test_connect_hooks_no_stack_still_updates_actions(self):
        """Even without a stack, connect should call _update_undo_redo_actions."""
        manager = _make_manager()
        manager._current_perspective = MagicMock(undo_stack=None)

        manager._connect_undo_redo_hooks()

        # Actions should be disabled since there's no stack
        manager._workspace.actionUndo.setEnabled.assert_called_with(False)
        manager._workspace.actionRedo.setEnabled.assert_called_with(False)

    def test_disconnect_hooks_noop_when_nothing_connected(self):
        """Disconnecting with no prior connection should not raise."""
        manager = _make_manager()
        manager._connected_undo_stack = None
        manager._connected_tabbed_perspective = None
        manager._disconnect_undo_redo_hooks()  # must not raise

    def test_disconnect_hooks_tolerates_runtime_error(self):
        """Disconnecting a signal that was already disconnected is handled gracefully."""
        manager = _make_manager()
        stack = MagicMock()
        stack.stackChanged.disconnect.side_effect = RuntimeError("already disconnected")
        manager._connected_undo_stack = stack
        manager._connected_tabbed_perspective = None

        manager._disconnect_undo_redo_hooks()  # must not raise

        assert manager._connected_undo_stack is None

    def test_active_undo_stack_returns_none_without_perspective(self):
        manager = _make_manager()
        manager._current_perspective = None
        assert manager._active_undo_stack() is None

    def test_active_undo_stack_returns_perspective_stack(self):
        manager = _make_manager()
        stack = MagicMock()
        manager._current_perspective = MagicMock(undo_stack=stack)
        assert manager._active_undo_stack() is stack

    def test_active_undo_stack_handles_missing_undo_stack_attr(self):
        """A perspective without undo_stack attribute should return None."""
        manager = _make_manager()
        perspective = MagicMock(spec=[])  # no attributes
        manager._current_perspective = perspective
        assert manager._active_undo_stack() is None

    def test_tab_switch_updates_stack_connection(self):
        """Switching tabs should connect the new tab's stack for signal updates."""
        manager = _make_manager()

        old_stack = MagicMock()
        old_stack.stackChanged = MagicMock()
        manager._connected_undo_stack = old_stack
        manager._connected_tabbed_perspective = None

        new_stack = MagicMock()
        new_stack.stackChanged = MagicMock()
        new_stack.can_undo.return_value = True
        new_stack.can_redo.return_value = False
        new_stack.undo_text.return_value = "Undo Change radius"
        new_stack.redo_text.return_value = "Redo"

        manager._current_perspective = MagicMock(undo_stack=new_stack)

        # Simulate what _on_perspective_tab_changed does
        manager._disconnect_undo_redo_hooks()
        manager._connect_undo_redo_hooks()

        old_stack.stackChanged.disconnect.assert_called_once()
        new_stack.stackChanged.connect.assert_called_once()
        assert manager._connected_undo_stack is new_stack
        manager._workspace.actionUndo.setEnabled.assert_called_with(True)
