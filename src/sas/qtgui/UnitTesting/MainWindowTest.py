import sys
import unittest

from PyQt4.QtGui import *
from PyQt4.QtTest import QTest
from PyQt4.QtCore import *
from mock import MagicMock

# Local
from MainWindow import MainSasViewWindow
from MainWindow import SplashScreen

app = QApplication(sys.argv)

class MainWindowTest(unittest.TestCase):
    '''Test the Main Window GUI'''
    def setUp(self):
        '''Create the GUI'''

        self.widget = MainSasViewWindow(None)

    def tearDown(self):
        '''Destroy the GUI'''
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        '''Test the GUI in its default state'''
        self.assertIsInstance(self.widget, QMainWindow)
        self.assertIsInstance(self.widget.centralWidget(), QWorkspace)
        
    def testSplashScreen(self):
        """
        """
        splash = SplashScreen()
        self.assertIsInstance(splash, QSplashScreen)
       
if __name__ == "__main__":
    unittest.main()
