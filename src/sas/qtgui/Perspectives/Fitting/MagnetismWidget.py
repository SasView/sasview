"""
Widget/logic for magnetism.
"""
import logging
from importlib import resources

from PySide6 import QtCore, QtGui, QtWidgets

from sas.qtgui.Perspectives.Fitting import FittingUtilities

# Local UI
from sas.qtgui.Perspectives.Fitting.UI.MagnetismWidget import Ui_MagnetismWidgetUI
from sas.qtgui.Perspectives.Fitting.ViewDelegate import MagnetismViewDelegate

logger = logging.getLogger(__name__)


class MagnetismWidget(QtWidgets.QWidget, Ui_MagnetismWidgetUI):
    updateDataSignal = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super(MagnetismWidget, self).__init__()

        self.setupUi(self)
        self.lstMagnetic.isEnabled = True
        self._magnet_model = None   # the page's ParameterItemModel of the magnetism table
        self._fitting_widget = parent
        FittingUtilities.setTableProperties(self.lstMagnetic)
        self.lstMagnetic.setItemDelegate(MagnetismViewDelegate(self))
        self.lstMagnetic.installEventFilter(self)

        self.lstMagnetic.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.lstMagnetic.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)
        self.cmdMagneticDisplay.clicked.connect(self.onDisplayMagneticAngles)

        # Magnetic angles explained in one picture
        self.magneticAnglesWidget = QtWidgets.QWidget()
        labl = QtWidgets.QLabel(self.magneticAnglesWidget)
        with resources.open_binary("sas.qtgui.images", "M_angles_pic.png") as file:
            image_data = file.read()
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(image_data)
        labl.setPixmap(pixmap)
        self.magneticAnglesWidget.setFixedSize(pixmap.width(), pixmap.height())

    def onDisplayMagneticAngles(self) -> None:
        """
        Display a simple image showing direction of magnetic angles
        """
        self.magneticAnglesWidget.show()
