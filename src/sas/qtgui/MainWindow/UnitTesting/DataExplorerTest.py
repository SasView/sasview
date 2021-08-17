import sys
import time
import unittest
import random

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtTest import QTest
from PyQt5.QtCore import *
from unittest.mock import MagicMock
from unittest.mock import patch
from mpl_toolkits.mplot3d import Axes3D

# set up import paths
import path_prepare

# Local
from sas.qtgui.Plotting.PlotterData import Data1D, Data2D
from sas.sascalc.dataloader.loader import Loader
from sas.qtgui.MainWindow.DataManager import DataManager

from sas.qtgui.MainWindow.DataExplorer import DataExplorerWindow
from sas.qtgui.MainWindow.GuiManager import GuiManager
from sas.qtgui.Utilities.GuiUtils import *
from sas.qtgui.UnitTesting.TestUtils import QtSignalSpy
from sas.qtgui.Plotting.Plotter import Plotter
from sas.qtgui.Plotting.Plotter2D import Plotter2D
import sas.qtgui.Plotting.PlotHelper as PlotHelper

from sas.sasview import __version__ as SASVIEW_VERSION

if not QApplication.instance():
    app = QApplication(sys.argv)


class MyPerspective(object):
    def __init__(self):
        self.name = "Dummy Perspective"

    def communicator(self):
        return Communicate()

    def allowBatch(self):
        return True

    def allowSwap(self):
        return True

    def setData(self, data_item=None, is_batch=False):
        return None

    def swapData(self, data_item=None, is_batch=False):
        return None

    def title(self):
        return self.name


class dummy_manager(object):
    def __init__(self):
        self._perspective = MyPerspective()

    def communicator(self):
        return Communicate()

    def perspective(self):
        return self._perspective

    def workspace(self):
        return None

    class _parent(object):
        screen_width = 1024
        screen_height = 768

