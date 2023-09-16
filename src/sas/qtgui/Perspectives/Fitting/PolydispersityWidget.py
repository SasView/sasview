"""
Widget/logic for polydispersity.
"""
import numpy as np
from PySide6 import QtCore
from PySide6 import QtGui
from PySide6 import QtWidgets

from sas.qtgui.Perspectives.Fitting.ViewDelegate import PolyViewDelegate
from sas.qtgui.Perspectives.Fitting import FittingUtilities
# Local UI
from sas.qtgui.Perspectives.Fitting.UI.PolydispersityWidget import Ui_PolydispersityWidgetUI


class PolydispersityWidget(QtWidgets.QWidget, Ui_PolydispersityWidgetUI):
    smearingChangedSignal = QtCore.Signal()
    def __init__(self, parent=None):
        super(PolydispersityWidget, self).__init__()

        self.setupUi(self)
        self.lstPoly.isEnabled = True
        self.poly_model = FittingUtilities.ToolTippedItemModel()
        self.is2D = False
        FittingUtilities.setTableProperties(self.lstPoly)
        self.lstPoly.setItemDelegate(PolyViewDelegate(self))
        self.lstPoly.installEventFilter(self)

        # self.lstPoly.itemDelegate().combo_updated.connect(self.onPolyComboIndexChange)
        # self.lstPoly.itemDelegate().filename_updated.connect(self.onPolyFilenameChange)

        self.lstPoly.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        # self.lstPoly.customContextMenuRequested.connect(self.showModelContextMenu)
        self.lstPoly.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)

    def polyModel(self):
        """
        Return the polydispersity model
        """
        return self.poly_model

    # def setModel(self, model):
    #     """
    #     Set the polydispersity model
    #     """
    #     self.poly_model = model
    #     self.lstPoly.setModel(self.poly_model)
    #     self.lstPoly.setItemDelegate(PolyViewDelegate(self))
    #     self.lstPoly.installEventFilter(self)


    def setPolyModel(self, model_parameters=None):
        """
        Set polydispersity values
        """
        if model_parameters is None:
            return
        self.poly_model.clear()

        parameters = model_parameters.form_volume_parameters
        if self.is2D:
            parameters += model_parameters.orientation_parameters

        [self.setPolyModelParameters(i, param) for i, param in \
            enumerate(parameters) if param.polydisperse]

        FittingUtilities.addPolyHeadersToModel(self.poly_model)
