
import pytest
from PySide6 import QtGui, QtWidgets

# Local
from sas.qtgui.Plotting.AddText import AddText


class AddTextTest:
    '''Test the AddText'''

    @pytest.fixture(autouse=True)
    def widget(self, qapp):
        '''Create/Destroy the AddText'''
        w = AddText(None)
        yield w
        w.close()

    def testDefaults(self, widget):
        '''Test the GUI in its default state'''
        assert isinstance(widget, QtWidgets.QDialog)
        assert isinstance(widget._font, QtGui.QFont)
        assert widget._color == "black"

    @pytest.mark.skip(reason="2022-09 already broken")
    def testOnFontChange(self, widget, mocker):
        '''Test the QFontDialog output'''
        font_1 = QtGui.QFont("Helvetica", 15)
        mocker.patch.object(QtWidgets.QFontDialog, 'getFont', return_value=(font_1, True))
        # Call the method
        widget.onFontChange(None)
        # Check that the text field got the new font info
        assert widget.textEdit.currentFont() == font_1

        # See that rejecting the dialog doesn't modify the font
        font_2 = QtGui.QFont("Arial", 9)
        mocker.patch.object(QtWidgets.QFontDialog, 'getFont', return_value=(font_2, False))
        # Call the method
        widget.onFontChange(None)
        # Check that the text field retained the previous font info
        assert widget.textEdit.currentFont() == font_1

    def testOnColorChange(self, widget, mocker):
        ''' Test the QColorDialog output'''
        new_color = QtGui.QColor("red")
        mocker.patch.object(QtWidgets.QColorDialog, 'getColor', return_value=new_color)
        # Call the method
        widget.onColorChange(None)
        # Check that the text field got the new color info for text
        assert widget.textEdit.palette().vertex_coloring(QtGui.QPalette.Text) == new_color
        # ... and the hex value of this color is correct
        assert widget.color() == "#ff0000"
