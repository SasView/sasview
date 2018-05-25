from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtTest import *
import inspect

def WarningTestNotImplemented(method_name=None):
    """
    Prints warning about a non-implemented test.
    Test name retrieved from stack trace.
    """
    if method_name is not None:
        print(("\nWARNING: %s needs implementing!"%method_name))
    else:
        (frame, filename, line_number,
            function_name, lines, index) = inspect.getouterframes(inspect.currentframe())[1]
        print(("\nWARNING: %s needs implementing!"%function_name))

class QtSignalSpy(QObject):
    """
    Helper class for testing Qt signals.
    """
    def __init__(self, widget, signal, parent=None):
        """
        """
        super(QtSignalSpy, self).__init__(parent)

        self._recorder = {}
        self._count = 0
        self._signal = []

        # Assign our own slot to the emitted signal
        try:
            if isinstance(signal, pyqtBoundSignal):
                signal.connect(self.slot)
            elif hasattr(widget, signal):
                getattr(widget, signal).connect(self.slot)
            else:
                widget.signal.connect(slot)
        except AttributeError:
            msg = "Wrong construction of QtSignalSpy instance"
            raise RuntimeError(msg)

    def slot(self, *args, **kwargs):
        """
        Record emitted signal.
        """
        self._recorder[self._count] = {
            'args'   : args,
            'kwargs' : kwargs,
            }

        self._count += 1
        self._signal = [args, kwargs]

    def signal(self, index=None):
        if index is None:
            return self._signal
        else:
            return self._signal[index]

    def count(self):
        return self._count

    def called(self):
        return self._recorder
