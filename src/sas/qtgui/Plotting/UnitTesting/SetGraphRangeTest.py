
import pytest
from PySide6 import QtGui, QtWidgets

# Local
from sas.qtgui.Plotting.SetGraphRange import SetGraphRange


class SetGraphRangeTest:
    '''Test the SetGraphRange'''

    @pytest.fixture(autouse=True)
    def widget(self, qapp):
        '''Create/Destroy the SetGraphRange'''
        w = SetGraphRange(None)
        yield w
        w.close()

    def testDefaults(self, widget):
        '''Test the GUI in its default state'''
        assert isinstance(widget, QtWidgets.QDialog)
        assert widget.windowTitle() == "Set Graph Range"
        assert isinstance(widget.txtXmin, QtWidgets.QLineEdit)
        assert isinstance(widget.txtXmin.validator(), QtGui.QDoubleValidator)

    def testGoodRanges(self, widget):
        '''Test the X range values set by caller'''
        assert widget.xrange() == (0.0, 0.0)
        assert widget.yrange() == (0.0, 0.0)

        new_widget = SetGraphRange(None, ("1.0", 2.0), (8.0, "-2"))
        assert new_widget.xrange() == (1.0, 2.0)
        assert new_widget.yrange() == (8.0, -2.0)


    def testBadRanges(self, widget):
        '''Test the incorrect X range values set by caller'''
        with pytest.raises(ValueError):
            new_widget = SetGraphRange(None, ("1.0", "aa"), (None, "@"))
            assert new_widget.xrange() == (1.0, 0.0)
            assert new_widget.yrange() == (0.0, 0.0)

        with pytest.raises(AssertionError):
            new_widget = SetGraphRange(None, "I'm a tuple", None)
            assert new_widget.xrange() == (1.0, 0.0)
            assert new_widget.yrange() == (0.0, 0.0)
