import sys
import unittest

from PyQt4.QtGui import *
from PyQt4.QtTest import QTest
from PyQt4.QtCore import *
from mock import MagicMock

# Local
from GuiUtils import Communicate
from UnitTesting.TestUtils import *

app = QApplication(sys.argv)

class TestUtilsTest(unittest.TestCase):
    '''Test TestUtils'''

    def testQtSignalSpy(self):
        '''Create the Spy the correct way'''

        widget = QWidget()
        signal = Communicate.statusBarUpdateSignal
        self.spy = QtSignalSpy(widget, signal)

        # Emit a signal
        signal.emit('aa')

        # Test the spy object

if __name__ == "__main__":
    unittest.main()
