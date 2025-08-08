import random
import time

import pytest
from PySide6.QtCore import QItemSelectionModel, QPoint, QSize, QSortFilterProxyModel, Qt
from PySide6.QtGui import QIcon, QStandardItem, QStandardItemModel
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox, QTabWidget, QTreeView

from sasdata.dataloader.loader import Loader

import sas.qtgui.Plotting.PlotHelper as PlotHelper
from sas.qtgui.MainWindow.DataExplorer import DataExplorerWindow
from sas.qtgui.MainWindow.DataManager import DataManager
from sas.qtgui.Plotting.Plotter import Plotter
from sas.qtgui.Plotting.Plotter2D import Plotter2D

# Local
from sas.qtgui.Plotting.PlotterData import Data1D, Data2D, DataRole
from sas.qtgui.UnitTesting.TestUtils import QtSignalSpy
from sas.qtgui.Utilities.GuiUtils import Communicate, HashableStandardItem
from sas.system.version import __version__ as SASVIEW_VERSION


class MyPerspective:
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


class dummy_manager:
    def __init__(self):
        self._perspective = MyPerspective()

    def communicator(self):
        return Communicate()

    def perspective(self):
        return self._perspective

    def workspace(self):
        return None

    class _parent:
        screen_width = 1024
        screen_height = 768


