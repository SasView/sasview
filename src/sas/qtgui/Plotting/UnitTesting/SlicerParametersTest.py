import sys
import unittest
from unittest.mock import MagicMock

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import QtTest
from PyQt4 import QtWebKit

# set up import paths
import sas.qtgui.path_prepare

from sas.qtgui.UnitTesting.TestUtils import QtSignalSpy

# Local
from sas.qtgui.Plotting.SlicerParameters import SlicerParameters

if not QtGui.QApplication.instance():
    app = QtGui.QApplication(sys.argv)

class SlicerParametersTest(unittest.TestCase):
    '''Test the SlicerParameters dialog'''
    def setUp(self):
        '''Create the SlicerParameters dialog'''

        item1 = QtGui.QStandardItem("dromekage")
        item2 = QtGui.QStandardItem("999.0")
        self.model = QtGui.QStandardItemModel()
        self.model.appendRow([item1, item2])
        self.widget = SlicerParameters(model=self.model)

    def tearDown(self):
        '''Destroy the model'''
        self.widget = None

    def testDefaults(self):
        '''Test the GUI in its default state'''
        #self.widget.mapper
        self.assertIsInstance(self.widget.proxy, QtGui.QIdentityProxyModel)
        self.assertIsInstance(self.widget.lstParams.itemDelegate(), QtGui.QStyledItemDelegate)
        self.assertTrue(self.widget.lstParams.model().columnReadOnly(0))
        self.assertFalse(self.widget.lstParams.model().columnReadOnly(1))

        # Test the proxy model
        self.assertEqual(self.widget.lstParams.model(), self.widget.proxy)
        self.assertEqual(self.widget.proxy.columnCount(), 2)
        self.assertEqual(self.widget.proxy.rowCount(), 1)
        self.assertEqual(self.widget.model.item(0,0).text(), 'dromekage')
        self.assertEqual(self.widget.model.item(0,1).text(), '999.0')

        # Check the flags in the proxy model
        flags = self.widget.proxy.flags(self.widget.proxy.index(0,0))
        self.assertFalse(flags & QtCore.Qt.ItemIsEditable)
        self.assertTrue(flags & QtCore.Qt.ItemIsSelectable)
        self.assertTrue(flags & QtCore.Qt.ItemIsEnabled)

    def testClose(self):
        ''' Assure that clicking on Close triggers right behaviour'''
        self.widget.show()

        # Set up the spy
        spy_close = QtSignalSpy(self.widget, self.widget.close_signal)
        # Click on the "Close" button
        QtTest.QTest.mouseClick(self.widget.buttonBox.button(QtGui.QDialogButtonBox.Close), QtCore.Qt.LeftButton)
        # Check the signal
        self.assertEqual(spy_close.count(), 1)
        # Assure the window got closed
        self.assertFalse(self.widget.isVisible())

    def testOnHelp(self):
        ''' Assure clicking on help returns QtWeb view on requested page'''
        self.widget.show()

        #Mock the QWebView method
        QtWebKit.QWebView.show = MagicMock()
        QtWebKit.QWebView.load = MagicMock()

        # Invoke the action
        self.widget.onHelp()

        # Check if show() got called
        self.assertTrue(QtWebKit.QWebView.show.called)

        # Assure the filename is correct
        self.assertIn("graph_help.html", QtWebKit.QWebView.load.call_args[0][0].toString())
        
    def testSetModel(self):
        ''' Test if resetting the model works'''
        
        item1 = QtGui.QStandardItem("s1")
        item2 = QtGui.QStandardItem("5.0")
        new_model = QtGui.QStandardItemModel()
        new_model.appendRow([item1, item2])
        item1 = QtGui.QStandardItem("s2")
        item2 = QtGui.QStandardItem("20.0")
        new_model.appendRow([item1, item2])
        # Force the new model onto the widget
        self.widget.setModel(model=new_model)

        # Test if the widget got it
        self.assertEqual(self.widget.model.columnCount(), 2)
        self.assertEqual(self.widget.model.rowCount(), 2)
        self.assertEqual(self.widget.model.item(0,0).text(), 's1')
        self.assertEqual(self.widget.model.item(1,0).text(), 's2')


        
if __name__ == "__main__":
    unittest.main()
