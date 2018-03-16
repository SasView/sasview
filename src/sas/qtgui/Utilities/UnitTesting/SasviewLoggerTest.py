import sys
import unittest
import logging

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

# set up import paths
import sas.qtgui.path_prepare

# Local
from sas.qtgui.Utilities.SasviewLogger import XStream
from sas.qtgui.Utilities.SasviewLogger import QtHandler

if not QApplication.instance():
    app = QApplication(sys.argv)

class SasviewLoggerTest(unittest.TestCase):
    def setUp(self):
        """
        Prepare the logger
        """
        self.logger = logging.getLogger(__name__)
        handler = QtHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)

        self.outHandlerGui=QTextBrowser()


    def testQtHandler(self):
        """
        Test redirection of all levels of logging
        """
        # Attach the listeners
        XStream.stderr().messageWritten.connect( self.outHandlerGui.insertPlainText )
        XStream.stdout().messageWritten.connect( self.outHandlerGui.insertPlainText )

        # Send the signals
        self.logger.debug('debug message')
        self.logger.info('info message')
        self.logger.warning('warning message')
        self.logger.error('error message')
        sys.stdout.write('with stdout')
        sys.stderr.write('with stderr')

        out=self.outHandlerGui.toPlainText()

        # Assure everything got logged
        self.assertIn('DEBUG: debug message', out)
        self.assertIn('INFO: info message', out)
        self.assertIn('WARNING: warning message', out)
        self.assertIn('ERROR: error message', out)
        self.assertIn('with stdout', out)
        self.assertIn('with stderr', out)

if __name__ == "__main__":
    unittest.main()
