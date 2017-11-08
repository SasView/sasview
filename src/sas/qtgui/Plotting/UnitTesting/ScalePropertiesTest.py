import sys
import unittest

from PyQt5 import QtGui, QtWidgets

# set up import paths
import sas.qtgui.path_prepare

# Local
from sas.qtgui.Plotting.ScaleProperties import ScaleProperties

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)

class ScalePropertiesTest(unittest.TestCase):
    '''Test the ScaleProperties'''
    def setUp(self):
        '''Create the ScaleProperties'''

        self.widget = ScaleProperties(None)

    def tearDown(self):
        '''Destroy the GUI'''
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        '''Test the GUI in its default state'''
        self.assertIsInstance(self.widget, QtWidgets.QDialog)
        self.assertEqual(self.widget.windowTitle(), "Scale Properties")
        self.assertEqual(self.widget.cbX.count(), 6)
        self.assertEqual(self.widget.cbY.count(), 12)
        self.assertEqual(self.widget.cbView.count(), 6)
        
    def testGetValues(self):
        '''Test the values returned'''
        self.assertEqual(self.widget.getValues(), ("x", "y"))
        self.widget.cbX.setCurrentIndex(2)
        self.widget.cbY.setCurrentIndex(4)
        self.assertEqual(self.widget.getValues(), ("x^(4)", "y*x^(2)"))

    def testSettingView(self):
        '''Test various settings of view'''
        self.widget.cbView.setCurrentIndex(1)
        self.assertEqual(self.widget.getValues(), ("x", "y"))
        self.widget.cbView.setCurrentIndex(5)
        self.assertEqual(self.widget.getValues(), ("x", "y*x^(2)"))

        # Assure the View combobox resets on the x index changes
        self.assertNotEqual(self.widget.cbView.currentIndex(), 0)
        self.widget.cbX.setCurrentIndex(2)
        self.assertEqual(self.widget.cbView.currentIndex(), 0)

        # Same for Y
        self.widget.cbView.setCurrentIndex(6)
        self.assertNotEqual(self.widget.cbView.currentIndex(), 0)
        self.widget.cbY.setCurrentIndex(2)
        self.assertEqual(self.widget.cbView.currentIndex(), 0)
      
if __name__ == "__main__":
    unittest.main()
