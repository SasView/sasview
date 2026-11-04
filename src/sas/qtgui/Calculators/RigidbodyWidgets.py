"""Small widgets shared by the rigid-body calculator's views.

Small actions are shown as symbols rather than worded buttons, which keeps the controls from crowding out the script and the structure;
every symbol carries a tooltip naming what it does.
"""

from collections.abc import Callable

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from pyausaxs.gui.core.palette import PALETTE
from PySide6 import QtCore, QtGui, QtWidgets

MUTED_STYLE = f"color: {PALETTE['muted']};"
HEADING_STYLE = f"color: {PALETTE['text']}; font-weight: bold;"

# the primary action of a view (Run, Send to script), and the colour it turns while that action can be cancelled (Stop)
PRIMARY_STYLE = (
    f"QPushButton {{ background-color: {PALETTE['accent']}; color: white; font-weight: bold; border: none; border-radius: 4px;"
    " padding: 6px 14px; }"
    f"QPushButton:hover {{ background-color: {PALETTE['accent_hover']}; }}"
    f"QPushButton:disabled {{ background-color: {PALETTE['border']}; color: {PALETTE['muted']}; }}"
)
DANGER_STYLE = PRIMARY_STYLE.replace(PALETTE["accent_hover"], PALETTE["danger_hover"]).replace(PALETTE["accent"], PALETTE["danger"])


def glyph_icon(glyph: str, colour: str, size: int = 16, *, background: str | None = None) -> QtGui.QIcon:
    """A symbol drawn as an icon, for places that take an icon rather than text (e.g. an action inside a line edit); optionally on a
    filled, rounded badge."""
    screen = QtGui.QGuiApplication.primaryScreen()
    ratio = screen.devicePixelRatio() if screen is not None else 1.0
    pixmap = QtGui.QPixmap(int(size * ratio), int(size * ratio))
    pixmap.setDevicePixelRatio(ratio)
    pixmap.fill(QtCore.Qt.GlobalColor.transparent)
    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QtGui.QPainter.RenderHint.TextAntialiasing)
    if background is not None:
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QColor(background))
        painter.drawRoundedRect(QtCore.QRectF(0, 0, size, size), size / 4, size / 4)
    font = QtGui.QFont()
    font.setPixelSize(int(size * (0.75 if background is not None else 0.9)))
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(QtGui.QColor(colour))
    painter.drawText(QtCore.QRectF(0, 0, size, size), QtCore.Qt.AlignmentFlag.AlignCenter, glyph)
    painter.end()
    return QtGui.QIcon(pixmap)


def structure_figure() -> tuple[Figure, object]:
    """A figure holding one borderless 3D axis that fills it. No layout engine: with the axis hidden there is nothing for one to fit, and
    re-fitting on every frame of a rotation costs a third of the frame. Opting out explicitly matters, since SasView's plots switch
    `figure.autolayout` on globally."""
    figure = Figure(layout="none")
    figure.subplots_adjust(left=0, right=1, bottom=0, top=1)
    axes = figure.add_subplot(111, projection="3d")
    axes.set_axis_off()
    return figure, axes


