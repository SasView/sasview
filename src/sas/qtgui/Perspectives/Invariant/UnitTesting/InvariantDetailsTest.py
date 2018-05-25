import sys
import time
import numpy
import logging
import unittest
from PyQt5 import QtGui, QtWidgets
from PyQt5 import QtCore
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt
from unittest.mock import MagicMock
from unittest.mock import patch

from twisted.internet import threads

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

        # # High-Q
        self.widget._model.setItem(WIDGETS.W_ENABLE_HIGHQ,
                                   QtGui.QStandardItem('false'))
        # self._model.item(WIDGETS.D_HIGH_QSTAR)
        # self._model.item(WIDGETS.D_HIGH_QSTAR_ERR)

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

        self.assertIsInstance(self.widget, QtWidgets.QDialog)

        self.assertEqual(self.widget.progressBarLowQ.minimum(), 0)
        self.assertEqual(self.widget.progressBarLowQ.maximum(), 100)

        self.assertEqual(self.widget.progressBarData.minimum(), 0)
        self.assertEqual(self.widget.progressBarData.maximum(), 100)

        self.assertEqual(self.widget.progressBarHighQ.minimum(), 0)
        self.assertEqual(self.widget.progressBarHighQ.maximum(), 100)


        # Tooltips
        self.assertEqual(self.widget.txtQData.toolTip(), "Invariant in the data set's Q range.")

        self.assertEqual(self.widget.txtQDataErr.toolTip(), "Uncertainty on the invariant from data's range.")

        self.assertEqual(self.widget.txtQLowQ.toolTip(), "Extrapolated invariant from low-Q range.")

        self.assertEqual(self.widget.txtQLowQErr.toolTip(), "Uncertainty on the invariant from low-Q range.")

        self.assertEqual(self.widget.txtQHighQ.toolTip(), "Extrapolated invariant from high-Q range.")

        self.assertEqual(self.widget.txtQHighQErr.toolTip(), "Uncertainty on the invariant from high-Q range.")

    def testOnOK(self):
        """ Test closing dialog"""
        okButton = self.widget.cmdOK
        QTest.mouseClick(okButton, Qt.LeftButton)

    def testShowDialog(self):
        """ """
        self.widget.showDialog()
        # Low Q true
        self.assertEqual(self.widget.qlow , 9.0)

        self.assertEqual(self.widget.txtQLowQ.text(), '9.0')

        self.assertEqual(self.widget.progress_low_qstar, 90.0)

        self.assertEqual(self.widget.qstar_total, 10.0)

        self.assertEqual(self.widget.txtQData.text(), '10.0')

        self.assertEqual(self.widget.txtQDataErr.text(), '0.1')

        # High Q false
        self.assertEqual(self.widget.txtQHighQ.text(), '')
        self.assertEqual(self.widget.txtQHighQErr.text(), '')
        self.assertEqual(self.widget.progress_high_qstar, 0.0)  #  = 0
        self.widget.qhigh  # = 0

        # Progressbars
        self.assertEqual(self.widget.progressBarLowQ.value(), self.widget.progress_low_qstar)

        self.assertEqual(self.widget.progressBarLowQ.value(), self.widget.progress_low_qstar)

        self.assertEqual(self.widget.progressBarHighQ.value(), self.widget.progress_high_qstar)

    # TODO to complete
    def testCheckValues(self):
        """ """
        self.widget.qstart_total = None
        self.assertEqual(self.widget.checkValues(), "Invariant not calculated.\n")

        self.widget.qstar_total = 0
        self.assertEqual(self.widget.checkValues(), "Invariant is zero. \n " \
                          "The calculations are likely to be unreliable!\n")

        self.widget.qstar_total = 10
        self.widget.progress_qstar = 'error'
        self.assertIn("Error occurred when computing invariant from data.", self.widget.checkValues())

        self.widget.progress_qstar = 0

        self.widget.progress_low_qstar = 10
        self.assertEqual(self.widget.checkValues(),
                         'Extrapolated contribution at Low Q is higher than 5% of the invariant.\nThe sum of all extrapolated contributions is higher than 5% of the invariant.\n')

        self.widget.progress_low_qstar = -1
        self.assertEqual(self.widget.checkValues(), "Extrapolated contribution at Low Q < 0.\n")


if __name__ == "__main__":
    unittest.main()
