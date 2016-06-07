from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtTest import *

class QtSignalSpy(QObject):
    """
    Helper class for testing Qt signals.
    """
    def __init__(self, widget, signal, parent=None):
        """
        """
        super(QtSignalSpy, self).__init__(parent)

        self._connector = {}
        self._count = 0
        self._signal = [None, None]

        # Assign our own slot to the emitted signal
        if isinstance(signal, pyqtBoundSignal):
            signal.connect(self.slot)
        elif hasattr(widget, signal):
            getattr(widget, signal).connect(self.slot)
        else:
            widget.signal.connect(slot)

    def slot(self, *args, **kwargs):
        """
        Record emitted signal.
        """
        self._connector[self._count] = {
            'args'   : args,
            'kwargs' : kwargs,
            }

        self._count += 1
        self._signal = [args, kwargs]

    def signal(self, index=None):
        """
        """
        if index == None:
            return self._signal
        else:
            return self._signal[index]

    def count(self):
        """
        """
        return self._count

    def called(self):
        """
        """
        return self._connector
