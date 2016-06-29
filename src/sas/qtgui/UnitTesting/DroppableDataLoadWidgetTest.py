import sys
import unittest

from PyQt4.QtGui import QApplication
from PyQt4.QtTest import QTest
from PyQt4.QtCore import Qt
from DroppableDataLoadWidget import DroppableDataLoadWidget

app = QApplication(sys.argv)

class DroppableDataLoadWidgetTest(unittest.TestCase):
    '''Test the DroppableDataLoadWidget GUI'''
    def setUp(self):
        '''Create the GUI'''
        self.form = DroppableDataLoadWidget()

if __name__ == "__main__":
    unittest.main()
