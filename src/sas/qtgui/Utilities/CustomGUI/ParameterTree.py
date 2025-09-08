from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QTreeWidget


class QParameterTreeWidget(QTreeWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.disabled_text = ""

    def setDisabledText(self, text):
        self.disabled_text = text
        self.viewport().update()

    def paintEvent(self, event):
        super().paintEvent(event)

        if not self.isEnabled() and self.disabled_text:
            painter = QPainter(self.viewport())
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.TextAntialiasing)
            painter.setPen(QPen(QColor(170, 170, 170)))  # Light gray color for text
            painter.setFont(QFont("Segoe UI", 11, italic=True))

            rect = self.viewport().rect()
            painter.drawText(rect, Qt.AlignCenter, self.disabled_text)
