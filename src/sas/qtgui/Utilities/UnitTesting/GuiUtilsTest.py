import sys
import webbrowser
import pytest

from PySide6 import QtCore
from PySide6 import QtGui, QtWidgets
from unittest.mock import MagicMock

# SV imports
from sasdata.dataloader.loader import Loader
from sas.qtgui.MainWindow.DataManager import DataManager
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.PlotterData import Data2D

# Tested module
from sas.qtgui.Utilities.GuiUtils import *


class GuiUtilsTest:
    '''Test the GUI Utilities methods'''

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


    def testCommunicate(self, qapp):
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
            assert signal in dir(com)

    def testupdateModelItem(self, qapp):
        """
        Test the generic QModelItem update method
        """
        test_item = QtGui.QStandardItem()
        test_list = ['aa', 4, True, ]
        name = "Black Sabbath"

        # update the item
        updateModelItem(test_item, test_list, name)

        # Make sure test_item got all data added
        assert test_item.child(0).text() == name
        list_from_item = test_item.child(0).data()
        assert isinstance(list_from_item, list)
        assert list_from_item[0] == test_list[0]
        assert list_from_item[1] == test_list[1]
        assert list_from_item[2] == test_list[2]

    @pytest.mark.xfail(reason="2022-09 already broken")
    def testupdateModelItemWithPlot(self, qapp):
        """
        Test the QModelItem checkbox update method
        """
        # test_item = QtGui.QStandardItem()
        # test_list = ['aa','11']
        # update_data = test_list
        # name = "Black Sabbath"

        # # update the item
        # updateModelItemWithPlot(test_item, update_data, name)

        test_item = QtGui.QStandardItem()
        update_data = Data1D(x=[1.0, 2.0, 3.0], y=[10.0, 11.0, 12.0])
        name = "Black Sabbath"
        update_data.id = '[0]data0'
        update_data.name = 'data0'
        # update the item
        updateModelItemWithPlot(test_item, update_data, name)

        # Make sure test_item got all data added
        assert test_item.child(0).text() == name
        assert test_item.child(0).isCheckable()
        data_from_item = test_item.child(0).child(0).data()
        assert isinstance(data_from_item, Data1D)
        assert list(data_from_item.x) == [1.0, 2.0, 3.0]
        assert list(data_from_item.y) == [10.0, 11.0, 12.0]
        assert test_item.rowCount() == 1

        # add another dataset (different from the first one)
        update_data1 = Data1D(x=[1.1, 2.1, 3.1], y=[10.1, 11.1, 12.1])
        update_data1.id = '[0]data1'
        update_data1.name = 'data1'
        name1 = "Black Sabbath1"
        # update the item and check number of rows
        updateModelItemWithPlot(test_item, update_data1, name1)

        assert test_item.rowCount() == 2

        # add another dataset (with the same name as the first one)
        # check that number of rows was not changed but data have been updated
        update_data2 = Data1D(x=[4.0, 5.0, 6.0], y=[13.0, 14.0, 15.0])
        update_data2.id = '[1]data0'
        update_data2.name = 'data0'
        name2 = "Black Sabbath2"
        updateModelItemWithPlot(test_item, update_data2, name2)
        assert test_item.rowCount() == 2

        data_from_item = test_item.child(0).child(0).data()
        assert list(data_from_item.x) == [4.0, 5.0, 6.0]
        assert list(data_from_item.y) == [13.0, 14.0, 15.0]


    def testPlotsFromCheckedItems(self, qapp):
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
        test_item0.setData(test_list0)

        # Checked item 1
        test_item1 = QtGui.QStandardItem(True)
        test_item1.setCheckable(True)
        test_item1.setCheckState(QtCore.Qt.Checked)
        object_item = QtGui.QStandardItem()
        object_item.setData(test_list1)
        test_item1.setChild(0, object_item)

        checkbox_item.setChild(0, test_item0)
        checkbox_item.appendRow(test_item1)

        # Unchecked item 2
        test_item2 = QtGui.QStandardItem(True)
        test_item2.setCheckable(True)
        test_item2.setCheckState(QtCore.Qt.Unchecked)
        object_item = QtGui.QStandardItem()
        object_item.setData(test_list2)
        test_item2.setChild(0, object_item)
        checkbox_item.appendRow(test_item2)

        checkbox_model.appendRow(checkbox_item)

        # Pull out the "plottable" documents
        plot_list = plotsFromCheckedItems(checkbox_model)

        # Make sure only the checked data is present
        # FRIDAY IN
        assert test_list0 in plot_list[0]
        # SATURDAY IN
        assert test_list1 in plot_list[1]
        # MONDAY NOT IN
        assert test_list2 not in plot_list[0]
        assert test_list2 not in plot_list[1]

    @pytest.mark.xfail(reason="2022-09 already broken - input file issue")
    def testInfoFromData(self, qapp):
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
        assert isinstance(item, QtGui.QStandardItem)
        assert item.rowCount() == 5
        assert item.text() == "Info"
        assert p_file in item.child(0).text()
        assert "Run" in item.child(1).text()
        assert "Data1D" in item.child(2).text()
        assert p_file in item.child(3).text()
        assert "Process" in item.child(4).text()

    def testOpenLink(self, mocker):
        """
        Opening a link in the external browser
        """
        good_url1 = r"http://test.test.com"
        good_url2 = r"mailto:test@mail.com"
        good_url3 = r"https://127.0.0.1"

        bad_url1 = ""
        bad_url2 = QtGui.QStandardItem()
        bad_url3 = r"poop;//**I.am.a.!bad@url"

        mocker.patch.object(webbrowser, 'open')
        openLink(good_url1)
        openLink(good_url2)
        openLink(good_url3)
        assert webbrowser.open.call_count == 3

        with pytest.raises(AttributeError):
            openLink(bad_url1)
        with pytest.raises(AttributeError):
            openLink(bad_url2)
        with pytest.raises(AttributeError):
            openLink(bad_url3)

    def testRetrieveData1d(self):
        """
        """
        with pytest.raises(AttributeError):
            retrieveData1d("BOOP")

        #data = Data1D()
        #with pytest.raises(ValueError):
        #    retrieveData1d(data)

        data = Data1D(x=[1.0, 2.0, 3.0], y=[10.0, 11.0, 12.0])

        text = retrieveData1d(data)

        assert "Temperature:" in text
        assert "Beam_size:" in text
        assert "X_min = 1.0:  X_max = 3.0" in text
        assert "3.0 \t12.0 \t0.0 \t0.0" in text

    def testRetrieveData2d(self):
        """
        """
        with pytest.raises(AttributeError):
            retrieveData2d("BOOP")
        data = Data2D(image=[1.0, 2.0, 3.0],
                      err_image=[0.01, 0.02, 0.03],
                      qx_data=[0.1, 0.2, 0.3],
                      qy_data=[0.1, 0.2, 0.3])

        text = retrieveData2d(data)

        assert "Type:         Data2D" in text
        assert "I_min = 1.0" in text
        assert "I_max = 3.0" in text
        assert "2 \t0.3 \t0.3 \t3.0 \t0.03 \t0.0 \t0.0" in text

    def testOnTXTSave(self):
        """
        Test the file writer for saving 1d/2d data
        """
        path = "test123"
        save_path = path + ".txt"
        if os.path.isfile(path):
            os.remove(path)
        if os.path.isfile(save_path):
            os.remove(save_path)

        # Broken data
        data = Data1D(x=[1.0, 2.0, 3.0], y=[])
        # Expect a raise
        with pytest.raises(IndexError):
            onTXTSave(data, path)

        # Good data - no dX/dY
        data = Data1D(x=[1.0, 2.0, 3.0], y=[10.0, 11.0, 12.0])
        onTXTSave(data, path)

        assert os.path.isfile(save_path)
        with open(save_path,'r') as out:
            data_read = out.read()
            expected = \
            "<X> <Y>\n"+\
            "1.000000000000000e+00 1.000000000000000e+01\n" +\
            "2.000000000000000e+00 1.100000000000000e+01\n" +\
            "3.000000000000000e+00 1.200000000000000e+01\n"

            assert expected == data_read

        if os.path.isfile(save_path):
            os.remove(save_path)

        # Good data - with dX/dY
        data = Data1D(x=[1.0, 2.0, 3.0], y=[10.0, 11.0, 12.0],
                      dx=[0.1, 0.2, 0.3], dy=[0.1, 0.2, 0.3])

        onTXTSave(data, path)
        with open(save_path,'r') as out:
            data_read = out.read()
            assert "<X> <Y> <dY> <dX>\n" in data_read
            assert "1.000000000000000e+00 1.000000000000000e+01 1.000000000000000e-01 1.000000000000000e-01\n" in data_read
            assert "2.000000000000000e+00 1.100000000000000e+01 2.000000000000000e-01 2.000000000000000e-01\n" in data_read
            assert "3.000000000000000e+00 1.200000000000000e+01 3.000000000000000e-01 3.000000000000000e-01\n" in data_read

        if os.path.isfile(save_path):
            os.remove(save_path)

    def testSaveAnyData(self, qapp, caplog, mocker):
        """
        Test the generic GUIUtils.saveAnyData method
        """
        data = Data1D(x=[1.0, 2.0, 3.0], y=[10.0, 11.0, 12.0],
                      dx=[0.1, 0.2, 0.3], dy=[0.1, 0.2, 0.3])

        # Test the .txt format
        file_name = "test123_out"
        file_name_save = "test123_out.txt"
        mocker.patch.object(QtWidgets.QFileDialog, 'getSaveFileName', return_value=(file_name,''))
        data.filename = "test123.txt"
        self.genericFileSaveTest(data, file_name, file_name_save, "ASCII", caplog=caplog)

        data = Data2D(image=[1.0, 2.0, 3.0],
                      err_image=[0.01, 0.02, 0.03],
                      qx_data=[0.1, 0.2, 0.3],
                      qy_data=[0.1, 0.2, 0.3])

        # Test the .txt format
        file_name = "test123_out"
        file_name_save = "test123_out.dat"
        mocker.patch.object(QtWidgets.QFileDialog, 'getSaveFileName', return_value=(file_name,''))
        data.filename = "test123.dat"
        self.genericFileSaveTest(data, file_name, file_name_save, "IGOR", caplog=caplog)

    def testSaveData1D(self, qapp, caplog, mocker):
        """
        Test the 1D file save method
        """
        data = Data1D(x=[1.0, 2.0, 3.0], y=[10.0, 11.0, 12.0],
                      dx=[0.1, 0.2, 0.3], dy=[0.1, 0.2, 0.3])

        # Test the .txt format
        file_name = "test123_out.txt"
        mocker.patch.object(QtWidgets.QFileDialog, 'getSaveFileName', return_value=(file_name,''))
        data.filename = "test123.txt"
        self.genericFileSaveTest(data, file_name)

        # Test the .xml format
        file_name = "test123_out.xml"
        mocker.patch.object(QtWidgets.QFileDialog, 'getSaveFileName', return_value=(file_name,''))
        data.filename = "test123.xml"
        self.genericFileSaveTest(data, file_name)

        # Test the wrong format
        file_name = "test123_out.mp3"
        mocker.patch.object(QtWidgets.QFileDialog, 'getSaveFileName', return_value=(file_name,''))
        data.filename = "test123.mp3"
        self.genericFileSaveTest(data, file_name, file_name, "ASCII", "1D", caplog=caplog)

    def testSaveData2D(self, qapp, caplog, mocker):
        """
        Test the 1D file save method
        """
        data = Data2D(image=[1.0, 2.0, 3.0],
                      err_image=[0.01, 0.02, 0.03],
                      qx_data=[0.1, 0.2, 0.3],
                      qy_data=[0.1, 0.2, 0.3])

        # Test the .txt format
        file_name = "test123_out.dat"
        mocker.patch.object(QtWidgets.QFileDialog, 'getSaveFileName', return_value=(file_name,''))
        data.filename = "test123.dat"
        self.genericFileSaveTest(data, file_name)

        # Test the wrong format
        file_name = "test123_out.mp3"
        mocker.patch.object(QtWidgets.QFileDialog, 'getSaveFileName', return_value=(file_name,''))
        data.filename = "test123.mp3"
        self.genericFileSaveTest(data, file_name, file_name, "IGOR", "2D", caplog=caplog)

    def genericFileSaveTest(self, data, name, name_full="", file_format="ASCII", level=None, caplog=False):
        if level == '1D':
            saveMethod = saveData1D
        elif level == "2D":
            saveMethod = saveData2D
        else:
            saveMethod = saveAnyData

        name_full = name if name_full == "" else name_full

        if caplog:
            with caplog.at_level(logging.WARNING):
                saveMethod(data)
                #assert len(cm.output) == 1
                assert (f"Unknown file type specified when saving {name}."
                        + f" Saving in {file_format} format.") in caplog.text
        else:
            saveMethod(data)
        assert os.path.isfile(name_full)
        os.remove(name_full)
        assert not os.path.isfile(name_full)

    def testXYTransform(self, qapp):
        """ Assure the unit/legend transformation is correct"""
        data = Data1D(x=[1.0, 2.0, 3.0], y=[10.0, 11.0, 12.0],
                      dx=[0.1, 0.2, 0.3], dy=[0.1, 0.2, 0.3])

        xLabel, yLabel, xscale, yscale = xyTransform(data, xLabel="x", yLabel="y")
        assert xLabel == "()"
        assert xscale == "linear"
        assert yscale == "linear"

        xLabel, yLabel, xscale, yscale = xyTransform(data, xLabel="x^(2)", yLabel="1/y")
        assert xLabel == "^{2}(()^{2})"
        assert yLabel == "1/(()^{-1})"
        assert xscale == "linear"
        assert yscale == "linear"

        xLabel, yLabel, xscale, yscale = xyTransform(data, xLabel="x^(4)", yLabel="ln(y)")
        assert xLabel == "^{4}(()^{4})"
        assert yLabel == "\\ln{()}()"
        assert xscale == "linear"
        assert yscale == "linear"

        xLabel, yLabel, xscale, yscale = xyTransform(data, xLabel="ln(x)", yLabel="y^(2)")
        assert xLabel == "\\ln{()}()"
        assert yLabel == "^{2}(()^{2})"
        assert xscale == "linear"
        assert yscale == "linear"

        xLabel, yLabel, xscale, yscale = xyTransform(data, xLabel="log10(x)", yLabel="y*x^(2)")
        assert xLabel == "()"
        assert yLabel == " \\ \\ ^{2}(()^{2})"
        assert xscale == "log"
        assert yscale == "linear"

        xLabel, yLabel, xscale, yscale = xyTransform(data, xLabel="log10(x^(4))", yLabel="y*x^(4)")
        assert xLabel == "^{4}(()^{4})"
        assert yLabel == " \\ \\ ^{4}(()^{16})"
        assert xscale == "log"
        assert yscale == "linear"

        xLabel, yLabel, xscale, yscale = xyTransform(data, xLabel="x", yLabel="1/sqrt(y)")
        assert yLabel == "1/\\sqrt{}(()^{-0.5})"
        assert yscale == "linear"

        xLabel, yLabel, xscale, yscale = xyTransform(data, xLabel="x", yLabel="log10(y)")
        assert yLabel == "()"
        assert yscale == "log"

        xLabel, yLabel, xscale, yscale = xyTransform(data, xLabel="x", yLabel="ln(y*x)")
        assert yLabel == "\\ln{( \\ \\ )}()"
        assert yscale == "linear"

        xLabel, yLabel, xscale, yscale = xyTransform(data, xLabel="x", yLabel="ln(y*x^(2))")
        assert yLabel == "\\ln ( \\ \\ ^{2})(()^{2})"
        assert yscale == "linear"

        xLabel, yLabel, xscale, yscale = xyTransform(data, xLabel="x", yLabel="ln(y*x^(4))")
        assert yLabel == "\\ln ( \\ \\ ^{4})(()^{4})"
        assert yscale == "linear"

        xLabel, yLabel, xscale, yscale = xyTransform(data, xLabel="x", yLabel="log10(y*x^(4))")
        assert yLabel == " \\ \\ ^{4}(()^{4})"
        assert yscale == "log"

    def testReplaceHTMLwithUTF8(self):
        ''' test single character replacement '''
        s = None
        with pytest.raises(AttributeError):
            result = replaceHTMLwithUTF8(s)

        s = ""
        assert replaceHTMLwithUTF8(s) == s

        s = "aaaa"
        assert replaceHTMLwithUTF8(s) == s

        s = "&#x212B; &#x221e;      &#177;"
        assert replaceHTMLwithUTF8(s) == "Å ∞      ±"

    def testReplaceHTMLwithASCII(self):
        ''' test single character replacement'''
        s = None
        with pytest.raises(AttributeError):
            result = replaceHTMLwithASCII(s)

        s = ""
        assert replaceHTMLwithASCII(s) == s

        s = "aaaa"
        assert replaceHTMLwithASCII(s) == s

        s = "&#x212B; &#x221e;      &#177;"
        assert replaceHTMLwithASCII(s) == "Ang inf      +/-"

    def testConvertUnitToUTF8(self):
        ''' test unit string replacement'''
        s = None
        assert convertUnitToUTF8(s) is None

        s = ""
        assert convertUnitToUTF8(s) == s

        s = "aaaa"
        assert convertUnitToUTF8(s) == s

        s = "1/A"
        assert convertUnitToUTF8(s) == "Å<sup>-1</sup>"

        s = "Ang"
        assert convertUnitToUTF8(s) == "Å"

        s = "1e-6/Ang^2"
        assert convertUnitToUTF8(s) == "10<sup>-6</sup>/Å<sup>2</sup>"

        s = "inf"
        assert convertUnitToUTF8(s) == "∞"

        s = "1/cm"
        assert convertUnitToUTF8(s) == "cm<sup>-1</sup>"

    def testConvertUnitToHTML(self):
        ''' test unit string replacement'''
        s = None
        assert convertUnitToHTML(s) is None

        s = ""
        assert convertUnitToHTML(s) == s

        s = "aaaa"
        assert convertUnitToHTML(s) == s

        s = "1/A"
        assert convertUnitToHTML(s) == "&#x212B;<sup>-1</sup>"

        s = "Ang"
        assert convertUnitToHTML(s) == "&#x212B;"

        s = "1e-6/Ang^2"
        assert convertUnitToHTML(s) == "10<sup>-6</sup>/&#x212B;<sup>2</sup>"

        s = "inf"
        assert convertUnitToHTML(s) == "&#x221e;"
        s = "-inf"

        assert convertUnitToHTML(s) == "-&#x221e;"

        s = "1/cm"
        assert convertUnitToHTML(s) == "cm<sup>-1</sup>"

    def testParseName(self):
        '''test parse out a string from the beinning of a string'''
        # good input
        value = "_test"
        assert parseName(value, '_') == 'test'
        value = "____test____"
        assert parseName(value, '_') == '___test____'
        assert parseName(value, '___') == '_test____'
        assert parseName(value, 'test') == '____test____'
        # bad input
        with pytest.raises(TypeError):
            parseName(value, None)
        with pytest.raises(TypeError):
            parseName(None, '_')
        value = []
        with pytest.raises(TypeError):
            parseName(value, '_')
        value = 1.44
        with pytest.raises(TypeError):
            parseName(value, 'p')
        value = 100
        with pytest.raises(TypeError):
            parseName(value, 'p')

    @pytest.mark.xfail(reason="2022-09 already broken")
    def testToDouble(self):
        '''test homemade string-> double converter'''
        #good values
        value = "1"
        assert toDouble(value) == 1.0
        value = "1.2"
        # has to be AlmostEqual due to numerical rounding
        assert toDouble(value) == pytest.approx(1.2, abs=1e-6)
        value = "2,1"
        assert toDouble(value) == pytest.approx(2.1, abs=1e-6)

        # bad values
        value = None
        with pytest.raises(TypeError):
            toDouble(value)
        value = "MyDouble"
        with pytest.raises(TypeError):
            toDouble(value)
        value = [1,2.2]
        with pytest.raises(TypeError):
            toDouble(value)


