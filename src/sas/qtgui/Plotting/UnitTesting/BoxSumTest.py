import sys
import unittest
from mock import MagicMock

from PyQt4 import QtGui
from PyQt4 import QtCore

# set up import paths
import path_prepare

# Local
from sas.qtgui.Plotting.BoxSum import BoxSum

if not QtGui.QApplication.instance():
    app = QtGui.QApplication(sys.argv)

class BoxSumTest(unittest.TestCase):
    '''Test the BoxSum'''
    def setUp(self):
        '''Create the BoxSum'''
        # example model
        model = QtGui.QStandardItemModel()
        parameters = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]
        for index, parameter in enumerate(parameters):
            model.setData(model.index(0, index),parameter)
        self.widget = BoxSum(None, model=model)

    def tearDown(self):
        '''Destroy the GUI'''
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        '''Test the GUI in its default state'''
        self.assertIsInstance(self.widget.mapper.mappedWidgetAt(0), QtGui.QLineEdit)
        self.assertIsInstance(self.widget.mapper.mappedWidgetAt(1), QtGui.QLineEdit)
        self.assertIsInstance(self.widget.mapper.mappedWidgetAt(2), QtGui.QLineEdit)
        self.assertIsInstance(self.widget.mapper.mappedWidgetAt(3), QtGui.QLineEdit)
        self.assertIsInstance(self.widget.mapper.mappedWidgetAt(4), QtGui.QLabel)
        self.assertIsInstance(self.widget.mapper.mappedWidgetAt(5), QtGui.QLabel)
        self.assertIsInstance(self.widget.mapper.mappedWidgetAt(6), QtGui.QLabel)
        self.assertIsInstance(self.widget.mapper.mappedWidgetAt(7), QtGui.QLabel)
        self.assertIsInstance(self.widget.mapper.mappedWidgetAt(8), QtGui.QLabel)
        
        
if __name__ == "__main__":
    unittest.main()
