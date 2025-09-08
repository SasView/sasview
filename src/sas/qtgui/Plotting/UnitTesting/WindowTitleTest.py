
import pytest
from PySide6 import QtWidgets

# Local
from sas.qtgui.Plotting.WindowTitle import WindowTitle


class WindowTitleTest:
    '''Test the WindowTitle'''

    @pytest.fixture(autouse=True)
    def widget(self, qapp):
        '''Create/Destroy the WindowTitle'''
        w = WindowTitle(None, new_title="some title")

        yield w

        w.close()

    def testDefaults(self, widget):
        '''Test the GUI in its default state'''
        widget.show()
        assert isinstance(widget, QtWidgets.QDialog)
        assert widget.windowTitle() == "Modify Window Title"

    def testTitle(self, widget):
        '''Modify the title'''
        widget.show()
        QtWidgets.qApp.processEvents()
        # make sure we have the pre-set title
        assert widget.txtTitle.text() == "some title"
        # Clear the control and set it to something else
        widget.txtTitle.clear()
        widget.txtTitle.setText("5 elephants")
        QtWidgets.qApp.processEvents()
        # Retrieve value
        new_title = widget.title()
        # Check
        assert new_title == "5 elephants"
