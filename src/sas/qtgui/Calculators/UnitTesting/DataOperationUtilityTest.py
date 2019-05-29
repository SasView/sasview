import sys
import time
import numpy
import logging
import unittest
import webbrowser

from PyQt5 import QtGui, QtWidgets
from PyQt5 import QtCore
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt
from unittest.mock import MagicMock
from unittest.mock import patch

from twisted.internet import threads

from sas.qtgui.Calculators.DataOperationUtilityPanel import DataOperationUtilityPanel
from sas.qtgui.Utilities.GuiUtils import *
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.PlotterData import Data2D
from sas.qtgui.MainWindow.DataState import DataState

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)

BG_COLOR_ERR = 'background-color: rgb(244, 170, 164);'

class DataOperationUtilityTest(unittest.TestCase):
    """Test the ResolutionCalculator"""
    def setUp(self):
        """Create the ResolutionCalculator"""

        class dummy_manager(object):
            def communicator(self):
                return Communicate()

        self.widget = DataOperationUtilityPanel(dummy_manager())

    def tearDown(self):
        """Destroy the DataOperationUtility"""
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        """Test the GUI in its default state"""

        self.assertIsInstance(self.widget, QtWidgets.QDialog)

        self.assertEqual(self.widget.windowTitle(), "Data Operation")
        self.assertEqual(self.widget.groupBox.title(), "Data Operation "
                                                       "[ + (add); "
                                                       "- (subtract); "
                                                       "* (multiply); "
                                                       "/ (divide); "
                                                       "| (append)]")
        # size
        self.assertEqual(self.widget.size().height(), 425)
        self.assertEqual(self.widget.size().width(), 951)

        # content of line edits
        self.assertEqual(self.widget.txtNumber.text(), '1.0')
        self.assertEqual(self.widget.txtOutputData.text(), 'MyNewDataName')

        # content of comboboxes and default text / index
        self.assertFalse(self.widget.cbData1.isEditable())
        self.assertEqual(self.widget.cbData1.count(), 1)
        self.assertEqual(self.widget.cbData1.currentText(),
                         'No Data Available')

        self.assertFalse(self.widget.cbData2.isEditable())
        self.assertEqual(self.widget.cbData2.count(), 1)
        self.assertEqual(self.widget.cbData2.currentText(),
                         'No Data Available')

        self.assertFalse(self.widget.cbOperator.isEditable())
        self.assertEqual(self.widget.cbOperator.count(), 5)
        self.assertEqual(self.widget.cbOperator.currentText(), '+')
        self.assertListEqual([self.widget.cbOperator.itemText(i) for i in
                              range(self.widget.cbOperator.count())],
                             ['+', '-', '*', '/', '|'])

        # Tooltips
        self.assertEqual(str(self.widget.cmdCompute.toolTip()), "Generate the Data "
                                                           "and send to Data "
                                                           "Explorer.")
        self.assertEqual(str(self.widget.cmdClose.toolTip()), "Close this panel.")
        self.assertEqual(str(self.widget.cmdHelp.toolTip()),
                         "Get help on Data Operations.")
        self.assertEqual(self.widget.txtNumber.toolTip(), "If no Data2 loaded, "
                                                "enter a number to be "
                                                "applied to Data1 using "
                                                "the operator")
        self.assertEqual(str(self.widget.cbOperator.toolTip()), "Add: +\n"
                                                           "Subtract: - \n"
                                                           "Multiply: *\n"
                                                           "Divide: /\n"
                                                           "Append(Combine): |")

        self.assertFalse(self.widget.cmdCompute.isEnabled())
        self.assertFalse(self.widget.txtNumber.isEnabled())

        self.assertIsInstance(self.widget.layoutOutput,QtWidgets.QHBoxLayout)
        self.assertIsInstance(self.widget.layoutData1,QtWidgets.QHBoxLayout)
        self.assertIsInstance(self.widget.layoutData2,QtWidgets.QHBoxLayout)

        # To store input datafiles
        self.assertIsNone(self.widget.filenames)
        self.assertEqual(self.widget.list_data_items, [])
        self.assertIsNone(self.widget.data1)
        self.assertIsNone(self.widget.data2)
        # To store the result
        self.assertIsNone(self.widget.output)
        self.assertFalse(self.widget.data2OK)
        self.assertFalse(self.widget.data1OK)

        self.widget.newPlot = MagicMock()
        self.assertTrue(self.widget.newPlot.called_once())
        self.assertTrue(self.widget.newPlot.called_once())
        self.assertTrue(self.widget.newPlot.called_once())

    def testHelp(self):
        """ Assure help file is shown """
        self.widget.manager.showHelp = MagicMock()
        self.widget.onHelp()
        self.assertTrue(self.widget.manager.showHelp.called_once())
        args = self.widget.manager.showHelp.call_args
        self.assertIn('data_operator_help.html', args[0][0])

    def testOnReset(self):
        """ Test onReset function """
        # modify gui
        self.widget.txtNumber.setText('2.3')
        self.widget.onReset()
        self.assertEqual(self.widget.txtNumber.text(), '1.0')

    def testOnClose(self):
        """ test Closing window """
        closeButton = self.widget.cmdClose
        QTest.mouseClick(closeButton, Qt.LeftButton)


    def testOnCompute(self):
        """ Test onCompute function """

        # define the data
        self.widget.data1 = Data1D(x=[1.0, 2.0, 3.0], y=[11.0, 12.0, 13.0],
                                   dx=[0.1, 0.2, 0.3], dy=[0.1, 0.2, 0.3])
        self.widget.data2 = 1

        # mock update of plot
        self.widget.updatePlot = MagicMock()

        # enable onCompute to run (check on data type)
        self.widget.onCheckChosenData = MagicMock(return_value=True)

        # run onCompute
        self.widget.onCompute()

        # check output:
        # x unchanged, y incremented by 1 (=data2) and updatePlot called
        self.assertListEqual(self.widget.output.x.tolist(),
                             self.widget.data1.x.tolist())
        self.assertListEqual(self.widget.output.y.tolist(), [12.0, 13.0, 14.0])
        self.assertTrue(self.widget.updatePlot.called_once())

        self.widget.onPrepareOutputData = MagicMock()

        self.assertTrue(self.widget.onPrepareOutputData.called_once())

    def testOnSelectData1(self):
        """ Test ComboBox for Data1 """
        # Case 1: no data loaded
        self.widget.onSelectData1()
        self.assertIsNone(self.widget.data1)
        self.assertFalse(self.widget.data1OK)
        self.assertFalse(self.widget.cmdCompute.isEnabled())

        # Case 2: data1 is a datafile
        self.widget.filenames = MagicMock(
            return_value={'datafile1': 'details'})
        self.widget.updatePlot = MagicMock()

        self.widget.cbData1.addItems(['Select Data', 'datafile1'])
        self.widget.cbData1.setCurrentIndex(self.widget.cbData1.count()-1)
        self.assertTrue(self.widget.updatePlot.called_once())
        # Compute button disabled if data2OK == False
        self.assertEqual(self.widget.cmdCompute.isEnabled(), self.widget.data2OK)

    def testOnSelectData2(self):
        """ Test ComboBox for Data2 """
        self.widget.updatePlot = MagicMock()
        # Case 1: no data loaded
        self.widget.onSelectData2()
        self.assertIsNone(self.widget.data2)
        self.assertFalse(self.widget.data2OK)
        self.assertFalse(self.widget.cmdCompute.isEnabled())

        # Case 2: when empty combobox
        self.widget.cbData2.clear()
        self.widget.onSelectData2()
        self.assertFalse(self.widget.txtNumber.isEnabled())
        self.assertFalse(self.widget.cmdCompute.isEnabled())

        # Case 3: when Data2 is Number
        # add 'Number' to combobox Data2
        self.widget.cbData2.addItem('Number')
        # select 'Number' for cbData2
        self.widget.cbData2.setCurrentIndex(self.widget.cbData2.count()-1)
        self.widget.onSelectData2()
        # check that line edit is now enabled
        self.assertTrue(self.widget.txtNumber.isEnabled())
        # Compute button enabled only if data1OK True
        self.assertEqual(self.widget.cmdCompute.isEnabled(), self.widget.data1OK)
        self.assertIsInstance(self.widget.data2, float)
        # call updatePlot
        self.assertTrue(self.widget.updatePlot.called_once())

        # Case 4: when Data2 is a file
        self.widget.filenames = MagicMock(
            return_value={'datafile2': 'details'})
        self.widget.cbData2.addItems(['Select Data', 'Number', 'datafile2'])
        self.widget.cbData2.setCurrentIndex(self.widget.cbData2.count() - 1)
        self.assertTrue(self.widget.updatePlot.called_once())
        # editing of txtNumber is disabled when Data2 is a file
        self.assertFalse(self.widget.txtNumber.isEnabled())
        # Compute button enabled only if data1OK True
        self.assertEqual(self.widget.cmdCompute.isEnabled(),
                         self.widget.data1OK)
        # call updatePlot
        self.assertTrue(self.widget.updatePlot.called_once())

    def testUpdateCombobox(self):
        """ Test change of contents of comboboxes for Data1 and Data2 """
        # Create input data
        data1 = Data1D(x=[1.0, 2.0, 3.0], y=[11.0, 12.0, 13.0],
                       dx=[0.1, 0.2, 0.3], dy=[0.1, 0.2, 0.3])

        data2 = Data2D(image=[0.1] * 4,
                       qx_data=[1.0, 2.0, 3.0, 4.0],
                       qy_data=[10.0, 11.0, 12.0, 13.0],
                       dqx_data=[0.1, 0.2, 0.3, 0.4],
                       dqy_data=[0.1, 0.2, 0.3, 0.4],
                       q_data=[1, 2, 3, 4],
                       xmin=-1.0, xmax=5.0,
                       ymin=-1.0, ymax=15.0,
                       zmin=-1.0, zmax=20.0)

        filenames = {'datafile2': DataState(data2),
                                 'datafile1': DataState(data1)}

        # call function
        self.widget.updateCombobox(filenames)

        # check modifications of comboboxes
        AllItemsData1 = [self.widget.cbData1.itemText(indx)
                         for indx in range(self.widget.cbData1.count())]
        self.assertListEqual(AllItemsData1, ['Select Data',
                                             'datafile2',
                                             'datafile1'])

        AllItemsData2 = [self.widget.cbData2.itemText(indx)
                         for indx in range(self.widget.cbData2.count())]
        self.assertListEqual(AllItemsData2,
                             ['Select Data', 'Number',
                              'datafile2', 'datafile1'])

    def testOnSelectOperator(self):
        """ Change GUI when operator changed """
        self.assertEqual(self.widget.lblOperatorApplied.text(),self.widget.cbOperator.currentText())

        self.widget.cbOperator.setCurrentIndex(2)
        self.assertEqual(self.widget.lblOperatorApplied.text(),
                         self.widget.cbOperator.currentText())

    def testOnInputCoefficient(self):
        """
        Check input of number when a coefficient is required for operation
        """
        # clear input for coefficient -> error
        self.widget.txtNumber.clear()
        # check that color of background changed to notify error
        self.assertIn(BG_COLOR_ERR, self.widget.txtNumber.styleSheet())


    def testCheckChosenData(self):
        """ Test check of data compatibility """
        # set the 2 following to True since we want to check
        # the compatibility of dimensions
        self.widget.data1OK = True
        self.widget.data2OK = True

        # Case 1: incompatible dimensions
        self.widget.data1 = Data1D(x=[1.0, 2.0, 3.0], y=[11.0, 12.0, 13.0],
                                   dx=[0.1, 0.2, 0.3], dy=[0.1, 0.2, 0.3])

        self.widget.data2 = Data2D(image=[0.1] * 4,
                           qx_data=[1.0, 2.0, 3.0, 4.0],
                           qy_data=[10.0, 11.0, 12.0, 13.0],
                           dqx_data=[0.1, 0.2, 0.3, 0.4],
                           dqy_data=[0.1, 0.2, 0.3, 0.4],
                           q_data=[1, 2, 3, 4],
                           xmin=-1.0, xmax=5.0,
                           ymin=-1.0, ymax=15.0,
                           zmin=-1.0, zmax=20.0)

        self.assertFalse(self.widget.onCheckChosenData())

        # Case 2 : compatible 1 dimension
        self.widget.data1 = Data1D(x=[1.0, 2.0, 3.0], y=[11.0, 12.0, 13.0],
                                   dx=[0.1, 0.2, 0.3], dy=[0.1, 0.2, 0.3])

        self.widget.data2 = Data1D(x=[1.0, 2.0, 3.0], y=[1.0, 2.0, 3.0],
                                   dx=[0.1, 0.2, 0.3], dy=[0.1, 0.2, 0.3])

        self.assertTrue(self.widget.onCheckChosenData())

        # Case 3: compatible 2 dimension
        self.widget.data1 = Data2D(image=[0.1] * 4,
                                   qx_data=[1.0, 2.0, 3.0, 4.0],
                                   qy_data=[10.0, 11.0, 12.0, 13.0],
                                   dqx_data=[0.1, 0.2, 0.3, 0.4],
                                   dqy_data=[0.1, 0.2, 0.3, 0.4],
                                   q_data=[1, 2, 3, 4],
                                   xmin=-1.0, xmax=5.0,
                                   ymin=-1.0, ymax=15.0,
                                   zmin=-1.0, zmax=20.0)

        self.widget.data2 = Data2D(image=[0.1] * 4,
                                   qx_data=[1.0, 2.0, 3.0, 4.0],
                                   qy_data=[10.0, 11.0, 12.0, 13.0],
                                   dqx_data=[0.1, 0.2, 0.3, 0.4],
                                   dqy_data=[0.1, 0.2, 0.3, 0.4],
                                   q_data=[1, 2, 3, 4],
                                   xmin=-1.0, xmax=5.0,
                                   ymin=-1.0, ymax=15.0,
                                   zmin=-1.0, zmax=20.0)

        self.assertTrue(self.widget.onCheckChosenData())

        # Case 4: Different 1D
        self.widget.data1 = Data1D(x=[1.0, 2.0, 3.0], y=[11.0, 12.0, 13.0],
                                   dx=[0.1, 0.2, 0.3], dy=[0.1, 0.2, 0.3])

        self.widget.data2 = Data1D(x=[0.0, 1.0, 2.0], y=[1.0, 2.0, 3.0],
                                   dx=[0.1, 0.2, 0.3], dy=[0.1, 0.2, 0.3])

        self.assertFalse(self.widget.onCheckChosenData())

        # Case 5: Data2 is a Number
        self.widget.cbData2.clear()
        self.widget.cbData2.addItem('Number')
        self.widget.cbData2.setCurrentIndex(0)
        self.assertEqual(self.widget.cbData2.currentText(), 'Number')
        self.assertTrue(self.widget.onCheckChosenData())

    def testOnCheckOutputName(self):
        """ Test OutputName for result of operation """
        self.widget.txtOutputData.clear()
        self.assertFalse(self.widget.onCheckOutputName())

        self.widget.list_data_items = ['datafile1', 'datafile2']
        self.widget.txtOutputData.setText('datafile0')
        self.assertTrue(self.widget.onCheckOutputName())
        self.assertIn('', self.widget.txtOutputData.styleSheet())

        self.widget.txtOutputData.clear()
        self.widget.txtOutputData.setText('datafile1')
        self.assertFalse(self.widget.onCheckOutputName())
        self.assertIn(BG_COLOR_ERR, self.widget.txtOutputData.styleSheet())

    def testFindId(self):
        """ Test function to find id of file in list of filenames"""
        data_for_id = Data1D(x=[1.0, 2.0, 3.0], y=[11.0, 12.0, 13.0],
                                   dx=[0.1, 0.2, 0.3], dy=[0.1, 0.2, 0.3])

        self.widget.filenames = {'datafile2': DataState(data_for_id),
                                 'datafile1': DataState(data_for_id)}

        id_out = self.widget._findId('datafile2')
        self.assertEqual(id_out, 'datafile2')

    def testExtractData(self):
        """
        Test function to extract data to be computed from input filenames
        """
        data1 = Data1D(x=[1.0, 2.0, 3.0], y=[11.0, 12.0, 13.0],
                       dx=[0.1, 0.2, 0.3], dy=[0.1, 0.2, 0.3])

        data2 = Data2D(image=[0.1] * 4,
                                   qx_data=[1.0, 2.0, 3.0, 4.0],
                                   qy_data=[10.0, 11.0, 12.0, 13.0],
                                   dqx_data=[0.1, 0.2, 0.3, 0.4],
                                   dqy_data=[0.1, 0.2, 0.3, 0.4],
                                   q_data=[1, 2, 3, 4],
                                   xmin=-1.0, xmax=5.0,
                                   ymin=-1.0, ymax=15.0,
                                   zmin=-1.0, zmax=20.0)

        self.widget.filenames = {'datafile2': DataState(data2),
                                 'datafile1': DataState(data1)}

        output1D = self.widget._extractData('datafile1')
        self.assertTrue(isinstance(output1D, Data1D))

        output2D = self.widget._extractData('datafile2')
        self.assertIsInstance(output2D, Data2D)

    # TODO
    def testOnPrepareOutputData(self):
        """ """
        pass

    # new_item = GuiUtils.createModelItemWithPlot(
    #     QtCore.QVariant(self.output), name=self.txtOutputData.text())
    # new_datalist_item = {str(self.txtOutputData.text()) + str(time.time()):
    #                          self.output}
    # self.communicator. \
    #     updateModelFromDataOperationPanelSignal.emit(new_item,
    #                                                  new_datalist_item)


if __name__ == "__main__":
    unittest.main()
