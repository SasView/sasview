from PySide6.QtCore import QEvent, QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPalette, QPen
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget


class _DownloadIcon(QWidget):
    """A tray with a downward arrow, drawn in the palette's colours so it
    follows light and dark themes."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.active = False
        self.setFixedSize(QSize(64, 64))

    def paintEvent(self, event):
        role = QPalette.ColorRole.Highlight if self.active else QPalette.ColorRole.PlaceholderText
        pen = QPen(self.palette().color(role), 4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(pen)
        r = QRectF(self.rect()).adjusted(6, 6, -6, -6)
        cx = r.center().x()
        # Arrow
        painter.drawLine(QPointF(cx, r.top()), QPointF(cx, r.top() + r.height() * 0.6))
        head = r.width() * 0.2
        tip = QPointF(cx, r.top() + r.height() * 0.6)
        painter.drawLine(tip, QPointF(cx - head, tip.y() - head))
        painter.drawLine(tip, QPointF(cx + head, tip.y() - head))
        # Tray
        tray_top = r.top() + r.height() * 0.55
        painter.drawPolyline([
            QPointF(r.left(), tray_top),
            QPointF(r.left(), r.bottom()),
            QPointF(r.right(), r.bottom()),
            QPointF(r.right(), tray_top),
        ])


class _ClickTarget(QWidget):
    """The icon and text plus generous padding around them, clickable as one."""

    clicked = Signal()
    hovered = Signal(bool)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)

    def enterEvent(self, event):
        self.hovered.emit(True)

    def leaveEvent(self, event):
        self.hovered.emit(False)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
            self.clicked.emit()


class DropHint(QWidget):
    """Shown in place of the data tree while it's empty, to advertise that files
    can be loaded or dropped. Drops are handled by the explorer: this widget
    doesn't accept them, so they pass through to its parent."""

    load_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._hovered = False
        self._dragging = False

        self.target = _ClickTarget(self)
        self.target.clicked.connect(self.load_requested)
        self.target.hovered.connect(self._setHovered)
        self.icon = _DownloadIcon(self.target)
        # Not interactive, so clicks on the text fall through to the target.
        self.label = QLabel(self.target)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        target_layout = QVBoxLayout(self.target)
        target_layout.setContentsMargins(40, 32, 40, 32)
        target_layout.addWidget(self.icon, 0, Qt.AlignmentFlag.AlignHCenter)
        target_layout.addSpacing(12)
        target_layout.addWidget(self.label)

        layout = QVBoxLayout(self)
        layout.addStretch()
        layout.addWidget(self.target, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()

        # Match the tree's background so swapping between them doesn't jump.
        self.setAutoFillBackground(True)
        self.setBackgroundRole(QPalette.ColorRole.Base)
        self._refresh()

    def setActive(self, active: bool):
        """Highlight while files are being dragged over the explorer."""
        self._dragging = active
        self._refresh()

    def _setHovered(self, hovered: bool):
        self._hovered = hovered
        self._refresh()

    def changeEvent(self, event):
        # The text colours are baked into the label's HTML, so redo them when the
        # theme changes.
        if event.type() in (QEvent.Type.PaletteChange, QEvent.Type.ApplicationPaletteChange):
            self._refresh()
        super().changeEvent(event)

    def _refresh(self):
        highlighted = self._dragging or self._hovered
        self.icon.active = highlighted
        self.icon.update()
        palette = self.palette()
        background = palette.color(QPalette.ColorRole.Base)

        def opaque(role: QPalette.ColorRole) -> str:
            # PlaceholderText is usually Text with ~50% alpha, and .name() would
            # drop the alpha, so blend it onto the background first.
            c = palette.color(role)
            a = c.alphaF()
            return QColor(
                round(c.red() * a + background.red() * (1 - a)),
                round(c.green() * a + background.green() * (1 - a)),
                round(c.blue() * a + background.blue() * (1 - a)),
            ).name()

        text = opaque(QPalette.ColorRole.Highlight if highlighted else QPalette.ColorRole.Text)
        muted = opaque(QPalette.ColorRole.Highlight if highlighted else QPalette.ColorRole.PlaceholderText)
        self.label.setText(
            f'<span style="color:{text};"><b>Choose a file</b></span>'
            f'<span style="color:{muted};"> or drag it here.</span>'
        )