class DoubleValidatorTest:
    """ Test the validator for floats """
    @pytest.fixture(autouse=True)
    def validator(self, qapp):
        '''Create/Destroy the validator'''
        v = DoubleValidator()
        yield v

    def testValidateGood(self, validator):
        """Test a valid float """
        QtCore.QLocale.setDefault(QtCore.QLocale('en_US'))
        float_good = "170"
        assert validator.validate(float_good, 1)[0] == QtGui.QValidator.Acceptable
        float_good = "170.11"
        ## investigate: a double returns Invalid here!
        ##assert self.validator.validate(float_good, 1)[0] == QtGui.QValidator.Acceptable
        float_good = "17e2"
        assert validator.validate(float_good, 1)[0] == QtGui.QValidator.Acceptable

    def testValidateBad(self, validator):
        """Test a bad float """
        float_bad = None
        assert validator.validate(float_bad, 1)[0] == QtGui.QValidator.Intermediate
        float_bad = [1]
        with pytest.raises(TypeError):
           validator.validate(float_bad, 1)
        float_bad = "1,3"
        assert validator.validate(float_bad, 1)[0] == QtGui.QValidator.Invalid

    def notestFixup(self, validator):
        """Fixup of a float"""
        float_to_fixup = "1,3"
        validator.fixup(float_to_fixup)
        assert float_to_fixup == "13"


