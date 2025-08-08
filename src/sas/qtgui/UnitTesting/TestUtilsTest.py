from PySide6.QtWidgets import QWidget

from sas.qtgui.UnitTesting.TestUtils import QtSignalSpy

# Local
from sas.qtgui.Utilities.GuiUtils import Communicate


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
