import sys
import unittest

from PyQt4 import QtGui

# set up import paths
import path_prepare

# Local
from WindowTitle import WindowTitle

app = QtGui.QApplication(sys.argv)

class WindowTitleTest(unittest.TestCase):
    '''Test the WindowTitle'''
    def setUp(self):
        '''Create the WindowTitle'''
        self.widget = WindowTitle(None, new_title="some title")

    def tearDown(self):
        '''Destroy the GUI'''
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        '''Test the GUI in its default state'''
        self.widget.show()
        self.assertIsInstance(self.widget, QtGui.QDialog)
        self.assertEqual(self.widget.windowTitle(), "Modify Window Title")
        
    def testTitle(self):
        '''Modify the title'''
        self.widget.show()
        app.processEvents()
        # make sure we have the pre-set title
        self.assertEqual(self.widget.txtTitle.text(), "some title")
        # Clear the control and set it to something else
        self.widget.txtTitle.clear()
        self.widget.txtTitle.setText("5 elephants")
        # Retrieve value
        new_title = self.widget.title()
        # Check
        self.assertEqual(new_title, "5 elephants")
       
if __name__ == "__main__":
    unittest.main()
