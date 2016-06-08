import sys
import unittest

from PyQt4.QtGui import *
from PyQt4.QtTest import QTest
from PyQt4.QtCore import *
from mock import MagicMock

# Local
from sas.sasgui.guiframe.dataFitting import Data1D
from DataExplorer import DataExplorerWindow
from GuiManager import GuiManager
from GuiUtils import *
from UnitTesting.TestUtils import QtSignalSpy

app = QApplication(sys.argv)

class DataExplorerTest(unittest.TestCase):
    '''Test the Data Explorer GUI'''
    def setUp(self):
        '''Create the GUI'''
        class dummy_manager(object):
            def communicator(self):
                return Communicate()

        self.form = DataExplorerWindow(None, dummy_manager())

    def tearDown(self):
        '''Destroy the GUI'''
        self.form.close()
        self.form = None

    def testDefaults(self):
        '''Test the GUI in its default state'''
        self.assertIsInstance(self.form, QTabWidget)
        self.assertIsInstance(self.form.treeView, QTreeView)
        self.assertIsInstance(self.form.listView, QListView)
        self.assertEqual(self.form.count(), 2)

        self.assertEqual(self.form.cmdLoad.text(), "Load")
        self.assertEqual(self.form.cmdDelete.text(), "Delete")
        self.assertEqual(self.form.cmdSendTo.text(), "Send to")
        self.assertEqual(self.form.chkBatch.text(), "Batch mode")
        self.assertFalse(self.form.chkBatch.isChecked())

        self.assertEqual(self.form.cbSelect.count(), 6)
        self.assertEqual(self.form.cbSelect.currentIndex(), 0)

        # Class is in the default state even without pressing OK
        self.assertEqual(self.form.treeView.model().rowCount(), 0)
        self.assertEqual(self.form.treeView.model().columnCount(), 0)
        self.assertEqual(self.form.model.rowCount(), 0)
        self.assertEqual(self.form.model.columnCount(), 0)
        
    def testLoadButton(self):
        loadButton = self.form.cmdLoad

        # Mock the system file open method
        QtGui.QFileDialog.getOpenFileName = MagicMock(return_value=None)

        # Click on the Load button
        QTest.mouseClick(loadButton, Qt.LeftButton)

        # Test the getOpenFileName() dialog called once
        self.assertTrue(QtGui.QFileDialog.getOpenFileName.called)
        QtGui.QFileDialog.getOpenFileName.assert_called_once()

    def testDeleteButton(self):

        deleteButton = self.form.cmdDelete

        # Mock the confirmation dialog with return=Yes

        # Populate the model

        # Assure the checkbox is on

        # Click on the delete  button
        QTest.mouseClick(deleteButton, Qt.LeftButton)

        # Test the warning dialog called once
        # self.assertTrue(QtGui.QFileDialog.getOpenFileName.called)

        # Assure the model contains no items

    def testSendToButton(self):        
        sendToButton = self.form.cmdSendTo

        # Mock the current perspective set_data method

        # Populate the model

        # Assure the checkbox is on

        # Click on the Send To  button
        QTest.mouseClick(sendToButton, Qt.LeftButton)

        # Test the set_data method called once
        # self.assertTrue(QtGui.QFileDialog.getOpenFileName.called)

        # Assure the model contains no items

    def testDataSelection(self):
        """
        Tests the functionality of the Selection Option combobox
        """
        # Populate the model with 1d and 2d data
        filename = ["cyl_400_20.txt", "Dec07031.ASC"]
        self.form.readData(filename)

        # Unselect all data
        self.form.cbSelect.setCurrentIndex(1)

        # Test the current selection
        item1D = self.form.model.item(0)
        item2D = self.form.model.item(1)
        self.assertTrue(item1D.checkState() == QtCore.Qt.Unchecked)
        self.assertTrue(item2D.checkState() == QtCore.Qt.Unchecked)        

        # Select all data
        self.form.cbSelect.setCurrentIndex(0)

        # Test the current selection
        self.assertTrue(item1D.checkState() == QtCore.Qt.Checked)
        self.assertTrue(item2D.checkState() == QtCore.Qt.Checked)        

        # select 1d data
        self.form.cbSelect.setCurrentIndex(2)

        # Test the current selection
        self.assertTrue(item1D.checkState() == QtCore.Qt.Checked)
        self.assertTrue(item2D.checkState() == QtCore.Qt.Unchecked)        

        # unselect 1d data
        self.form.cbSelect.setCurrentIndex(3)

        # Test the current selection
        self.assertTrue(item1D.checkState() == QtCore.Qt.Unchecked)
        self.assertTrue(item2D.checkState() == QtCore.Qt.Unchecked)        

        # select 2d data
        self.form.cbSelect.setCurrentIndex(4)

        # Test the current selection
        self.assertTrue(item1D.checkState() == QtCore.Qt.Unchecked)
        self.assertTrue(item2D.checkState() == QtCore.Qt.Checked)        

        # unselect 2d data
        self.form.cbSelect.setCurrentIndex(5)

        # Test the current selection
        self.assertTrue(item1D.checkState() == QtCore.Qt.Unchecked)
        self.assertTrue(item2D.checkState() == QtCore.Qt.Unchecked)        

        # choose impossible index and assure the code raises
        #with self.assertRaises(Exception):
        #    self.form.cbSelect.setCurrentIndex(6)

    def testReadData(self):
        """
        Test the readData() method
        """
        filename = ["cyl_400_20.txt"]
        self.form.manager.add_data = MagicMock()

        # Initialize signal spy instances
        spy_status_update = QtSignalSpy(self.form, self.form.communicate.statusBarUpdateSignal)
        spy_data_received = QtSignalSpy(self.form, self.form.communicate.fileDataReceivedSignal)

        # Read in the file
        self.form.readData(filename)

        # Expected two status bar updates
        self.assertEqual(spy_status_update.count(), 2)
        self.assertIn(filename[0], str(spy_status_update.called()[0]['args'][0]))
        self.assertIn("Loading Data Complete", str(spy_status_update.called()[1]['args'][0]))

        # Expect one Data Received signal
        self.assertEqual(spy_data_received.count(), 1)

        # Assure returned dictionary has correct data
        # We don't know the data ID, so need to iterate over dict
        data_dict = spy_data_received.called()[0]['args'][0]
        for data_key, data_value in data_dict.iteritems():
            self.assertIsInstance(data_value, Data1D)

        # Check that the model contains the item
        self.assertEqual(self.form.model.rowCount(), 1)
        self.assertEqual(self.form.model.columnCount(), 1)

        # The 0th item header should be the name of the file
        model_item = self.form.model.index(0,0)
        model_name = str(self.form.model.data(model_item).toString())
        self.assertEqual(model_name, filename[0])

        # Assure add_data on data_manager was called (last call)
        self.assertTrue(self.form.manager.add_data.called)

    def testGetWList(self):
        """
        """
        list = self.form.getWlist()
        defaults = 'All (*.*);;canSAS files (*.xml);;SESANS files' +\
            ' (*.ses);;ASCII files (*.txt);;IGOR 2D files (*.asc);;' +\
            'IGOR/DAT 2D Q_map files (*.dat);;IGOR 1D files (*.abs);;'+\
            'HFIR 1D files (*.d1d);;DANSE files (*.sans);;NXS files (*.nxs)'
        self.assertEqual(defaults, list)

    def testLoadComplete(self):
        """
        """
        # Initialize signal spy instances        
        spy_status_update = QtSignalSpy(self.form, self.form.communicate.statusBarUpdateSignal)
        spy_data_received = QtSignalSpy(self.form, self.form.communicate.fileDataReceivedSignal)

        # Need an empty Data1D object
        mockData = Data1D()

        # Call the tested method
        self.form.loadComplete({"a":mockData}, message="test message")

        # test the signals 
        self.assertEqual(spy_status_update.count(), 1)
        self.assertIn("message", str(spy_status_update.called()[0]['args'][0]))
        self.assertEqual(spy_data_received.count(), 1)

        # The data_manager update is going away, so don't bother testing
       
if __name__ == "__main__":
    unittest.main()
