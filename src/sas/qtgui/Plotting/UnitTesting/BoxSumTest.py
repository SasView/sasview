import sys
import unittest
from unittest.mock import MagicMock

from PyQt5 import QtGui,QtWidgets
from PyQt5 import QtCore

# set up import paths
import path_prepare

# Local
from sas.qtgui.Plotting.BoxSum import BoxSum

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)

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
        self.assertIsInstance(self.widget.mapper.mappedWidgetAt(0), QtWidgets.QLineEdit)
        self.assertIsInstance(self.widget.mapper.mappedWidgetAt(1), QtWidgets.QLineEdit)
        self.assertIsInstance(self.widget.mapper.mappedWidgetAt(2), QtWidgets.QLineEdit)
        self.assertIsInstance(self.widget.mapper.mappedWidgetAt(3), QtWidgets.QLineEdit)
        self.assertIsInstance(self.widget.mapper.mappedWidgetAt(4), QtWidgets.QLabel)
        self.assertIsInstance(self.widget.mapper.mappedWidgetAt(5), QtWidgets.QLabel)
        self.assertIsInstance(self.widget.mapper.mappedWidgetAt(6), QtWidgets.QLabel)
        self.assertIsInstance(self.widget.mapper.mappedWidgetAt(7), QtWidgets.QLabel)
        self.assertIsInstance(self.widget.mapper.mappedWidgetAt(8), QtWidgets.QLabel)
        
        
if __name__ == "__main__":
    unittest.main()
