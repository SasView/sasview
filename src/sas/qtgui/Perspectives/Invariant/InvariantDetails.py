import sys
import os
from PyQt5 import QtCore
from PyQt5 import QtGui, QtWidgets

# local
from .UI.InvariantDetailsUI import Ui_Dialog
from .InvariantUtils import WIDGETS

# ERROR_COLOR = wx.Colour(255, 0, 0, 128)
# EXTRAPOLATION_COLOR = wx.Colour(169, 169, 168, 128)
# INVARIANT_COLOR = wx.Colour(67, 208, 128, 128)

class DetailsDialog(QtWidgets.QDialog, Ui_Dialog):
    """
    This class stores some values resulting from invariant calculations.
    Given the value of total invariant, this class can also
    determine the percentage of invariants resulting from extrapolation.
    """
    def __init__(self, parent):
        super(DetailsDialog, self).__init__(parent)

        self.setupUi(self)

        DEFAULT_STYLE = """
        QProgressBar{
            border: 2px solid grey;
            border-radius: 5px;
            text-align: center
        }

        QProgressBar::chunk {
            background-color: #b1daf9;
            width: 10px;
            margin: 1px;
        }
        """
        self.progressBarLowQ.setStyleSheet(DEFAULT_STYLE)
        self.progressBarData.setStyleSheet(DEFAULT_STYLE)
        self.progressBarHighQ.setStyleSheet(DEFAULT_STYLE)

        self.progressBarLowQ.setMinimum(0)
        self.progressBarLowQ.setMaximum(100)

        self.progressBarData.setMinimum(0)
        self.progressBarData.setMaximum(100)

        self.progressBarHighQ.setMinimum(0)
        self.progressBarHighQ.setMaximum(100)

        # Modify font in order to display Angstrom symbol correctly
        new_font = 'font-family: -apple-system, "Helvetica Neue", "Ubuntu";'
        self.lblQLowQUnits.setStyleSheet(new_font)
        self.lblQDataUnits.setStyleSheet(new_font)
        self.lblQHighQUnits.setStyleSheet(new_font)

        self.cmdOK.clicked.connect(self.accept)

        self.warning_msg = "No Details on calculations available...\n"

        # invariant total
        self.qstar_total = None
        self.qhigh = None
        self.qlow = None
        self._model = None

        self.progress_low_qstar = 0.0
        self.progress_high_qstar = 0.0
        self.progress_qstar = 100.0

    def setModel(self, model):
        """ """
        self._model = model

    def showDialog(self):
        """ Fill the dialog with values of calculated Q, progress bars"""
        # Pull out data from the model
        self.qstar_total = float(self._model.item(WIDGETS.W_INVARIANT).text())

        self.txtQData.setText(str(self.qstar_total))
        self.txtQDataErr.setText(self._model.item(WIDGETS.W_INVARIANT_ERR).text())

        # Reset progress counters
        self.progress_low_qstar = 0.0
        self.progress_high_qstar = 0.0
        self.progress_qstar = 100.0

        # Low-Q
        if self._model.item(WIDGETS.W_ENABLE_LOWQ).text() == "true":
            self.qlow = float(self._model.item(WIDGETS.D_LOW_QSTAR).text())

            self.txtQLowQ.setText(str(self.qlow))
            self.txtQLowQErr.setText(self._model.item(WIDGETS.D_LOW_QSTAR_ERR).text())
            try:
                self.progress_low_qstar = (self.qlow/self.qstar_total)*100.0
            except:
                self.progress_low_qstar = 'error'

        # High-Q
        if self._model.item(WIDGETS.W_ENABLE_HIGHQ).text() == "true":
            self.qhigh = float(self._model.item(WIDGETS.D_HIGH_QSTAR).text())

            self.txtQHighQ.setText(str(self.qhigh))
            self.txtQHighQErr.setText(self._model.item(WIDGETS.D_HIGH_QSTAR_ERR).text())
            try:
                self.progress_high_qstar = (self.qhigh/self.qstar_total)*100.0
            except:
                self.progress_high_qstar = 'error'

        try:
            self.progress_qstar -= self.progress_low_qstar + self.progress_high_qstar
        except:
            self.progress_qstar = 'error'

        # check values and display warning
        if self.checkValues():
            self.lblWarning.setText(self.checkValues())

        # update progress bars
        if self.progress_low_qstar == 'error':
            self.progressBarLowQ.setValue(0)
        else:
            self.progressBarLowQ.setValue(self.progress_low_qstar)

        if self.progress_high_qstar == 'error':
            self.progressBarHighQ.setValue(0)
        else:
            self.progressBarHighQ.setValue(self.progress_high_qstar)

        if self.progress_qstar == 'error':
            self.progressBarData.setValue(0)
        else:
            self.progressBarData.setValue(self.progress_qstar)

        self.show()

    def checkValues(self):
        """
        Create a warning message to be displayed in panel
        if problems with values
        """

        if self.qstar_total is None:
            warning_msg = "Invariant not calculated.\n"
            return warning_msg
        elif self.qstar_total == 0:
            warning_msg = "Invariant is zero. \n " \
                          "The calculations are likely to be unreliable!\n"
            return warning_msg

        msg = ''
        if self.progress_qstar == 'error':
            msg += 'Error occurred when computing invariant from data.\n '
        try:
            if float(self.progress_qstar) > 100:
                msg += "Invariant Q contribution is greater than 100% .\n"
        except ValueError:
            # Text message, skip msg update
            pass

        if self.progress_low_qstar == 'error':
            try:
                float(self.qlow)
            except:
                msg += "Error occurred when computing extrapolated invariant"
                msg += " at low-Q region.\n"

        elif self.progress_low_qstar is not None:
            if self.progress_low_qstar >= 5:
                msg += "Extrapolated contribution at Low Q is higher "
                msg += "than 5% of the invariant.\n"
            elif self.progress_low_qstar < 0:
                msg += "Extrapolated contribution at Low Q < 0.\n"
            elif self.progress_low_qstar > 100:
                msg += "Extrapolated contribution at Low Q is greater "
                msg += "than 100% .\n"

        # High-Q
        if self.progress_high_qstar == 'error':
            try:
                float(self.qhigh)
            except:
                msg += 'Error occurred when computing extrapolated'
                msg += ' invariant at high-Q region.\n'

        elif self.progress_high_qstar is not None:
            if self.progress_high_qstar >= 5:
                msg += "Extrapolated contribution at High Q is higher " \
                       "than 5% of the invariant.\n"
            elif self.progress_high_qstar < 0:

                msg += "Extrapolated contribution at High Q < 0.\n"
            elif self.progress_high_qstar > 100:

                msg += "Extrapolated contribution at High Q is greater " \
                       "than 100% .\n"

        if (self.progress_low_qstar not in [None, "error"]) and \
            (self.progress_high_qstar not in [None, "error"])\
            and self.progress_low_qstar + self.progress_high_qstar >= 5:

            msg += "The sum of all extrapolated contributions is higher " \
                   "than 5% of the invariant.\n"

        return msg
