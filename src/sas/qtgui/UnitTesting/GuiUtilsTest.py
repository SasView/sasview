import sys
import unittest
import webbrowser
import urlparse

from PyQt4 import QtCore
from PyQt4 import QtGui
from mock import MagicMock

# SV imports
from sas.sascalc.dataloader.loader import Loader
from sas.sasgui.guiframe.data_manager import DataManager

# Tested module
from GuiUtils import *

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
            'plotRequestedSignal'
        ]

        # Assure all signals are defined.
        for signal in list_of_signals:
            self.assertIn(signal, dir(com))


    def testUpdateModelItem(self):
        """
        Test the QModelItem update method
        """
        test_item = QtGui.QStandardItem()
        test_list = ['aa','11']
        update_data = QtCore.QVariant(test_list)
        name = "Black Sabbath"

        # update the item
        updateModelItem(test_item, update_data, name)
        
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
        self.assertIn(test_list0, plot_list)
        # SATURDAY IN
        self.assertIn(test_list1, plot_list)
        # MONDAY NOT IN
        self.assertNotIn(test_list2, plot_list)

    def testInfoFromData(self):
        """
        Test Info element extraction from a plottable object
        """
        loader = Loader()
        manager = DataManager()

        # get Data1D
        p_file="cyl_400_20.txt"
        output_object = loader.load(p_file)
        new_data = manager.create_gui_data(output_object, p_file)

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
        pass

if __name__ == "__main__":
    unittest.main()

