from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QPainter, QPalette, QPen, QPolygonF
from PySide6.QtWidgets import QMenu, QToolButton, QWidget

# The item types the explorer can show or hide: key -> menu label.
FILTER_TYPES: dict[str, str] = {
    "Data": "Data",
    "Perspective": "Perspectives",
    "Theory": "Theories",
    "Plot": "Plots",
}


class _StayOpenMenu(QMenu):
    """A menu whose checkable actions toggle without closing it, so several
    can be changed in one go."""

    def mouseReleaseEvent(self, event):
        action = self.activeAction()
        if action is not None and action.isCheckable() and action.isEnabled():
            action.trigger()
            return
        super().mouseReleaseEvent(event)


class DataExplorerFilterButton(QToolButton):
    """A small funnel button that opens a menu for choosing which item types
    the explorer shows. Everything is shown by default; while anything is
    hidden, the funnel is filled in so it's clear the view is filtered."""

    filters_changed = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setAutoRaise(True)
        self.setFixedSize(QSize(28, 28))
        self.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        # The funnel itself shows this opens something; the arrow is clutter.
        self.setStyleSheet("QToolButton::menu-indicator { image: none; }")

        menu = _StayOpenMenu(self)
        self._actions = {}
        for key, label in FILTER_TYPES.items():
            action = menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(True)
            action.toggled.connect(self._on_toggled)
            self._actions[key] = action
        menu.addSeparator()
        self._show_all = menu.addAction("Show all")
        self._show_all.triggered.connect(self.show_all)
        self.setMenu(menu)

        self._update_state()

    def shown_types(self) -> set[str]:
        """The keys of FILTER_TYPES whose items should be shown."""
        return {key for key, action in self._actions.items() if action.isChecked()}

    def is_filtering(self) -> bool:
        return len(self.shown_types()) < len(self._actions)

    def show_all(self):
        for action in self._actions.values():
            action.blockSignals(True)
            action.setChecked(True)
            action.blockSignals(False)
        self._on_toggled()

    def _on_toggled(self):
        self._update_state()
        self.filters_changed.emit()

    def _update_state(self):
        hidden = [FILTER_TYPES[key] for key, action in self._actions.items() if not action.isChecked()]
        if hidden:
            self.setToolTip(f"Hidden: {', '.join(hidden)}")
        else:
            self.setToolTip("Choose which item types to show")
        self._show_all.setEnabled(bool(hidden))
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        # Draw the funnel in the palette's colours so it follows light and dark
        # themes. Filled with the highlight colour while anything is hidden.
        filtering = self.is_filtering()
        role = QPalette.ColorRole.Highlight if filtering else QPalette.ColorRole.ButtonText
        colour = self.palette().color(role)
        if not self.isEnabled():
            colour = self.palette().color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText)

        r = QRectF(self.rect()).adjusted(7, 7, -7, -7)
        cx = r.center().x()
        neck = r.width() * 0.12
        neck_top = r.top() + r.height() * 0.5
        funnel = QPolygonF([
            QPointF(r.left(), r.top()),
            QPointF(r.right(), r.top()),
            QPointF(cx + neck, neck_top),
            QPointF(cx + neck, r.bottom()),
            QPointF(cx - neck, r.bottom() - r.height() * 0.15),
            QPointF(cx - neck, neck_top),
        ])

        pen = QPen(colour, 1.5)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(pen)
        painter.setBrush(colour if filtering else Qt.BrushStyle.NoBrush)
        painter.drawPolygon(funnel)
