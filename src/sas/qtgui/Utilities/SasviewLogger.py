import os
import sys
import logging

from PyQt5.QtCore import *


class XStream(QObject):
    _stdout = None
    _stderr = None
    messageWritten = pyqtSignal(str)

    def flush(self):
        pass

    def fileno(self):
        return -1

    def write(self, msg):
        if(not self.signalsBlocked()):
            self.messageWritten.emit(str(msg))

    @staticmethod
    def stdout():
        if(not XStream._stdout):
            XStream._stdout = XStream()
            sys.stdout = XStream._stdout
        return XStream._stdout

    @staticmethod
    def stderr():
        if(not XStream._stderr):
            XStream._stderr = XStream()
            sys.stderr = XStream._stderr
        return XStream._stderr

class QtHandler(logging.Handler):
    """
    Version of logging handler
    "emitting" the message to custom stdout()
    """
    def __init__(self):
        logging.Handler.__init__(self)

    def emit(self, record):
        record = self.format(record)
        if record:
            XStream.stdout().write('%s\n'%record)


# Define the default logger
logger = logging.getLogger()

# Add the file handler
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename=os.path.join(os.path.expanduser("~"),
                                          'sasview.log'))
# Add the qt-signal logger
handler = QtHandler()
handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(handler)
