import pytest
from PySide6 import QtGui, QtWidgets

# Local
from sas.qtgui.Plotting.BoxSum import BoxSum


class BoxSumTest:
    '''Test the BoxSum'''

    @pytest.fixture(autouse=True)
    def widget(self, qapp):
        '''Create/Destroy the BoxSum'''
        # example model
        model = QtGui.QStandardItemModel()
        parameters = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]
        for index, parameter in enumerate(parameters):
            model.setData(model.index(0, index),parameter)
        w = BoxSum(None, model=model)

        yield w

        '''Destroy the GUI'''
        w.close()

    def testDefaults(self, widget):
        '''Test the GUI in its default state'''
        assert isinstance(widget.mapper.mappedWidgetAt(0), QtWidgets.QLineEdit)
        assert isinstance(widget.mapper.mappedWidgetAt(1), QtWidgets.QLineEdit)
        assert isinstance(widget.mapper.mappedWidgetAt(2), QtWidgets.QLineEdit)
        assert isinstance(widget.mapper.mappedWidgetAt(3), QtWidgets.QLineEdit)
        assert isinstance(widget.mapper.mappedWidgetAt(4), QtWidgets.QLabel)
        assert isinstance(widget.mapper.mappedWidgetAt(5), QtWidgets.QLabel)
        assert isinstance(widget.mapper.mappedWidgetAt(6), QtWidgets.QLabel)
        assert isinstance(widget.mapper.mappedWidgetAt(7), QtWidgets.QLabel)
        assert isinstance(widget.mapper.mappedWidgetAt(8), QtWidgets.QLabel)
