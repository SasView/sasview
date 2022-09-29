import unittest
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt

from sas.qtgui.Perspectives.Invariant.InvariantDetails import DetailsDialog
from sas.qtgui.Perspectives.Invariant.InvariantUtils import WIDGETS

from sas.qtgui.Utilities.GuiUtils import *

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)

BG_COLOR_ERR = 'background-color: rgb(244, 170, 164);'


class InvariantDetailsTest(unittest.TestCase):
    """Test the Invariant Perspective Window"""
    def setUp(self):
        """Create the Invariant Details window"""

        self.widget = DetailsDialog(None)
        self.widget._model = QtGui.QStandardItemModel()
        self.widget._model.setItem(WIDGETS.W_INVARIANT, QtGui.QStandardItem(str(10.)))
        self.widget._model.setItem(WIDGETS.W_INVARIANT_ERR, QtGui.QStandardItem(str(0.1)))
        self.widget._model.setItem(WIDGETS.W_ENABLE_LOWQ, QtGui.QStandardItem('true'))
        self.widget._model.setItem(WIDGETS.D_LOW_QSTAR, QtGui.QStandardItem(str(9.)))
        self.widget._model.setItem(WIDGETS.D_LOW_QSTAR_ERR, QtGui.QStandardItem(str(0.03)))
        self.widget._model.setItem(WIDGETS.D_DATA_QSTAR, QtGui.QStandardItem(str(10.)))
        self.widget._model.setItem(WIDGETS.D_DATA_QSTAR_ERR, QtGui.QStandardItem(str(0.1)))
        self.widget._model.setItem(WIDGETS.D_HIGH_QSTAR, QtGui.QStandardItem(str(1.)))
        self.widget._model.setItem(WIDGETS.D_HIGH_QSTAR_ERR, QtGui.QStandardItem(str(0.01)))

        # High-Q
        self.widget._model.setItem(WIDGETS.W_ENABLE_HIGHQ, QtGui.QStandardItem('false'))

    def tearDown(self):
        """Destroy the Invariant Details window """
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        """Test the GUI in its default state"""

        self.widget.qstar_total = None
        self.widget.qhigh = None
        self.widget.qlow = None

        self.widget.progress_low_qstar = 0.0
        self.widget.progress_high_qstar = 0.0
        self.widget.progress_qstar = 100.0

        self.widget.warning_msg = "No Details on calculations available...\n"

        assert isinstance(self.widget, QtWidgets.QDialog)

        assert self.widget.progressBarLowQ.minimum() == 0
        assert self.widget.progressBarLowQ.maximum() == 100
        assert self.widget.progressBarData.minimum() == 0
        assert self.widget.progressBarData.maximum() == 100
        assert self.widget.progressBarHighQ.minimum() == 0
        assert self.widget.progressBarHighQ.maximum() == 100


        # Tooltips
        assert self.widget.txtQData.toolTip() == "Invariant in the data set's Q range."
        assert self.widget.txtQDataErr.toolTip() == "Uncertainty on the invariant from data's range."
        assert self.widget.txtQLowQ.toolTip() == "Extrapolated invariant from low-Q range."
        assert self.widget.txtQLowQErr.toolTip() == "Uncertainty on the invariant from low-Q range."
        assert self.widget.txtQHighQ.toolTip() == "Extrapolated invariant from high-Q range."
        assert self.widget.txtQHighQErr.toolTip() == "Uncertainty on the invariant from high-Q range."

    def testOnOK(self):
        """ Test closing dialog"""
        okButton = self.widget.cmdOK
        QTest.mouseClick(okButton, Qt.LeftButton)

    def testShowDialog(self):
        """ """
        self.widget.showDialog()
        # Low Q true
        assert self.widget.qlow == 9.0
        assert self.widget.txtQLowQ.text() == '9.0'
        assert self.widget.progress_low_qstar == 90.0
        assert self.widget.qstar_total == 10.0
        assert self.widget.txtQData.text() == '10.0'
        assert self.widget.txtQDataErr.text() == '0.1'

        # High Q false
        assert self.widget.txtQHighQ.text() == ''
        assert self.widget.txtQHighQErr.text() == ''
        assert self.widget.progress_high_qstar == 0.0

        # Progressbars
        assert self.widget.progressBarLowQ.value() == self.widget.progress_low_qstar
        assert self.widget.progressBarLowQ.value() == self.widget.progress_low_qstar
        assert self.widget.progressBarHighQ.value() == self.widget.progress_high_qstar

    def testCheckValues(self):
        """ """
        self.widget.qstart_total = None
        assert self.widget.checkValues() == "Invariant not calculated.\n"

        self.widget.qstar_total = 0
        return_string = self.widget.checkValues()
        assert "Invariant is zero." in return_string
        assert "The calculations are likely to be unreliable!" in return_string

        self.widget.qstar_total = 10
        assert "No Warnings to report" in self.widget.checkValues()

        self.widget.progress_qstar = 0
        self.widget.progress_low_qstar = 10
        return_string = self.widget.checkValues()
        assert 'Extrapolated contribution at Low Q is higher than 5% of the invariant.' in return_string
        assert 'The sum of all extrapolated contributions is higher than 5% of the invariant.' in return_string

        self.widget.progress_low_qstar = -1
        assert self.widget.checkValues() == "Extrapolated contribution at Low Q < 0.\n"


if __name__ == "__main__":
    unittest.main()
