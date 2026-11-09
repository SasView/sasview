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
    toggledSignal = QtCore.Signal(bool)  # Signal when magnetism is enabled/disabled

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super(MagnetismWidget, self).__init__()

        self.setupUi(self)
        self.lstMagnetic.isEnabled = True
        self._magnet_model = FittingUtilities.ToolTippedItemModel()
        self.is2D = False
        self.isActive = False
        self._fitting_widget = parent
        self.has_magnet_error_column = False
        # Magnetism widget table default index for function combobox
        # self.orig_poly_index = 4
        FittingUtilities.setTableProperties(self.lstMagnetic)
        self.lstMagnetic.setItemDelegate(MagnetismViewDelegate(self))
        self.lstMagnetic.installEventFilter(self)

        self.lstMagnetic.setModel(self._magnet_model)
        FittingUtilities.setTableProperties(self.lstMagnetic)
        # self.lstMagnetic.itemDelegate().combo_updated.connect(self.onPolyComboIndexChange)
        # self.lstMagnetic.itemDelegate().filename_updated.connect(self.onPolyFilenameChange)

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

    def toggleMagnetism(self, isChecked: bool) -> None:
        """
        Toggle magnetism.

        Args:
            isChecked: Whether magnetism is enabled
        """
        self.isActive = isChecked

        # Emit signal to notify parent that state changed
        self.toggledSignal.emit(isChecked)

