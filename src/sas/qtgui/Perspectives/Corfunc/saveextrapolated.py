import numpy as np

from PyQt5 import QtCore
from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox


from .UI.SaveExtrapolated import Ui_SaveExtrapolatedPanel

from typing import Callable


class UserInputInvalid(Exception):
    def __init__(self, message, *args):
        super().__init__(message, *args)
        self.message = message


class SaveExtrapolatedPopup(QDialog, Ui_SaveExtrapolatedPanel):
    """ Dialogue window for saving extrapolated data"""

    #trigger = QtCore.pyqtSignal(tuple)

    # pylint: disable=unused-argument
    def __init__(self, input_qs: np.ndarray, interpolation_function: Callable[[np.ndarray], np.ndarray], parent=None):
        super().__init__()

        self.parent = parent

        self.input_qs = input_qs
        self.interpolation_function = interpolation_function

        self.setupUi(self)

        self.setWindowTitle("Save extrapolated data")

        self.originalQ.clicked.connect(self.on_select_original_q)
        self.resampleQ.clicked.connect(self.on_select_resample_q)

        self.cmdOK.clicked.connect(self.on_ok)
        self.cmdCancel.clicked.connect(self.on_cancel)

        # Default values from input qs
        self.spnLow.setValue(input_qs[0])
        self.spnHigh.setValue(input_qs[-1])
        self.spnDelta.setValue(np.mean(input_qs[1:] - input_qs[:-1]))

        self.enable_disable_resample_group(False)


    def enable_disable_resample_group(self, enabled: bool):
        """ Set enabled state for all the resampling input fields"""

        # Probably a cleaner way of doing this?
        for component in [
            self.lblLow, self.lblHigh, self.lblDelta,
            self.spnLow, self.spnHigh, self.spnDelta,
            self.units1, self.units2, self.units3]:

            component.setEnabled(enabled)

    def on_select_original_q(self):
        """ Callback for selecting original q sampling"""
        self.enable_disable_resample_group(False)

    def on_select_resample_q(self):
        """ Callback for selecting resampled q"""
        self.enable_disable_resample_group(True)

    def on_ok(self):
        """ OK button pressed"""
        try:
            self._input_validation()

            if self.originalQ.isChecked():
                q = self.input_qs

            else:
                q = np.arange(
                    self.spnLow.value(),
                    self.spnHigh.value(),
                    self.spnDelta.value())

            intensity = self.interpolation_function(q)

            self._do_save(q, intensity)

            self.close()

        except UserInputInvalid as e:
            self._notify_user_error(e.message)

    def on_cancel(self):
        """ Cancel button pressed"""
        self.close()

    def _input_validation(self):
        """ Check input is valid, notify user if not"""

        # If not resampling, other parameters don't matter
        if self.originalQ.isChecked():
            return

        # Range values
        if self.spnLow.value() >= self.spnHigh.value():
            raise UserInputInvalid("High Q value should be greater than low Q value.")

        if self.spnDelta.value() <= 0:
            raise UserInputInvalid("Delta Q (sampling interval) should be a positive number.")

        return

    def _notify_user_error(self, message: str):
        """ Message box for showing error """

        popup = QMessageBox()
        popup.setIcon(QMessageBox.Warning)
        popup.setText(message)
        popup.setWindowTitle("Invalid input")
        popup.exec_()


    def _do_save(self, q: np.ndarray, intensity: np.ndarray):
        """
        Save data to a file
        """
        filename = QFileDialog.getSaveFileName(
            caption="Save As",
            filter="Tab separated values (*.tsv)",
            parent=None)[0]

        if not filename:
            return

        if "." not in filename:
            filename += ".tsv"

        with open(filename, "w") as outfile:
            outfile.write("Q\tI(q)\n")
            for q_value, i_value in zip(q, intensity):
                outfile.write("%.6g\t%.6g\n"%(q_value, i_value))