class FormulaValidatorTest:
    """ Test the formula validator """
    @pytest.fixture(autouse=True)
    def validator(self, qapp):
        '''Create/Destroy the validator'''
        v = FormulaValidator()
        yield v

    def testValidateGood(self, validator):
        """Test a valid Formula """
        formula_good = "H24O12C4C6N2Pu"
        assert validator.validate(formula_good, 1)[0] == QtGui.QValidator.Acceptable

        formula_good = "(H2O)0.5(D2O)0.5"
        assert validator.validate(formula_good, 1)[0] == QtGui.QValidator.Acceptable

    @pytest.mark.xfail(reason="2022-09 already broken")
    def testValidateBad(self, validator):
        """Test an invalid Formula """
        formula_bad = "H24 %%%O12C4C6N2Pu"
        pytest.raises(validator.validate(formula_bad, 1)[0])
        assert validator.validate(formula_bad, 1)[0] == QtGui.QValidator.Intermediate

        formula_bad = [1]
        assert self.validator.validate(formula_bad, 1)[0] == QtGui.QValidator.Intermediate

class HashableStandardItemTest:
    """ Test the reimplementation of QStandardItem """
    @pytest.fixture(autouse=True)
    def item(self, qapp):
        '''Create/Destroy the HashableStandardItem'''
        i = HashableStandardItem()
        yield i

    def testHash(self, item):
        '''assure the item returns hash'''
        assert item.__hash__() == 0

    def testIndexing(self, item):
        '''test that we can use HashableSI as an index'''
        dictionary = {}
        dictionary[item] = "wow!"
        assert dictionary[item] == "wow!"

    def testClone(self, item):
        '''let's see if we can clone the item'''
        item_clone = item.clone()
        assert item_clone.__hash__() == 0

    def testGetConstraints(self):
        '''test the method that reads constraints from a project and returns
        a dict with the constraints'''
        # create a project dict with constraints
        constraint1 = ['scale', 'scale', 'M2.scale', True, 'M2.scale']
        constraint2 = ['scale', 'scale', 'M1.scale', True, 'M1.scale']
        fit_params1 = {'tab_name': ['M1'], 'scale': [True, '1.0', None,
                                                     '0.0', 'inf',
                                                     constraint1], 'foo': 'bar'}
        fit_params2 = {'tab_name': ['M2'], 'scale': [True, '1.0', None,
                                                     '0.0', 'inf',
                                                     constraint2], 'foo': 'bar'}
        fit_page1 = {'fit_data': None, 'fit_params': [fit_params1]}
        fit_page2 = {'fit_data': None, 'fit_params': [fit_params2]}
        fit_project = {'dataset1': fit_page1, 'dataset2': fit_page2}
        # get the constraint_dict
        constraint_dict = getConstraints(fit_project)
        # we have two constraints on different fit pages
        assert len(constraint_dict) == 2
        # we have one constraint per fit page
        assert len(constraint_dict['M1']) == 1
        assert len(constraint_dict['M2']) == 1
        # check the constraints in the constraint_dict
        assert constraint_dict['M1'][0] == constraint1
        assert constraint_dict['M2'][0] == constraint2
