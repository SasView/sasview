import sys
import logging
import pytest

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

# Local
from sas.qtgui.Utilities.SasviewLogger import QtHandler


class SasviewLoggerTest:

    @pytest.fixture(autouse=True)
    def logger(self, qapp):
        '''Create/Destroy the logger'''
        l = logging.getLogger(__name__)
        self.handler = QtHandler()
        self.handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        l.addHandler(self.handler)
        l.setLevel(logging.DEBUG)

        self.outHandlerGui=QTextBrowser()

        yield l


    def testQtHandler(self, logger):
        """
        Test redirection of all levels of logging
        """
        # Attach the listener
        self.handler.messageWritten.connect(self.outHandlerGui.insertPlainText)

        # Send the signals
        logger.debug('debug message')
        logger.info('info message')
        logger.warning('warning message')
        logger.error('error message')

        out=self.outHandlerGui.toPlainText()

        # Assure everything got logged
        assert 'DEBUG: debug message' in out
        assert 'INFO: info message' in out
        assert 'WARNING: warning message' in out
        assert 'ERROR: error message' in out
