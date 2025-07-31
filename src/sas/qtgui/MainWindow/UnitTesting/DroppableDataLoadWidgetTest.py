import pytest
from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import QApplication

from sas.qtgui.MainWindow.DroppableDataLoadWidget import DroppableDataLoadWidget
from sas.qtgui.MainWindow.UnitTesting.DataExplorerTest import MyPerspective
from sas.qtgui.UnitTesting.TestUtils import QtSignalSpy
from sas.qtgui.Utilities.GuiUtils import Communicate


class DroppableDataLoadWidgetTest:
    '''Test the DroppableDataLoadWidget GUI'''

    @pytest.fixture(autouse=True)
    def form(self, qapp):
        '''Create/Destroy the DroppableDataLoadWidget'''
        class dummy_manager:
            def communicator(self):
                return Communicate()
            def perspective(self):
                return MyPerspective()

        f = DroppableDataLoadWidget(None, guimanager=dummy_manager())

        # create dummy mime object
        self.mime_data = QtCore.QMimeData()
        self.testfile = 'testfile.txt'
        self.mime_data.setUrls([QtCore.QUrl(self.testfile)])

        yield f

    def testDragIsOK(self, form):
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
        assert form.dragIsOK(good_drag_event)

        # Call the drag handler with bad event
        assert not form.dragIsOK(bad_drag_event)

    def testDropEvent(self, form):
        """
        Test what happens if an object is dropped onto the load widget
        """
        spy_file_read = QtSignalSpy(form, form.communicator.fileReadSignal)

        drop_event = QtGui.QDropEvent(QtCore.QPoint(0,0),
                                    QtCore.Qt.CopyAction,
                                    self.mime_data,
                                    QtCore.Qt.LeftButton,
                                    QtCore.Qt.NoModifier)

        form.dropEvent(drop_event)
        QApplication.processEvents()
        assert spy_file_read.count() == 1
        #assert self.testfile in str(spy_file_read.signal(index=0))