class PreviewCanvas(FigureCanvasQTAgg):
    """A matplotlib canvas paced for dragging a 3D view around.

    The stock Qt canvas renders whenever the event loop goes idle. Under Wayland, Qt hands over every pointer motion at the mouse's polling
    rate instead of merging them as X11 and Tk do, so a drag renders more frames than the screen can show, and each one holds up the input
    behind it. This canvas renders at most once per display frame, and passes hover events on (as `hovered`) at a modest rate and never
    mid-drag, when there is nothing to read out anyway."""

    hovered = QtCore.Signal(object)  # the matplotlib motion event, or None when the readout should clear
    _HOVER_MS = 30

    def __init__(self, figure: Figure):
        super().__init__(figure)
        screen = QtGui.QGuiApplication.primaryScreen()
        rate = screen.refreshRate() if screen is not None and screen.refreshRate() > 0 else 60.0
        self._frameMs = max(1, int(1000 / rate))
        self._frameClock = QtCore.QElapsedTimer()
        self._frameClock.start()
        self._frameTimer = QtCore.QTimer(self)
        self._frameTimer.setSingleShot(True)
        self._frameTimer.timeout.connect(self._renderFrame)
        self._hoverEvent = None
        self._hoverTimer = QtCore.QTimer(self)
        self._hoverTimer.setSingleShot(True)
        self._hoverTimer.setInterval(self._HOVER_MS)
        self._hoverTimer.timeout.connect(self._deliverHover)
        self.mpl_connect("motion_notify_event", self._queueHover)
        self.mpl_connect("button_press_event", lambda _e: self._dropHover())

    def draw_idle(self):
        if not hasattr(self, "_frameTimer"):  # called by the base class while it is still being set up
            return super().draw_idle()
        if not self._frameTimer.isActive():
            self._frameTimer.start(max(0, self._frameMs - self._frameClock.elapsed()))

    def _renderFrame(self):
        if self.width() <= 0 or self.height() <= 0:
            return
        self._frameClock.restart()
        self.draw()

    def _queueHover(self, event):
        gui = event.guiEvent
        if gui is not None and gui.buttons() != QtCore.Qt.MouseButton.NoButton:
            return  # mid-drag
        self._hoverEvent = event
        if not self._hoverTimer.isActive():
            self._hoverTimer.start()

    def _dropHover(self):
        """A drag starts: forget the pending readout and clear the shown one, which the moving view is about to make stale."""
        self._hoverEvent = None
        self._hoverTimer.stop()
        self.hovered.emit(None)

    def _deliverHover(self):
        event, self._hoverEvent = self._hoverEvent, None
        if event is not None:
            self.hovered.emit(event)


class GlyphButton(QtWidgets.QToolButton):
    """A flat button showing a single symbol: muted until hovered, so a row of them reads as quiet decoration rather than clutter. The
    tooltip names what it does, since nothing else on screen does."""

    def __init__(self, glyph: str, tooltip: str, *, hover: str | None = None, size: int = 15, parent=None):
        super().__init__(parent)
        self.setText(glyph)
        self.setToolTip(tooltip)
        self.setAutoRaise(True)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"QToolButton {{ color: {PALETTE['muted']}; border: none; padding: 1px 4px; font-size: {size}px; }}"
            f"QToolButton:hover {{ color: {hover or PALETTE['text']}; background-color: {PALETTE['surface_alt']}; border-radius: 3px; }}"
            f"QToolButton:disabled {{ color: {PALETTE['border']}; }}"
        )


class ToggleChip(QtWidgets.QToolButton):
    """A checkable chip for a display option: tinted with the accent while on, muted while off."""

    def __init__(self, text: str, tooltip: str, *, checked: bool = False, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setToolTip(tooltip)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"QToolButton {{ color: {PALETTE['muted']}; border: 1px solid {PALETTE['border']}; border-radius: 10px; padding: 2px 9px; }}"
            f"QToolButton:hover {{ border-color: {PALETTE['accent']}; }}"
            f"QToolButton:checked {{ color: {PALETTE['accent']}; background-color: {PALETTE['accent_soft']};"
            f" border-color: {PALETTE['accent_soft']}; }}"
            f"QToolButton:disabled {{ color: {PALETTE['border']}; border-color: {PALETTE['surface_alt']}; background-color: transparent; }}"
        )


