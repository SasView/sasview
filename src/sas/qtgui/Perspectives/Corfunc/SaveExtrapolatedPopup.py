from collections.abc import Callable
from pathlib import Path

import numpy as np
from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox

from .UI.SaveExtrapolated import Ui_SaveExtrapolatedPanel


class UserInputInvalid(Exception):
    def __init__(self, message, *args):
        super().__init__(message, *args)
        self.message = message


class SaveExtrapolatedPopup(QDialog, Ui_SaveExtrapolatedPanel):
    """ Dialogue window for saving extrapolated data"""

    #trigger = QtCore.Signal(tuple)

    # pylint: disable=unused-argument
    def __init__(
            self,
            input_qs: np.ndarray,
            interpolation_function: Callable[[np.ndarray], np.ndarray],
            background: float | None = None,
            parent=None):
        super().__init__()

        self.parent = parent

        self.input_qs = input_qs
        self.interpolation_function = interpolation_function
        self.background = background

        self.setupUi(self)

        self.setWindowTitle("Save extrapolated data")

        self.cmdOK.clicked.connect(self.on_ok)
        self.cmdCancel.clicked.connect(self.on_cancel)

        # Default values from input qs
        self.spnLow.setValue(input_qs[0])
        self.spnHigh.setValue(input_qs[-1])
        self.spnDelta.setValue(np.mean(input_qs[1:] - input_qs[:-1]))


    def on_ok(self):
        """ OK button pressed"""
        try:
            self._input_validation()

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
            None,
            "Save As (base name; writes _uncorrected and _corrected)",
            "",
            "Comma separated values (*.csv)",
            "")[0]

        if not filename:
            return

        selected_path = Path(filename)
        base_path = selected_path.with_suffix("")
        uncorrected_path = base_path.parent / f"{base_path.name}_uncorrected.csv"
        corrected_path = base_path.parent / f"{base_path.name}_corrected.csv"

        background = 0.0 if self.background is None else self.background
        background_subtracted_intensity = intensity - background

        with open(uncorrected_path, "w") as uncorrected_file:
            uncorrected_file.write("Q, I(q)\n")
            for q_value, i_value in zip(q, intensity):
                uncorrected_file.write("%.6g, %.6g\n" % (q_value, i_value))

        with open(corrected_path, "w") as corrected_file:
            corrected_file.write("Q, I(q)-Background\n")
            for q_value, i_subtracted in zip(q, background_subtracted_intensity):
                corrected_file.write("%.6g, %.6g\n" % (q_value, i_subtracted))

