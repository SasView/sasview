import os
import sys
import logging

from PySide2.QtCore import *


class QtHandler(QObject, logging.Handler):
    """
    Version of logging handler "emitting" the message to custom stdout()
    """
    messageWritten = Signal(str)

    def __init__(self):
        QObject.__init__(self)
        logging.Handler.__init__(self)

    def emit(self, record):
        record = self.format(record)
        if record:
            # self.messageWritten.emit('%s\n'%record)
            pass


def setup_qt_logging():
    # Define the default logger
    logger = logging.getLogger()

    # Add the qt-signal logger
    handler = QtHandler()
    handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s - %(levelname)s: %(message)s",
        datefmt="%H:%M:%S"
    ))
    logger.addHandler(handler)

    return handler
