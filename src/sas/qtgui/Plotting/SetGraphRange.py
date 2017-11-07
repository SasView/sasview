"""
Allows users to change the range of the current graph
"""
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

import sas.qtgui.Utilities.GuiUtils as GuiUtils

# Local UI
from sas.qtgui.UI import main_resources_rc
from sas.qtgui.Plotting.UI.SetGraphRangeUI import Ui_setGraphRangeUI

class SetGraphRange(QtWidgets.QDialog, Ui_setGraphRangeUI):
    def __init__(self, parent=None, x_range=(0.0, 0.0), y_range=(0.0, 0.0)):
        super(SetGraphRange, self).__init__()

        self.setupUi(self)
        assert(isinstance(x_range, tuple))
        assert(isinstance(y_range, tuple))

        self.txtXmin.setValidator(GuiUtils.DoubleValidator())
        self.txtXmax.setValidator(GuiUtils.DoubleValidator())
        self.txtYmin.setValidator(GuiUtils.DoubleValidator())
        self.txtYmax.setValidator(GuiUtils.DoubleValidator())

        self.txtXmin.setText(str(x_range[0]))
        self.txtXmax.setText(str(x_range[1]))
        self.txtYmin.setText(str(y_range[0]))
        self.txtYmax.setText(str(y_range[1]))

    def xrange(self):
        """
        Return a tuple with line edit content of (xmin, xmax)
        """
        return (float(self.txtXmin.text()),
                float(self.txtXmax.text()))

    def yrange(self):
        """
        Return a tuple with line edit content of (ymin, ymax)
        """
        return (float(self.txtYmin.text()),
                float(self.txtYmax.text()))
