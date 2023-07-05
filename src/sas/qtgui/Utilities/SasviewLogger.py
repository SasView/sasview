import os
import sys
import logging

from PySide6.QtCore import QObject, Signal

class QtPostman(QObject):
    messageWritten = Signal(str)

class QtLogger(logging.Handler):
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
            self.postman.messageWritten .emit(message)

def setup_qt_logging():
    # Define the default logger
    logger = logging.getLogger()

    # Add the qt-signal logger
    handler = QtLogger()
    handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s - %(levelname)s: %(message)s",
        datefmt="%H:%M:%S"
    ))
    logger.addHandler(handler)

    return handler
        