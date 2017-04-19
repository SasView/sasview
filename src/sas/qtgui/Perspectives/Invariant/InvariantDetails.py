import sys
import os
from PyQt4 import QtCore
from PyQt4 import QtGui

# local
from UI.InvariantDetailsUI import Ui_Dialog
from InvariantUtils import WIDGETS

class DetailsDialog(QtGui.QDialog, Ui_Dialog):
    """
    """
    def __init__(self, parent):
        super(DetailsDialog, self).__init__(parent)

        self.setupUi(self)

        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(100)

        self.progressBar_2.setMinimum(0)
        self.progressBar_2.setMaximum(100)

        self.progressBar_3.setMinimum(0)
        self.progressBar_3.setMaximum(100)

    def setModel(self, model):
        """
        """
        self._model = model

    def showDialog(self):
        """
        """
        # Pull out data from the model
        qstar_total = float(self._model.item(WIDGETS.W_INVARIANT).text())
        self.lineEdit_3.setText(str(qstar_total))
        self.lineEdit_4.setText(self._model.item(WIDGETS.W_INVARIANT_ERR).text())

        progress_low_qstar = 0.0
        progress_high_qstar = 0.0
        progress_qstar = 100.0

        if self._model.item(WIDGETS.W_ENABLE_LOWQ).text() == "true":
            qlow = float(self._model.item(WIDGETS.D_LOW_QSTAR).text())
            self.lineEdit.setText(str(qlow))
            self.lineEdit_2.setText(self._model.item(WIDGETS.D_LOW_QSTAR_ERR).text())
            progress_low_qstar = (qlow/qstar_total)*100.0

        if self._model.item(WIDGETS.W_ENABLE_HIGHQ).text() == "true":
            qhigh = float(self._model.item(WIDGETS.D_LOW_QSTAR).text())
            self.lineEdit.setText(str(qhigh))
            self.lineEdit_2.setText(self._model.item(WIDGETS.D_HIGH_QSTAR_ERR).text())
            progress_high_qstar = (qhigh/qstar_total)*100.0


        progress_qstar -= progress_low_qstar + progress_high_qstar

        self.progressBar.setValue(progress_low_qstar)
        self.progressBar_2.setValue(progress_qstar)           
        self.progressBar_3.setValue(progress_high_qstar)           

        self.show()
