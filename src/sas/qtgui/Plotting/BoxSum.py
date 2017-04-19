"""
Allows users to modify the box slicer parameters.
"""
from PyQt4 import QtGui
from PyQt4 import QtCore

# Local UI
from sas.qtgui.UI import main_resources_rc
from sas.qtgui.Plotting.UI.BoxSumUI import Ui_BoxSumUI

class BoxSum(QtGui.QDialog, Ui_BoxSumUI):
    apply_signal = QtCore.pyqtSignal(tuple, str)
    def __init__(self, parent=None, model=None):
        super(BoxSum, self).__init__()

        self.setupUi(self)
        assert isinstance(model, QtGui.QStandardItemModel)

        self.txtBoxHeight.setValidator(QtGui.QDoubleValidator())
        self.txtBoxWidth.setValidator(QtGui.QDoubleValidator())
        self.txtCenterX.setValidator(QtGui.QDoubleValidator())
        self.txtCenterY.setValidator(QtGui.QDoubleValidator())

        self.model = model
        self.mapper = QtGui.QDataWidgetMapper()
        self.mapper.setModel(self.model)

        # Map model items onto widget controls
        self.mapper.addMapping(self.txtBoxHeight, 0)
        self.mapper.addMapping(self.txtBoxWidth, 1)
        self.mapper.addMapping(self.txtCenterX, 2)
        self.mapper.addMapping(self.txtCenterY, 3)
        self.mapper.addMapping(self.lblAvg, 4, "text")
        self.mapper.addMapping(self.lblAvgErr, 5, "text")
        self.mapper.addMapping(self.lblSum, 6, "text")
        self.mapper.addMapping(self.lblSumErr, 7, "text")
        self.mapper.addMapping(self.lblNumPoints, 8, "text")

        # Populate the widgets with data from the first column
        self.mapper.toFirst()

        self.setFixedSize(self.minimumSizeHint())

