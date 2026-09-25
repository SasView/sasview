"""
Placement of workspace windows: inside the MDI area or detached as top-level windows.

The :class:`WorkspaceManager` is the single owner of the containers that host
perspectives, plots and helper panels. A hosted widget lives either in a
:class:`DetachableSubWindow` inside the main window's ``QMdiArea`` or in a
:class:`FloatingWindow`, a top-level window that can be moved to another
monitor. The widget itself is never re-created when it moves between the two,
so its state, models and signal connections are preserved.

Application code should not create, close or inspect ``QMdiSubWindow`` objects
directly. It should call :meth:`WorkspaceManager.add`, :meth:`~WorkspaceManager.close`,
:meth:`~WorkspaceManager.remove`, :meth:`~WorkspaceManager.set_visible`,
:meth:`~WorkspaceManager.minimize` and :meth:`~WorkspaceManager.activate`.

Lifecycle rules
---------------
* Closing a container forwards the close request to the hosted widget. If the
  widget refuses (for example a perspective that is not closable), the
  container stays open and is minimised instead.
* If the hosted widget closes itself (``widget.close()``, a dialog button,
  Escape) and accepts, the container is disposed of as well, so no empty
  frame remains. Whether the widget accepted is read from its close event,
  never inferred from timing.
* If the hosted widget merely hides itself (``QDialog.reject``, ``hide()``),
  the container is hidden and can be shown again with ``set_visible``.
* :meth:`~WorkspaceManager.remove` takes the widget out of its container without
  closing it. This is used when switching perspectives.
* Close notifications from hosted widgets (for example ``closeWidgetSignal``)
  are completion notices. Their receivers should clear references, not ask the
  manager to close the widget again.

Drag and drop
-------------
Dragging a subwindow's title bar out of the workspace starts a Qt drag showing a
thumbnail of the window; releasing it outside the workspace detaches the widget
at the cursor. Dragging the header strip of a floating window onto the workspace
attaches it where it is dropped; double-clicking the header attaches it too. The
drag itself never moves widgets between containers. The container that started
the drag applies the outcome once ``QDrag.exec`` has returned, so no container is
destroyed while its own event handler is running.

Geometry
--------
Each placement remembers its own normal (not minimised or maximised) geometry.
A widget returns to the rectangle it last had in the workspace, or as a
detached window. The first time it enters a placement, it keeps its content size.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import partial

from PySide6.QtCore import QEvent, QMimeData, QObject, QPoint, QRect, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QCursor, QDrag, QGuiApplication, QMouseEvent
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMdiArea,
    QMdiSubWindow,
    QMenu,
    QMenuBar,
    QRubberBand,
    QStyle,
    QStyleOptionTitleBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from shiboken6 import isValid

DETACH_TEXT = "Detach from Workspace"
ATTACH_TEXT = "Attach to Workspace"
# Mime type of a workspace window being dragged between the workspace and the desktop
WORKSPACE_MIME = "application/x-sasview-workspace-window"
# Largest thumbnail shown while dragging
_DRAG_PIXMAP_MAX = QSize(320, 240)

_MIN_MAX = Qt.WindowMinimized | Qt.WindowMaximized


@dataclass
class Placement:
    """Session-only record of where a hosted widget was last shown."""
    detached: bool = False
    mdi_geometry: QRect | None = None
    floating_geometry: QRect | None = None


@dataclass
class _DragState:
    """The workspace window currently being dragged."""
    widget: QWidget
    container: QWidget
    hotspot: QPoint      # grab point, in container coordinates
    size: QSize          # container size, for the drop indicator


class _HostedWidgetWatcher(QObject):
    """
    Event filter installed on a hosted widget by its container.

    A ``Close`` event is delivered to the widget from inside the filter, so the
    widget's own answer (``event.isAccepted()``) is known as soon as its handler
    returns, even if the handler runs a nested event loop. An explicit hide that
    is not part of an accepted close (``HideToParent`` after ``reject()`` or
    ``hide()``) is a dismissal. A hide caused by a parent being hidden is not an
    explicit hide and is ignored.
    """

    def __init__(self, container: _HostMixin):
        super().__init__(container)
        self._container = container
        # True while the hosted widget's close handler is running
        self.dispatching = False

    def eventFilter(self, obj, event):
        container = self._container
        event_type = event.type()
        if event_type == QEvent.Close:
            if container._suppress_child_close:
                # The widget has already closed. Let the container's base class
                # finish without running the widget's close handler a second time.
                event.accept()
                return True
            self.dispatching = True
            try:
                obj.event(event)
            finally:
                self.dispatching = False
            if event.isAccepted() and not container._forwarding_close:
                container._onHostedWidgetClosed()
            # Qt reads the result from the event; the handler must not run again
            return True
        if event_type == QEvent.HideToParent:
            if not (self.dispatching or container._forwarding_close or container._releasing
                    or container._closed or container._hosted_widget_closed):
                container._onHostedWidgetDismissed()
        elif event_type == QEvent.WindowTitleChange:
            container._onHostedWidgetTitleChanged(obj.windowTitle())
        return False


class _HostMixin:
    """Behaviour shared by both container types. Not a QObject on its own."""

    def _initHost(self, manager: WorkspaceManager):
        self._manager = manager
        self._watcher = _HostedWidgetWatcher(self)
        self._forwarding_close = False
        self._suppress_child_close = False
        self._releasing = False
        self._closed = False
        self._hosted_widget_closed = False
        self._normal_geometry: QRect | None = None
        self.setAttribute(Qt.WA_DeleteOnClose)

    # To be provided by subclasses
    def hostedWidget(self) -> QWidget | None:
        raise NotImplementedError

    def _takeHostedWidget(self) -> QWidget | None:
        raise NotImplementedError

    def releaseWidget(self) -> QWidget | None:
        """Take the hosted widget out without closing it. The widget becomes parentless and hidden."""
        widget = self.hostedWidget()
        if widget is None:
            return None
        self._releasing = True
        try:
            widget.removeEventFilter(self._watcher)
            return self._takeHostedWidget()
        finally:
            self._releasing = False

    def lastNormalGeometry(self) -> QRect:
        """The geometry the container had when it was last neither minimised nor maximised."""
        if self._normal_geometry is not None:
            return QRect(self._normal_geometry)
        return QRect(self.geometry())

    def _trackNormalGeometry(self):
        # Qt sets the minimised/maximised state before it changes the geometry
        if not self.windowState() & _MIN_MAX:
            self._normal_geometry = QRect(self.geometry())

    def _watch(self, widget: QWidget):
        widget.installEventFilter(self._watcher)

    def _onHostedWidgetClosed(self):
        """The hosted widget accepted a close it started itself."""
        widget = self.hostedWidget()
        self._hosted_widget_closed = True
        if widget is not None:
            self._manager._onWidgetClosed(widget, self)
        self.hide()
        # Dispose of the container once Qt has finished closing the widget
        QTimer.singleShot(0, self, self.close)

    def _onHostedWidgetDismissed(self):
        self.hide()
        self._manager._notifyActive()

    def _onHostedWidgetTitleChanged(self, title: str):
        pass

    def _forwardClose(self, event) -> bool:
        """
        Forward a close request to the hosted widget.
        Returns True if the container may close.
        """
        widget = self.hostedWidget()
        if widget is None or self._hosted_widget_closed:
            return True
        if self._watcher.dispatching:
            # The widget is closing right now; the container follows if it accepts
            event.ignore()
            return False
        self._forwarding_close = True
        try:
            accepted = widget.close()
        finally:
            self._forwarding_close = False
        if not accepted:
            event.ignore()
            if self.isVisible() and not self.isMinimized():
                self.showMinimized()
        return accepted

    def _finishClose(self, event):
        if not event.isAccepted():
            return
        widget = self.hostedWidget()
        self._closed = True
        if widget is not None:
            self._manager._onWidgetClosed(widget, self)


class DetachableSubWindow(QMdiSubWindow, _HostMixin):
    """MDI container with a detach entry in its system (title-bar icon) menu."""

    def __init__(self, manager: WorkspaceManager, parent=None):
        QMdiSubWindow.__init__(self, parent)
        self._initHost(manager)
        menu = self.systemMenu()
        if menu is not None:
            self._detach_action = QAction(DETACH_TEXT, self)
            self._detach_action.setObjectName("actionDetachSubWindow")
            self._detach_action.triggered.connect(self._requestDetach)
            first = menu.actions()[0] if menu.actions() else None
            menu.insertAction(first, self._detach_action)
            if first is not None:
                menu.insertSeparator(first)

    def hostWidget(self, widget: QWidget):
        self.setWidget(widget)
        self._watch(widget)
        self.setObjectName(f"{widget.objectName()}_subwindow")

    def hostedWidget(self):
        return self.widget()

    # --- tear-off by dragging the title bar out of the workspace ---------
    def isOnTitleBarLabel(self, pos: QPoint) -> bool:
        """True if ``pos`` (in subwindow coordinates) is on the title bar, but not on one of its buttons."""
        option = QStyleOptionTitleBar()
        option.initFrom(self)
        height = self.style().pixelMetric(QStyle.PM_TitleBarHeight, option, self)
        option.rect = QRect(0, 0, self.width(), height)
        option.titleBarFlags = self.windowFlags()
        if not option.rect.contains(pos):
            return False
        control = self.style().hitTestComplexControl(QStyle.CC_TitleBar, option, pos, self)
        return control == QStyle.SC_TitleBarLabel

    def mousePressEvent(self, event):
        self._tear_off_origin = None
        if event.button() == Qt.LeftButton and self.isOnTitleBarLabel(event.position().toPoint()):
            self._tear_off_origin = (event.position().toPoint(), event.globalPosition().toPoint())
            self._geometry_at_press = QRect(self.geometry())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        origin = getattr(self, "_tear_off_origin", None)
        if origin is not None and event.buttons() & Qt.LeftButton:
            local, pressed_at = origin
            now = event.globalPosition().toPoint()
            far_enough = (now - pressed_at).manhattanLength() >= QApplication.startDragDistance()
            if far_enough and not self._manager.viewportGlobalRect().contains(now):
                self._tear_off_origin = None
                # End the built-in move before handing the gesture over to drag and drop
                release = QMouseEvent(QEvent.MouseButtonRelease, event.position(), event.globalPosition(),
                                      Qt.LeftButton, Qt.NoButton, event.modifiers())
                super().mouseReleaseEvent(release)
                # Remember the pre-drag position as the workspace placement
                self.setGeometry(self._geometry_at_press)
                # May dispose of this subwindow; nothing may touch self afterwards
                self._manager.dragContainer(self, local)
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._tear_off_origin = None
        super().mouseReleaseEvent(event)

    def _takeHostedWidget(self):
        widget = self.widget()
        self.setWidget(None)
        return widget

    def _requestDetach(self):
        widget = self.widget()
        if widget is not None:
            # Defer so the system menu has finished executing before reparenting
            QTimer.singleShot(0, self._manager, lambda: self._manager.detach(widget))

    def moveEvent(self, event):
        super().moveEvent(event)
        self._trackNormalGeometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._trackNormalGeometry()

    def closeEvent(self, event):
        if not self._forwardClose(event):
            return
        # The hosted widget has closed (or there is none). Let QMdiSubWindow tidy
        # up the MDI area without sending the widget a second close event.
        self._suppress_child_close = True
        try:
            super().closeEvent(event)
        finally:
            self._suppress_child_close = False
        self._finishClose(event)


class _FloatingHeader(QFrame):
    """
    Header strip of a floating window: shows the title, offers an Attach button,
    and is the handle for dragging the window back onto the workspace.
    """

    def __init__(self, host: FloatingWindow):
        super().__init__(host)
        self._host = host
        self._press: tuple[QPoint, QPoint] | None = None
        self.setCursor(Qt.OpenHandCursor)
        self.setToolTip("Drag onto the workspace, or double-click, to attach this window")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._press = (event.position().toPoint(), event.globalPosition().toPoint())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._press is not None and event.buttons() & Qt.LeftButton:
            local, pressed_at = self._press
            if (event.globalPosition().toPoint() - pressed_at).manhattanLength() >= QApplication.startDragDistance():
                self._press = None
                # May dispose of the host; nothing may touch it afterwards
                self._host._manager.dragContainer(self._host, self.mapTo(self._host, local))
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._press = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._press = None
            self._host._requestAttach()
            return
        super().mouseDoubleClickEvent(event)


class FloatingWindow(QWidget, _HostMixin):
    """
    Top-level host for a detached widget.

    A slim header strip carries the window title and an attach button, so every
    detached window can be put back with the mouse, by button, by double-click
    or by dragging the header onto the workspace. The host registers no keyboard
    shortcut of its own; the application-wide shortcut lives on the main
    window's Window menu.
    """

    def __init__(self, manager: WorkspaceManager, parent=None):
        QWidget.__init__(self, parent, Qt.Window)
        self._initHost(manager)
        self._widget: QWidget | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.header = _FloatingHeader(self)
        self.header.setObjectName("floatingWindowHeader")
        self.header.setFrameShape(QFrame.StyledPanel)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(6, 1, 1, 1)
        self.titleLabel = QLabel(self.header)
        header_layout.addWidget(self.titleLabel, 1)
        self.attachButton = QToolButton(self.header)
        self.attachButton.setObjectName("cmdAttachToWorkspace")
        self.attachButton.setText(ATTACH_TEXT)
        self.attachButton.setToolTip("Put this window back into the SasView workspace")
        self.attachButton.setAutoRaise(True)
        self.attachButton.clicked.connect(self._requestAttach)
        header_layout.addWidget(self.attachButton)
        layout.addWidget(self.header)

    def hostWidget(self, widget: QWidget):
        self._widget = widget
        self.layout().addWidget(widget, 1)
        self._watch(widget)
        self._onHostedWidgetTitleChanged(widget.windowTitle())
        if not widget.windowIcon().isNull():
            self.setWindowIcon(widget.windowIcon())
        self.setObjectName(f"{widget.objectName()}_floating")

    def hostedWidget(self):
        return self._widget

    def _takeHostedWidget(self):
        widget = self._widget
        self.layout().removeWidget(widget)
        widget.setParent(None)
        self._widget = None
        return widget

    def headerHeight(self) -> int:
        return self.header.sizeHint().height()

    def _requestAttach(self):
        widget = self._widget
        if widget is not None:
            QTimer.singleShot(0, self._manager, lambda: self._manager.attach(widget))

    def _onHostedWidgetTitleChanged(self, title: str):
        self.setWindowTitle(title)
        self.titleLabel.setText(title)

    def event(self, event):
        if event.type() == QEvent.WindowActivate:
            self._manager._onFloatingWindowActivated(self)
        return super().event(event)

    def moveEvent(self, event):
        super().moveEvent(event)
        self._trackNormalGeometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._trackNormalGeometry()

    def closeEvent(self, event):
        if not self._forwardClose(event):
            return
        event.accept()
        self._finishClose(event)


def _clamp_to_screen(rect: QRect) -> QRect:
    """Keep a top-level window rectangle on an available screen."""
    screen = QGuiApplication.screenAt(rect.center()) or QGuiApplication.screenAt(rect.topLeft())
    if screen is None:
        screen = QGuiApplication.primaryScreen()
    if screen is None:
        return QRect(rect)
    available = screen.availableGeometry()
    width = min(rect.width(), available.width())
    height = min(rect.height(), available.height())
    x = min(max(rect.x(), available.left()), available.left() + available.width() - width)
    y = min(max(rect.y(), available.top()), available.top() + available.height() - height)
    return QRect(x, y, width, height)


class WorkspaceManager(QObject):
    """Single owner of where a workspace widget lives and who closes its container."""

    widgetDetached = Signal(QWidget)
    widgetAttached = Signal(QWidget)
    widgetClosed = Signal(QWidget)
    # Emitted when the effective active widget (see active_widget) changes
    activeWidgetChanged = Signal(object)

    def __init__(self, mdi: QMdiArea, main_window: QWidget):
        super().__init__(main_window)
        self._mdi = mdi
        self._main_window = main_window
        self._hosts: dict[QWidget, _HostMixin] = {}
        # Placement records, in the order widgets were first hosted
        self._placement: dict[QWidget, Placement] = {}
        self._active: QWidget | None = None
        self._notified_active: QWidget | None = None

        # Drag and drop of workspace windows
        self._drag: _DragState | None = None
        self._pending_drop: QPoint | None = None
        self._viewport = mdi.viewport()
        self._drop_indicator = QRubberBand(QRubberBand.Rectangle, self._viewport)
        mdi.setAcceptDrops(True)
        self._viewport.setAcceptDrops(True)
        self._viewport.installEventFilter(self)
        # New subwindows are sized once the workspace is visible (see _applyInitialSize)
        mdi.installEventFilter(self)

        mdi.subWindowActivated.connect(self._onSubWindowActivated)
        app = QApplication.instance()
        if app is not None:
            app.focusChanged.connect(self._onFocusChanged)

    # ------------------------------------------------------------------
    # Placement
    # ------------------------------------------------------------------
    def add(self, widget: QWidget, *, detached: bool = False, visible: bool = True) -> QWidget:
        """
        Host ``widget`` in the MDI area, or in a floating window when ``detached``.
        Returns the container. Adding a widget that is already hosted returns its
        current container unchanged.
        """
        if widget in self._hosts:
            return self._hosts[widget]

        placement = self._placementFor(widget)
        placement.detached = detached
        if detached:
            container = self._createFloating(widget, placement)
        else:
            container = self._createSubWindow(widget, placement)
        self._register(widget, container)

        if visible:
            self._show(container, widget)
        else:
            container.hide()
        self._notifyActive()
        return container

    def detach(self, widget: QWidget, *, position: QPoint | None = None) -> FloatingWindow:
        """
        Move a hosted widget from the MDI area into a floating window.
        ``position`` is a global top-left for the floating window; by default it
        appears where the widget was last floating, or over its workspace position.
        """
        container = self._hosts[widget]
        if isinstance(container, FloatingWindow):
            return container

        placement = self._placementFor(widget)
        was_visible = not container.isHidden()
        state = container.windowState() & _MIN_MAX
        normal = container.lastNormalGeometry()
        content_size = self._contentSize(widget) if state == Qt.WindowNoState else normal.size()
        placement.mdi_geometry = normal
        if position is None:
            position = self._mdi.viewport().mapToGlobal(normal.topLeft())
        elif placement.floating_geometry is not None:
            placement.floating_geometry.moveTopLeft(position)

        self._dispose(widget, container)
        host = self._createFloating(widget, placement, content_size=content_size, position=position)
        placement.detached = True
        self._register(widget, host)

        if was_visible:
            self._show(host, widget)
            if state != Qt.WindowNoState:
                host.setWindowState(state)
            host.raise_()
            host.activateWindow()
            self._setActive(widget)
        else:
            host.hide()
        self.widgetDetached.emit(widget)
        return host

    def attach(self, widget: QWidget, *, position: QPoint | None = None) -> DetachableSubWindow:
        """
        Move a floating widget back into the MDI area.
        ``position`` is a top-left in workspace coordinates; by default the widget
        returns to where it was last attached.
        """
        container = self._hosts[widget]
        if isinstance(container, DetachableSubWindow):
            return container

        placement = self._placementFor(widget)
        was_visible = not container.isHidden()
        state = container.windowState() & _MIN_MAX
        normal = container.lastNormalGeometry()
        content_size = (self._contentSize(widget) if state == Qt.WindowNoState
                        else QSize(normal.width(), normal.height() - container.headerHeight()))
        placement.floating_geometry = normal

        self._dispose(widget, container)
        sub = self._createSubWindow(widget, placement, position=position)
        placement.detached = False
        self._register(widget, sub)

        if was_visible:
            self._show(sub, widget)
            if placement.mdi_geometry is None:
                self._matchContentSize(sub, widget, content_size)
            if state != Qt.WindowNoState:
                sub.setWindowState(state)
            self._mdi.setActiveSubWindow(sub)
            self._setActive(widget)
        else:
            sub.hide()
        self.widgetAttached.emit(widget)
        return sub

    def toggle(self, widget: QWidget):
        """Detach an attached widget, or attach a detached one."""
        if widget is None or widget not in self._hosts:
            return None
        if self.is_detached(widget):
            return self.attach(widget)
        return self.detach(widget)

    def is_hosted(self, widget: QWidget) -> bool:
        return widget in self._hosts

    def is_detached(self, widget: QWidget) -> bool:
        return isinstance(self._hosts.get(widget), FloatingWindow)

    def container_of(self, widget: QWidget) -> QWidget | None:
        return self._hosts.get(widget)

    def last_placement(self, widget: QWidget) -> Placement | None:
        """Where the widget was last shown during this session, or None if never hosted."""
        return self._placement.get(widget)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def close(self, widget: QWidget) -> bool:
        """
        Ask the widget's container to close. The request is forwarded to the widget.
        Returns False if the widget refused. Unhosted widgets are closed directly.
        """
        container = self._hosts.get(widget)
        if container is None:
            return widget.close()
        return container.close()

    def remove(self, widget: QWidget):
        """Take the widget out of its container without closing it. The widget is hidden."""
        container = self._hosts.get(widget)
        if container is None:
            return
        placement = self._placementFor(widget)
        if isinstance(container, FloatingWindow):
            placement.floating_geometry = container.lastNormalGeometry()
        else:
            placement.mdi_geometry = container.lastNormalGeometry()
        self._dispose(widget, container)
        self._notifyActive()

    def forget(self, widget: QWidget):
        """Remove the widget and drop its placement record."""
        self.remove(widget)
        self._placement.pop(widget, None)

    def set_visible(self, widget: QWidget, visible: bool):
        """Show or hide a widget's container without closing the widget."""
        container = self._hosts.get(widget)
        if container is None:
            widget.setVisible(visible)
            return
        if visible:
            self._show(container, widget)
        else:
            container.hide()
        self._notifyActive()

    def minimize(self, widget: QWidget):
        container = self._hosts.get(widget)
        if container is None:
            widget.showMinimized()
        elif not container.isHidden():
            container.showMinimized()

    def activate(self, widget: QWidget):
        """Show, restore, raise and focus a widget wherever it lives."""
        container = self._hosts.get(widget)
        if container is None:
            widget.showNormal()
            widget.raise_()
            widget.activateWindow()
            return
        if container.isMinimized():
            container.showNormal()
        self._show(container, widget)
        if isinstance(container, FloatingWindow):
            container.raise_()
            container.activateWindow()
        else:
            # Bring the main window forward too, in case a detached window is active
            self._main_window.raise_()
            self._main_window.activateWindow()
            self._mdi.setActiveSubWindow(container)
        widget.setFocus()
        self._setActive(widget)

    def close_all_floating(self):
        """
        Close every floating window, for application shutdown.
        Widgets that refuse to close are taken out of their floating window instead.
        """
        for widget, container in list(self._hosts.items()):
            if not isinstance(container, FloatingWindow):
                continue
            if not container.close() and self._hosts.get(widget) is container:
                self.remove(widget)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    def hosted_widgets(self, *, include_hidden: bool = False) -> list[QWidget]:
        """Hosted widgets in the order they were first added. Minimised windows are included."""
        return [w for w in self._placement
                if w in self._hosts and (include_hidden or not self._hosts[w].isHidden())]

    def active_widget(self) -> QWidget | None:
        """
        The most recently activated hosted widget, attached or detached.

        Focus moving to a menu, the Data Explorer or another tool window does not
        change it, in the same way that QMdiArea keeps its current subwindow. It
        is None while that widget is unhosted or its window is hidden.
        """
        widget = self._active
        if widget is None:
            return None
        container = self._hosts.get(widget)
        if container is None or container.isHidden():
            return None
        return widget

    def mdi(self) -> QMdiArea:
        return self._mdi

    def viewportGlobalRect(self) -> QRect:
        """The workspace viewport in global coordinates."""
        viewport = self._mdi.viewport()
        return QRect(viewport.mapToGlobal(QPoint(0, 0)), viewport.size())

    # ------------------------------------------------------------------
    # Drag and drop
    # ------------------------------------------------------------------
    def dragContainer(self, container: QWidget, hotspot: QPoint):
        """
        Run a drag of a hosted window, then apply its outcome.

        Called by a container from its own mouse handler once the user has
        dragged far enough. Dropping onto the workspace attaches a floating
        window, or moves an attached one. Releasing a subwindow outside the
        workspace detaches it at the cursor. The container may be disposed of
        by the time this returns.
        """
        widget = container.hostedWidget()
        if widget is None or self._hosts.get(widget) is not container:
            return
        self._drag = _DragState(widget, container, QPoint(hotspot), QSize(container.size()))
        self._pending_drop = None
        try:
            self._runDrag(container, hotspot)
        finally:
            self._finishDrag()

    def _runDrag(self, container: QWidget, hotspot: QPoint):
        drag = QDrag(container)
        mime = QMimeData()
        mime.setData(WORKSPACE_MIME, b"1")
        drag.setMimeData(mime)
        pixmap = container.grab()
        if not pixmap.isNull():
            scale = min(1.0, _DRAG_PIXMAP_MAX.width() / max(1, pixmap.width()),
                        _DRAG_PIXMAP_MAX.height() / max(1, pixmap.height()))
            if scale < 1.0:
                pixmap = pixmap.scaled(pixmap.size() * scale, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            drag.setPixmap(pixmap)
            drag.setHotSpot(QPoint(int(hotspot.x() * scale), int(hotspot.y() * scale)))
        drag.exec(Qt.MoveAction)

    def _finishDrag(self):
        state, drop = self._drag, self._pending_drop
        self._drag = None
        self._pending_drop = None
        self._drop_indicator.hide()
        if state is None or not isValid(state.widget) or self._hosts.get(state.widget) is not state.container:
            return
        widget, container = state.widget, state.container
        if drop is not None:
            if isinstance(container, FloatingWindow):
                self.attach(widget, position=drop)
            else:
                container.move(drop)
                self._mdi.setActiveSubWindow(container)
            return
        if isinstance(container, DetachableSubWindow):
            cursor = QCursor.pos()
            if not self.viewportGlobalRect().contains(cursor):
                self.detach(widget, position=cursor - state.hotspot)

    def eventFilter(self, obj, event):
        # Comparisons here must not call into Qt objects, which may be gone during shutdown
        if obj is self._mdi and event.type() == QEvent.Show:
            # Runs before QMdiArea.showEvent, which then places (but no longer sizes) them
            self._applyPendingInitialSizes()
            return False
        # Drag events over the workspace viewport
        if self._drag is not None and obj is self._viewport:
            event_type = event.type()
            if event_type in (QEvent.DragEnter, QEvent.DragMove):
                if event.mimeData().hasFormat(WORKSPACE_MIME):
                    event.setDropAction(Qt.MoveAction)
                    event.accept()
                    self._showDropIndicator(event.position().toPoint())
                    return True
            elif event_type == QEvent.DragLeave:
                self._drop_indicator.hide()
            elif event_type == QEvent.Drop:
                if event.mimeData().hasFormat(WORKSPACE_MIME):
                    self._drop_indicator.hide()
                    # Applied by the drag source once QDrag.exec has returned
                    self._pending_drop = event.position().toPoint() - self._drag.hotspot
                    event.setDropAction(Qt.MoveAction)
                    event.accept()
                    return True
        return super().eventFilter(obj, event)

    def _showDropIndicator(self, pos: QPoint):
        self._drop_indicator.setGeometry(QRect(pos - self._drag.hotspot, self._drag.size))
        self._drop_indicator.show()
        self._drop_indicator.raise_()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _placementFor(self, widget: QWidget) -> Placement:
        placement = self._placement.get(widget)
        if placement is None:
            placement = Placement()
            self._placement[widget] = placement
            widget.destroyed.connect(partial(self._onWidgetDestroyed, id(widget)))
        return placement

    def _register(self, widget: QWidget, container: _HostMixin):
        self._hosts[widget] = container
        container.destroyed.connect(partial(self._onContainerDestroyed, id(widget), id(container)))

    def _createSubWindow(self, widget: QWidget, placement: Placement,
                         position: QPoint | None = None) -> DetachableSubWindow:
        # Parent to the viewport at construction, as QMdiArea.addSubWindow does.
        # QMdiSubWindow picks its title-bar icon in its constructor: without a parent
        # it finds no window icon and falls back to the style's default Qt icon.
        sub = DetachableSubWindow(self, self._mdi.viewport())
        sub.hostWidget(widget)
        self._mdi.addSubWindow(sub)
        if placement.mdi_geometry is not None:
            sub.setGeometry(placement.mdi_geometry)
        else:
            # Never shown in the workspace before: size it like QMdiArea would, once visible
            sub._initial_size_pending = True
        if position is not None:
            sub.move(position)
        return sub

    def _createFloating(self, widget: QWidget, placement: Placement,
                        content_size: QSize | None = None, position: QPoint | None = None) -> FloatingWindow:
        host = FloatingWindow(self, self._main_window)
        host.hostWidget(widget)
        if placement.floating_geometry is not None:
            host.setGeometry(_clamp_to_screen(placement.floating_geometry))
        else:
            size = content_size if content_size is not None else self._contentSize(widget)
            size = QSize(size.width(), size.height() + host.headerHeight())
            if position is None:
                position = self._defaultFloatingPosition()
            host.setGeometry(_clamp_to_screen(QRect(position, size)))
        return host

    def _defaultFloatingPosition(self) -> QPoint:
        window = self._main_window
        if window is not None and window.isVisible():
            return window.geometry().topLeft() + QPoint(60, 60)
        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            return screen.availableGeometry().topLeft() + QPoint(60, 60)
        return QPoint(60, 60)

    @staticmethod
    def _contentSize(widget: QWidget) -> QSize:
        if widget.testAttribute(Qt.WA_Resized):
            return QSize(widget.size())
        hint = widget.sizeHint()
        return hint if hint.isValid() else QSize(widget.size())

    @staticmethod
    def _matchContentSize(sub: QMdiSubWindow, widget: QWidget, content_size: QSize):
        dw = content_size.width() - widget.width()
        dh = content_size.height() - widget.height()
        if dw or dh:
            sub.resize(sub.width() + dw, sub.height() + dh)

    def _show(self, container: QWidget, widget: QWidget):
        if widget.isHidden():
            widget.show()
        container.show()
        self._applyInitialSize(container)

    def _applyInitialSize(self, container: QWidget):
        """
        Give a new subwindow the size QMdiArea.addSubWindow would give it.

        QMdiArea sizes a new subwindow to its size hint when it is added, but with
        an application stylesheet the polish that follows resizes the subwindow to
        its minimum before it is shown, which is what the user would see. Applying
        the rule again here, once the subwindow and the workspace are visible,
        makes the outcome independent of that ordering. Windows added while the
        workspace is still hidden are sized when the workspace is first shown.
        """
        if not getattr(container, "_initial_size_pending", False):
            return
        if not isinstance(container, DetachableSubWindow) or container.isHidden():
            return
        if not self._mdi.isVisible():
            return
        container._initial_size_pending = False
        if container.isMaximized() or container.isMinimized():
            return
        hint = container.sizeHint().boundedTo(self._viewport.size())
        container.resize(hint.expandedTo(container.minimumSizeHint()))

    def _applyPendingInitialSizes(self):
        for container in list(self._hosts.values()):
            self._applyInitialSize(container)

    def _dispose(self, widget: QWidget, container: _HostMixin):
        """Take the widget out of an old container and delete the empty container."""
        if self._hosts.get(widget) is container:
            del self._hosts[widget]
        container.releaseWidget()
        container.close()

    def _onWidgetClosed(self, widget: QWidget, container: _HostMixin):
        if not isValid(self) or self._hosts.get(widget) is not container:
            return
        del self._hosts[widget]
        self._placement.pop(widget, None)
        if self._active is widget:
            self._active = None
        self._notifyActive()
        self.widgetClosed.emit(widget)

    def _onContainerDestroyed(self, widget_id: int, container_id: int, *args):
        # Containers and the manager share the main window as parent, so the manager
        # may already be gone when a container is destroyed during shutdown
        if not isValid(self):
            return
        for widget, container in list(self._hosts.items()):
            if id(widget) == widget_id and id(container) == container_id:
                del self._hosts[widget]
        self._notifyActive()

    def _onWidgetDestroyed(self, widget_id: int, *args):
        """A hosted widget was deleted without closing: retire its now empty container."""
        if not isValid(self):
            return
        for widget in [w for w in self._placement if id(w) == widget_id]:
            self._placement.pop(widget, None)
            container = self._hosts.pop(widget, None)
            if self._active is widget:
                self._active = None
            if container is not None:
                container._hosted_widget_closed = True
                if isinstance(container, FloatingWindow):
                    container._widget = None
                # The container may itself be the one being destroyed; check once the
                # destruction has finished and close it only if it still exists
                QTimer.singleShot(0, self, partial(self._retireContainer, container))
        self._notifyActive()

    @staticmethod
    def _retireContainer(container: _HostMixin):
        if isValid(container):
            container.close()

    def _setActive(self, widget: QWidget | None):
        self._active = widget
        self._notifyActive()

    def _notifyActive(self):
        """Emit activeWidgetChanged when the effective active widget has changed."""
        if not isValid(self):
            return
        effective = self.active_widget()
        if effective is not self._notified_active:
            self._notified_active = effective
            self.activeWidgetChanged.emit(effective)

    def _onSubWindowActivated(self, sub):
        if sub is None:
            return
        widget = sub.widget()
        if widget is not None and self._hosts.get(widget) is sub:
            self._setActive(widget)

    def _onFloatingWindowActivated(self, host: FloatingWindow):
        if not isValid(self):
            return
        widget = host.hostedWidget()
        if widget is not None and self._hosts.get(widget) is host:
            self._setActive(widget)

    def _onFocusChanged(self, old, new):
        # Focus outside hosted windows (menus, the Data Explorer, dialogs) keeps
        # the last active window as the target of Window menu actions
        hosted = self._hostedWidgetContaining(new)
        if hosted is not None:
            self._setActive(hosted)

    def _hostedWidgetContaining(self, widget: QWidget | None) -> QWidget | None:
        current = widget
        while current is not None:
            if isinstance(current, (QMenu, QMenuBar)):
                return None
            if isinstance(current, _HostMixin):
                hosted = current.hostedWidget()
                return hosted if self._hosts.get(hosted) is current else None
            current = current.parentWidget()
        return None


def workspace_manager_for(obj) -> WorkspaceManager | None:
    """
    Find the application's WorkspaceManager for the object shapes used in SasView.

    * GuiManager and the main window expose ``workspace_manager``.
    * The Data Explorer refers to the GuiManager through ``parent``.
    * Plots refer to the Data Explorer through ``manager``, and helper panels
      are owned by a plot.

    Returns None for embedded quick plots and standalone widgets, which are then
    shown and closed directly.
    """
    manager = getattr(obj, "manager", None)
    candidates = [obj, getattr(obj, "parent", None), manager, getattr(manager, "parent", None)]
    for candidate in candidates:
        found = getattr(candidate, "workspace_manager", None)
        if isinstance(found, WorkspaceManager):
            return found
    return None