class DataExplorerTest(unittest.TestCase):
    '''Test the Data Explorer GUI'''
    def setUp(self):
        '''Create the GUI'''
        self.form = DataExplorerWindow(None, dummy_manager())

    def tearDown(self):
        '''Destroy the GUI'''
        self.form.close()
        self.form = None

    def testDefaults(self):
        '''Test the GUI in its default state'''
        # Tab widget
        self.assertIsInstance(self.form, QTabWidget)
        self.assertEqual(self.form.count(), 2)

        # Buttons - data tab
        self.assertEqual(self.form.cmdLoad.text(), "Load data")
        self.assertEqual(self.form.cmdDeleteData.text(), "Delete Data")
        self.assertEqual(self.form.cmdDeleteTheory.text(), "Delete")
        self.assertEqual(self.form.cmdFreeze.text(), "Freeze Theory")
        self.assertEqual(self.form.cmdSendTo.text(), "Send data to")
        self.assertEqual(self.form.cmdSendTo.iconSize(), QSize(32, 32))
        self.assertIsInstance(self.form.cmdSendTo.icon(), QIcon)
        self.assertEqual(self.form.chkBatch.text(), "Batch mode")
        self.assertFalse(self.form.chkBatch.isChecked())
        self.assertEqual(self.form.chkSwap.text(), "Swap data")
        self.assertFalse(self.form.chkSwap.isChecked())

        # Buttons - theory tab

        # Combo boxes
        self.assertEqual(self.form.cbSelect.count(), 6)
        self.assertEqual(self.form.cbSelect.currentIndex(), 0)

        # Models - data
        self.assertIsInstance(self.form.model, QStandardItemModel)
        self.assertEqual(self.form.treeView.model().rowCount(), 0)
        self.assertEqual(self.form.treeView.model().columnCount(), 0)
        self.assertEqual(self.form.model.rowCount(), 0)
        self.assertEqual(self.form.model.columnCount(), 0)
        self.assertIsInstance(self.form.data_proxy, QSortFilterProxyModel)
        self.assertEqual(self.form.data_proxy.sourceModel(), self.form.model)
        self.assertEqual("[^()]", str(self.form.data_proxy.filterRegExp().pattern()))
        self.assertIsInstance(self.form.treeView, QTreeView)

        # Models - theory
        self.assertIsInstance(self.form.theory_model, QStandardItemModel)
        self.assertEqual(self.form.freezeView.model().rowCount(), 0)
        self.assertEqual(self.form.freezeView.model().columnCount(), 0)
        self.assertEqual(self.form.theory_model.rowCount(), 0)
        self.assertEqual(self.form.theory_model.columnCount(), 0)
        self.assertIsInstance(self.form.theory_proxy, QSortFilterProxyModel)
        self.assertEqual(self.form.theory_proxy.sourceModel(), self.form.theory_model)
        self.assertEqual("[^()]", str(self.form.theory_proxy.filterRegExp().pattern()))
        self.assertIsInstance(self.form.freezeView, QTreeView)

    def testWidgets(self):
        """
        Test if all required widgets got added
        """
    def testLoadButton(self):
        loadButton = self.form.cmdLoad

        filename = "cyl_400_20.txt"
        # Initialize signal spy instances
        spy_file_read = QtSignalSpy(self.form, self.form.communicator.fileReadSignal)

        # Return no files.
        QFileDialog.getOpenFileNames = MagicMock(return_value=('',''))

        # Click on the Load button
        QTest.mouseClick(loadButton, Qt.LeftButton)

        # Test the getOpenFileName() dialog called once
        self.assertTrue(QFileDialog.getOpenFileNames.called)
        QFileDialog.getOpenFileNames.assert_called_once()

        # Make sure the signal has not been emitted
        self.assertEqual(spy_file_read.count(), 0)

        # Now, return a single file
        QFileDialog.getOpenFileNames = MagicMock(return_value=(filename,''))

        # Click on the Load button
        QTest.mouseClick(loadButton, Qt.LeftButton)
        qApp.processEvents()

        # Test the getOpenFileName() dialog called once
        self.assertTrue(QFileDialog.getOpenFileNames.called)
        QFileDialog.getOpenFileNames.assert_called_once()

        # Expected one spy instance
        #self.assertEqual(spy_file_read.count(), 1)
        #self.assertIn(filename, str(spy_file_read.called()[0]['args'][0]))

    def testLoadFiles(self):
        """
        Test progress bar update while loading of multiple files
        """
        # Set up the spy on progress bar update signal
        spy_progress_bar_update = QtSignalSpy(self.form,
            self.form.communicator.progressBarUpdateSignal)

        # Populate the model
        filename = ["cyl_400_20.txt", "P123_D2O_10_percent.dat", "cyl_400_20.txt"]
        self.form.readData(filename)

        # 0, 0, 33, 66, -1 -> 5 signals reaching progressBar
        self.assertEqual(spy_progress_bar_update.count(), 5)

        expected_list = [0, 0, 33, 66, -1]
        spied_list = [spy_progress_bar_update.called()[i]['args'][0] for i in range(5)]
        self.assertEqual(expected_list, spied_list)
        
    def testDeleteButton(self):
        """
        Functionality of the delete button
        """
        deleteButton = self.form.cmdDeleteData

        # Mock the confirmation dialog with return=No
        QMessageBox.question = MagicMock(return_value=QMessageBox.No)

        # Populate the model
        filename = ["cyl_400_20.txt", "cyl_400_20.txt", "cyl_400_20.txt"]
        self.form.readData(filename)

        # Assure the model contains three items
        self.assertEqual(self.form.model.rowCount(), 3)

        # Assure the checkboxes are on
        item1 = self.form.model.item(0)
        item2 = self.form.model.item(1)
        item3 = self.form.model.item(2)
        self.assertTrue(item1.checkState() == Qt.Checked)
        self.assertTrue(item2.checkState() == Qt.Checked)
        self.assertTrue(item3.checkState() == Qt.Checked)

        # Click on the delete  button
        QTest.mouseClick(deleteButton, Qt.LeftButton)

        # Test the warning dialog called once
        self.assertTrue(QMessageBox.question.called)

        # Assure the model still contains the items
        self.assertEqual(self.form.model.rowCount(), 3)

        # Now, mock the confirmation dialog with return=Yes
        QMessageBox.question = MagicMock(return_value=QMessageBox.Yes)

        # Click on the delete  button
        QTest.mouseClick(deleteButton, Qt.LeftButton)

        # Test the warning dialog called once
        self.assertTrue(QMessageBox.question.called)

        # Assure the model contains no items
        self.assertEqual(self.form.model.rowCount(), 0)

        # Click delete once again to assure no nasty behaviour on empty model
        QTest.mouseClick(deleteButton, Qt.LeftButton)

    def testDeleteTheory(self):
        """
        Test that clicking "Delete" in theories tab removes selected indices
        """
        deleteButton = self.form.cmdDeleteTheory

        # Mock the confirmation dialog with return=No
        QMessageBox.question = MagicMock(return_value=QMessageBox.No)

        # Populate the model
        item1 = HashableStandardItem(True)
        item1.setCheckable(True)
        item1.setCheckState(Qt.Checked)
        item1.setText("item 1")
        self.form.theory_model.appendRow(item1)
        item2 = HashableStandardItem(True)
        item2.setCheckable(True)
        item2.setCheckState(Qt.Unchecked)
        item2.setText("item 2")
        self.form.theory_model.appendRow(item2)

        # Assure the model contains two items
        self.assertEqual(self.form.theory_model.rowCount(), 2)

        # Assure the checkboxes are on
        self.assertTrue(item1.checkState() == Qt.Checked)
        self.assertTrue(item2.checkState() == Qt.Unchecked)

        # Click on the delete  button
        QTest.mouseClick(deleteButton, Qt.LeftButton)

        # Test the warning dialog called once
        self.assertTrue(QMessageBox.question.called)

        # Assure the model still contains the items
        self.assertEqual(self.form.theory_model.rowCount(), 2)

        # Now, mock the confirmation dialog with return=Yes
        QMessageBox.question = MagicMock(return_value=QMessageBox.Yes)

        # Click on the delete  button
        QTest.mouseClick(deleteButton, Qt.LeftButton)

        # Test the warning dialog called once
        self.assertTrue(QMessageBox.question.called)

        # Assure the model contains 1 item
        self.assertEqual(self.form.theory_model.rowCount(), 1)

        # Set the remaining item to checked
        self.form.theory_model.item(0).setCheckState(Qt.Checked)

        # Click on the delete button again
        QTest.mouseClick(deleteButton, Qt.LeftButton)

        # Assure the model contains no items
        self.assertEqual(self.form.theory_model.rowCount(), 0)

        # Click delete once again to assure no nasty behaviour on empty model
        QTest.mouseClick(deleteButton, Qt.LeftButton)


    def testSendToButton(self):
        """
        Test that clicking the Send To button sends checked data to a perspective
        """
        # Send empty data
        mocked_perspective = self.form._perspective()
        mocked_perspective.setData = MagicMock()

        # Click on the Send To  button
        QTest.mouseClick(self.form.cmdSendTo, Qt.LeftButton)

        # The set_data method not called
        self.assertFalse(mocked_perspective.setData.called)

        # Populate the model
        filename = ["cyl_400_20.txt"]
        self.form.readData(filename)

        QApplication.processEvents()

        # setData is the method we want to see called
        mocked_perspective.swapData = MagicMock()

        # Assure the checkbox is on
        self.form.cbSelect.setCurrentIndex(0)

        # Click on the Send To  button
        QTest.mouseClick(self.form.cmdSendTo, Qt.LeftButton)

        QApplication.processEvents()

        # Test the set_data method called
        self.assertTrue(mocked_perspective.setData.called)
        self.assertFalse(mocked_perspective.swapData.called)

        # Now select the swap data checkbox
        self.form.chkSwap.setChecked(True)

        # Click on the Send To  button
        QTest.mouseClick(self.form.cmdSendTo, Qt.LeftButton)

        QApplication.processEvents()

        # Now the swap data method should be called
        self.assertTrue(mocked_perspective.setData.called_once)
        self.assertTrue(mocked_perspective.swapData.called)

        # Test the exception block
        QMessageBox.exec_ = MagicMock()
        QMessageBox.setText = MagicMock()
        mocked_perspective.swapData = MagicMock(side_effect = Exception("foo"))

        # Click on the button to so the mocked swapData method raises an exception
        QTest.mouseClick(self.form.cmdSendTo, Qt.LeftButton)

        # Assure the message box popped up
        QMessageBox.exec_.assert_called_once()
        # With the right message
        QMessageBox.setText.assert_called_with("foo")

        # open another file
        filename = ["cyl_400_20.txt"]
        self.form.readData(filename)

        # Mock the warning message and the swapData method
        QMessageBox.exec_ = MagicMock()
        QMessageBox.setText = MagicMock()
        mocked_perspective.swapData = MagicMock()

        # Click on the button to swap both datasets to the perspective
        QTest.mouseClick(self.form.cmdSendTo, Qt.LeftButton)

        # Assure the message box popped up
        QMessageBox.exec_.assert_called_once()
        # With the right message
        QMessageBox.setText.assert_called_with(
            "Dummy Perspective does not allow replacing multiple data.")

    def testDataSelection(self):
        """
        Tests the functionality of the Selection Option combobox
        """
        # Populate the model with 1d and 2d data
        filename = ["cyl_400_20.txt", "P123_D2O_10_percent.dat"]
        self.form.readData(filename)

        # Wait a moment for data to load
        time.sleep(1)
        # Unselect all data
        self.form.cbSelect.activated.emit(1)
        # Test the current selection
        item1D = self.form.model.item(0)
        item2D = self.form.model.item(1)

        self.assertTrue(item1D.checkState() == Qt.Unchecked)
        self.assertTrue(item2D.checkState() == Qt.Unchecked)        

        # Select all data
        self.form.cbSelect.activated.emit(0)

        # Test the current selection
        self.assertTrue(item1D.checkState() == Qt.Checked)
        self.assertTrue(item2D.checkState() == Qt.Checked)        

        # select 1d data
        self.form.cbSelect.activated.emit(2)
        # Test the current selection
        self.assertTrue(item1D.checkState() == Qt.Checked)
        self.assertTrue(item2D.checkState() == Qt.Checked)

        # unselect 1d data
        self.form.cbSelect.activated.emit(3)

        # Test the current selection
        self.assertTrue(item1D.checkState() == Qt.Unchecked)
        self.assertTrue(item2D.checkState() == Qt.Checked)

        # select 2d data
        self.form.cbSelect.activated.emit(4)

        # Test the current selection
        self.assertTrue(item1D.checkState() == Qt.Unchecked)
        self.assertTrue(item2D.checkState() == Qt.Checked)        

        # unselect 2d data
        self.form.cbSelect.activated.emit(5)

        # Test the current selection
        self.assertTrue(item1D.checkState() == Qt.Unchecked)
        self.assertTrue(item2D.checkState() == Qt.Unchecked)        

    def testFreezeTheory(self):
        """
        Assure theory freeze functionality works
        """
        # Not yet tested - agree on design first.
        pass

    def testRecursivelyCloneItem(self):
        """
        Test the rescursive QAbstractItem/QStandardItem clone
        """
        # Create an item with several branches
        item1 = QStandardItem()
        item2 = QStandardItem()
        item3 = QStandardItem()
        item4 = QStandardItem()
        item5 = QStandardItem()
        item6 = QStandardItem()

        item4.appendRow(item5)
        item2.appendRow(item4)
        item2.appendRow(item6)
        item1.appendRow(item2)
        item1.appendRow(item3)

        # Clone
        new_item = self.form.recursivelyCloneItem(item1)

        # assure the trees look identical
        self.assertEqual(item1.rowCount(), new_item.rowCount())
        self.assertEqual(item1.child(0).rowCount(), new_item.child(0).rowCount())
        self.assertEqual(item1.child(1).rowCount(), new_item.child(1).rowCount())
        self.assertEqual(item1.child(0).child(0).rowCount(), new_item.child(0).child(0).rowCount())

    def testReadData(self):
        """
        Test the low level readData() method
        """
        filename = ["cyl_400_20.txt"]
        self.form.manager.add_data = MagicMock()

        # Initialize signal spy instances
        spy_status_update = QtSignalSpy(self.form, self.form.communicator.statusBarUpdateSignal)
        spy_data_received = QtSignalSpy(self.form, self.form.communicator.fileDataReceivedSignal)

        # Read in the file
        self.form.readData(filename)

        # Expected two status bar updates
        self.assertEqual(spy_status_update.count(), 2)
        self.assertIn(filename[0], str(spy_status_update.called()[0]['args'][0]))


        # Check that the model contains the item
        self.assertEqual(self.form.model.rowCount(), 1)
        self.assertEqual(self.form.model.columnCount(), 1)

        # The 0th item header should be the name of the file
        model_item = self.form.model.index(0,0)
        model_name = self.form.model.data(model_item)
        self.assertEqual(model_name, filename[0])

    def skip_testDisplayHelp(self): # Skip due to help path change
        """
        Test that the Help window gets shown correctly
        """
        partial_url = "qtgui/MainWindow/data_explorer_help.html"
        button1 = self.form.cmdHelp
        button2 = self.form.cmdHelp_2

        # Click on the Help button
        QTest.mouseClick(button1, Qt.LeftButton)
        qApp.processEvents()

        # Check the browser
        self.assertIn(partial_url, str(self.form._helpView.url()))
        # Close the browser
        self.form._helpView.close()

        # Click on the Help_2 button
        QTest.mouseClick(button2, Qt.LeftButton)
        qApp.processEvents()
        # Check the browser
        self.assertIn(partial_url, str(self.form._helpView.url()))

    def testLoadFile(self):
        """
        Test the threaded call to readData()
        """
        #self.form.loadFile()
        pass

    def testGetWList(self):
        """
        Test the list of known extensions
        """
        w_list = self.form.getWlist()

        defaults = 'All (*.*);;canSAS files (*.xml);;SESANS files' +\
            ' (*.ses);;ASCII files (*.txt);;' +\
            'IGOR/DAT 2D Q_map files (*.dat);;IGOR 1D files (*.abs);;'+\
            'DANSE files (*.sans)'
        default_list = defaults.split(';;')

        for def_format in default_list:
            self.assertIn(def_format, w_list)
       
    def testLoadComplete(self):
        """
        Test the callback method updating the data object
        """
        message="Loading Data Complete"
        data_dict = {"a1":Data1D()}
        output_data = (data_dict, message)

        self.form.manager.add_data = MagicMock()

        # Initialize signal spy instances
        spy_status_update = QtSignalSpy(self.form, self.form.communicator.statusBarUpdateSignal)
        spy_data_received = QtSignalSpy(self.form, self.form.communicator.fileDataReceivedSignal)

        # Read in the file
        self.form.loadComplete(output_data)

        # "Loading data complete" no longer sent in LoadFile but in callback
        self.assertIn("Loading Data Complete", str(spy_status_update.called()[0]['args'][0]))

        # Expect one Data Received signal
        self.assertEqual(spy_data_received.count(), 1)

        # Assure returned dictionary has correct data
        # We don't know the data ID, so need to iterate over dict
        data_dict = spy_data_received.called()[0]['args'][0]
        for data_key, data_value in data_dict.items():
            self.assertIsInstance(data_value, Data1D)

        # Assure add_data on data_manager was called (last call)
        self.assertTrue(self.form.manager.add_data.called)

    @patch('sas.qtgui.Utilities.GuiUtils.plotsFromCheckedItems')
    def testNewPlot1D(self, test_patch):
        """
        Creating new plots from Data1D/2D
        """
        loader = Loader()
        manager = DataManager()
        PlotHelper.clear()
        self.form.enableGraphCombo(None)

        # Make sure the controls are disabled
        self.assertFalse(self.form.cbgraph.isEnabled())
        self.assertFalse(self.form.cmdAppend.isEnabled())

        # get Data1D
        p_file="cyl_400_20.txt"
        output_object = loader.load(p_file)
        new_data = [(None, manager.create_gui_data(output_object[0], p_file))]
        _, test_data = new_data[0]
        self.assertTrue(f'Data file generated by SasView v{SASVIEW_VERSION}' in
                        test_data.notes)

        # Mask retrieval of the data
        test_patch.return_value = new_data

        # Mask plotting
        self.form.parent.workspace = MagicMock()

        # Call the plotting method
        self.form.newPlot()

        time.sleep(1)
        QApplication.processEvents()

        # The plot was registered
        self.assertEqual(len(PlotHelper.currentPlots()), 1)

        self.assertTrue(self.form.cbgraph.isEnabled())
        self.assertTrue(self.form.cmdAppend.isEnabled())

    @patch('sas.qtgui.Utilities.GuiUtils.plotsFromCheckedItems')
    def testNewPlot2D(self, test_patch):
        """
        Creating new plots from Data1D/2D
        """
        loader = Loader()
        manager = DataManager()
        PlotHelper.clear()
        self.form.enableGraphCombo(None)

        # Make sure the controls are disabled
        self.assertFalse(self.form.cbgraph.isEnabled())
        self.assertFalse(self.form.cmdAppend.isEnabled())

        # get Data2D
        p_file="P123_D2O_10_percent.dat"
        output_object = loader.load(p_file)
        new_data = [(None, manager.create_gui_data(output_object[0], p_file))]

        # Mask retrieval of the data
        test_patch.return_value = new_data

        # Mask plotting
        self.form.parent.workspace = MagicMock()

        # Call the plotting method
        #self.form.newPlot()
        #QApplication.processEvents()

        # The plot was registered
        #self.assertEqual(len(PlotHelper.currentPlots()), 1)

        #self.assertTrue(self.form.cbgraph.isEnabled())
        #self.assertTrue(self.form.cmdAppend.isEnabled())

    @patch('sas.qtgui.Utilities.GuiUtils.plotsFromCheckedItems')
    def testAppendPlot(self, test_patch):
        """
        Creating new plots from Data1D/2D
        """
        loader = Loader()
        manager = DataManager()

        PlotHelper.clear()
        self.form.enableGraphCombo(None)

        # Make sure the controls are disabled
        self.assertFalse(self.form.cbgraph.isEnabled())
        self.assertFalse(self.form.cmdAppend.isEnabled())

        # get Data1D
        p_file="cyl_400_20.txt"
        output_object = loader.load(p_file)
        output_item = QStandardItem()
        new_data = [(output_item, manager.create_gui_data(output_object[0], p_file))]

        # Mask plotting
        self.form.parent.workspace = MagicMock()

        # Mask the plot show call
        Plotter.show = MagicMock()

        # Mask retrieval of the data
        test_patch.return_value = new_data

        # Call the plotting method
        self.form.newPlot()

        # Call the plotting method again, so we have 2 graphs
        self.form.newPlot()

        QApplication.processEvents()
        # See that we have two plots
        self.assertEqual(len(PlotHelper.currentPlots()), 2)

        # Add data to plot #1
        self.form.cbgraph.setCurrentIndex(1)
        self.form.appendPlot()

        # See that we still have two plots
        self.assertEqual(len(PlotHelper.currentPlots()), 2)

    def testUpdateGraphCombo(self):
        """
        Test the combo box update
        """
        PlotHelper.clear()

        graph_list=["1","2","3"]
        self.form.updateGraphCombo(graph_list)

        self.assertEqual(self.form.cbgraph.count(), 3)
        self.assertEqual(self.form.cbgraph.currentText(), '1')

        graph_list=[]
        self.form.updateGraphCombo(graph_list)
        self.assertEqual(self.form.cbgraph.count(), 0)

    def testUpdateModelFromPerspective(self):
        """
        Assure the model update is correct
        """
        good_item = QStandardItem()
        bad_item = "I'm so bad"

        self.form.model.reset = MagicMock()

        self.form.updateModelFromPerspective(good_item)

        # See that the model got reset
        # self.form.model.reset.assert_called_once()

        # See that the bad item causes raise
        with self.assertRaises(Exception):
            self.form.updateModelFromPerspective(bad_item)

    def testContextMenu(self):
        """
        See if the context menu is present
        """
        # get Data1D
        p_file=["cyl_400_20.txt"]
        # Read in the file
        output, message = self.form.readData(p_file)
        self.form.loadComplete((output, message))

        # Pick up the treeview index corresponding to that file
        index = self.form.treeView.indexAt(QPoint(5,5))
        self.form.show()

        # Find out the center pointof the treeView row
        rect = self.form.treeView.visualRect(index).center()

        self.form.context_menu.exec_ = MagicMock()

        # Move the mouse pointer to the first row
        QTest.mouseMove(self.form.treeView.viewport(), pos=rect)

        # This doesn't invoke the action/signal. Investigate why?
        # QTest.mouseClick(self.form.treeView.viewport(), Qt.RightButton, pos=rect)

        # Instead, send the signal directly
        self.form.treeView.customContextMenuRequested.emit(rect)

        # See that the menu has been shown
        self.form.context_menu.exec_.assert_called_once()

    def baseNameStateCheck(self):
        """
        Helper method for the Name Change Tests Below - Check the base state of the window
        """
        self.assertTrue(hasattr(self.form, "nameChangeBox"))
        self.assertTrue(self.form.nameChangeBox.isModal())
        self.assertEqual(self.form.nameChangeBox.windowTitle(), "Display Name Change")
        self.assertFalse(self.form.nameChangeBox.isVisible())
        self.assertIsNone(self.form.nameChangeBox.data)
        self.assertIsNone(self.form.nameChangeBox.model_item)
        self.assertFalse(self.form.nameChangeBox.txtCurrentName.isEnabled())
        self.assertFalse(self.form.nameChangeBox.txtDataName.isEnabled())
        self.assertFalse(self.form.nameChangeBox.txtFileName.isEnabled())
        self.assertFalse(self.form.nameChangeBox.txtNewCategory.isEnabled())
        self.assertEqual(self.form.nameChangeBox.txtCurrentName.text(), "")
        self.assertEqual(self.form.nameChangeBox.txtDataName.text(), "")
        self.assertEqual(self.form.nameChangeBox.txtFileName.text(), "")
        self.assertEqual(self.form.nameChangeBox.txtNewCategory.text(), "")

    def testNameDictionary(self):
        """
        Testing the name dictionary self.form.manager.data_name_dict to catch edge cases
        """
        names_to_delete = []
        names_with_brackets = ["test", "test [brackets]", "test [brackets", "test brackets]"]
        names_numbered = ["test [1]", "test [2]"]
        names_edge_cases = ["test [1] [2]", "test [2] [1]"]
        # Ensure items not of type() == str return empty string
        self.assertEqual("", self.form.manager.rename(names_with_brackets))
        self.assertEqual("", self.form.manager.rename(self))
        self.assertNotIn("", self.form.manager.data_name_dict)
        # Test names with brackets
        for i, name in enumerate(names_with_brackets):
            # Send to rename method which populates data_name_dict
            names_to_delete.append(self.form.manager.rename(name))
            # Ensure each name is unique
            self.assertEqual(i + 1, len(self.form.manager.data_name_dict))
            self.assertEqual(1, len(self.form.manager.data_name_dict[name]))
        for i, name in enumerate(names_with_brackets):
            names_to_delete.append(self.form.manager.rename(name))
            self.assertEqual(4, len(self.form.manager.data_name_dict))
            self.assertEqual(2, len(self.form.manager.data_name_dict[name]))
            self.assertEqual(self.form.manager.data_name_dict[name], [0,1])
        for i, name in enumerate(names_numbered):
            return_name = self.form.manager.rename(name)
            names_to_delete.append(return_name)
            self.assertEqual(return_name, f"test [{i+2}]")
            self.assertEqual(4, len(self.form.manager.data_name_dict))
            self.assertNotIn(name, self.form.manager.data_name_dict)
        self.assertEqual([0,1,2,3], self.form.manager.data_name_dict['test'])
        for i, name in enumerate(names_edge_cases):
            names_to_delete.append(self.form.manager.rename(name))
            self.assertEqual(5 + i, len(self.form.manager.data_name_dict))
            self.assertIn(name, self.form.manager.data_name_dict)
        # Names will be truncated when matching numbers
        # Shuffle the list to be sure deletion order doesn't matter
        random.shuffle(names_to_delete)
        for i, name in enumerate(names_to_delete):
            items_left = 0
            self.form.manager.remove_item_from_data_name_dict(name)
            for value in self.form.manager.data_name_dict.values():
                items_left += len(value)
            self.assertLess(items_left, len(names_to_delete))
        # Data name dictionary should be empty at this point
        self.assertEqual(0, len(self.form.manager.data_name_dict))

    def testNameChange(self):
        """
        Test the display name change routines
        """
        # Define Constants
        FILE_NAME = "cyl_400_20.txt"
        TEST_STRING_1 = "test value change"
        TEST_STRING_2 = "TEST VALUE CHANGE"
        # Test base state of the name change window
        self.baseNameStateCheck()
        # Get Data1D
        p_file=[FILE_NAME]
        # Read in the file
        output, message = self.form.readData(p_file)
        key = list(output.keys())
        output[key[0]].title = TEST_STRING_1
        self.form.loadComplete((output, message))

        # select the data and run name change routine
        self.form.treeView.selectAll()
        self.form.changeName()

        # Test window state after adding data
        self.assertTrue(self.form.nameChangeBox.isVisible())
        self.assertIsNotNone(self.form.nameChangeBox.data)
        self.assertIsNotNone(self.form.nameChangeBox.model_item)
        self.assertEqual(self.form.nameChangeBox.txtCurrentName.text(), FILE_NAME)
        self.assertEqual(self.form.nameChangeBox.txtDataName.text(), TEST_STRING_1)
        self.assertEqual(self.form.nameChangeBox.txtFileName.text(), FILE_NAME)
        self.assertTrue(self.form.nameChangeBox.rbExisting.isChecked())
        self.assertFalse(self.form.nameChangeBox.rbDataName.isChecked())
        self.assertFalse(self.form.nameChangeBox.rbFileName.isChecked())
        self.assertFalse(self.form.nameChangeBox.rbNew.isChecked())

        # Take the existing name
        self.form.nameChangeBox.cmdOK.click()
        self.form.changeName()
        self.assertEqual(self.form.nameChangeBox.txtCurrentName.text(), FILE_NAME)

        # Take the title
        self.form.nameChangeBox.rbDataName.setChecked(True)
        self.assertFalse(self.form.nameChangeBox.rbExisting.isChecked())
        self.form.nameChangeBox.cmdOK.click()
        self.form.changeName()
        self.assertEqual(self.form.nameChangeBox.txtCurrentName.text(), TEST_STRING_1)

        # Take the file name again
        self.form.nameChangeBox.rbFileName.setChecked(True)
        self.assertFalse(self.form.nameChangeBox.rbExisting.isChecked())
        self.form.nameChangeBox.cmdOK.click()
        self.form.changeName()
        self.assertEqual(self.form.nameChangeBox.txtCurrentName.text(), FILE_NAME)

        # Take the user-defined name, which is empty - should retain existing value
        self.form.nameChangeBox.rbNew.setChecked(True)
        self.assertFalse(self.form.nameChangeBox.rbExisting.isChecked())
        self.form.nameChangeBox.cmdOK.click()
        self.form.changeName()
        self.assertEqual(self.form.nameChangeBox.txtCurrentName.text(), FILE_NAME)

        # Take a different user-defined name
        self.form.nameChangeBox.rbNew.setChecked(True)
        self.form.nameChangeBox.txtNewCategory.setText(TEST_STRING_2)
        self.assertFalse(self.form.nameChangeBox.rbExisting.isChecked())
        self.form.nameChangeBox.cmdOK.click()
        self.form.changeName()
        self.assertEqual(self.form.nameChangeBox.txtCurrentName.text(), TEST_STRING_2)

        # Test cancel button
        self.form.nameChangeBox.rbNew.setChecked(True)
        self.form.nameChangeBox.txtNewCategory.setText(TEST_STRING_1)
        self.form.nameChangeBox.cmdCancel.click()
        self.form.changeName()
        self.assertEqual(self.form.nameChangeBox.txtCurrentName.text(), TEST_STRING_2)
        self.form.nameChangeBox.cmdOK.click()

        # Test delete data
        self.form.nameChangeBox.removeData(None)  # Nothing should happen
        self.assertEqual(self.form.nameChangeBox.txtCurrentName.text(), TEST_STRING_2)
        self.form.nameChangeBox.removeData([self.form.nameChangeBox.model_item])  # Should return to base state
        self.baseNameStateCheck()

    def testShowDataInfo(self):
        """
        Test of the showDataInfo method
        """
        # get Data1D
        p_file=["cyl_400_20.txt"]
        # Read in the file
        output, message = self.form.readData(p_file)
        self.form.loadComplete((output, message))

        # select the data
        self.form.treeView.selectAll()

        # Call the tested method
        self.form.showDataInfo()

        # Test the properties
        self.assertTrue(self.form.txt_widget.isReadOnly())
        self.assertEqual(self.form.txt_widget.windowTitle(), "Data Info: cyl_400_20.txt")
        self.assertIn("Waveln_max", self.form.txt_widget.toPlainText())

        # Slider moved all the way up
        self.assertEqual(self.form.txt_widget.verticalScrollBar().sliderPosition(), 0)

    def testSaveDataAs(self):
        """
        Test the Save As context menu action
        """
        # get Data1D
        p_file=["cyl_400_20.txt"]
        # Read in the file
        output, message = self.form.readData(p_file)
        self.form.loadComplete((output, message))

        # select the data
        self.form.treeView.selectAll()

        QFileDialog.getSaveFileName = MagicMock(return_value=("cyl_400_20_out", "(*.txt)"))

        # Call the tested method
        self.form.saveDataAs()
        filter = 'Text files (*.txt);;Comma separated value files (*.csv);;CanSAS 1D files (*.xml);;NXcanSAS files (*.h5);;All files (*.*)'
        QFileDialog.getSaveFileName.assert_called_with(
                                caption="Save As",
                                filter=filter,
                                options=16,
                                parent=None)
        QFileDialog.getSaveFileName.assert_called_once()

        # get Data2D
        p_file=["P123_D2O_10_percent.dat"]
        # Read in the file
        output, message = self.form.readData(p_file)
        self.form.loadComplete((output, message))

        # select the data
        index = self.form.model.index(1, 0)
        selmodel = self.form.treeView.selectionModel()
        selmodel.setCurrentIndex(index, QItemSelectionModel.NoUpdate)
        selmodel.select(index, QItemSelectionModel.Select|QItemSelectionModel.Rows)

        QFileDialog.getSaveFileName = MagicMock(return_value="test.xyz")

        # Call the tested method
        self.form.saveDataAs()
        QFileDialog.getSaveFileName.assert_called_with(
                                caption="Save As",
                                filter='IGOR/DAT 2D file in Q_map (*.dat);;NXcanSAS files (*.h5);;All files (*.*)',
                                options=16,
                                parent=None)
        QFileDialog.getSaveFileName.assert_called_once()

    def testQuickDataPlot(self):
        """
        Quick data plot generation.
        """
        # get Data1D
        p_file=["cyl_400_20.txt"]
        # Read in the file
        output, message = self.form.readData(p_file)
        self.form.loadComplete((output, message))

        # select the data
        self.form.treeView.selectAll()

        Plotter.show = MagicMock() # for masking the display

        self.form.quickDataPlot()
        self.assertTrue(Plotter.show.called)

    def notestQuickData3DPlot(self):
        """
        Slow(er) 3D data plot generation.
        """
        # get Data1D
        p_file=["P123_D2O_10_percent.dat"]
        # Read in the file
        output, message = self.form.readData(p_file)
        self.form.loadComplete((output, message))

        # select the data
        self.form.treeView.selectAll()

        Plotter2D.show = MagicMock() # for masking the display

        self.form.quickData3DPlot()

        self.assertTrue(Plotter2D.show.called)

    def testShowEditMask(self):
        """
        Edit mask on a 2D plot.

        TODO: add content once plotting finalized
        """
        pass

    def testDeleteItem(self):
        """
        Delete selected item from data explorer
        """

        # Mock the confirmation dialog with return=No
        QMessageBox.question = MagicMock(return_value=QMessageBox.No)

        # Populate the model
        filename = ["cyl_400_20.txt", "cyl_400_20.txt", "cyl_400_20.txt"]
        self.form.readData(filename)
        self.assertEqual(len(self.form.manager.data_name_dict), 1)
        self.assertEqual(len(self.form.manager.data_name_dict["cyl_400_20.txt"]), 3)
        self.assertEqual(max(self.form.manager.data_name_dict["cyl_400_20.txt"]), 2)

        # Assure the model contains three items
        self.assertEqual(self.form.model.rowCount(), 3)

        # Add an item to first file item
        item1 = QtGui.QStandardItem("test")
        item1.setCheckable(True)
        self.form.model.item(0).appendRow(item1)

        # Check the new item is in

        self.assertTrue(self.form.model.item(0).hasChildren())

        #select_item = self.form.model.item(0).child(3)
        select_item = self.form.model.item(0)
        select_index = self.form.model.indexFromItem(select_item)

        # Open up items
        self.form.current_view.expandAll()

        # Select the newly created item
        self.form.current_view.selectionModel().select(select_index, QtCore.QItemSelectionModel.Rows)

        # Attempt at deleting
        self.form.deleteSelectedItem()

        # Test the warning dialog called once
        self.assertTrue(QMessageBox.question.called)

        # Assure the model still contains the items
        self.assertEqual(self.form.model.rowCount(), 3)

        # Now, mock the confirmation dialog with return=Yes
        QMessageBox.question = MagicMock(return_value=QMessageBox.Yes)

        # Select the newly created item
        self.form.current_view.selectionModel().select(select_index, QtCore.QItemSelectionModel.Rows)
        # delete it. now for good
        self.form.deleteSelectedItem()

        # Test the warning dialog called once
        self.assertTrue(QMessageBox.question.called)

        # Assure the model contains no items
        self.assertEqual(self.form.model.rowCount(), 3)

    def testClosePlotsForItem(self):
        """
        Delete selected item from data explorer should also delete corresponding plots
        """
        # Mock the confirmation dialog with return=No
        QMessageBox.question = MagicMock(return_value=QMessageBox.No)

        loader = Loader()
        manager = DataManager()
        PlotHelper.clear()
        self.form.enableGraphCombo(None)

        # Make sure the controls are disabled
        self.assertFalse(self.form.cbgraph.isEnabled())
        self.assertFalse(self.form.cmdAppend.isEnabled())

        # Populate the model
        filename = ["cyl_400_20.txt"]
        self.form.readData(filename)

        # Mask plotting
        self.form.parent.workspace = MagicMock()

        # Call the plotting method
        self.form.newPlot()

        time.sleep(1)
        QApplication.processEvents()

        # The plot was registered
        self.assertEqual(len(PlotHelper.currentPlots()), 1)
        self.assertEqual(len(self.form.plot_widgets), 1)
        # could have leftovers from previous tests
        #self.assertEqual(list(self.form.plot_widgets.keys()), ['Graph3'])
        self.assertEqual(len(self.form.plot_widgets.keys()), 1)

        # data index
        model_item = self.form.model.item(0,0)

        # Call the method
        self.form.closePlotsForItem(model_item)

        # See that no plot remained
        self.assertEqual(len(PlotHelper.currentPlots()), 0)
        self.assertEqual(len(self.form.plot_widgets), 0)

    def testPlotsFromMultipleData1D(self):
        """
        Tests interplay between plotting 1D datasets and plotting
        a single 1D dataset from two separate fit tabs
        GH issue 1546
        """
        # prepare active_plots
        plot1 = Plotter(parent=self.form)
        data1 = Data1D()
        data1.name = 'p1'
        data1.plot_role = Data1D.ROLE_DATA
        plot1.data = data1

        plot2 = Plotter(parent=self.form)
        data2 = Data1D()
        data2.name = 'M2 [p1]'
        data2.plot_role = Data1D.ROLE_DEFAULT
        plot2.data = data2

        plot3 = Plotter(parent=self.form)
        data3 = Data1D()
        data3.name = 'Residuals for M2[p1]'
        data3.plot_role = Data1D.ROLE_RESIDUAL
        plot3.data = data3

        # pretend we're displaying three plots
        self.form.active_plots['p1'] = plot1
        self.form.active_plots['M2 [p1]'] = plot2
        self.form.active_plots['Residuals for M2[p1]'] = plot3

        # redoing plots from the same tab
        # data -> must be shown
        self.assertFalse(self.form.isPlotShown(data1))

        # model and residuals are already shown
        self.assertTrue(self.form.isPlotShown(data2))
        self.assertTrue(self.form.isPlotShown(data3))

        # Try from different fit page
        plot4 = Plotter(parent=self.form)
        data4 = Data1D()
        data4.name = 'M1 [p1]'
        data4.plot_role = Data1D.ROLE_DEFAULT
        plot4.data = data1
        # same data but must show, since different model
        self.assertFalse(self.form.isPlotShown(data4))

    def testPlotsFromMultipleData2D(self):
        """
        Tests interplay between plotting 2D datasets and plotting
        a single 2D dataset from two separate fit tabs
        GH issue 1546
        """
        # prepare active_plots
        plot1 = Plotter(parent=self.form)
        data1 = Data2D()
        data1.name = 'p1'
        data1.plot_role = Data1D.ROLE_DATA
        plot1.data = data1

        plot2 = Plotter(parent=self.form)
        data2 = Data2D()
        data2.name = 'M2 [p1]'
        data2.plot_role = Data1D.ROLE_DEFAULT
        plot2.data = data2

        plot3 = Plotter(parent=self.form)
        data3 = Data2D()
        data3.name = 'Residuals for M2[p1]'
        data3.plot_role = Data1D.ROLE_RESIDUAL
        plot3.data = data3

        # pretend we're displaying three plots
        self.form.active_plots['p1'] = plot1
        self.form.active_plots['M2 [p1]'] = plot2
        self.form.active_plots['Residuals for M2[p1]'] = plot3

        # redoing plots from the same tab
        # data -> Already there, don't show
        self.assertTrue(self.form.isPlotShown(data1))

        # model and residuals are already shown
        self.assertTrue(self.form.isPlotShown(data2))
        self.assertTrue(self.form.isPlotShown(data3))

        # Try from different fit page
        plot4 = Plotter(parent=self.form)
        data4 = Data2D()
        data4.name = 'M1 [p1]'
        plot4.data = data1
        # same data but must show, since different model
        self.assertFalse(self.form.isPlotShown(data4))

if __name__ == "__main__":
    unittest.main()
