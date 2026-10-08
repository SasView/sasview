"""
GuiManager behaviour that depends on the WorkspaceManager.

A GuiManager is built without its constructor, on a main window that uses the
real SasView menu definitions. This exercises the real menu actions, shortcut,
perspective placement decision and quit path without loading perspectives or
calculators.
"""
from types import SimpleNamespace
from unittest import mock

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLineEdit, QMainWindow, QMdiArea, QVBoxLayout, QWidget

import sas.qtgui.MainWindow.GuiManager as GuiManagerModule
from sas import config
from sas.qtgui.MainWindow.GuiManager import GuiManager
from sas.qtgui.MainWindow.UI.MainWindowUI import Ui_SasView
from sas.qtgui.MainWindow.WorkspaceManager import FloatingWindow, WorkspaceManager
from sas.qtgui.Utilities.GuiUtils import Communicate


def flush():
    for _ in range(3):
        QApplication.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


class MainWindow(QMainWindow, Ui_SasView):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.workspace = QMdiArea(self)
        self.setCentralWidget(self.workspace)
        self.workspace_manager = WorkspaceManager(self.workspace, self)


class Hosted(QWidget):
    def __init__(self, allow_close=True):
        super().__init__()
        self.allow_close = allow_close
        self.editor = QLineEdit(self)
        QVBoxLayout(self).addWidget(self.editor)

    def closeEvent(self, event):
        event.setAccepted(self.allow_close)


class FakePerspective(Hosted):
    supports_reports = False
    supports_copy = False
    supports_copy_latex = False
    supports_copy_excel = False
    supports_paste = False
    supports_fitting_menu = False

    def __init__(self, name):
        super().__init__(allow_close=False)
        self.name = name

    def isSerializable(self):
        return False

    def setClosable(self, value=True):
        self.allow_close = value


