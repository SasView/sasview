import sys
import unittest

from PyQt4.QtGui import QApplication
from PyQt4.QtTest import QTest
from PyQt4.QtCore import Qt
from DroppableDataLoadWidget import DroppableDataLoadWidget
from GuiUtils import *

app = QApplication(sys.argv)

class DroppableDataLoadWidgetTest(unittest.TestCase):
    '''Test the DroppableDataLoadWidget GUI'''
    def setUp(self):
        '''Create the GUI'''
        class dummy_manager(object):
            def communicator(self):
                return Communicate()
            def perspective(self):
                return MyPerspective()

        self.form = DroppableDataLoadWidget(None, guimanager=dummy_manager())
        # create dummy mime objects

    def testDragIsOK(self):
        """
        Test the item being dragged over the load widget
        """
        pass

    def testDropEvent(self):
        """
        Test what happens if an object is dropped onto the load widget
        """
        pass

if __name__ == "__main__":
    unittest.main()
