import sys
import unittest
from unittest.mock import MagicMock

from PyQt5 import QtGui, QtWidgets
from PyQt5 import QtCore

# set up import paths
import sas.qtgui.path_prepare

# Local
from sas.qtgui.Plotting.SlicerModel import SlicerModel

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)

class SlicerModelTest(unittest.TestCase):
    '''Test the SlicerModel'''
    def setUp(self):
        '''Create the SlicerModel'''
        class SModel(SlicerModel):
            params = {"a":1, "b":2}
            def __init__(self):
                SlicerModel.__init__(self)
            def getParams(self):
                return self.params
            def setParams(self, par):
                self.params = par
        self.model = SModel()

    def tearDown(self):
        '''Destroy the model'''
        self.model = None

    def testBaseClass(self):
        '''Assure that SlicerModel contains pure virtuals'''
        model = SlicerModel()
        with self.assertRaises(NotImplementedError):
            model.setParams()
        with self.assertRaises(NotImplementedError):
            model.setModelFromParams()

    def testDefaults(self):
        '''Test the GUI in its default state'''
        self.assertIsInstance(self.model.model(), QtGui.QStandardItemModel)

    def testSetModelFromParams(self):
        '''Test the model update'''
        # Add a row to params
        new_dict = self.model.getParams()
        new_dict["c"] = 3
        self.model.setParams(new_dict)

        # Call the update
        self.model.setModelFromParams()

        # Check the new model.
        self.assertEqual(self.model.model().rowCount(), 3)
        self.assertEqual(self.model.model().columnCount(), 2)

    def testSetParamsFromModel(self):
        ''' Test the parameters update'''
        # First - the default model
        self.model.setModelFromParams()
        self.assertEqual(self.model.model().rowCount(), 2)
        self.assertEqual(self.model.model().columnCount(), 2)

        # Add a row
        item1 = QtGui.QStandardItem("c")
        item2 = QtGui.QStandardItem(3)
        self.model.model().appendRow([item1, item2])
        # Check the new model. The update should be automatic
        self.assertEqual(self.model.model().rowCount(), 3)
        self.assertEqual(self.model.model().columnCount(), 2)


if __name__ == "__main__":
    unittest.main()
