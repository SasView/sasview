import sys
import unittest

# Tested module
from GuiUtils import *

class GuiUtilsTest(unittest.TestCase):
    '''Test the GUI Utilities methods'''
    def setUp(self):
        '''Empty'''
        pass

    def tearDown(self):
        '''empty'''
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
            'updateModelFromPerspectiveSignal'
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

if __name__ == "__main__":
    unittest.main()

