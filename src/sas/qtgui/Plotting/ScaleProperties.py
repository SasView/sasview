from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

import sas.sasview
from sas.qtgui.UI import main_resources_rc

from sas.qtgui.UI import main_resources_rc
from sas.qtgui.Plotting.UI.ScalePropertiesUI import Ui_scalePropertiesUI

x_values = ["x", "x^(2)", "x^(4)", "ln(x)", "log10(x)", "log10(x^(4))"]
y_values = ["y", "1/y", "ln(y)", "y^(2)", "y*x^(2)", "y*x^(4)", "1/sqrt(y)",
            "log10(y)", "ln(y*x)", "ln(y*x^(2))", "ln(y*x^(4))", "log10(y*x^(4))"]
view_values = ["--", "Linear y vs x", "Guinier lny vs x^(2)",
            "XS Guinier ln(y*x) vs x^(2)", "Porod y*x^(4) vs x^(4)", "Kratky y*x^(2) vs x"]
view_to_xy = {
    view_values[0]: [None, None], # custom
    view_values[1]: [0, 0], # linear
    view_values[2]: [1, 2], # Guinier
    view_values[3]: [1, 8], # XS Guinier
    view_values[4]: [2, 5], # Porod
    view_values[5]: [0, 4], # Kratky
}
class ScaleProperties(QtWidgets.QDialog, Ui_scalePropertiesUI):
    def __init__(self, parent=None, init_scale_x='x', init_scale_y='y'):
        super(ScaleProperties, self).__init__(parent)
        self.setupUi(self)

        # Set up comboboxes
        self.cbX.addItems(x_values)
        self.cbY.addItems(y_values)
        self.cbView.addItems(view_values)
        # Resize the dialog only AFTER the boxes are populated
        self.setFixedSize(self.minimumSizeHint())

        # Set up the initial values for x and y.
        # This avoids keeping a QModel instance here.
        if init_scale_x in x_values and init_scale_y in y_values:
            self.cbX.setCurrentIndex(x_values.index(init_scale_x))
            self.cbY.setCurrentIndex(y_values.index(init_scale_y))

        # Connect combobox index change to a custom method
        self.cbView.currentIndexChanged.connect(self.viewIndexChanged)
        self.cbX.currentIndexChanged.connect(self.xyIndexChanged)
        self.cbY.currentIndexChanged.connect(self.xyIndexChanged)

    def getValues(self):
        """
        Return current values from comboboxes
        """
        return str(self.cbX.currentText()), str(self.cbY.currentText())

    def viewIndexChanged(self, index):
        """
        Update X and Y labels based on the "View" index
        """
        if index > 0:
            # Disable signals so xyIndexChanged() doesn't get called
            self.cbX.blockSignals(True)
            self.cbY.blockSignals(True)

            # Update the sub-controls
            self.cbX.setCurrentIndex(view_to_xy[view_values[index]][0])
            self.cbY.setCurrentIndex(view_to_xy[view_values[index]][1])
            # Re-enable the signals

            self.cbX.blockSignals(False)
            self.cbY.blockSignals(False)

    def xyIndexChanged(self, index):
        """
        Update View label based on the "X" and "Y" index
        """
        self.cbView.setCurrentIndex(0)
