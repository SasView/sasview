import sys
import unittest

from PyQt4.QtGui import *
from PyQt4.QtTest import QTest
from PyQt4.QtCore import *
from mock import MagicMock

# Local
from GuiManager import GuiManager

#app = QApplication(sys.argv)

class GuiManagerTest(unittest.TestCase):
    '''Test the WelcomePanel'''
    def setUp(self):
        '''Create the tested object'''

        self.manager = GuiManager(None)

    def tearDown(self):
        '''Destroy the GUI'''
        self.manager = None

    def testDefaults(self):
        '''Test the object in its default state'''
        pass
        
    def testUpdatePerspective(self):
        """
        """
        pass

    def testUpdateStatusBar(self):
        """
        """
        pass

    def testSetData(self):
        """
        """
        pass

    def testSetData(self):
        """
        """
        pass

    def testActions(self):
        """
        """
        pass

    # test each action separately
       
if __name__ == "__main__":
    unittest.main()

