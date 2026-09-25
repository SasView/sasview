"""
Tests for WorkspaceManager: placement of workspace windows in the MDI area or detached.

Every transition is followed by delivering deferred deletions, because the
old container is disposed of with deleteLater and must not take the new
registration with it.
"""
from types import SimpleNamespace
from unittest import mock

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QMimeData, QPoint, QPointF, QRect, Qt, QTimer
from PySide6.QtGui import (
    QAction,
    QColor,
    QCursor,
    QDrag,
    QDragEnterEvent,
    QDragLeaveEvent,
    QDragMoveEvent,
    QDropEvent,
    QIcon,
    QMouseEvent,
    QPixmap,
    QStandardItemModel,
)
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMdiArea,
    QMenu,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)
from shiboken6 import isValid

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.MainWindow.WorkspaceManager import (
    ATTACH_TEXT,
    DETACH_TEXT,
    WORKSPACE_MIME,
    DetachableSubWindow,
    FloatingWindow,
    WorkspaceManager,
    workspace_manager_for,
)
from sas.qtgui.Plotting.BoxSum import BoxSum
from sas.qtgui.Plotting.Plotter import Plotter


def flush():
    """Process pending events, including deferred deletions."""
    for _ in range(3):
        QApplication.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


class Hosted(QWidget):
    """A hosted widget that counts close events and can refuse to close."""

    def __init__(self, allow_close=True, title="Hosted"):
        super().__init__()
        self.allow_close = allow_close
        self.close_events = 0
        self.editor = QLineEdit(self)
        QVBoxLayout(self).addWidget(self.editor)
        self.setWindowTitle(title)

    def closeEvent(self, event):
        self.close_events += 1
        if self.allow_close:
            event.accept()
        else:
            event.ignore()


class NestedLoopHosted(Hosted):
    """Runs a nested event loop in its close handler, like a confirmation dialog would."""

    def closeEvent(self, event):
        self.close_events += 1
        loop = QEventLoop()
        QTimer.singleShot(20, loop.quit)
        loop.exec()
        event.setAccepted(self.allow_close)


class HostedDialog(QDialog):
    """A dialog that notifies an owner from its close handler, like the slicer panels."""

    def __init__(self, on_close=None):
        super().__init__()
        self.on_close = on_close
        self.close_events = 0
        QVBoxLayout(self).addWidget(QLabel("dialog", self))

    def closeEvent(self, event):
        self.close_events += 1
        if self.on_close is not None:
            self.on_close(self)
        event.accept()


MODES = [pytest.param(False, id="attached"), pytest.param(True, id="detached")]


def mouse(widget, event_type, local, buttons=Qt.LeftButton):
    """Send a synthetic left-button mouse event to ``widget`` at ``local`` coordinates."""
    local = QPoint(local)
    event = QMouseEvent(event_type, QPointF(local), QPointF(widget.mapToGlobal(local)),
                        Qt.LeftButton, buttons, Qt.NoModifier)
    QApplication.sendEvent(widget, event)
    return event


def workspace_mime():
    mime = QMimeData()
    mime.setData(WORKSPACE_MIME, b"1")
    return mime


def deliver_drop(viewport, pos, mime=None):
    """Deliver a drag-enter followed by a drop at ``pos`` (viewport coordinates); returns the drop event."""
    mime = mime or workspace_mime()
    enter = QDragEnterEvent(pos, Qt.MoveAction, mime, Qt.LeftButton, Qt.NoModifier)
    QApplication.sendEvent(viewport, enter)
    drop = QDropEvent(QPointF(pos), Qt.MoveAction, mime, Qt.LeftButton, Qt.NoModifier)
    QApplication.sendEvent(viewport, drop)
    return drop


