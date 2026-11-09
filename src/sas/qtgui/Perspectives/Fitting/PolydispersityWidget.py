"""
The polydispersity tab. Its table shows the page's document (``ParameterItemModel``, which
the page sets as ``poly_model``); the widget keeps the distribution choice, which may ask for
an array file.
"""
import logging
import os

from PySide6 import QtCore, QtWidgets

from sasmodels.weights import MODELS as POLYDISPERSITY_MODELS

from sas.qtgui.Perspectives.Fitting import FittingUtilities
from sas.qtgui.Perspectives.Fitting.model.parameters import ArrayDistribution, Dispersion, Table

# Local UI
from sas.qtgui.Perspectives.Fitting.UI.PolydispersityWidget import Ui_PolydispersityWidgetUI
from sas.qtgui.Perspectives.Fitting.ViewDelegate import PolyViewDelegate

logger = logging.getLogger(__name__)

class PolydispersityWidget(QtWidgets.QWidget, Ui_PolydispersityWidgetUI):
    updateDataSignal = QtCore.Signal()
    deletePlotSignal = QtCore.Signal(str)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super(PolydispersityWidget, self).__init__()

        self.setupUi(self)
        self.lstPoly.isEnabled = True
        self.poly_model = None      # the page's ParameterItemModel of the polydispersity table
        self._fitting_widget = parent
        FittingUtilities.setTableProperties(self.lstPoly)
        self.lstPoly.setItemDelegate(PolyViewDelegate(self))
        self.lstPoly.installEventFilter(self)

        self.lstPoly.itemDelegate().filename_updated.connect(self.onPolyFilenameChange)

        self.lstPoly.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        # self.lstPoly.customContextMenuRequested.connect(self.showModelContextMenu)
        self.lstPoly.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)

    @staticmethod
    def polyNameToParam(param_name: str) -> str:
        """
        Translate polydisperse QTable representation into parameter name
        """
        param_name = param_name.replace('Distribution of ', '')
        param_name += '.width'
        return param_name

    def onPolyFilenameChange(self, row_index: int) -> None:
        """
        Respond to filename_updated signal from the delegate
        """
        # For the given row, invoke the "array" combo handler
        array_caption = 'array'

        # Get the combo box reference
        ind = self.poly_model.index(row_index, self.poly_model.column("function"))
        widget = self.lstPoly.indexWidget(ind)

        # Update the combo box so it displays "array"
        widget.blockSignals(True)
        widget.setCurrentIndex(self.lstPoly.itemDelegate().POLYDISPERSE_FUNCTIONS.index(array_caption))
        widget.blockSignals(False)

        # Invoke the file reader
        self.onPolyComboIndexChange(array_caption, row_index)

    def onPolyComboIndexChange(self, combo_string: str, row_index: int) -> None:
        """
        A distribution chosen for a width: a controller intent. 'array' asks for its weights file
        and makes the width unfitted; a named distribution takes its default npts and nsigmas.
        """
        page = self._fitting_widget
        if page.controller.muted:
            return
        key = page.keyAt(row_index, Table.POLY)
        if key is None:
            return
        current = page.document.parameters[key].dispersion
        if combo_string == "array":
            try:
                array = self.loadPolydispArray(row_index)
            except OSError:
                # Cancelled or unreadable: show the current distribution again
                combo = self.lstPoly.indexWidget(self.poly_model.index(row_index, self.poly_model.column("function")))
                if combo is not None:
                    combo.blockSignals(True)
                    combo.setCurrentIndex(combo.findText(current.type))
                    combo.blockSignals(False)
                return
            page.controller.set_parameter(key, dispersion=Dispersion(current.npts, current.nsigmas, "array", array),
                                          fit=False)
            return
        if combo_string not in POLYDISPERSITY_MODELS:
            logger.error("Error in setting the dispersion model. Reverting to Gaussian.")
            combo_string = "gaussian"
        defaults = POLYDISPERSITY_MODELS[combo_string].default
        page.controller.set_parameter(key, dispersion=Dispersion(defaults['npts'], defaults['nsigmas'], combo_string))

    def loadPolydispArray(self, row_index: int) -> ArrayDistribution:
        """
        Show the load file dialog and read the weights file; OSError if none is chosen
        """
        datafile = QtWidgets.QFileDialog.getOpenFileName(
            self, "Choose a weight file", "", "All files (*.*)", None,
            QtWidgets.QFileDialog.DontUseNativeDialog)[0]

        if not datafile:
            logger.info("No weight data chosen.")
            raise OSError

        values = []
        weights = []
        def appendData(data_tuple: list[str]) -> None:
            """
            Fish out floats from a tuple of strings
            """
            try:
                values.append(float(data_tuple[0]))
                weights.append(float(data_tuple[1]))
            except (ValueError, IndexError):
                # just pass through if line with bad data
                return

        with open(datafile) as column_file:
            column_data = [line.rstrip().split() for line in column_file.readlines()]
            [appendData(line) for line in column_data]

        return ArrayDistribution(tuple(values), tuple(weights), os.path.basename(str(datafile)))

