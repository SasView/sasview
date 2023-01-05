"""
Allows users to modify the box slicer parameters.
"""
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

import sas.sasview.Utilities.GuiUtils as GuiUtils

# Local UI
from sas.sasview.UI import main_resources_rc
from sas.sasview.Plotting.UI.BoxSumUI import Ui_BoxSumUI

class BoxSum(QtWidgets.QDialog, Ui_BoxSumUI):
    closeWidgetSignal = QtCore.pyqtSignal()
    def __init__(self, parent=None, model=None):
        super(BoxSum, self).__init__()

        self.setupUi(self)
        assert isinstance(model, QtGui.QStandardItemModel)

        self.txtBoxHeight.setValidator(GuiUtils.DoubleValidator())
        self.txtBoxWidth.setValidator(GuiUtils.DoubleValidator())
        self.txtCenterX.setValidator(GuiUtils.DoubleValidator())
        self.txtCenterY.setValidator(GuiUtils.DoubleValidator())

        self.model = model
        self.mapper = QtWidgets.QDataWidgetMapper()
        self.mapper.setModel(self.model)

        # Map model items onto widget controls
        self.mapper.addMapping(self.txtBoxHeight, 0)
        self.mapper.addMapping(self.txtBoxWidth, 1)
        self.mapper.addMapping(self.txtCenterX, 2)
        self.mapper.addMapping(self.txtCenterY, 3)
        self.mapper.addMapping(self.lblAvg, 4, b"text")
        self.mapper.addMapping(self.lblAvgErr, 5, b"text")
        self.mapper.addMapping(self.lblSum, 6, b"text")
        self.mapper.addMapping(self.lblSumErr, 7, b"text")
        self.mapper.addMapping(self.lblNumPoints, 8, b"text")

        # Populate the widgets with data from the first column
        self.mapper.toFirst()

        self.setFixedSize(self.minimumSizeHint())

        # Handle the Close button click
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Close).clicked.connect(lambda:self.closeWidgetSignal.emit())

