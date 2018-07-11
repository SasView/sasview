import os
import sys
import logging

from PyQt5.QtCore import *


class XStream(QObject):
    """
    Imitates, loosely, an `io.TextIOWrapper` class in order to intercept
    messages going to stdout and stderr.

    To intercept messages to stdout, use:

    .. code-block:: python
       XStream.stdout().messageWritten.mySignalHandler()

    All messages to stdout will now also be emitted to your handler. Use
    `XStream.stderr()` in the same way to intercept stderr messages.

    An additional function, `XStream.write_log()`, emits a message only to the
    messageWritten signal, and not the stdout or stderr streams. It is intended
    for separation of log handling between console and Qt, as reflected in the
    name.
    """
    _stdout = None
    _stderr = None
    messageWritten = pyqtSignal(str)

    _real_stream = None

    def flush(self):
        pass

    def fileno(self):
        return -1

    def write(self, msg):
        """
        'msg' is emitted in the messageWritten signal, and is also written to
        the original stream. This means stdout/stderr messages have been
        redirected to a custom location (e.g. in-widget), but also reach
        console output.

        :param msg: message to write
        :return: None
        """
        if(not self.signalsBlocked()):
            self.messageWritten.emit(str(msg))
        self._real_stream.write(msg)

    def write_log(self, msg):
        """
        'msg' is only emitted in the messageWritten signal, not in the original
        stdout/stderr stream, for the purposes of logging. Use in, e.g. a
        custom logging handler's emit() function.

        :param msg: message to write
        :return: None
        """
        if(not self.signalsBlocked()):
            self.messageWritten.emit(str(msg))

    @staticmethod
    def stdout():
        """
        Creates imitation of sys.stdout.
        :return: An XStream instance that interfaces exactly like sys.stdout,
                 but, has redirection capabilities through the
                 messageWritten(str) signal.
        """
        if(not XStream._stdout):
            XStream._stdout = XStream()
            XStream._stdout._real_stream = sys.stdout
            sys.stdout = XStream._stdout
        return XStream._stdout

    @staticmethod
    def stderr():
        """
        Creates imitation of sys.stderr.
        :return: An XStream instance that interfaces exactly like sys.stderr,
                 but, has redirection capabilities through the
                 messageWritten(str) signal.
        """
        if(not XStream._stderr):
            XStream._stderr = XStream()
            XStream._stderr._real_stream = sys.stderr
            sys.stderr = XStream._stderr
        return XStream._stderr


class QtHandler(logging.Handler):
    """
    Version of logging handler "emitting" the message to custom stdout()
    """
    def __init__(self):
        logging.Handler.__init__(self)

    def emit(self, record):
        record = self.format(record)
        if record:
            XStream.stdout().write_log('%s\n'%record)


# Define the default logger
logger = logging.getLogger()

# Add the qt-signal logger
handler = QtHandler()
handler.setFormatter(logging.Formatter(
    fmt="%(asctime)s - %(levelname)s: %(message)s",
    datefmt="%H:%M:%S"
))
logger.addHandler(handler)
