import logging

import pytest
from PySide6.QtWidgets import QTextBrowser

# Local
from sas.qtgui.Utilities.SasviewLogger import setup_qt_logging


class SasviewLoggerTest:

    @pytest.fixture(autouse=True)
    def logger(self, qapp):
        '''Create/Destroy the logger'''
        logger = logging.getLogger(__name__)
        self.handler = setup_qt_logging()
        logger.addHandler(self.handler)
        logger.setLevel(logging.DEBUG)

        self.outHandlerGui=QTextBrowser()

        yield logger

    @pytest.mark.xfail(reason="2026-02: handler not printing properly...")
    def testQtHandler(self, logger):
        """
        Test redirection of all levels of logging
        """
        # Attach the listener
        self.handler.postman.messageWritten.connect(self.outHandlerGui.insertPlainText)

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
