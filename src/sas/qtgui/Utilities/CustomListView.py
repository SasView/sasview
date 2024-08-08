
import PySide6.QtGui as QtGui

from PySide6.QtWidgets import QListView

class CustomListView(QListView):
    """
    Custom QListView that overwrites paint event to trigger when the delegate is disabled.
    Necessary to draw the overlay if there are no items in the table.
    """
    def __init__(self, parent=None):
        super(CustomListView, self).__init__(parent)
        self.delegate = None  # To store the delegate

    def setDelegate(self, delegate):
        self.delegate = delegate
        self.setItemDelegate(delegate)

    def paintEvent(self, event):
        super(CustomListView, self).paintEvent(event)
        # If the delegate is disabled, draw the overlay
        if self.delegate and self.delegate.disabled:
            painter = QtGui.QPainter(self.viewport())
            self.delegate.paintDisabledOverlay(painter)