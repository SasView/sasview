import sys

from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtTest import QTest
from PySide2.QtCore import *

# Local
from sas.qtgui.Utilities.GuiUtils import Communicate
from sas.qtgui.UnitTesting.TestUtils import *

class TestUtilsTest:
    '''Test TestUtils'''

    def testQtSignalSpy(self, qapp):
        '''Create the Spy the correct way'''
        test_string = 'my precious'

        def signalReceived(signal):
            # Test the signal callback
            assert signal == test_string

        communicator = Communicate()
        communicator.statusBarUpdateSignal.connect(signalReceived)

        # Define the signal spy for testing
        widget = QWidget()
        spy = QtSignalSpy(widget, communicator.statusBarUpdateSignal)

        # Emit a signal
        communicator.statusBarUpdateSignal.emit(test_string)

        # Was the signal caught by the signal spy?
        assert spy.count() == 1
