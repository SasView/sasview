import logging

from PySide6.QtCore import QObject, Signal


class SasViewLogFormatter(logging.Formatter):
    LOG_FORMAT = "%(asctime)s - <b{}>%(levelname)s</b>: %(message)s"
    DATE_FORMAT = "%H:%M:%S"

    LOG_COLORS = {"WARNING": "orange", "ERROR": "red", "CRITICAL": "red"}
    def format(self, record):
        """
        Give extra formatting on error messages
        """
        level_style = ""
        if record.levelname in self.LOG_COLORS:
            level_style = f' style="color: {self.LOG_COLORS[record.levelname]}"'

        return logging.Formatter(fmt=self.LOG_FORMAT.format(level_style), datefmt=self.DATE_FORMAT).format(record)

class QtPostman(QObject):
    messageWritten = Signal(object)

class QtHandler(logging.Handler):
    """
    Emit python log messages through a Qt signal. Receivers can connect
    to *handler.postman.messageWritten* with a method accepting the
    formatted log entry produced by the logger.
    """
    def __init__(self):
        logging.Handler.__init__(self)
        self.postman = QtPostman()

    def emit(self, record):
        message = self.format(record)
        if message:
            self.postman.messageWritten.emit((message, record))

def setup_qt_logging():
    # Add the qt-signal logger
    logger = logging.root

    # If a QtHandler is already defined in log.ini then use it. This allows
    # config to override the default message formatting. We don't do this
    # by default because we may be using sasview as a library and don't
    # want to load Qt.
    for handler in logger.handlers:
        if isinstance(handler, QtHandler):
            return handler

    handler = QtHandler()
    handler.setFormatter(SasViewLogFormatter())
    logger.addHandler(handler)
    return handler