class WorkspaceManagerTest:

    @pytest.fixture(autouse=True)
    def env(self, qapp):
        window = QMainWindow()
        mdi = QMdiArea()
        window.setCentralWidget(mdi)
        window.resize(1000, 800)
        window.show()
        manager = WorkspaceManager(mdi, window)
        flush()
        yield SimpleNamespace(window=window, mdi=mdi, manager=manager)
        window.close()
        window.deleteLater()
        flush()

    @staticmethod
    def live_subwindows(env):
        return [s for s in env.mdi.subWindowList() if isValid(s) and s.widget() is not None]

    # ------------------------------------------------------------------
    # Placement
    # ------------------------------------------------------------------
    def testAddHostsInMdiArea(self, env):
        widget = Hosted()
        container = env.manager.add(widget)
        flush()
        assert isinstance(container, DetachableSubWindow)
        assert env.manager.container_of(widget) is container
        assert env.manager.is_hosted(widget)
        assert not env.manager.is_detached(widget)
        assert env.manager.hosted_widgets() == [widget]
        assert env.mdi.subWindowList() == [container]
        assert widget.isVisible()

    def testSubWindowShowsMainWindowIconLikeQMdiArea(self, env):
        '''Attached windows draw the application icon, as subwindows created by Qt do'''
        red = QPixmap(32, 32)
        red.fill(QColor("red"))
        env.window.setWindowIcon(QIcon(red))

        def red_title_bar_pixels(sub):
            sub.setGeometry(QRect(10, 10, 300, 200))
            flush()
            image = sub.grab().toImage()
            return sum(1 for x in range(40) for y in range(30)
                       if (c := image.pixelColor(x, y)).red() > 200 and c.green() < 60 and c.blue() < 60)

        reference = env.mdi.addSubWindow(QWidget())
        reference.show()
        expected = red_title_bar_pixels(reference)
        assert expected > 0

        hosted = env.manager.add(Hosted())
        assert red_title_bar_pixels(hosted) == expected

    @staticmethod
    def table_widget():
        widget = QWidget()
        QVBoxLayout(widget).addWidget(QTableWidget(20, 6))
        return widget

    @pytest.fixture
    def stylesheet(self, qapp):
        '''SasView applies an application-wide stylesheet, which changes when subwindows are polished'''
        qapp.setStyleSheet("* {font-size: 11pt;}")
        yield
        qapp.setStyleSheet("")

    def testNewSubWindowTakesQtInitialSizeUnderStylesheet(self, env, stylesheet):
        '''A new attached window gets the size QMdiArea.addSubWindow would give it'''
        reference = env.mdi.addSubWindow(self.table_widget())
        reference.show()
        flush()
        assert reference.width() > 200 and reference.height() > 150

        hosted = env.manager.add(self.table_widget())
        flush()
        assert hosted.size() == reference.size()

    def testWindowsAddedBeforeWorkspaceIsShownAreSizedOnShow(self, qapp, stylesheet):
        '''Perspectives and panels are added at start-up, before the main window is visible'''
        window = QMainWindow()
        mdi = QMdiArea()
        window.setCentralWidget(mdi)
        window.resize(1000, 800)
        manager = WorkspaceManager(mdi, window)
        try:
            hosted = manager.add(self.table_widget())
            hidden = manager.add(self.table_widget(), visible=False)
            window.show()
            flush()
            reference = mdi.addSubWindow(self.table_widget())
            reference.show()
            flush()
            assert hosted.size() == reference.size()

            # A panel kept hidden at start-up is sized when it is first shown
            manager.set_visible(hidden.hostedWidget(), True)
            flush()
            assert hidden.size() == reference.size()
        finally:
            window.close()
            window.deleteLater()
            flush()

    def testNewSubWindowStaysMaximisedWhenWorkspaceIsMaximised(self, env, stylesheet):
        first = env.manager.add(self.table_widget())
        first.showMaximized()
        flush()
        second = env.manager.add(self.table_widget())
        flush()
        assert second.isMaximized()
        assert second.size() == env.mdi.viewport().size()

    def testAddDetachedCreatesFloatingWindow(self, env):
        widget = Hosted()
        container = env.manager.add(widget, detached=True)
        flush()
        assert isinstance(container, FloatingWindow)
        assert container.isWindow()
        assert container.parentWidget() is env.window
        assert env.mdi.subWindowList() == []
        assert widget.isVisible()

    def testAddingHostedWidgetAgainIsNoOp(self, env):
        widget = Hosted()
        container = env.manager.add(widget)
        assert env.manager.add(widget, detached=True) is container
        assert not env.manager.is_detached(widget)

    # ------------------------------------------------------------------
    # Drag and drop
    # ------------------------------------------------------------------
    @staticmethod
    def title_label_point(sub):
        return QPoint(sub.width() // 2, 10)

    def testTitleBarHitTestExcludesButtonsAndBody(self, env):
        sub = env.manager.add(Hosted())
        sub.setGeometry(QRect(20, 20, 400, 300))
        flush()
        assert sub.isOnTitleBarLabel(self.title_label_point(sub))
        assert not sub.isOnTitleBarLabel(QPoint(sub.width() - 10, 10))   # close button
        assert not sub.isOnTitleBarLabel(QPoint(8, 10))                   # system menu
        assert not sub.isOnTitleBarLabel(QPoint(100, 150))                # body

    def testTitleBarDragOutsideWorkspaceDetachesAtCursor(self, env, monkeypatch):
        # Keep the workspace small so a point below it is still on the (offscreen) screen
        env.window.resize(400, 300)
        widget = Hosted()
        sub = env.manager.add(widget)
        sub.setGeometry(QRect(20, 20, 200, 150))
        flush()
        outside = env.manager.viewportGlobalRect().bottomLeft() + QPoint(150, 30)
        drags = []
        monkeypatch.setattr(QDrag, "exec", lambda self, *args: drags.append(self.mimeData().formats()) or Qt.IgnoreAction)
        monkeypatch.setattr(QCursor, "pos", staticmethod(lambda: outside))

        grab = self.title_label_point(sub)
        mouse(sub, QEvent.MouseButtonPress, grab)
        # Still inside the workspace: no drag yet
        mouse(sub, QEvent.MouseMove, grab + QPoint(30, 30))
        assert drags == []
        # Beyond the workspace edge: drag starts and ends outside
        mouse(sub, QEvent.MouseMove, QPoint(-60, 10))
        flush()

        assert drags == [[WORKSPACE_MIME]]
        assert env.manager.is_detached(widget)
        host = env.manager.container_of(widget)
        assert host.isVisible()
        assert host.geometry().topLeft() == outside - grab
        # The pre-drag position is remembered for re-attaching
        assert env.manager.last_placement(widget).mdi_geometry == QRect(20, 20, 200, 150)

    def testTitleBarDragDroppedInWorkspaceMovesWindow(self, env, monkeypatch):
        widget = Hosted()
        sub = env.manager.add(widget)
        sub.setGeometry(QRect(20, 20, 400, 300))
        flush()
        grab = self.title_label_point(sub)
        drop_at = QPoint(300, 200)

        def fake_exec(drag, *args):
            deliver_drop(env.mdi.viewport(), drop_at)
            return Qt.MoveAction

        monkeypatch.setattr(QDrag, "exec", fake_exec)
        mouse(sub, QEvent.MouseButtonPress, grab)
        mouse(sub, QEvent.MouseMove, QPoint(-60, 10))
        flush()

        assert not env.manager.is_detached(widget)
        assert env.manager.container_of(widget) is sub
        assert sub.pos() == drop_at - grab
        assert not env.manager._drop_indicator.isVisible()

    def testDragCancelledInsideWorkspaceChangesNothing(self, env, monkeypatch):
        widget = Hosted()
        sub = env.manager.add(widget)
        sub.setGeometry(QRect(20, 20, 400, 300))
        flush()
        monkeypatch.setattr(QDrag, "exec", lambda self, *args: Qt.IgnoreAction)
        inside = env.manager.viewportGlobalRect().center()
        monkeypatch.setattr(QCursor, "pos", staticmethod(lambda: inside))

        mouse(sub, QEvent.MouseButtonPress, self.title_label_point(sub))
        mouse(sub, QEvent.MouseMove, QPoint(-60, 10))
        flush()
        assert env.manager.container_of(widget) is sub
        assert sub.geometry() == QRect(20, 20, 400, 300)

    def testPressOnCloseButtonNeverStartsDrag(self, env, monkeypatch):
        widget = Hosted()
        sub = env.manager.add(widget)
        sub.setGeometry(QRect(20, 20, 400, 300))
        flush()
        drags = []
        monkeypatch.setattr(QDrag, "exec", lambda self, *args: drags.append(1) or Qt.IgnoreAction)
        mouse(sub, QEvent.MouseButtonPress, QPoint(sub.width() - 10, 10))
        mouse(sub, QEvent.MouseMove, QPoint(-60, 10))
        flush()
        assert drags == []

    def testHeaderDragDroppedInWorkspaceAttachesAtDropPoint(self, env, monkeypatch):
        widget = Hosted()
        host = env.manager.add(widget, detached=True)
        flush()
        header = host.header
        grab = QPoint(header.width() // 2, header.height() // 2)
        hotspot = header.mapTo(host, grab)
        drop_at = QPoint(250, 180)

        def fake_exec(drag, *args):
            assert drag.mimeData().hasFormat(WORKSPACE_MIME)
            deliver_drop(env.mdi.viewport(), drop_at)
            return Qt.MoveAction

        monkeypatch.setattr(QDrag, "exec", fake_exec)
        mouse(header, QEvent.MouseButtonPress, grab)
        mouse(header, QEvent.MouseMove, grab + QPoint(40, 40))
        flush()

        assert not env.manager.is_detached(widget)
        sub = env.manager.container_of(widget)
        assert isinstance(sub, DetachableSubWindow)
        assert sub.pos() == drop_at - hotspot
        assert not isValid(host)

    def testHeaderDragCancelledKeepsFloatingWindow(self, env, monkeypatch):
        widget = Hosted()
        host = env.manager.add(widget, detached=True)
        host.setGeometry(QRect(100, 100, 400, 300))
        flush()
        monkeypatch.setattr(QDrag, "exec", lambda self, *args: Qt.IgnoreAction)
        outside = env.manager.viewportGlobalRect().topLeft() + QPoint(-150, 100)
        monkeypatch.setattr(QCursor, "pos", staticmethod(lambda: outside))

        grab = QPoint(host.header.width() // 2, host.header.height() // 2)
        mouse(host.header, QEvent.MouseButtonPress, grab)
        mouse(host.header, QEvent.MouseMove, grab + QPoint(40, 40))
        flush()
        assert env.manager.container_of(widget) is host
        assert host.geometry() == QRect(100, 100, 400, 300)

    def testHeaderDoubleClickAttaches(self, env):
        widget = Hosted()
        host = env.manager.add(widget, detached=True)
        flush()
        mouse(host.header, QEvent.MouseButtonDblClick, QPoint(10, 5))
        flush()
        assert not env.manager.is_detached(widget)
        assert isinstance(env.manager.container_of(widget), DetachableSubWindow)

    def testDropIndicatorFollowsWorkspaceDragOnly(self, env):
        widget = Hosted()
        host = env.manager.add(widget, detached=True)
        flush()
        viewport = env.mdi.viewport()
        indicator = env.manager._drop_indicator
        hotspot = QPoint(30, 8)

        # A drag from elsewhere (for example a file) is left alone
        env.manager._drag = None
        foreign = QMimeData()
        foreign.setText("not a window")
        enter = QDragEnterEvent(QPoint(50, 50), Qt.CopyAction, foreign, Qt.LeftButton, Qt.NoModifier)
        QApplication.sendEvent(viewport, enter)
        assert not indicator.isVisible()

        # A workspace window drag shows where the window will land
        from sas.qtgui.MainWindow.WorkspaceManager import _DragState
        env.manager._drag = _DragState(widget, host, hotspot, host.size())
        # Drag events do not own their mime data; keep it alive for their lifetime
        mime = workspace_mime()
        try:
            enter = QDragEnterEvent(QPoint(100, 100), Qt.MoveAction, mime, Qt.LeftButton, Qt.NoModifier)
            QApplication.sendEvent(viewport, enter)
            assert enter.isAccepted()
            move = QDragMoveEvent(QPoint(140, 120), Qt.MoveAction, mime, Qt.LeftButton, Qt.NoModifier)
            QApplication.sendEvent(viewport, move)
            assert indicator.isVisible()
            assert indicator.geometry() == QRect(QPoint(140, 120) - hotspot, host.size())
            QApplication.sendEvent(viewport, QDragLeaveEvent())
            assert not indicator.isVisible()
        finally:
            env.manager._drag = None
            env.manager._pending_drop = None

    def testRepeatedDetachAttachRoundTrip(self, env):
        widget = Hosted()
        sub = env.manager.add(widget)
        sub.setGeometry(QRect(20, 30, 400, 300))
        flush()
        mdi_geometry = QRect(sub.geometry())

        for _ in range(3):
            content = widget.size()
            host = env.manager.detach(widget)
            flush()
            # The old container is gone and did not take the new registration with it
            assert env.manager.container_of(widget) is host
            assert isValid(host)
            assert self.live_subwindows(env) == []
            assert env.window.findChildren(DetachableSubWindow) == []
            assert widget.parentWidget() is host
            assert widget.isVisible()
            assert widget.size() == content

            sub = env.manager.attach(widget)
            flush()
            assert env.manager.container_of(widget) is sub
            assert env.mdi.subWindowList() == [sub]
            assert env.window.findChildren(FloatingWindow) == []
            assert sub.geometry() == mdi_geometry
            assert widget.isVisible()

        assert widget.close_events == 0
        assert env.manager.hosted_widgets() == [widget]

    def testMaximizedSubWindowKeepsNormalGeometryAcrossTransfer(self, env):
        widget = Hosted()
        sub = env.manager.add(widget)
        sub.setGeometry(QRect(71, 83, 401, 303))
        flush()
        sub.showMaximized()
        flush()

        env.manager.detach(widget)
        flush()
        sub = env.manager.attach(widget)
        flush()
        sub.showNormal()
        flush()
        assert sub.geometry() == QRect(71, 83, 401, 303)

    def testMaximizedFloatingWindowKeepsNormalGeometryAcrossTransfer(self, env):
        widget = Hosted()
        env.manager.add(widget)
        host = env.manager.detach(widget)
        host.setGeometry(QRect(100, 120, 500, 400))
        flush()
        host.showMaximized()
        flush()

        env.manager.attach(widget)
        flush()
        host = env.manager.detach(widget)
        flush()
        host.showNormal()
        flush()
        assert host.geometry() == QRect(100, 120, 500, 400)

    def testFloatingGeometryIsRestored(self, env):
        widget = Hosted()
        env.manager.add(widget)
        host = env.manager.detach(widget)
        host.setGeometry(QRect(100, 120, 500, 400))
        flush()
        env.manager.attach(widget)
        flush()
        host = env.manager.detach(widget)
        flush()
        assert host.geometry() == QRect(100, 120, 500, 400)

    def testDetachAndAttachAreIdempotent(self, env):
        widget = Hosted()
        sub = env.manager.add(widget)
        assert env.manager.attach(widget) is sub
        host = env.manager.detach(widget)
        flush()
        assert env.manager.detach(widget) is host
        flush()
        assert env.manager.container_of(widget) is host

    def testUnhostedWidgetRaises(self, env):
        with pytest.raises(KeyError):
            env.manager.detach(Hosted())
        with pytest.raises(KeyError):
            env.manager.attach(Hosted())
        assert env.manager.toggle(Hosted()) is None

    def testDetachingHiddenPanelKeepsItHidden(self, env):
        widget = Hosted()
        env.manager.add(widget, visible=False)
        host = env.manager.detach(widget)
        flush()
        assert host.isHidden()
        env.manager.set_visible(widget, True)
        flush()
        assert host.isVisible()
        assert widget.isVisible()

    def testTitleFollowsHostedWidget(self, env):
        widget = Hosted(title="Graph1")
        host = env.manager.add(widget, detached=True)
        widget.setWindowTitle("Graph1 renamed")
        flush()
        assert host.windowTitle() == "Graph1 renamed"
        assert host.titleLabel.text() == "Graph1 renamed"

    def testSystemMenuDetachAndAttachButton(self, env):
        widget = Hosted()
        sub = env.manager.add(widget)
        detach_actions = [a for a in sub.systemMenu().actions() if a.text() == DETACH_TEXT]
        assert len(detach_actions) == 1
        detach_actions[0].trigger()
        flush()
        host = env.manager.container_of(widget)
        assert isinstance(host, FloatingWindow)
        assert host.attachButton.text() == ATTACH_TEXT

        host.attachButton.click()
        flush()
        assert isinstance(env.manager.container_of(widget), DetachableSubWindow)

    def testFloatingWindowRegistersNoShortcut(self, env):
        host = env.manager.add(Hosted(), detached=True)
        shortcuts = [a for a in host.findChildren(QAction) if not a.shortcut().isEmpty()]
        assert shortcuts == []

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    @pytest.mark.parametrize("detached", MODES)
    def testClosingAcceptingWidgetDisposesContainer(self, env, detached):
        widget = Hosted()
        container = env.manager.add(widget, detached=detached)
        closed = []
        env.manager.widgetClosed.connect(closed.append)
        flush()

        assert env.manager.close(widget)
        flush()
        assert widget.close_events == 1
        assert closed == [widget]
        assert not env.manager.is_hosted(widget)
        assert env.manager.last_placement(widget) is None
        assert not isValid(container)
        assert self.live_subwindows(env) == []

    @pytest.mark.parametrize("detached", MODES)
    def testRefusingWidgetMinimisesContainerRepeatedly(self, env, detached):
        widget = Hosted(allow_close=False)
        container = env.manager.add(widget, detached=detached)
        flush()

        assert not env.manager.close(widget)
        flush()
        assert container.isMinimized()
        assert env.manager.container_of(widget) is container

        env.manager.activate(widget)
        flush()
        assert not container.isMinimized()

        assert not container.close()
        flush()
        assert container.isMinimized()
        assert widget.close_events == 2
        assert isValid(widget)

    @pytest.mark.parametrize("detached", MODES)
    def testRefusedCloseIsNotBypassedByImmediateRequest(self, env, detached):
        widget = Hosted(allow_close=False)
        container = env.manager.add(widget, detached=detached)
        flush()

        # No event-loop turn between the refusal and the next request
        assert widget.close() is False
        assert env.manager.close(widget) is False
        flush()
        assert widget.close_events == 2
        assert isValid(widget)
        assert env.manager.container_of(widget) is container
        assert isValid(container)

    @pytest.mark.parametrize("detached", MODES)
    def testAcceptedCloseWithNestedEventLoopDisposesContainer(self, env, detached):
        widget = NestedLoopHosted()
        container = env.manager.add(widget, detached=detached)
        flush()

        assert widget.close() is True
        flush()
        assert widget.close_events == 1
        assert not env.manager.is_hosted(widget)
        assert not isValid(container)
        assert self.live_subwindows(env) == []

    @pytest.mark.parametrize("detached", MODES)
    def testRefusalWithNestedEventLoopKeepsContainer(self, env, detached):
        widget = NestedLoopHosted(allow_close=False)
        container = env.manager.add(widget, detached=detached)
        flush()

        assert widget.close() is False
        flush()
        assert env.manager.container_of(widget) is container
        assert not container.isHidden()
        assert env.manager.close(widget) is False
        flush()
        assert isValid(widget) and isValid(container)

    @pytest.mark.parametrize("detached", MODES)
    def testDestroyedWidgetRetiresContainer(self, env, detached):
        widget = Hosted()
        container = env.manager.add(widget, detached=detached)
        env.manager.activate(widget)
        flush()

        widget.deleteLater()
        flush()
        assert not isValid(container)
        assert env.manager.hosted_widgets(include_hidden=True) == []
        assert env.manager.active_widget() is None
        assert env.window.findChildren(FloatingWindow) == []
        assert self.live_subwindows(env) == []

    @pytest.mark.parametrize("detached", MODES)
    def testDirectChildCloseDisposesContainer(self, env, detached):
        widget = Hosted()
        container = env.manager.add(widget, detached=detached)
        flush()

        widget.close()
        flush()
        assert widget.close_events == 1
        assert not env.manager.is_hosted(widget)
        assert not isValid(container)
        assert self.live_subwindows(env) == []

    @pytest.mark.parametrize("detached", MODES)
    def testOwnerClosingDuringChildCloseRunsHandlerOnce(self, env, detached):
        closed_by_owner = []

        def owner_cleanup(dialog):
            closed_by_owner.append(dialog)
            env.manager.close(dialog)

        dialog = HostedDialog(on_close=owner_cleanup)
        container = env.manager.add(dialog, detached=detached)
        flush()

        dialog.close()
        flush()
        assert dialog.close_events == 1
        assert closed_by_owner == [dialog]
        assert not env.manager.is_hosted(dialog)
        assert not isValid(container)

    @pytest.mark.parametrize("detached", MODES)
    def testDialogRejectHidesContainer(self, env, detached):
        dialog = HostedDialog()
        container = env.manager.add(dialog, detached=detached)
        flush()

        dialog.reject()
        flush()
        assert container.isHidden()
        assert env.manager.is_hosted(dialog)
        assert dialog.close_events == 0
        assert env.manager.hosted_widgets() == []

        env.manager.set_visible(dialog, True)
        flush()
        assert container.isVisible()
        assert dialog.isVisible()

    @pytest.mark.parametrize("detached", MODES)
    def testRemoveKeepsWidgetAndPlacement(self, env, detached):
        widget = Hosted()
        container = env.manager.add(widget, detached=detached)
        flush()

        env.manager.remove(widget)
        flush()
        assert isValid(widget)
        assert widget.parentWidget() is None
        assert widget.isHidden()
        assert widget.close_events == 0
        assert not env.manager.is_hosted(widget)
        assert not isValid(container)
        placement = env.manager.last_placement(widget)
        assert placement is not None and placement.detached == detached

        container = env.manager.add(widget, detached=placement.detached)
        flush()
        assert env.manager.is_detached(widget) == detached
        assert widget.isVisible()

    def testForgetDropsPlacement(self, env):
        widget = Hosted()
        env.manager.add(widget)
        env.manager.forget(widget)
        flush()
        assert env.manager.last_placement(widget) is None
        assert env.manager.hosted_widgets(include_hidden=True) == []

    def testMinimizeWorksInBothModes(self, env):
        attached, detached = Hosted(), Hosted()
        env.manager.add(attached)
        env.manager.add(detached, detached=True)
        flush()
        env.manager.minimize(attached)
        env.manager.minimize(detached)
        flush()
        assert env.manager.container_of(attached).isMinimized()
        assert env.manager.container_of(detached).isMinimized()
        assert env.manager.hosted_widgets() == [attached, detached]

    def testCloseAllFloating(self, env):
        accepting = Hosted()
        refusing = Hosted(allow_close=False)
        attached = Hosted()
        env.manager.add(accepting, detached=True)
        env.manager.add(refusing, detached=True)
        env.manager.add(attached)
        flush()

        env.manager.close_all_floating()
        flush()
        assert not env.manager.is_hosted(accepting)
        assert not env.manager.is_hosted(refusing)
        assert isValid(refusing)
        assert env.manager.is_hosted(attached)
        assert env.window.findChildren(FloatingWindow) == []

    # ------------------------------------------------------------------
    # Queries and activation
    # ------------------------------------------------------------------
    def testHostedWidgetsOrderAndVisibility(self, env):
        first, hidden, third = Hosted(), Hosted(), Hosted()
        env.manager.add(first)
        env.manager.add(hidden, visible=False)
        env.manager.add(third, detached=True)
        flush()
        assert env.manager.hosted_widgets() == [first, third]
        assert env.manager.hosted_widgets(include_hidden=True) == [first, hidden, third]

        env.manager.detach(first)
        env.manager.attach(third)
        flush()
        assert env.manager.hosted_widgets() == [first, third]

    def testActiveWidgetTracking(self, env):
        floating_a, floating_b, attached = Hosted(), Hosted(), Hosted()
        env.manager.add(floating_a, detached=True)
        env.manager.add(floating_b, detached=True)
        env.manager.add(attached)
        flush()
        changes = []
        env.manager.activeWidgetChanged.connect(changes.append)

        for widget in (floating_a, floating_b, attached):
            env.manager.activate(widget)
            flush()
            assert env.manager.active_widget() is widget

        # Focus moving into a child editor of a hosted widget resolves to that widget
        env.manager._onFocusChanged(None, floating_a.editor)
        assert env.manager.active_widget() is floating_a
        count = len(changes)
        env.manager._onFocusChanged(None, floating_a.editor)
        assert len(changes) == count

        # Opening a menu does not change the target of Window menu actions
        menu = QMenu()
        env.manager._onFocusChanged(None, menu)
        assert env.manager.active_widget() is floating_a

        # Focus elsewhere, such as the Data Explorer, keeps the last active window
        env.manager._onFocusChanged(None, QLineEdit())
        assert env.manager.active_widget() is floating_a

        # A hidden window is not a target
        env.manager.set_visible(floating_a, False)
        assert env.manager.active_widget() is None

    @pytest.mark.parametrize("detached", MODES)
    def testActiveNotificationFollowsVisibility(self, env, detached):
        widget = HostedDialog()
        env.manager.add(widget, detached=detached)
        env.manager.activate(widget)
        flush()
        changes = []
        env.manager.activeWidgetChanged.connect(changes.append)

        env.manager.set_visible(widget, False)
        assert changes == [None]
        env.manager.set_visible(widget, True)
        assert changes == [None, widget]

        # The same widget activated again while already valid emits nothing
        env.manager.activate(widget)
        assert changes == [None, widget]

        # Dismissal by the widget itself behaves the same way
        widget.reject()
        flush()
        assert changes == [None, widget, None]
        env.manager.activate(widget)
        assert changes == [None, widget, None, widget]

    def testActiveWidgetClearedOnClose(self, env):
        widget = Hosted()
        env.manager.add(widget, detached=True)
        env.manager.activate(widget)
        env.manager.close(widget)
        flush()
        assert env.manager.active_widget() is None

    # ------------------------------------------------------------------
    # Integration with plots and helpers
    # ------------------------------------------------------------------
    def testWorkspaceManagerLookup(self, env):
        gui_manager = SimpleNamespace(workspace_manager=env.manager)
        data_explorer = SimpleNamespace(parent=gui_manager)
        plot = SimpleNamespace(manager=data_explorer)
        assert workspace_manager_for(plot) is env.manager
        assert workspace_manager_for(mock.MagicMock()) is None
        assert workspace_manager_for(SimpleNamespace(manager=None)) is None
        assert workspace_manager_for(QWidget()) is None

    def testPlotContextMenuOnlyForHostedPlots(self, env):
        communicator = mock.MagicMock()
        data_explorer = SimpleNamespace(parent=SimpleNamespace(workspace_manager=env.manager),
                                        communicator=communicator)
        plot = Plotter(data_explorer, quickplot=True)

        plot.createContextMenuQuick()
        plot.addWorkspaceActionsToContextMenu()
        texts = [a.text() for a in plot.contextMenu.actions()]
        assert DETACH_TEXT not in texts and ATTACH_TEXT not in texts

        env.manager.add(plot)
        plot.createContextMenuQuick()
        plot.addWorkspaceActionsToContextMenu()
        texts = [a.text() for a in plot.contextMenu.actions()]
        assert DETACH_TEXT in texts
        # The entry sits before Help
        assert texts.index(DETACH_TEXT) < texts.index("Help")

        env.manager.detach(plot)
        flush()
        plot.createContextMenuQuick()
        plot.addWorkspaceActionsToContextMenu()
        assert ATTACH_TEXT in [a.text() for a in plot.contextMenu.actions()]
        env.manager.close(plot)
        flush()

    @pytest.mark.parametrize("detached", MODES)
    def testPlotCloseNotifiesListenersOnce(self, env, detached, monkeypatch):
        communicator = mock.MagicMock()
        monkeypatch.setattr(GuiUtils, "communicator", communicator)
        data_explorer = SimpleNamespace(parent=SimpleNamespace(workspace_manager=env.manager))
        plot = Plotter(data_explorer, quickplot=True)
        env.manager.add(plot, detached=detached)
        flush()

        plot.close()
        flush()
        communicator.activeGraphsSignal.emit.assert_called_once_with([plot, True])
        assert not env.manager.is_hosted(plot)

    @pytest.mark.parametrize("route", ["button", "escape", "close"])
    def testBoxSumNotifiesOwnerOnceForEveryDismissal(self, env, route):
        box = BoxSum(model=QStandardItemModel())
        notifications = []
        box.closeWidgetSignal.connect(lambda: notifications.append(1))
        container = env.manager.add(box, detached=True)
        flush()

        if route == "button":
            box.buttonBox.button(box.buttonBox.StandardButton.Close).click()
        elif route == "escape":
            box.reject()
        else:
            container.close()
        flush()
        assert notifications == [1]
        assert not env.manager.is_hosted(box)
