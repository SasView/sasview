import sys
import unittest

from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
from PyQt5 import QtCore

# set up import paths
import path_prepare

from sas.qtgui.MainWindow.DroppableDataLoadWidget import DroppableDataLoadWidget
from sas.qtgui.Utilities.GuiUtils import *
from sas.qtgui.UnitTesting.TestUtils import QtSignalSpy

if not QApplication.instance():
    app = QApplication(sys.argv)

class DroppableDataLoadWidgetTest(unittest.TestCase):
    '''Test the DroppableDataLoadWidget GUI'''
    def setUp(self):
        '''Create the GUI'''
        class dummy_manager(object):
            def communicator(self):
                return Communicate()
            def perspective(self):
                return MyPerspective()

        self.form = DroppableDataLoadWidget(None, guimanager=dummy_manager())

        # create dummy mime object
        self.mime_data = QtCore.QMimeData()
        self.testfile = 'testfile.txt'
        self.mime_data.setUrls([QtCore.QUrl(self.testfile)])

    def testDragIsOK(self):
        """
        Test the item being dragged over the load widget
        """
        good_drag_event = QtGui.QDragMoveEvent(QtCore.QPoint(0,0),
                                               QtCore.Qt.CopyAction,
                                               self.mime_data,
                                               QtCore.Qt.LeftButton,
                                               QtCore.Qt.NoModifier)
        mime_data = QtCore.QMimeData()
        bad_drag_event = QtGui.QDragMoveEvent(QtCore.QPoint(0,0),
                                               QtCore.Qt.CopyAction,
                                               mime_data,
                                               QtCore.Qt.LeftButton,
                                               QtCore.Qt.NoModifier)

        # Call the drag handler with good event
        self.assertTrue(self.form.dragIsOK(good_drag_event))

        # Call the drag handler with bad event
        self.assertFalse(self.form.dragIsOK(bad_drag_event))

    def testDropEvent(self):
        """
        Test what happens if an object is dropped onto the load widget
        """
        spy_file_read = QtSignalSpy(self.form, self.form.communicator.fileReadSignal)

        drop_event = QtGui.QDropEvent(QtCore.QPoint(0,0),
                                    QtCore.Qt.CopyAction,
                                    self.mime_data,
                                    QtCore.Qt.LeftButton,
                                    QtCore.Qt.NoModifier)

        self.form.dropEvent(drop_event)
        QApplication.processEvents()
        self.assertEqual(spy_file_read.count(), 1)
        self.assertIn(self.testfile, str(spy_file_read.signal(index=0)))


if __name__ == "__main__":
    unittest.main()
