import sys
import unittest
import webbrowser

from PyQt4 import QtCore
from PyQt4 import QtGui
from mock import MagicMock

# set up import paths
import sas.qtgui.path_prepare

# SV imports
from sas.sascalc.dataloader.loader import Loader
from sas.qtgui.MainWindow.DataManager import DataManager
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.PlotterData import Data2D

# Tested module
from sas.qtgui.Utilities.GuiUtils import *

if not QtGui.QApplication.instance():
    app = QtGui.QApplication(sys.argv)

class GuiUtilsTest(unittest.TestCase):
    '''Test the GUI Utilities methods'''
    def setUp(self):
        '''Empty'''
        pass

    def tearDown(self):
        '''Empty'''
        pass

    def testDefaults(self):
        """
        Test all the global constants defined in the file.
        """
        # Should probably test the constants in the file,
        # but this will done after trimming down GuiUtils
        # and retaining only necessary variables.
        pass

    def testGetAppDir(self):
        """
        """
        pass

    def testGetUserDirectory(self):
        """
        Simple test of user directory getter
        """
        home_dir = os.path.expanduser("~")
        self.assertIn(home_dir, get_user_directory())

    def testCommunicate(self):
        """
        Test the container class with signal definitions
        """
        com = Communicate()

        # All defined signals
        list_of_signals = [
            'fileReadSignal',
            'fileDataReceivedSignal',
            'statusBarUpdateSignal',
            'updatePerspectiveWithDataSignal',
            'updateModelFromPerspectiveSignal',
            'plotRequestedSignal',
            'progressBarUpdateSignal',
            'activeGraphName',
            'sendDataToPanelSignal',
            'updateModelFromDataOperationPanelSignal'
        ]

        # Assure all signals are defined.
        for signal in list_of_signals:
            self.assertIn(signal, dir(com))

    def testupdateModelItem(self):
        """
        Test the generic QModelItem update method
        """
        test_item = QtGui.QStandardItem()
        test_list = ['aa', 4, True, ]
        name = "Black Sabbath"

        # update the item
        updateModelItem(test_item, test_list, name)

        # Make sure test_item got all data added
        self.assertEqual(test_item.child(0).text(), name)
        list_from_item = test_item.child(0).data().toList()
        self.assertIsInstance(list_from_item, list)
        self.assertEqual(list_from_item[0].toPyObject(), test_list[0])
        self.assertEqual(list_from_item[1].toPyObject(), test_list[1])
        self.assertEqual(list_from_item[2].toPyObject(), test_list[2])

    def testupdateModelItemWithPlot(self):
        """
        Test the QModelItem checkbox update method
        """
        test_item = QtGui.QStandardItem()
        test_list = ['aa','11']
        update_data = QtCore.QVariant(test_list)
        name = "Black Sabbath"

        # update the item
        updateModelItemWithPlot(test_item, update_data, name)
        
        # Make sure test_item got all data added
        self.assertEqual(test_item.child(0).text(), name)
        self.assertTrue(test_item.child(0).isCheckable())
        list_from_item = test_item.child(0).child(0).data().toPyObject()
        self.assertIsInstance(list_from_item, list)
        self.assertEqual(str(list_from_item[0]), test_list[0])
        self.assertEqual(str(list_from_item[1]), test_list[1])


    def testPlotsFromCheckedItems(self):
        """
        Test addition of a plottable to the model
        """

        # Mockup data
        test_list0 = "FRIDAY"
        test_list1 = "SATURDAY"
        test_list2 = "MONDAY"

        # Main item ("file")
        checkbox_model = QtGui.QStandardItemModel()
        checkbox_item = QtGui.QStandardItem(True)
        checkbox_item.setCheckable(True)
        checkbox_item.setCheckState(QtCore.Qt.Checked)
        test_item0 = QtGui.QStandardItem()
        test_item0.setData(QtCore.QVariant(test_list0))

        # Checked item 1
        test_item1 = QtGui.QStandardItem(True)
        test_item1.setCheckable(True)
        test_item1.setCheckState(QtCore.Qt.Checked)
        object_item = QtGui.QStandardItem()
        object_item.setData(QtCore.QVariant(test_list1))
        test_item1.setChild(0, object_item)

        checkbox_item.setChild(0, test_item0)
        checkbox_item.appendRow(test_item1)

        # Unchecked item 2
        test_item2 = QtGui.QStandardItem(True)
        test_item2.setCheckable(True)
        test_item2.setCheckState(QtCore.Qt.Unchecked)
        object_item = QtGui.QStandardItem()
        object_item.setData(QtCore.QVariant(test_list2))
        test_item2.setChild(0, object_item)
        checkbox_item.appendRow(test_item2)

        checkbox_model.appendRow(checkbox_item)

        # Pull out the "plottable" documents
        plot_list = plotsFromCheckedItems(checkbox_model)

        # Make sure only the checked data is present
        # FRIDAY IN
        self.assertIn(test_list0, plot_list[0])
        # SATURDAY IN
        self.assertIn(test_list1, plot_list[1])
        # MONDAY NOT IN
        self.assertNotIn(test_list2, plot_list[0])
        self.assertNotIn(test_list2, plot_list[1])

    def testInfoFromData(self):
        """
        Test Info element extraction from a plottable object
        """
        loader = Loader()
        manager = DataManager()

        # get Data1D
        p_file="cyl_400_20.txt"
        output_object = loader.load(p_file)
        new_data = manager.create_gui_data(output_object[0], p_file)

        # Extract Info elements into a model item
        item = infoFromData(new_data)

        # Test the item and its children
        self.assertIsInstance(item, QtGui.QStandardItem)
        self.assertEqual(item.rowCount(), 5)
        self.assertEqual(item.text(), "Info")
        self.assertIn(p_file,   item.child(0).text())
        self.assertIn("Run",    item.child(1).text())
        self.assertIn("Data1D", item.child(2).text())
        self.assertIn(p_file,   item.child(3).text())
        self.assertIn("Process",item.child(4).text())

    def testOpenLink(self):
        """
        Opening a link in the external browser
        """
        good_url1 = r"http://test.test.com"
        good_url2 = r"mailto:test@mail.com"
        good_url3 = r"https://127.0.0.1"

        bad_url1 = ""
        bad_url2 = QtGui.QStandardItem()
        bad_url3 = r"poop;//**I.am.a.!bad@url"

        webbrowser.open = MagicMock()
        openLink(good_url1)
        openLink(good_url2)
        openLink(good_url3)
        self.assertEqual(webbrowser.open.call_count, 3)

        with self.assertRaises(AttributeError):
            openLink(bad_url1)
        with self.assertRaises(AttributeError):
            openLink(bad_url2)
        with self.assertRaises(AttributeError):
            openLink(bad_url3)

    def testRetrieveData1d(self):
        """
        """
        with self.assertRaises(AttributeError):
            retrieveData1d("BOOP")

        #data = Data1D()
        #with self.assertRaises(ValueError):
        #    retrieveData1d(data)

        data = Data1D(x=[1.0, 2.0, 3.0], y=[10.0, 11.0, 12.0])

        text = retrieveData1d(data)

        self.assertIn("Temperature:", text)
        self.assertIn("Beam_size:", text)
        self.assertIn("X_min = 1.0:  X_max = 3.0", text)
        self.assertIn("3.0 \t12.0 \t0.0 \t0.0", text)

    def testRetrieveData2d(self):
        """
        """
        with self.assertRaises(AttributeError):
            retrieveData2d("BOOP")
        data = Data2D(image=[1.0, 2.0, 3.0],
                      err_image=[0.01, 0.02, 0.03],
                      qx_data=[0.1, 0.2, 0.3],
                      qy_data=[0.1, 0.2, 0.3])

        text = retrieveData2d(data)

        self.assertIn("Type:         Data2D", text)
        self.assertIn("I_min = 1.0", text)
        self.assertIn("I_max = 3.0", text)
        self.assertIn("2 \t0.3 \t0.3 \t3.0 \t0.03 \t0.0 \t0.0", text)

    def testOnTXTSave(self):
        """
        Test the file writer for saving 1d/2d data
        """
        path = "test123"
        if os.path.isfile(path):
            os.remove(path)

        # Broken data
        data = Data1D(x=[1.0, 2.0, 3.0], y=[])
        # Expect a raise
        with self.assertRaises(IndexError):
            onTXTSave(data, path)

        # Good data - no dX/dY
        data = Data1D(x=[1.0, 2.0, 3.0], y=[10.0, 11.0, 12.0])
        onTXTSave(data, path)

        self.assertTrue(os.path.isfile(path))
        with open(path,'r') as out:
            data_read = out.read()
            self.assertEqual("<X>   <Y>\n1  10\n2  11\n3  12\n", data_read)

        if os.path.isfile(path):
            os.remove(path)

        # Good data - with dX/dY
        data = Data1D(x=[1.0, 2.0, 3.0], y=[10.0, 11.0, 12.0],
                      dx=[0.1, 0.2, 0.3], dy=[0.1, 0.2, 0.3])

        onTXTSave(data, path)
        with open(path,'r') as out:
            data_read = out.read()
            self.assertIn("<X>   <Y>   <dY>   <dX>\n", data_read)
            self.assertIn("1  10  0.1  0.1\n", data_read)
            self.assertIn("2  11  0.2  0.2\n", data_read)
            self.assertIn("3  12  0.3  0.3\n", data_read)

        if os.path.isfile(path):
            os.remove(path)

    def testSaveData1D(self):
        """
        Test the 1D file save method
        """
        data = Data1D(x=[1.0, 2.0, 3.0], y=[10.0, 11.0, 12.0],
                      dx=[0.1, 0.2, 0.3], dy=[0.1, 0.2, 0.3])

        # Test the .txt format
        file_name = "test123_out.txt"
        QtGui.QFileDialog.getSaveFileName = MagicMock(return_value=file_name)
        data.filename = "test123.txt"
        saveData1D(data)
        self.assertTrue(os.path.isfile(file_name))
        os.remove(file_name)

        # Test the .xml format
        file_name = "test123_out.xml"
        QtGui.QFileDialog.getSaveFileName = MagicMock(return_value=file_name)
        data.filename = "test123.xml"
        saveData1D(data)
        self.assertTrue(os.path.isfile(file_name))
        os.remove(file_name)

        # Test the wrong format
        file_name = "test123_out.mp3"
        QtGui.QFileDialog.getSaveFileName = MagicMock(return_value=file_name)
        data.filename = "test123.mp3"
        saveData1D(data)
        self.assertFalse(os.path.isfile(file_name))

    def testSaveData2D(self):
        """
        Test the 1D file save method
        """
        data = Data2D(image=[1.0, 2.0, 3.0],
                      err_image=[0.01, 0.02, 0.03],
                      qx_data=[0.1, 0.2, 0.3],
                      qy_data=[0.1, 0.2, 0.3])

        # Test the .txt format
        file_name = "test123_out.dat"
        QtGui.QFileDialog.getSaveFileName = MagicMock(return_value=file_name)
        data.filename = "test123.dat"
        saveData2D(data)
        self.assertTrue(os.path.isfile(file_name))
        os.remove(file_name)

        # Test the wrong format
        file_name = "test123_out.mp3"
        QtGui.QFileDialog.getSaveFileName = MagicMock(return_value=file_name)
        data.filename = "test123.mp3"
        saveData2D(data)
        self.assertFalse(os.path.isfile(file_name))

    def testXYTransform(self):
        """ Assure the unit/legend transformation is correct"""
        data = Data1D(x=[1.0, 2.0, 3.0], y=[10.0, 11.0, 12.0],
                      dx=[0.1, 0.2, 0.3], dy=[0.1, 0.2, 0.3])

        xLabel, yLabel, xscale, yscale = xyTransform(data, xLabel="x", yLabel="y")
        self.assertEqual(xLabel, "()")
        self.assertEqual(xscale, "linear")
        self.assertEqual(yscale, "linear")

        xLabel, yLabel, xscale, yscale = xyTransform(data, xLabel="x^(2)", yLabel="1/y")
        self.assertEqual(xLabel, "^{2}(()^{2})")
        self.assertEqual(yLabel, "1/(()^{-1})")
        self.assertEqual(xscale, "linear")
        self.assertEqual(yscale, "linear")

        xLabel, yLabel, xscale, yscale = xyTransform(data, xLabel="x^(4)", yLabel="ln(y)")
        self.assertEqual(xLabel, "^{4}(()^{4})")
        self.assertEqual(yLabel, "\\ln{()}()")
        self.assertEqual(xscale, "linear")
        self.assertEqual(yscale, "linear")

        xLabel, yLabel, xscale, yscale = xyTransform(data, xLabel="ln(x)", yLabel="y^(2)")
        self.assertEqual(xLabel, "\\ln{()}()")
        self.assertEqual(yLabel, "^{2}(()^{2})")
        self.assertEqual(xscale, "linear")
        self.assertEqual(yscale, "linear")

        xLabel, yLabel, xscale, yscale = xyTransform(data, xLabel="log10(x)", yLabel="y*x^(2)")
        self.assertEqual(xLabel, "()")
        self.assertEqual(yLabel, " \\ \\ ^{2}(()^{2})")
        self.assertEqual(xscale, "log")
        self.assertEqual(yscale, "linear")

        xLabel, yLabel, xscale, yscale = xyTransform(data, xLabel="log10(x^(4))", yLabel="y*x^(4)")
        self.assertEqual(xLabel, "^{4}(()^{4})")
        self.assertEqual(yLabel, " \\ \\ ^{4}(()^{16})")
        self.assertEqual(xscale, "log")
        self.assertEqual(yscale, "linear")

        xLabel, yLabel, xscale, yscale = xyTransform(data, xLabel="x", yLabel="1/sqrt(y)")
        self.assertEqual(yLabel, "1/\\sqrt{}(()^{-0.5})")
        self.assertEqual(yscale, "linear")

        xLabel, yLabel, xscale, yscale = xyTransform(data, xLabel="x", yLabel="log10(y)")
        self.assertEqual(yLabel, "()")
        self.assertEqual(yscale, "log")

        xLabel, yLabel, xscale, yscale = xyTransform(data, xLabel="x", yLabel="ln(y*x)")
        self.assertEqual(yLabel, "\\ln{( \\ \\ )}()")
        self.assertEqual(yscale, "linear")

        xLabel, yLabel, xscale, yscale = xyTransform(data, xLabel="x", yLabel="ln(y*x^(2))")
        self.assertEqual(yLabel, "\\ln ( \\ \\ ^{2})(()^{2})")
        self.assertEqual(yscale, "linear")

        xLabel, yLabel, xscale, yscale = xyTransform(data, xLabel="x", yLabel="ln(y*x^(4))")
        self.assertEqual(yLabel, "\\ln ( \\ \\ ^{4})(()^{4})")
        self.assertEqual(yscale, "linear")

        xLabel, yLabel, xscale, yscale = xyTransform(data, xLabel="x", yLabel="log10(y*x^(4))")
        self.assertEqual(yLabel, " \\ \\ ^{4}(()^{4})")
        self.assertEqual(yscale, "log")


class FormulaValidatorTest(unittest.TestCase):
    """ Test the formula validator """
    def setUp(self):
        '''Create the validator'''
        self.validator = FormulaValidator()

    def tearDown(self):
        '''Destroy the validator'''
        self.validator = None

    def testValidateGood(self):
        """Test a valid Formula """
        formula_good = "H24O12C4C6N2Pu"
        self.assertEqual(self.validator.validate(formula_good, 1)[0], QtGui.QValidator.Acceptable)

        formula_good = "(H2O)0.5(D2O)0.5"
        self.assertEqual(self.validator.validate(formula_good, 1)[0], QtGui.QValidator.Acceptable)

    def testValidateBad(self):
        """Test a valid Formula """
        formula_bad = "H24 %%%O12C4C6N2Pu"
        self.assertRaises(self.validator.validate(formula_bad, 1)[0])
        self.assertEqual(self.validator.validate(formula_bad, 1)[0], QtGui.QValidator.Intermediate)

        formula_bad = [1]
        self.assertEqual(self.validator.validate(formula_bad, 1)[0], QtGui.QValidator.Intermediate)


if __name__ == "__main__":
    unittest.main()

