import sys
import unittest

from PyQt4.QtGui import *
from PyQt4.QtTest import QTest
from PyQt4.QtCore import *
from mock import MagicMock

# Local
from sas.qtgui.Utilities.GuiUtils import Communicate
from sas.qtgui.UnitTesting.TestUtils import *

app = QApplication(sys.argv)

class TestUtilsTest(unittest.TestCase):
    '''Test TestUtils'''

    def testQtSignalSpy(self):
        '''Create the Spy the correct way'''
        test_string = 'my precious'

        def signalReceived(signal):
            # Test the signal callback
            self.assertEqual(signal, test_string)

        communicator = Communicate()
        communicator.statusBarUpdateSignal.connect(signalReceived)

        # Define the signal spy for testing
        widget = QWidget()
        spy = QtSignalSpy(widget, communicator.statusBarUpdateSignal)

        # Emit a signal
        communicator.statusBarUpdateSignal.emit(test_string)

        # Was the signal caught by the signal spy?
        self.assertEqual(spy.count(), 1)

if __name__ == "__main__":
    unittest.main()
