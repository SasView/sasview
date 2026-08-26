import logging

import pytest
from PySide6.QtWidgets import QTextBrowser

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

        try:
            yield logger
        finally:
            # Remove the QtHandler logger assigned by setup_qt_logging
            logging.root.removeHandler(self.handler)

    def testQtHandler(self, logger):
        """
        Test redirection of all levels of logging
        """
        # Attach the listener. The QtHandler postman emits a (message, record)
        # pair as the signal. We only want the message, not the associated record.
        self.handler.postman.messageWritten.connect(lambda signal: self.outHandlerGui.insertPlainText(signal[0]))

        # Send the signals
        logger.debug('debug message')
        logger.info('info message')
        logger.warning('warning message')
        logger.error('error message')

        out=self.outHandlerGui.toPlainText()

        # Assure everything got logged
        assert 'DEBUG' in out and 'debug message' in out
        assert 'INFO' in out and 'info message' in out
        assert 'WARNING' in out and 'warning message' in out
        assert 'ERROR' in out and 'error message' in out
