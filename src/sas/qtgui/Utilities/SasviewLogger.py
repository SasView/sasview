import os
import sys
import logging

from PySide6.QtCore import QObject, Signal

LOG_FORMAT = "%(asctime)s - %(levelname)s: %(message)s"
DATE_FORMAT = "%H:%M:%S"

class QtPostman(QObject):
    messageWritten = Signal(str)

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
            self.postman.messageWritten.emit(message)

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
    handler.setFormatter(logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT))
    logger.addHandler(handler)
    return handler
