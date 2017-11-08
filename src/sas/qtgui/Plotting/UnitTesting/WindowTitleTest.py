import sys
import unittest

from PyQt5 import QtGui, QtWidgets

# set up import paths
import sas.qtgui.path_prepare

# Local
from sas.qtgui.Plotting.WindowTitle import WindowTitle

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)

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
        self.assertIsInstance(self.widget, QtWidgets.QDialog)
        self.assertEqual(self.widget.windowTitle(), "Modify Window Title")
        
    def testTitle(self):
        '''Modify the title'''
        self.widget.show()
        QtWidgets.qApp.processEvents()
        # make sure we have the pre-set title
        self.assertEqual(self.widget.txtTitle.text(), "some title")
        # Clear the control and set it to something else
        self.widget.txtTitle.clear()
        self.widget.txtTitle.setText("5 elephants")
        QtWidgets.qApp.processEvents()
        # Retrieve value
        new_title = self.widget.title()
        # Check
        self.assertEqual(new_title, "5 elephants")
       
if __name__ == "__main__":
    unittest.main()
