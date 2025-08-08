import pytest
from pyside6 import QtGui, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from sas.qtgui.Perspectives.Invariant.InvariantDetails import DetailsDialog
from sas.qtgui.Perspectives.Invariant.InvariantUtils import WIDGETS

BG_COLOR_ERR = 'background-color: rgb(244, 170, 164);'


class InvariantDetailsTest:
    """Test the Invariant Perspective Window"""

    @pytest.fixture(autouse=True)
    def widget(self, qapp):
        '''Create/Destroy the Invariant Details window'''

        w = DetailsDialog(None)
        w._model = QtGui.QStandardItemModel()
        w._model.setItem(WIDGETS.W_INVARIANT, QtGui.QStandardItem(str(10.)))
        w._model.setItem(WIDGETS.W_INVARIANT_ERR, QtGui.QStandardItem(str(0.1)))
        w._model.setItem(WIDGETS.W_ENABLE_LOWQ, QtGui.QStandardItem('true'))
        w._model.setItem(WIDGETS.D_LOW_QSTAR, QtGui.QStandardItem(str(9.)))
        w._model.setItem(WIDGETS.D_LOW_QSTAR_ERR, QtGui.QStandardItem(str(0.03)))
        w._model.setItem(WIDGETS.D_DATA_QSTAR, QtGui.QStandardItem(str(10.)))
        w._model.setItem(WIDGETS.D_DATA_QSTAR_ERR, QtGui.QStandardItem(str(0.1)))
        w._model.setItem(WIDGETS.D_HIGH_QSTAR, QtGui.QStandardItem(str(1.)))
        w._model.setItem(WIDGETS.D_HIGH_QSTAR_ERR, QtGui.QStandardItem(str(0.01)))

        # High-Q
        w._model.setItem(WIDGETS.W_ENABLE_HIGHQ, QtGui.QStandardItem('false'))

        yield w

        """Destroy the Invariant Details window """
        w.close()

    def testDefaults(self, widget):
        """Test the GUI in its default state"""

        widget.qstar_total = None
        widget.qhigh = None
        widget.qlow = None

        widget.progress_low_qstar = 0.0
        widget.progress_high_qstar = 0.0
        widget.progress_qstar = 100.0

        widget.warning_msg = "No Details on calculations available...\n"

        assert isinstance(widget, QtWidgets.QDialog)

        assert widget.progressBarLowQ.minimum() == 0
        assert widget.progressBarLowQ.maximum() == 100
        assert widget.progressBarData.minimum() == 0
        assert widget.progressBarData.maximum() == 100
        assert widget.progressBarHighQ.minimum() == 0
        assert widget.progressBarHighQ.maximum() == 100


        # Tooltips
        assert widget.txtQData.toolTip() == "Invariant in the data set's Q range."
        assert widget.txtQDataErr.toolTip() == "Uncertainty on the invariant from data's range."
        assert widget.txtQLowQ.toolTip() == "Extrapolated invariant from low-Q range."
        assert widget.txtQLowQErr.toolTip() == "Uncertainty on the invariant from low-Q range."
        assert widget.txtQHighQ.toolTip() == "Extrapolated invariant from high-Q range."
        assert widget.txtQHighQErr.toolTip() == "Uncertainty on the invariant from high-Q range."

    def testOnOK(self, widget):
        """ Test closing dialog"""
        okButton = widget.cmdOK
        QTest.mouseClick(okButton, Qt.LeftButton)

    def testShowDialog(self, widget):
        """ """
        widget.showDialog()
        # Low Q true
        assert widget.qlow == 9.0
        assert widget.txtQLowQ.text() == '9.0'
        assert widget.progress_low_qstar == 90.0
        assert widget.qstar_total == 10.0
        assert widget.txtQData.text() == '10.0'
        assert widget.txtQDataErr.text() == '0.1'

        # High Q false
        assert widget.txtQHighQ.text() == ''
        assert widget.txtQHighQErr.text() == ''
        assert widget.progress_high_qstar == 0.0

        # Progressbars
        assert widget.progressBarLowQ.value() == widget.progress_low_qstar
        assert widget.progressBarLowQ.value() == widget.progress_low_qstar
        assert widget.progressBarHighQ.value() == widget.progress_high_qstar

    def testCheckValues(self, widget):
        """ """
        widget.qstart_total = None
        assert widget.checkValues() == "Invariant not calculated.\n"

        widget.qstar_total = 0
        return_string = widget.checkValues()
        assert "Invariant is zero." in return_string
        assert "The calculations are likely to be unreliable!" in return_string

        widget.qstar_total = 10
        assert "No Warnings to report" in widget.checkValues()

        widget.progress_qstar = 0
        widget.progress_low_qstar = 10
        return_string = widget.checkValues()
        assert 'Extrapolated contribution at Low Q is higher than 5% of the invariant.' in return_string
        assert 'The sum of all extrapolated contributions is higher than 5% of the invariant.' in return_string

        widget.progress_low_qstar = -1
        assert widget.checkValues() == "Extrapolated contribution at Low Q < 0.\n"