class CollapsibleSection(QtWidgets.QWidget):
    """A titled section whose body folds away behind its header. Sections are independent, so any number can be open at once. The body
    is a form, so the labels of its rows line up."""

    def __init__(self, title: str, *, expanded: bool, parent=None):
        super().__init__(parent)
        self._title = title
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.header = QtWidgets.QPushButton()
        self.header.setCheckable(True)
        self.header.setFlat(True)
        self.header.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.header.setStyleSheet(
            f"QPushButton {{ {HEADING_STYLE} border: none; border-bottom: 1px solid {PALETTE['border']}; padding: 5px 2px;"
            " text-align: left; background: transparent; }"
            f"QPushButton:hover {{ color: {PALETTE['accent']}; }}"
        )
        layout.addWidget(self.header)
        self.body = QtWidgets.QWidget()
        self.form = QtWidgets.QFormLayout(self.body)
        self.form.setContentsMargins(4, 4, 0, 8)
        self.form.setHorizontalSpacing(8)
        self.form.setVerticalSpacing(4)
        self.form.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.body)
        self.header.toggled.connect(self.setExpanded)
        self.setExpanded(expanded)

    def setTitle(self, title: str):
        self._title = title
        self.setExpanded(self.isExpanded())

    def setExpanded(self, expanded: bool):
        self.header.setChecked(expanded)
        self.header.setText(("▾  " if expanded else "▸  ") + self._title)
        self.body.setVisible(expanded)

    def isExpanded(self) -> bool:
        return self.header.isChecked()

    def addHeading(self, text: str):
        """A quiet sub-heading, grouping the rows below it."""
        label = QtWidgets.QLabel(text)
        label.setStyleSheet(f"{MUTED_STYLE} font-size: 11px; margin-top: 6px;")
        self.form.addRow(label)


class ActionField(QtWidgets.QWidget):
    """A one-line action: a field whose placeholder carries the expected format, applied by Return or by the ⏎ inside it. The ⏎ turns green
    while applying would actually do something (see setReady), so the user can tell at a glance when a selection is enough.

    `prefill` seeds the field with a real value rather than a hint, for an action whose one sensible answer can just be submitted; it is
    restored whenever the field is cleared. `extra` is a GlyphButton placed after the field, e.g. to reveal an optional setting."""

    triggered = QtCore.Signal()

    def __init__(self, hint: str, tooltip: str, *, prefill: str = "", parent=None):
        super().__init__(parent)
        self._prefill = prefill
        self._ready = False
        self._dimmed = False
        self._idle_icon = glyph_icon("⏎", PALETTE["muted"], 18)
        self._ready_icon = glyph_icon("⏎", "white", 18, background=PALETTE["ready"])
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.edit = QtWidgets.QLineEdit(prefill)
        self.edit.setPlaceholderText(hint)
        self.edit.setToolTip(tooltip)
        self.apply = self.edit.addAction(self._idle_icon, QtWidgets.QLineEdit.ActionPosition.TrailingPosition)
        self.apply.setToolTip("Apply (Return)")
        layout.addWidget(self.edit, 1)
        self.edit.returnPressed.connect(self.triggered.emit)
        self.apply.triggered.connect(lambda: self.triggered.emit())

    def addButton(self, button: QtWidgets.QAbstractButton):
        self.layout().addWidget(button)

    def text(self) -> str:
        return self.edit.text()

    def clear(self):
        self.edit.setText(self._prefill)

    def setReady(self, ready: bool):
        self._ready = ready
        self.apply.setIcon(self._ready_icon if ready else self._idle_icon)
        self._restyle()

    def isReady(self) -> bool:
        return self._ready

    def setDimmed(self, dimmed: bool):
        """Grey the text out, for an action that is usable but no longer the obvious next step."""
        self._dimmed = dimmed
        self._restyle()

    def _restyle(self):
        rules = []
        if self._ready:
            rules.append(f"border: 1px solid {PALETTE['ready']}; border-radius: 2px; padding: 1px;")
        if self._dimmed:
            rules.append(f"color: {PALETTE['muted']};")
        self.edit.setStyleSheet(f"QLineEdit {{ {' '.join(rules)} }}" if rules else "")


def add_action_row(section: CollapsibleSection, label: str, hint: str, tooltip: str, command: Callable[[], None], *,
                   prefill: str = "") -> ActionField:
    """Add a labelled ActionField running `command` to a section's form."""
    field = ActionField(hint, tooltip, prefill=prefill)
    field.triggered.connect(command)
    title = QtWidgets.QLabel(label)
    title.setStyleSheet(MUTED_STYLE)
    section.form.addRow(title, field)
    return field