class GuiManagerWorkspaceTest:

    @pytest.fixture
    def gui(self, qapp):
        window = MainWindow()
        window.resize(1000, 800)
        window.show()
        gui = GuiManager.__new__(GuiManager)
        gui._workspace = gui._parent = window
        gui.communicator = Communicate()
        gui._current_perspective = None
        gui.loadedPerspectives = {}
        gui._connected_undo_stack = None
        gui._connected_tabbed_perspective = None
        gui.addTriggers()
        flush()
        yield gui
        window.close()
        window.deleteLater()
        flush()

    @staticmethod
    def perspectives(gui, *names):
        gui.loadedPerspectives = {name: FakePerspective(name) for name in names}
        return [gui.loadedPerspectives[name] for name in names]

    def testPerspectivePreferenceAppliesOnFirstPresentationOnly(self, gui, monkeypatch):
        manager = gui.workspace_manager
        a, b, c = self.perspectives(gui, "A", "B", "C")
        monkeypatch.setattr(config, "OPEN_PERSPECTIVE_DETACHED", False)

        gui.perspectiveChanged("A")
        flush()
        assert gui.perspective() is a and not manager.is_detached(a)

        # The user detaches A, switches away and back: A returns detached
        manager.detach(a)
        gui.perspectiveChanged("B")
        flush()
        assert not manager.is_hosted(a) and not manager.is_detached(b)
        gui.perspectiveChanged("A")
        flush()
        assert manager.is_detached(a)

        # Turning the preference on does not move perspectives already shown...
        monkeypatch.setattr(config, "OPEN_PERSPECTIVE_DETACHED", True)
        gui.perspectiveChanged("B")
        flush()
        assert not manager.is_detached(b)
        # ...but applies to one shown for the first time
        gui.perspectiveChanged("C")
        flush()
        assert manager.is_detached(c)

        # Turning it off again does not move C back
        monkeypatch.setattr(config, "OPEN_PERSPECTIVE_DETACHED", False)
        gui.perspectiveChanged("A")
        gui.perspectiveChanged("C")
        flush()
        assert manager.is_detached(c)

    def testDetachShortcutFromKeyboard(self, gui):
        manager = gui.workspace_manager
        widget = Hosted()
        manager.add(widget)
        manager.activate(widget)
        flush()
        transitions = []
        manager.widgetDetached.connect(lambda w: transitions.append("detached"))
        manager.widgetAttached.connect(lambda w: transitions.append("attached"))

        widget.editor.setFocus()
        QTest.keyClick(widget.editor, Qt.Key_D, Qt.ControlModifier | Qt.ShiftModifier)
        flush()
        assert transitions == ["detached"]
        assert manager.is_detached(widget)

        # From a child editor inside the floating window: exactly one transition back
        manager.activate(widget)
        widget.editor.setFocus()
        QTest.keyClick(widget.editor, Qt.Key_D, Qt.ControlModifier | Qt.ShiftModifier)
        flush()
        assert transitions == ["detached", "attached"]
        assert not manager.is_detached(widget)

    def testDetachActionFollowsActiveWindowVisibility(self, gui):
        manager = gui.workspace_manager
        action = gui._workspace.actionDetachWindow
        widget = Hosted()
        manager.add(widget, detached=True)
        manager.activate(widget)
        flush()
        assert action.isEnabled()
        assert action.text() == "Attach Window to Workspace"

        # No Window menu is opened in between: the action must follow notifications
        manager.set_visible(widget, False)
        assert not action.isEnabled()
        manager.set_visible(widget, True)
        manager.activate(widget)
        assert action.isEnabled()

        manager.attach(widget)
        flush()
        assert action.text() == "Detach Window from Workspace"

    def testNextAndPreviousIncludeDetachedAndSkipHidden(self, gui):
        manager = gui.workspace_manager
        first, hidden, detached = Hosted(), Hosted(), Hosted()
        manager.add(first)
        manager.add(hidden, visible=False)
        manager.add(detached, detached=True)
        flush()
        manager.activate(first)
        flush()
        assert manager.active_widget() is first

        # Window activation is asynchronous; process it after each step
        gui._workspace.actionNext.trigger()
        flush()
        assert manager.active_widget() is detached
        gui._workspace.actionNext.trigger()
        flush()
        assert manager.active_widget() is first
        gui._workspace.actionPrevious.trigger()
        flush()
        assert manager.active_widget() is detached
        assert manager.container_of(hidden).isHidden()

    @pytest.mark.parametrize("confirmed", [False, True], ids=["cancelled", "accepted"])
    def testQuitWithMixedWindows(self, gui, monkeypatch, confirmed):
        manager = gui.workspace_manager
        plot = Hosted()
        perspective = FakePerspective("Fitting")
        attached = Hosted()
        manager.add(plot, detached=True)
        manager.add(perspective, detached=True)
        manager.add(attached)
        flush()

        monkeypatch.setattr(GuiManagerModule, "hidable_dialog",
                            lambda *args, **kwargs: SimpleNamespace(result=confirmed, ask_again=True))
        monkeypatch.setattr(GuiManagerModule, "reactor", mock.MagicMock())
        monkeypatch.setattr(config, "SHOW_EXIT_MESSAGE", True)
        gui.saveCustomConfig = mock.MagicMock()

        assert gui.quitApplication() is confirmed
        flush()

        if confirmed:
            assert gui._workspace.findChildren(FloatingWindow) == []
            assert not manager.is_hosted(plot)
            # A perspective that refuses to close is taken out of its window, not destroyed
            assert not manager.is_hosted(perspective)
            assert perspective.parentWidget() is None
            gui.saveCustomConfig.assert_called_once()
        else:
            assert manager.is_detached(plot) and manager.is_detached(perspective)
            assert len(gui._workspace.findChildren(FloatingWindow)) == 2
            gui.saveCustomConfig.assert_not_called()
        assert manager.is_hosted(attached) and not manager.is_detached(attached)