class DataExplorerTest:
    '''Test the Data Explorer GUI'''
    @pytest.fixture(autouse=True)
    def form(self, qapp):
        '''Create/Destroy the UI'''
        f = DataExplorerWindow(None, dummy_manager())
        yield f
        f.close()

    def testDefaults(self, form):
        '''Test the GUI in its default state'''
        # Tab widget
        assert isinstance(form, QTabWidget)
        assert form.count() == 2

        # Buttons - data tab
        assert form.cmdLoad.text() == "Load data"
        assert form.cmdDeleteData.text() == "Delete Data"
        assert form.cmdDeleteTheory.text() == "Delete"
        assert form.cmdFreeze.text() == "Freeze Theory"
        assert form.cmdSendTo.text() == "Send data to"
        assert form.cmdSendTo.iconSize() == QSize(32, 32)
        assert isinstance(form.cmdSendTo.icon(), QIcon)
        assert form.chkBatch.text() == "Batch mode"
        assert not form.chkBatch.isChecked()
        assert form.chkSwap.text() == "Swap data"
        assert not form.chkSwap.isChecked()

        # Buttons - theory tab

        # Combo boxes
        assert form.cbSelect.count() == 6
        assert form.cbSelect.currentIndex() == 0

        # Models - data
        assert isinstance(form.model, QStandardItemModel)
        assert form.treeView.model().rowCount() == 0
        assert form.treeView.model().columnCount() == 0
        assert form.model.rowCount() == 0
        assert form.model.columnCount() == 0
        assert isinstance(form.data_proxy, QSortFilterProxyModel)
        assert form.data_proxy.sourceModel() == form.model
        assert str(form.data_proxy.filterRegExp().pattern()) == ".+"
        assert isinstance(form.treeView, QTreeView)

        # Models - theory
        assert isinstance(form.theory_model, QStandardItemModel)
        assert form.freezeView.model().rowCount() == 0
        assert form.freezeView.model().columnCount() == 0
        assert form.theory_model.rowCount() == 0
        assert form.theory_model.columnCount() == 0
        assert isinstance(form.theory_proxy, QSortFilterProxyModel)
        assert form.theory_proxy.sourceModel() == form.theory_model
        assert str(form.theory_proxy.filterRegExp().pattern()) == ".+"
        assert isinstance(form.freezeView, QTreeView)

    def testWidgets(self, form):
        """
        Test if all required widgets got added
        """

    @pytest.mark.xfail(reason="2022-09 already broken - input file issue")
    def testLoadButton(self, form, mocker):
        loadButton = form.cmdLoad

        filename = "cyl_400_20.txt"
        # Initialize signal spy instances
        spy_file_read = QtSignalSpy(form, form.communicator.fileReadSignal)

        # Return no files.
        mocker.patch.object(QFileDialog, 'getOpenFileNames', return_value=('',''))

        # Click on the Load button
        QTest.mouseClick(loadButton, Qt.LeftButton)

        # Test the getOpenFileName() dialog called once
        assert QFileDialog.getOpenFileNames.called
        QFileDialog.getOpenFileNames.assert_called_once()

        # Make sure the signal has not been emitted
        assert spy_file_read.count() == 0

        # Now, return a single file
        mocker.patch.object(QFileDialog, 'getOpenFileNames', return_value=(filename,''))

        # Click on the Load button
        QTest.mouseClick(loadButton, Qt.LeftButton)
        qApp.processEvents()

        # Test the getOpenFileName() dialog called once
        assert QFileDialog.getOpenFileNames.called
        QFileDialog.getOpenFileNames.assert_called_once()

        # Expected one spy instance
        #assert spy_file_read.count() == 1
        #assert filename in str(spy_file_read.called()[0]['args'][0])

    @pytest.mark.xfail(reason="2022-09 already broken - input file issue")
    def testLoadFiles(self, form):
        """
        Test progress bar update while loading of multiple files
        """
        # Set up the spy on progress bar update signal
        spy_progress_bar_update = QtSignalSpy(form,
            form.communicator.progressBarUpdateSignal)

        # Populate the model
        filename = ["cyl_400_20.txt", "P123_D2O_10_percent.dat", "cyl_400_20.txt"]
        form.readData(filename)

        # 0, 0, 33, 66, -1 -> 5 signals reaching progressBar
        assert spy_progress_bar_update.count() == 5

        expected_list = [0, 0, 33, 66, -1]
        spied_list = [spy_progress_bar_update.called()[i]['args'][0] for i in range(5)]
        assert expected_list == spied_list

    @pytest.mark.xfail(reason="2022-09 already broken - input file issue")
    def testDeleteButton(self, form, mocker):
        """
        Functionality of the delete button
        """
        deleteButton = form.cmdDeleteData

        # Mock the confirmation dialog with return=No
        mocker.patch.object(QMessageBox, 'question', return_value=QMessageBox.No)

        # Populate the model
        filename = ["cyl_400_20.txt", "cyl_400_20.txt", "cyl_400_20.txt"]
        form.readData(filename)

        # Assure the model contains three items
        assert form.model.rowCount() == 3

        # Assure the checkboxes are on
        item1 = form.model.item(0)
        item2 = form.model.item(1)
        item3 = form.model.item(2)
        assert item1.checkState() == Qt.Checked
        assert item2.checkState() == Qt.Checked
        assert item3.checkState() == Qt.Checked

        # Click on the delete  button
        QTest.mouseClick(deleteButton, Qt.LeftButton)

        # Test the warning dialog called once
        assert QMessageBox.question.called

        # Assure the model still contains the items
        assert form.model.rowCount() == 3

        # Now, mock the confirmation dialog with return=Yes
        mocker.patch.object(QMessageBox, 'question', return_value=QMessageBox.Yes)

        # Click on the delete  button
        QTest.mouseClick(deleteButton, Qt.LeftButton)

        # Test the warning dialog called once
        assert QMessageBox.question.called

        # Assure the model contains no items
        assert form.model.rowCount() == 0

        # Click delete once again to assure no nasty behaviour on empty model
        QTest.mouseClick(deleteButton, Qt.LeftButton)

    def testDeleteTheory(self, form, mocker):
        """
        Test that clicking "Delete" in theories tab removes selected indices
        """
        deleteButton = form.cmdDeleteTheory

        # Mock the confirmation dialog with return=No
        mocker.patch.object(QMessageBox, 'question', return_value=QMessageBox.No)

        # Populate the model
        item1 = HashableStandardItem(True)
        item1.setCheckable(True)
        item1.setCheckState(Qt.Checked)
        item1.setText("item 1")
        form.theory_model.appendRow(item1)
        item2 = HashableStandardItem(True)
        item2.setCheckable(True)
        item2.setCheckState(Qt.Unchecked)
        item2.setText("item 2")
        form.theory_model.appendRow(item2)

        # Assure the model contains two items
        assert form.theory_model.rowCount() == 2

        # Assure the checkboxes are on
        assert item1.checkState() == Qt.Checked
        assert item2.checkState() == Qt.Unchecked

        # Click on the delete  button
        QTest.mouseClick(deleteButton, Qt.LeftButton)

        # Test the warning dialog called once
        assert QMessageBox.question.called

        # Assure the model still contains the items
        assert form.theory_model.rowCount() == 2

        # Now, mock the confirmation dialog with return=Yes
        mocker.patch.object(QMessageBox, 'question', return_value=QMessageBox.Yes)

        # Click on the delete  button
        QTest.mouseClick(deleteButton, Qt.LeftButton)

        # Test the warning dialog called once
        assert QMessageBox.question.called

        # Assure the model contains 1 item
        assert form.theory_model.rowCount() == 1

        # Set the remaining item to checked
        form.theory_model.item(0).setCheckState(Qt.Checked)

        # Click on the delete button again
        QTest.mouseClick(deleteButton, Qt.LeftButton)

        # Assure the model contains no items
        assert form.theory_model.rowCount() == 0

        # Click delete once again to assure no nasty behaviour on empty model
        QTest.mouseClick(deleteButton, Qt.LeftButton)

    @pytest.mark.xfail(reason="2022-09 already broken - input file issue")
    def testSendToButton(self, form, mocker):
        """
        Test that clicking the Send To button sends checked data to a perspective
        """
        # Send empty data
        mocked_perspective = form._perspective()
        mocker.patch.object(mocked_perspective, 'setData')

        # Click on the Send To  button
        QTest.mouseClick(form.cmdSendTo, Qt.LeftButton)

        # The set_data method not called
        assert not mocked_perspective.setData.called

        # Populate the model
        filename = ["cyl_400_20.txt"]
        form.readData(filename)

        QApplication.processEvents()

        # setData is the method we want to see called
        mocker.patch.object(mocked_perspective, 'swapData')

        # Assure the checkbox is on
        form.cbSelect.setCurrentIndex(0)

        # Click on the Send To  button
        QTest.mouseClick(form.cmdSendTo, Qt.LeftButton)

        QApplication.processEvents()

        # Test the set_data method called
        assert mocked_perspective.setData.called
        assert not mocked_perspective.swapData.called

        # Now select the swap data checkbox
        form.chkSwap.setChecked(True)

        # Click on the Send To  button
        QTest.mouseClick(form.cmdSendTo, Qt.LeftButton)

        QApplication.processEvents()

        # Now the swap data method should be called
        assert mocked_perspective.setData.called_once
        assert mocked_perspective.swapData.called

        # Test the exception block
        mocker.patch.object(QMessageBox, 'exec_')
        mocker.patch.object(QMessageBox, 'setText')
        mocker.patch.object(mocked_perspective, 'swapData', side_effect = Exception("foo"))

        # Click on the button to so the mocked swapData method raises an exception
        QTest.mouseClick(form.cmdSendTo, Qt.LeftButton)

        # Assure the message box popped up
        QMessageBox.exec_.assert_called_once()
        # With the right message
        QMessageBox.setText.assert_called_with("foo")

        # open another file
        filename = ["cyl_400_20.txt"]
        form.readData(filename)

        # Mock the warning message and the swapData method
        mocker.patch.object(QMessageBox, 'exec_')
        mocker.patch.object(QMessageBox, 'setText')
        mocker.patch.object(mocked_perspective, 'swapData')

        # Click on the button to swap both datasets to the perspective
        QTest.mouseClick(form.cmdSendTo, Qt.LeftButton)

        # Assure the message box popped up
        QMessageBox.exec_.assert_called_once()
        # With the right message
        QMessageBox.setText.assert_called_with(
            "Dummy Perspective does not allow replacing multiple data.")

    @pytest.mark.xfail(reason="2022-09 already broken - input file issue")
    def testDataSelection(self, form):
        """
        Tests the functionality of the Selection Option combobox
        """
        # Populate the model with 1d and 2d data
        filename = ["cyl_400_20.txt", "P123_D2O_10_percent.dat"]
        form.readData(filename)

        # Wait a moment for data to load
        time.sleep(1)
        # Unselect all data
        form.cbSelect.activated.emit(1)
        # Test the current selection
        item1D = form.model.item(0)
        item2D = form.model.item(1)

        assert item1D.checkState() == Qt.Unchecked
        assert item2D.checkState() == Qt.Unchecked

        # Select all data
        form.cbSelect.activated.emit(0)

        # Test the current selection
        assert item1D.checkState() == Qt.Checked
        assert item2D.checkState() == Qt.Checked

        # select 1d data
        form.cbSelect.activated.emit(2)
        # Test the current selection
        assert item1D.checkState() == Qt.Checked
        assert item2D.checkState() == Qt.Checked

        # unselect 1d data
        form.cbSelect.activated.emit(3)

        # Test the current selection
        assert item1D.checkState() == Qt.Unchecked
        assert item2D.checkState() == Qt.Checked

        # select 2d data
        form.cbSelect.activated.emit(4)

        # Test the current selection
        assert item1D.checkState() == Qt.Unchecked
        assert item2D.checkState() == Qt.Checked

        # unselect 2d data
        form.cbSelect.activated.emit(5)

        # Test the current selection
        assert item1D.checkState() == Qt.Unchecked
        assert item2D.checkState() == Qt.Unchecked

    def testFreezeTheory(self, form):
        """
        Assure theory freeze functionality works
        """
        # Not yet tested - agree on design first.
        pass

    def testRecursivelyCloneItem(self, form):
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
        new_item = form.recursivelyCloneItem(item1)

        # assure the trees look identical
        assert item1.rowCount() == new_item.rowCount()
        assert item1.child(0).rowCount() == new_item.child(0).rowCount()
        assert item1.child(1).rowCount() == new_item.child(1).rowCount()
        assert item1.child(0).child(0).rowCount() == new_item.child(0).child(0).rowCount()

    @pytest.mark.xfail(reason="2022-09 already broken - input file issue")
    def testReadData(self, form, mocker):
        """
        Test the low level readData() method
        """
        filename = ["cyl_400_20.txt"]
        mocker.patch.object(form.manager, 'add_data')

        # Initialize signal spy instances
        spy_status_update = QtSignalSpy(form, form.communicator.statusBarUpdateSignal)
        spy_data_received = QtSignalSpy(form, form.communicator.fileDataReceivedSignal)

        # Read in the file
        form.readData(filename)

        # Expected two status bar updates
        assert spy_status_update.count() == 2
        assert filename[0] in str(spy_status_update.called()[0]['args'][0])


        # Check that the model contains the item
        assert form.model.rowCount() == 1
        assert form.model.columnCount() == 1

        # The 0th item header should be the name of the file
        model_item = form.model.index(0,0)
        model_name = form.model.data(model_item)
        assert model_name == filename[0]

    def skip_testDisplayHelp(self, form): # Skip due to help path change
        """
        Test that the Help window gets shown correctly
        """
        partial_url = "qtgui/MainWindow/data_explorer_help.html"
        button1 = form.cmdHelp
        button2 = form.cmdHelp_2

        # Click on the Help button
        QTest.mouseClick(button1, Qt.LeftButton)
        qApp.processEvents()

        # Check the browser
        assert partial_url in str(form._helpView.web())
        # Close the browser
        form._helpView.close()

        # Click on the Help_2 button
        QTest.mouseClick(button2, Qt.LeftButton)
        qApp.processEvents()
        # Check the browser
        assert partial_url in str(form._helpView.web())

    def testLoadFile(self, form):
        """
        Test the threaded call to readData()
        """
        #form.loadFile()
        pass

    def testGetWList(self, form):
        """
        Test the list of known extensions
        """
        w_list = form.getWlist()

        defaults = 'All (*.*);;canSAS files (*.xml);;SESANS files' +\
            ' (*.ses);;ASCII files (*.txt);;' +\
            'IGOR/DAT 2D Q_map files (*.dat);;IGOR 1D files (*.abs);;'+\
            'DANSE files (*.sans)'
        default_list = defaults.split(';;')

        for def_format in default_list:
            assert def_format in w_list

    def testLoadComplete(self, form, mocker):
        """
        Test the callback method updating the data object
        """
        message="Loading Data Complete"
        data_dict = {"a1":Data1D()}
        output_data = (data_dict, message)

        mocker.patch.object(form.manager, 'add_data')

        # Initialize signal spy instances
        spy_status_update = QtSignalSpy(form, form.communicator.statusBarUpdateSignal)
        spy_data_received = QtSignalSpy(form, form.communicator.fileDataReceivedSignal)

        # Read in the file
        form.loadComplete(output_data)

        # "Loading data complete" no longer sent in LoadFile but in callback
        assert "Loading Data Complete" in str(spy_status_update.called()[0]['args'][0])

        # Expect one Data Received signal
        assert spy_data_received.count() == 1

        # Assure returned dictionary has correct data
        # We don't know the data ID, so need to iterate over dict
        data_dict = spy_data_received.called()[0]['args'][0]
        for data_key, data_value in data_dict.items():
            assert isinstance(data_value, Data1D)

        # Assure add_data on data_manager was called (last call)
        assert form.manager.add_data.called

    @pytest.mark.xfail(reason="2022-09 already broken - input file issue")
    def testNewPlot1D(self, form, mocker):
        """
        Creating new plots from Data1D/2D
        """
        loader = Loader()
        manager = DataManager()
        PlotHelper.clear()
        form.enableGraphCombo(None)

        # Make sure the controls are disabled
        assert not form.cbgraph.isEnabled()
        assert not form.cmdAppend.isEnabled()

        # get Data1D
        p_file="cyl_400_20.txt"
        output_object = loader.load(p_file)
        new_data = [(None, manager.create_gui_data(output_object[0], p_file))]
        _, test_data = new_data[0]
        assert f'Data file generated by SasView v{SASVIEW_VERSION}' in \
                        test_data.notes

        # Mask retrieval of the data
        mocker.patch.object(sas.qtgui.Utilities.GuiUtils, 'plotsFromCheckedItems', return_value=new_data)

        # Mask plotting
        mocker.patch.object(form.parent, 'workspace')

        # Call the plotting method
        form.newPlot()

        time.sleep(1)
        QApplication.processEvents()

        # The plot was registered
        assert len(PlotHelper.currentPlotIds()) == 1

        assert form.cbgraph.isEnabled()
        assert form.cmdAppend.isEnabled()

    @pytest.mark.xfail(reason="2022-09 already broken - input file issue")
    def testNewPlot2D(self, form, mocker):
        """
        Creating new plots from Data1D/2D
        """
        loader = Loader()
        manager = DataManager()
        PlotHelper.clear()
        form.enableGraphCombo(None)

        # Make sure the controls are disabled
        assert not form.cbgraph.isEnabled()
        assert not form.cmdAppend.isEnabled()

        # get Data2D
        p_file="P123_D2O_10_percent.dat"
        output_object = loader.load(p_file)
        new_data = [(None, manager.create_gui_data(output_object[0], p_file))]

        # Mask retrieval of the data
        mocker.patch.object(sas.qtgui.Utilities.GuiUtils, 'plotsFromCheckedItems', return_value=new_data)

        # Mask plotting
        mocker.patch.object(form.parent, 'workspace')

        # Call the plotting method
        #form.newPlot()
        #QApplication.processEvents()

        # The plot was registered
        #assert len(PlotHelper.currentPlots() == 1

        #assert form.cbgraph.isEnabled()
        #assert form.cmdAppend.isEnabled()

    @pytest.mark.xfail(reason="2022-09 already broken - input file issue")
    def testAppendPlot(self, form, mocker):
        """
        Creating new plots from Data1D/2D
        """
        loader = Loader()
        manager = DataManager()

        PlotHelper.clear()
        form.enableGraphCombo(None)

        # Make sure the controls are disabled
        assert not form.cbgraph.isEnabled()
        assert not form.cmdAppend.isEnabled()

        # get Data1D
        p_file="cyl_400_20.txt"
        output_object = loader.load(p_file)
        output_item = QStandardItem()
        new_data = [(output_item, manager.create_gui_data(output_object[0], p_file))]

        # Mask plotting
        mocker.patch.object(form.parent, 'workspace')

        # Mask the plot show call
        mocker.patch.object(Plotter, 'show')

        # Mask retrieval of the data
        mocker.patch.object(sas.qtgui.Utilities.GuiUtils, 'plotsFromCheckedItems', return_value=new_data)

        # Call the plotting method
        form.newPlot()

        # Call the plotting method again, so we have 2 graphs
        form.newPlot()

        QApplication.processEvents()
        # See that we have two plots
        assert len(PlotHelper.currentPlotIds()) == 2

        # Add data to plot #1
        form.cbgraph.setCurrentIndex(1)
        form.appendPlot()

        # See that we still have two plots
        assert len(PlotHelper.currentPlotIds()) == 2

    def testUpdateGraphCombo(self, form):
        """
        Test the combo box update
        """
        PlotHelper.clear()

        graph_list=["1","2","3"]
        form.updateGraphCombo(graph_list)

        assert form.cbgraph.count() == 3
        assert form.cbgraph.currentText() == '1'

        graph_list=[]
        form.updateGraphCombo(graph_list)
        assert form.cbgraph.count() == 0

    def testUpdateModelFromPerspective(self, form, mocker):
        """
        Assure the model update is correct
        """
        good_item = QStandardItem()
        bad_item = "I'm so bad"

        mocker.patch.object(form.model, 'reset', create=True)

        form.updateModelFromPerspective(good_item)

        # See that the model got reset
        # form.model.reset.assert_called_once()

        # See that the bad item causes raise
        with pytest.raises(Exception):
            form.updateModelFromPerspective(bad_item)

    @pytest.mark.xfail(reason="2022-09 already broken - input file issue")
    def testContextMenu(self, form, mocker):
        """
        See if the context menu is present
        """
        # get Data1D
        p_file=["cyl_400_20.txt"]
        # Read in the file
        output, message = form.readData(p_file)
        form.loadComplete((output, message))

        # Pick up the treeview index corresponding to that file
        index = form.treeView.indexAt(QPoint(5,5))
        form.show()

        # Find out the center pointof the treeView row
        rect = form.treeView.visualRect(index).center()

        mocker.patch.object(form.context_menu, 'exec_')

        # Move the mouse pointer to the first row
        QTest.mouseMove(form.treeView.viewport(), pos=rect)

        # This doesn't invoke the action/signal. Investigate why?
        # QTest.mouseClick(form.treeView.viewport(), Qt.RightButton, pos=rect)

        # Instead, send the signal directly
        form.treeView.customContextMenuRequested.emit(rect)

        # See that the menu has been shown
        form.context_menu.exec_.assert_called_once()

    def baseNameStateCheck(self, form):
        """
        Helper method for the Name Change Tests Below - Check the base state of the window
        """
        assert hasattr(form, "nameChangeBox")
        assert form.nameChangeBox.isModal()
        assert form.nameChangeBox.windowTitle() == "Display Name Change"
        assert not form.nameChangeBox.isVisible()
        assert form.nameChangeBox.data is None
        assert form.nameChangeBox.model_item is None
        assert not form.nameChangeBox.txtCurrentName.isEnabled()
        assert not form.nameChangeBox.txtDataName.isEnabled()
        assert not form.nameChangeBox.txtFileName.isEnabled()
        assert not form.nameChangeBox.txtNewCategory.isEnabled()
        assert form.nameChangeBox.txtCurrentName.text() == ""
        assert form.nameChangeBox.txtDataName.text() == ""
        assert form.nameChangeBox.txtFileName.text() == ""
        assert form.nameChangeBox.txtNewCategory.text() == ""

    def testNameDictionary(self, form):
        """
        Testing the name dictionary form.manager.data_name_dict to catch edge cases
        """
        names_to_delete = []
        names_with_brackets = ["test", "test [brackets]", "test [brackets", "test brackets]"]
        names_numbered = ["test [1]", "test [2]"]
        names_edge_cases = ["test [1] [2]", "test [2] [1]"]
        # Ensure items not of type() == str return empty string
        assert form.manager.rename(names_with_brackets) == ""
        assert form.manager.rename(self) == ""
        assert "" not in form.manager.data_name_dict
        # Test names with brackets
        for i, name in enumerate(names_with_brackets):
            # Send to rename method which populates data_name_dict
            names_to_delete.append(form.manager.rename(name))
            # Ensure each name is unique
            assert i + 1 == len(form.manager.data_name_dict)
            assert len(form.manager.data_name_dict[name]) == 1
        for i, name in enumerate(names_with_brackets):
            names_to_delete.append(form.manager.rename(name))
            assert len(form.manager.data_name_dict) == 4
            assert len(form.manager.data_name_dict[name]) == 2
            assert form.manager.data_name_dict[name] == [0,1]
        for i, name in enumerate(names_numbered):
            return_name = form.manager.rename(name)
            names_to_delete.append(return_name)
            assert return_name == f"test [{i+2}]"
            assert len(form.manager.data_name_dict) == 4
            assert name not in form.manager.data_name_dict
        assert form.manager.data_name_dict['test'] == [0,1,2,3]
        for i, name in enumerate(names_edge_cases):
            names_to_delete.append(form.manager.rename(name))
            assert 5 + i == len(form.manager.data_name_dict)
            assert name in form.manager.data_name_dict
        # Names will be truncated when matching numbers
        # Shuffle the list to be sure deletion order doesn't matter
        random.shuffle(names_to_delete)
        for i, name in enumerate(names_to_delete):
            items_left = 0
            form.manager.remove_item_from_data_name_dict(name)
            for value in form.manager.data_name_dict.values():
                items_left += len(value)
            assert items_left < len(names_to_delete)
        # Data name dictionary should be empty at this point
        assert len(form.manager.data_name_dict) == 0

    @pytest.mark.xfail(reason="2022-09 already broken - input file issue")
    def testNameChange(self, form):
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
        output, message = form.readData(p_file)
        key = list(output.keys())
        output[key[0]].title = TEST_STRING_1
        form.loadComplete((output, message))

        # select the data and run name change routine
        form.treeView.selectAll()
        form.changeName()

        # Test window state after adding data
        assert form.nameChangeBox.isVisible()
        assert form.nameChangeBox.data is not None
        assert form.nameChangeBox.model_item is not None
        assert form.nameChangeBox.txtCurrentName.text() == FILE_NAME
        assert form.nameChangeBox.txtDataName.text() == TEST_STRING_1
        assert form.nameChangeBox.txtFileName.text() == FILE_NAME
        assert form.nameChangeBox.rbExisting.isChecked()
        assert not form.nameChangeBox.rbDataName.isChecked()
        assert not form.nameChangeBox.rbFileName.isChecked()
        assert not form.nameChangeBox.rbNew.isChecked()

        # Take the existing name
        form.nameChangeBox.cmdOK.click()
        form.changeName()
        assert form.nameChangeBox.txtCurrentName.text() == FILE_NAME

        # Take the title
        form.nameChangeBox.rbDataName.setChecked(True)
        assert not form.nameChangeBox.rbExisting.isChecked()
        form.nameChangeBox.cmdOK.click()
        form.changeName()
        assert form.nameChangeBox.txtCurrentName.text() == TEST_STRING_1

        # Take the file name again
        form.nameChangeBox.rbFileName.setChecked(True)
        assert not form.nameChangeBox.rbExisting.isChecked()
        form.nameChangeBox.cmdOK.click()
        form.changeName()
        assert form.nameChangeBox.txtCurrentName.text() == FILE_NAME

        # Take the user-defined name, which is empty - should retain existing value
        form.nameChangeBox.rbNew.setChecked(True)
        assert not form.nameChangeBox.rbExisting.isChecked()
        form.nameChangeBox.cmdOK.click()
        form.changeName()
        assert form.nameChangeBox.txtCurrentName.text() == FILE_NAME

        # Take a different user-defined name
        form.nameChangeBox.rbNew.setChecked(True)
        form.nameChangeBox.txtNewCategory.setText(TEST_STRING_2)
        assert not form.nameChangeBox.rbExisting.isChecked()
        form.nameChangeBox.cmdOK.click()
        form.changeName()
        assert form.nameChangeBox.txtCurrentName.text() == TEST_STRING_2

        # Test cancel button
        form.nameChangeBox.rbNew.setChecked(True)
        form.nameChangeBox.txtNewCategory.setText(TEST_STRING_1)
        form.nameChangeBox.cmdCancel.click()
        form.changeName()
        assert form.nameChangeBox.txtCurrentName.text() == TEST_STRING_2
        form.nameChangeBox.cmdOK.click()

        # Test delete data
        form.nameChangeBox.removeData(None)  # Nothing should happen
        assert form.nameChangeBox.txtCurrentName.text() == TEST_STRING_2
        form.nameChangeBox.removeData([form.nameChangeBox.model_item])  # Should return to base state
        self.baseNameStateCheck()

    @pytest.mark.xfail(reason="2022-09 already broken - input file issue")
    def testShowDataInfo(self, form):
        """
        Test of the showDataInfo method
        """
        # get Data1D
        p_file=["cyl_400_20.txt"]
        # Read in the file
        output, message = form.readData(p_file)
        form.loadComplete((output, message))

        # select the data
        form.treeView.selectAll()

        # Call the tested method
        form.showDataInfo()

        # Test the properties
        assert form.txt_widget.isReadOnly()
        assert form.txt_widget.windowTitle() == "Data Info: cyl_400_20.txt"
        assert "Waveln_max" in form.txt_widget.toPlainText()

        # Slider moved all the way up
        assert form.txt_widget.verticalScrollBar().sliderPosition() == 0

    @pytest.mark.xfail(reason="2022-09 already broken - input file issue")
    def testSaveDataAs(self, form, mocker):
        """
        Test the Save As context menu action
        """
        # get Data1D
        p_file=["cyl_400_20.txt"]
        # Read in the file
        output, message = form.readData(p_file)
        form.loadComplete((output, message))

        # select the data
        form.treeView.selectAll()

        mocker.patch.object(QFileDialog, 'getSaveFileName', return_value=("cyl_400_20_out", "(*.txt)"))

        # Call the tested method
        form.saveDataAs()
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
        output, message = form.readData(p_file)
        form.loadComplete((output, message))

        # select the data
        index = form.model.index(1, 0)
        selmodel = form.treeView.selectionModel()
        selmodel.setCurrentIndex(index, QItemSelectionModel.NoUpdate)
        selmodel.select(index, QItemSelectionModel.Select|QItemSelectionModel.Rows)

        mocker.patch.object(QFileDialog, 'getSaveFileName', return_value="test.xyz")

        # Call the tested method
        form.saveDataAs()
        QFileDialog.getSaveFileName.assert_called_with(
                                caption="Save As",
                                filter='IGOR/DAT 2D file in Q_map (*.dat);;NXcanSAS files (*.h5);;All files (*.*)',
                                options=16,
                                parent=None)
        QFileDialog.getSaveFileName.assert_called_once()

    @pytest.mark.xfail(reason="2022-09 already broken - input file issue")
    def testQuickDataPlot(self, form, mocker):
        """
        Quick data plot generation.
        """
        # get Data1D
        p_file=["cyl_400_20.txt"]
        # Read in the file
        output, message = form.readData(p_file)
        form.loadComplete((output, message))

        # select the data
        form.treeView.selectAll()

        mocker.patch.object(Plotter, 'show') # for masking the display

        form.quickDataPlot()
        assert Plotter.show.called

    def notestQuickData3DPlot(self, form, mocker):
        """
        Slow(er) 3D data plot generation.
        """
        # get Data1D
        p_file=["P123_D2O_10_percent.dat"]
        # Read in the file
        output, message = form.readData(p_file)
        form.loadComplete((output, message))

        # select the data
        form.treeView.selectAll()

        mocker.patch.object(Plotter2D, 'show') # for masking the display

        form.quickData3DPlot()

        assert Plotter2D.show.called

    def testShowEditMask(self, form):
        """
        Edit mask on a 2D plot.

        TODO: add content once plotting finalized
        """
        pass

    @pytest.mark.xfail(reason="2022-09 already broken - input file issue")
    def testDeleteItem(self, form, mocker):
        """
        Delete selected item from data explorer
        """

        # Mock the confirmation dialog with return=No
        mocker.patch.object(QMessageBox, 'question', return_value=QMessageBox.No)

        # Populate the model
        filename = ["cyl_400_20.txt", "cyl_400_20.txt", "cyl_400_20.txt"]
        form.readData(filename)
        assert len(form.manager.data_name_dict) == 1
        assert len(form.manager.data_name_dict["cyl_400_20.txt"]) == 3
        assert max(form.manager.data_name_dict["cyl_400_20.txt"]) == 2

        # Assure the model contains three items
        assert form.model.rowCount() == 3

        # Add an item to first file item
        item1 = QStandardItem("test")
        item1.setCheckable(True)
        form.model.item(0).appendRow(item1)

        # Check the new item is in

        assert form.model.item(0).hasChildren()

        #select_item = form.model.item(0).child(3)
        select_item = form.model.item(0)
        select_index = form.model.indexFromItem(select_item)

        # Open up items
        form.current_view.expandAll()

        # Select the newly created item
        form.current_view.selectionModel().select(select_index, QItemSelectionModel.Rows)

        # Attempt at deleting
        form.deleteFile()

        # Test the warning dialog called once
        assert QMessageBox.question.called

        # Assure the model still contains the items
        assert form.model.rowCount() == 3

        # Now, mock the confirmation dialog with return=Yes
        mocker.patch.object(QMessageBox, 'question', return_value=QMessageBox.Yes)

        # Select the newly created item
        form.current_view.selectionModel().select(select_index, QItemSelectionModel.Rows)
        # delete it. now for good
        form.deleteFile()

        # Test the warning dialog called once
        assert QMessageBox.question.called

        # Assure the model contains no items
        assert form.model.rowCount() == 3

    @pytest.mark.xfail(reason="2022-09 already broken - input file issue")
    def testClosePlotsForItem(self, form, mocker):
        """
        Delete selected item from data explorer should also delete corresponding plots
        """
        # Mock the confirmation dialog with return=No
        mocker.patch.object(QMessageBox, 'question', return_value=QMessageBox.No)

        loader = Loader()
        manager = DataManager()
        PlotHelper.clear()
        form.enableGraphCombo(None)

        # Make sure the controls are disabled
        assert not form.cbgraph.isEnabled()
        assert not form.cmdAppend.isEnabled()

        # Populate the model
        filename = ["cyl_400_20.txt"]
        form.readData(filename)

        # Mask plotting
        mocker.patch.object(form.parent, 'workspace')

        # Call the plotting method
        form.newPlot()

        time.sleep(1)
        QApplication.processEvents()

        # The plot was registered
        assert len(PlotHelper.currentPlotIds()) == 1
        assert len(form.plot_widgets) == 1
        # could have leftovers from previous tests
        #assert list(form.plot_widgets.keys()) == ['Graph3']
        assert len(form.plot_widgets.keys()) == 1

        # data index
        model_item = form.model.item(0,0)

        # Call the method
        form.closePlotsForItem(model_item)

        # See that no plot remained
        assert len(PlotHelper.currentPlotIds()) == 0
        assert len(form.plot_widgets) == 0

    def testPlotsFromMultipleData1D(self, form):
        """
        Tests interplay between plotting 1D datasets and plotting
        a single 1D dataset from two separate fit tabs
        GH issue 1546
        """
        # prepare active_plots
        plot1 = Plotter(parent=form)
        data1 = Data1D()
        data1.name = 'p1'
        data1.plot_role = DataRole.ROLE_DATA
        plot1.data = data1

        plot2 = Plotter(parent=form)
        data2 = Data1D()
        data2.name = 'M2 [p1]'
        data2.plot_role = DataRole.ROLE_DEFAULT
        plot2.data = data2

        plot3 = Plotter(parent=form)
        data3 = Data1D()
        data3.name = 'Residuals for M2[p1]'
        data3.plot_role = DataRole.ROLE_RESIDUAL
        plot3.data = data3

        # pretend we're displaying three plots
        form.active_plots['p1'] = plot1
        form.active_plots['M2 [p1]'] = plot2
        form.active_plots['Residuals for M2[p1]'] = plot3

        # redoing plots from the same tab
        # data -> must be shown
        assert form.isPlotShown(data1)

        # model and residuals are already shown
        assert form.isPlotShown(data2)
        assert form.isPlotShown(data3)

        # Try from different fit page
        plot4 = Plotter(parent=form)
        data4 = Data1D()
        data4.name = 'M1 [p1]'
        data4.plot_role = DataRole.ROLE_DEFAULT
        plot4.data = data1
        # same data but must show, since different model
        assert not form.isPlotShown(data4)

    def testPlotsFromMultipleData2D(self, form):
        """
        Tests interplay between plotting 2D datasets and plotting
        a single 2D dataset from two separate fit tabs
        GH issue 1546
        """
        # prepare active_plots
        plot1 = Plotter(parent=form)
        data1 = Data2D()
        data1.name = 'p1'
        data1.plot_role = DataRole.ROLE_DATA
        plot1.data = data1

        plot2 = Plotter(parent=form)
        data2 = Data2D()
        data2.name = 'M2 [p1]'
        data2.plot_role = DataRole.ROLE_DEFAULT
        plot2.data = data2

        plot3 = Plotter(parent=form)
        data3 = Data2D()
        data3.name = 'Residuals for M2[p1]'
        data3.plot_role = DataRole.ROLE_RESIDUAL
        plot3.data = data3

        # pretend we're displaying three plots
        form.active_plots['p1'] = plot1
        form.active_plots['M2 [p1]'] = plot2
        form.active_plots['Residuals for M2[p1]'] = plot3

        # redoing plots from the same tab
        # data -> Already there, don't show
        assert form.isPlotShown(data1)

        # model and residuals are already shown
        assert form.isPlotShown(data2)
        assert form.isPlotShown(data3)

        # Try from different fit page
        plot4 = Plotter(parent=form)
        data4 = Data2D()
        data4.name = 'M1 [p1]'
        plot4.data = data1
        # same data but must show, since different model
        assert not form.isPlotShown(data4)
