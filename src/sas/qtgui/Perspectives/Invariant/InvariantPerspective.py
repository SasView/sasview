# global
import copy
import logging
import math
from typing import Literal

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets
from twisted.internet import reactor, threads

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Plotting import PlotterData
from sas.qtgui.Plotting.PlotterData import Data1D, DataRole
from sas.qtgui.Utilities.ExtrapolationSlider import ExtrapolationSlider, SliderPerspective

# sas-global
from sas.sascalc.invariant import invariant
from sas.sascalc.util import ExtrapolationParameters

# local
from ..perspective import Perspective
from .InvariantDetails import DetailsDialog
from .InvariantUtils import WIDGETS, safe_float
from .UI.TabbedInvariantUI import Ui_tabbedInvariantUI

# The min/max q-values to be used when extrapolating
Q_MINIMUM = 1e-5
Q_MAXIMUM = 10
# Default power law for extrapolation
DEFAULT_POWER_VALUE = 4
# Small epsilon for floating point adjustments
ADJUST_EPS = 1e-7

# Background of line edits if settings OK or wrong
BG_DEFAULT = ""
BG_RED = "background-color: rgb(244, 170, 164);"

logger = logging.getLogger(__name__)


class InvariantWindow(QtWidgets.QDialog, Ui_tabbedInvariantUI, Perspective):
    """The controller responsible for managing signal slots connections for the gui and providing an interface to the data model."""

    name = "Invariant"
    ext = "inv"

    @property
    def title(self) -> str:
        """Provides the perspective name."""
        return "Invariant Perspective"

    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle(self.title)
        self.resize(self.minimumSizeHint())

        # GUI components
        self.parent = parent
        self._manager = parent
        self._reactor = reactor
        self._model_item = QtGui.QStandardItem()
        self._allow_close: bool = False

        # Communication
        self.communicate = self._manager.communicator()
        self.communicate.dataDeletedSignal.connect(self.removeData)

        self.detailsDialog = DetailsDialog(self)
        self.detailsDialog.cmdOK.clicked.connect(self.enableStatus)

        # Data
        self._data: Data1D | None = None
        self._path: str = ""
        self._calculator: invariant.InvariantCalculator | None = None

        self.initialize_variables()
        self.setup_slider()
        self.setup_tooltips()
        self.setup_validators()

        # Let's choose the Standard Item Model
        self.model = QtGui.QStandardItemModel(self)

        # Connect buttons to slots
        self.setupSlots()  # Needs to be done early so default values propagate properly
        self.setupModel()
        self.setupMapper()
        self.setup_default_enablement()
        self.check_status()

        # Go to the first data item
        self.mapper.toFirst()

    @property
    def extrapolation_parameters(self) -> ExtrapolationParameters | None:
        if self._data is not None:
            return ExtrapolationParameters(
                ex_q_min=float(Q_MINIMUM),
                data_q_min=safe_float(self.model.item(WIDGETS.W_QMIN).text()),
                point_1=safe_float(self.model.item(WIDGETS.W_GUINIER_END_EX).text()),
                point_2=safe_float(self.model.item(WIDGETS.W_POROD_START_EX).text()),
                point_3=safe_float(self.model.item(WIDGETS.W_POROD_END_EX).text()),
                data_q_max=safe_float(self.model.item(WIDGETS.W_QMAX).text()),
                ex_q_max=float(Q_MAXIMUM),
            )
        else:
            return None

    def initialize_variables(self) -> None:
        """Initialize class variables."""

        # Initial input params
        self._background: float = 0.0
        self._scale: float = 1.0
        self._contrast: float | None = None
        self._contrast_err: float | None = None
        self._porod: float | None = None
        self._porod_err: float | None = None
        self._volfrac1: float | None = None
        self._volfrac1_err: float | None = None

        self._low_extrapolate: bool = False
        self._low_guinier: bool = True
        self._low_fit: bool = False
        self._low_power_value: float = DEFAULT_POWER_VALUE
        self._high_extrapolate: bool = False
        self._high_fit: bool = False
        self._high_power_value: float | None = DEFAULT_POWER_VALUE

        # Define plots
        self.high_extrapolation_plot: PlotterData | None = None
        self.low_extrapolation_plot: PlotterData | None = None

    def setup_slider(self) -> None:
        """Setup the extrapolation slider."""
        self.slider = ExtrapolationSlider(perspective=SliderPerspective.INVARIANT)
        self.sliderLayout.insertWidget(1, self.slider)

    def setup_tooltips(self) -> None:
        """Setup tooltips for the widgets"""
        self.cmdStatus.setToolTip("Get more details of computation such as fraction from extrapolation")
        self.cmdCalculate.setToolTip("Compute invariant")
        self.txtInvariantTot.setToolTip("Total invariant [Q*], including extrapolated regions.")
        self.txtHighQPower_ex.setToolTip("Exponent to apply to the Power_law function.")
        self.txtLowQPower_ex.setToolTip("Exponent to apply to the Power_law function.")
        self.chkHighQ_ex.setToolTip("Check to extrapolate data at high-Q")
        self.chkLowQ_ex.setToolTip("Check to extrapolate data at low-Q")
        self.txtGuinierEnd_ex.setToolTip("Q value where low-Q extrapolation ends")
        self.txtPorodStart_ex.setToolTip("Q value where high-Q extrapolation starts")
        self.txtPorodEnd_ex.setToolTip("Q value where high-Q extrapolation ends")

    def setup_validators(self) -> None:
        """Set validators for line edits."""
        self.txtBackgd.setValidator(GuiUtils.DoubleValidator())
        self.txtScale.setValidator(GuiUtils.DoubleValidator())
        self.txtPorodCst.setValidator(GuiUtils.DoubleValidator())
        self.txtPorodCstErr.setValidator(GuiUtils.DoubleValidator())
        self.txtContrast.setValidator(GuiUtils.DoubleValidator())
        self.txtContrastErr.setValidator(GuiUtils.DoubleValidator())
        self.txtVolFrac1.setValidator(GuiUtils.DoubleValidator())
        self.txtVolFrac1Err.setValidator(GuiUtils.DoubleValidator())
        self.txtGuinierEnd_ex.setValidator(GuiUtils.DoubleValidator())
        self.txtPorodStart_ex.setValidator(GuiUtils.DoubleValidator())
        self.txtPorodEnd_ex.setValidator(GuiUtils.DoubleValidator())
        self.txtLowQPower_ex.setValidator(GuiUtils.DoubleValidator())
        self.txtHighQPower_ex.setValidator(GuiUtils.DoubleValidator())

    def setup_default_enablement(self) -> None:
        """Setup the default enablement of the widgets."""
        self.tabWidget.setCurrentIndex(0)
        self.rbContrast.setChecked(True)

        self.rbLowQGuinier_ex.setEnabled(False)
        self.rbLowQPower_ex.setEnabled(False)
        self.rbLowQFit_ex.setEnabled(False)
        self.rbLowQFix_ex.setEnabled(False)
        self.rbHighQFit_ex.setEnabled(False)
        self.rbHighQFix_ex.setEnabled(False)
        self.txtLowQPower_ex.setEnabled(False)
        self.txtHighQPower_ex.setEnabled(False)
        self.update_progress_bars()

        self.check_status()

    def enable_calculation(self, enabled: bool = True, display: str = "Calculate") -> None:
        """
        Enable or disable the calculation button and display appropriate reason.

        :param enabled: enable or disable the calculation button, default is True
        :param display: display text for the calculation button, default is "Calculate"
        """
        self.cmdCalculate.setEnabled(enabled)
        self.cmdCalculate.setText(display)

    def enable_extrapolation_text(self, state: bool) -> None:
        """
        Enable or disable the text fields in the extrapolation tab

        :param state: enable or disable the text fields
        """
        self.txtGuinierEnd_ex.setEnabled(state)
        self.txtPorodStart_ex.setEnabled(state)
        self.txtPorodEnd_ex.setEnabled(state)

    def get_low_q_extrapolation_upper_limit(self) -> float:
        """
        Get the low Q extrapolation upper limit

        :return: low Q extrapolation upper limit
        """
        q_value: float = self._data.x[int(self._low_points) - 1]
        return q_value

    def set_low_q_extrapolation_upper_limit(self, value: float) -> None:
        """
        Set the low Q extrapolation upper limit

        :param value: low Q extrapolation upper limit
        """
        self._low_points = (np.abs(self._data.x - value)).argmin() + 1

    def get_high_q_extrapolation_lower_limit(self) -> float:
        """
        Get the high Q extrapolation lower limit

        :return: high Q extrapolation lower limit
        """
        q_value: float = self._data.x[len(self._data.x) - int(self._high_points) - 1]
        return q_value

    def set_high_q_extrapolation_lower_limit(self, value: float) -> None:
        """
        Set the high Q extrapolation lower limit

        :param value: high Q extrapolation lower limit
        """
        self._high_points = len(self._data.x) - (np.abs(self._data.x - value)).argmin() + 1

    def enableStatus(self) -> None:
        """Enable the status button."""
        self.cmdStatus.setEnabled(True)

    def setClosable(self, value: bool = True) -> None:
        """Allow outsiders to close this widget."""
        self._allow_close = value

    def isSerializable(self) -> bool:
        """Tell the caller that this perspective writes its state."""
        return True

    def closeEvent(self, event) -> None:
        """Overwrite QDialog close method to allow for custom widget close."""
        if self._allow_close:
            # reset the closability flag
            self.setClosable(value=False)
            # Tell the MdiArea to close the container if it is visible
            if self.parentWidget():
                self.parentWidget().close()
            event.accept()
        else:
            event.ignore()
            self.setWindowState(QtCore.Qt.WindowMinimized)

    def update_from_model(self) -> None:
        """Update the globals based on the data in the model."""
        background_text = self.model.item(WIDGETS.W_BACKGROUND).text()
        self._background = float(background_text) if background_text != "" else 0.0

        scale_text = self.model.item(WIDGETS.W_SCALE).text()
        self._scale = float(scale_text) if scale_text != "" else 1.0

        porod_text = self.model.item(WIDGETS.W_POROD_CST).text()
        self._porod = float(porod_text) if porod_text else None

        porod_err_text = self.model.item(WIDGETS.W_POROD_CST_ERR).text()
        self._porod_err = float(porod_err_text) if porod_err_text else None

        contrast_text = self.model.item(WIDGETS.W_CONTRAST).text()
        self._contrast = float(contrast_text) if contrast_text else None

        contrast_err_text = self.model.item(WIDGETS.W_CONTRAST_ERR).text()
        self._contrast_err = float(contrast_err_text) if contrast_err_text else None

        volfrac1_text = self.model.item(WIDGETS.W_VOLFRAC1).text()
        self._volfrac1 = float(volfrac1_text) if volfrac1_text else None

        volfrac1_err_text = self.model.item(WIDGETS.W_VOLFRAC1_ERR).text()
        self._volfrac1_err = float(volfrac1_err_text) if volfrac1_err_text else None

        self._low_extrapolate = str(self.model.item(WIDGETS.W_ENABLE_LOWQ_EX).text()) == "true"
        self._low_guinier = self.rbLowQGuinier_ex.isChecked()
        self._low_power = str(self.model.item(WIDGETS.W_LOWQ_POWER_EX).text()) == "true"
        self._low_fit = self.rbLowQFit_ex.isChecked()
        self._low_fix = self.rbLowQFix_ex.isChecked()
        self._low_power_value = float(self.model.item(WIDGETS.W_LOWQ_POWER_VALUE_EX).text())

        self._high_extrapolate = str(self.model.item(WIDGETS.W_ENABLE_HIGHQ_EX).text()) == "true"
        self._high_fit = self.rbHighQFit_ex.isChecked()
        self._high_fix = self.rbHighQFix_ex.isChecked()
        self._high_power_value = float(self.model.item(WIDGETS.W_HIGHQ_POWER_VALUE_EX).text())

    def calculate_invariant(self) -> None:
        """Use twisted to thread the calculations away"""
        # Find out if extrapolation needs to be used.
        extrapolation: str | None = None
        if self._low_extrapolate and self._high_extrapolate:
            extrapolation = "both"
        elif self._high_extrapolate:
            extrapolation = "high"
        elif self._low_extrapolate:
            extrapolation = "low"

        # Modify the Calculate button to indicate background process
        self.enable_calculation(enabled=False, display="Calculating...")

        # Send the calculations to separate thread.
        d = threads.deferToThread(self.calculate_thread, extrapolation)

        # Add deferred callback for call return
        d.addCallback(self.deferredPlot)
        d.addErrback(self.on_calculation_failed)

    def on_calculation_failed(self, reason: Exception) -> None:
        """Handle calculation failure."""
        logger.error(f"calculation failed: {reason}")
        self.check_status()

    def deferredPlot(self, model: QtGui.QStandardItemModel) -> None:
        """Run the GUI/model update in the main thread"""
        reactor.callFromThread(lambda: self.plot_result(model))
        self.check_status()

    def check_status(self) -> None:
        """
        Check the status of the input fields and enable the calculate button if:
        - Data is present,
        - The selected radio button corresponds to a field with a valid value.
        """
        if self._data is None:
            self.enable_calculation(enabled=False, display="Calculate (No data)")
            return

        # Update from model first to ensure instance variables are current
        self.update_from_model()

        # Check ONLY the field that corresponds to the selected radio button
        has_valid_input = False
        if self.rbVolFrac.isChecked():
            has_valid_input = self._volfrac1 is not None
        elif self.rbContrast.isChecked():
            has_valid_input = self._contrast is not None

        if has_valid_input:
            self.enable_calculation()
        else:
            self.enable_calculation(enabled=False, display="Calculate (Enter volume fraction or contrast)")

    def plot_result(self, model: QtGui.QStandardItemModel) -> None:
        """Plot result of calculation"""
        self.model = model
        self._data = GuiUtils.dataFromItem(self._model_item)

        # Close the initial data plot that was created in setData()
        if self._model_item is not None and (self.high_extrapolation_plot or self.low_extrapolation_plot):
            self._manager.filesWidget.closePlotsForItem(self._model_item)

        # Send the modified model item to replace initial plot
        plots = [self._model_item]

        if self.high_extrapolation_plot:
            self.high_extrapolation_plot.plot_role = DataRole.ROLE_DEFAULT
            self.high_extrapolation_plot.symbol = "Line"
            self.high_extrapolation_plot.custom_color = "#2ca02c"
            self.high_extrapolation_plot.show_errors = False
            self.high_extrapolation_plot.show_q_range_sliders = True
            self.high_extrapolation_plot.slider_update_on_move = False
            self.high_extrapolation_plot.slider_perspective_name = self.name
            self.high_extrapolation_plot.slider_low_q_input = self.txtPorodStart_ex.text()
            self.high_extrapolation_plot.slider_low_q_setter = ["set_high_q_extrapolation_lower_limit"]
            self.high_extrapolation_plot.slider_low_q_getter = ["get_high_q_extrapolation_lower_limit"]
            self.high_extrapolation_plot.slider_high_q_input = self.txtPorodEnd_ex.text()
            GuiUtils.updateModelItemWithPlot(
                self._model_item, self.high_extrapolation_plot, self.high_extrapolation_plot.title
            )
            plots.append(self.high_extrapolation_plot)
        if self.low_extrapolation_plot:
            self.low_extrapolation_plot.plot_role = DataRole.ROLE_DEFAULT
            self.low_extrapolation_plot.symbol = "Line"
            self.low_extrapolation_plot.custom_color = "#ff7f0e"
            self.low_extrapolation_plot.show_errors = False
            self.low_extrapolation_plot.show_q_range_sliders = True
            self.low_extrapolation_plot.slider_update_on_move = False
            self.low_extrapolation_plot.slider_perspective_name = self.name
            self.low_extrapolation_plot.slider_low_q_input = self.extrapolation_parameters.ex_q_min
            self.low_extrapolation_plot.slider_high_q_input = self.txtGuinierEnd_ex.text()
            self.low_extrapolation_plot.slider_high_q_setter = ["set_low_q_extrapolation_upper_limit"]
            self.low_extrapolation_plot.slider_high_q_getter = ["get_low_q_extrapolation_upper_limit"]
            GuiUtils.updateModelItemWithPlot(
                self._model_item, self.low_extrapolation_plot, self.low_extrapolation_plot.title
            )
            plots.append(self.low_extrapolation_plot)

        if len(plots) > 1:
            self.communicate.plotRequestedSignal.emit(plots)

        # Update the details dialog in case it is open
        self.update_details_widget()

        # Update progress bars
        self.update_progress_bars()

    def update_details_widget(self) -> None:
        """On demand update of the details widget."""
        if self.detailsDialog.isVisible():
            self.onStatus()

    def calculate_thread(self, extrapolation: str) -> None:
        """Perform Invariant calculations."""
        self.update_from_model()

        # Set base values
        msg = ""
        qstar_low: float | Literal["ERROR"] = 0.0
        qstar_low_err: float | Literal["ERROR"] = 0.0
        qstar_high: float | Literal["ERROR"] = 0.0
        qstar_high_err: float | Literal["ERROR"] = 0.0
        calculation_failed: bool = False
        low_calculation_pass: bool = False
        high_calculation_pass: bool = False

        temp_data = copy.deepcopy(self._data)

        # Update calculator with background, scale, and data values
        self._calculator.background = self._background
        self._calculator.scale = self._scale
        self._calculator.set_data(temp_data)

        # Low Q extrapolation calculations
        if self._low_extrapolate:
            if self._low_guinier:
                function_low = "guinier"
                self._low_power_value = None
            else:
                function_low = "power_law"
                if self._low_fit:
                    self._low_power_value = None
                elif self._low_fix:
                    self._low_power_value = float(self.model.item(WIDGETS.W_LOWQ_POWER_VALUE_EX).text())

            try:
                q_end_val: float = float(self.txtGuinierEnd_ex.text())

                # Find the index of the data point closest to q_end_val
                n_pts: int = int(np.abs(self._data.x - q_end_val).argmin()) + 1

                if n_pts not in range(1, len(self._data.x) + 1):
                    raise ValueError("Number of points in low-q Guinier end is out of valid bounds")

                self._low_points = n_pts

            except ValueError:
                logger.warning("Could not convert low-q Guinier end value to number of points: {str(ex)}")

            self._calculator.set_extrapolation(
                range="low", npts=int(self._low_points), function=function_low, power=self._low_power_value
            )

            try:
                extrapolation_start: float = float(self.extrapolation_parameters.ex_q_min)
                # If the start is in the data range, set the low q limit to None and let the calculator handle it
                low_q_limit: float | None = None if extrapolation_start > self._data.x[0] else extrapolation_start
                qstar_low, qstar_low_err = self._calculator.get_qstar_low(low_q_limit)
                low_calculation_pass = True
            except Exception as ex:
                logger.warning(f"Low-q calculation failed: {str(ex)}")
                qstar_low = "ERROR"
                qstar_low_err = "ERROR"

        # Remove the existing extrapolation plot if it exists and calculation failed
        if self.low_extrapolation_plot and not low_calculation_pass:
            model_items: list[QtGui.QStandardItem] = GuiUtils.getChildrenFromItem(self._model_item)
            for item in model_items:
                if item.text() == self.low_extrapolation_plot.title:
                    reactor.callFromThread(self._manager.filesWidget.closePlotsForItem, item)
                    reactor.callFromThread(self._model_item.removeRow, item.row())
                    break
            self.low_extrapolation_plot = None

        reactor.callFromThread(self.update_model_from_thread, WIDGETS.D_LOW_QSTAR, qstar_low)
        reactor.callFromThread(self.update_model_from_thread, WIDGETS.D_LOW_QSTAR_ERR, qstar_low_err)

        # High Q Extrapolation calculations
        if self._high_extrapolate:
            function_high: str = "power_law"
            if self._high_fit:
                self._high_power_value = None
            elif self._high_fix:
                self._high_power_value = float(self.model.item(WIDGETS.W_HIGHQ_POWER_VALUE_EX).text())

            try:
                q_start_val = float(self.txtPorodStart_ex.text())

                # Find the index of the data point closest to q_start_val
                idx = int((np.abs(self._data.x - q_start_val)).argmin())

                # Compute number of points from that index to the end
                n_pts_high: int = len(self._data.x) - idx

                if n_pts_high not in range(1, len(self._data.x) + 1):
                    raise ValueError("Number of points in high-q Porod start is out of valid bounds")

                self._high_points = n_pts_high

            except ValueError:
                logger.warning("Could not convert Porod start value to number of points.")

            self._calculator.set_extrapolation(
                range="high", npts=int(self._high_points), function=function_high, power=self._high_power_value
            )

            try:
                extrapolation_end: float = float(self.extrapolation_parameters.ex_q_max)
                # If the end is in the data range, set the high q limit to None and let the calculator handle it
                high_q_limit: float | None = None if extrapolation_end < self._data.x[-1] else extrapolation_end
                qstar_high, qstar_high_err = self._calculator.get_qstar_high(high_q_limit)
                high_calculation_pass: bool = True
            except Exception as ex:
                logger.warning(f"High-q calculation failed: {str(ex)}")
                qstar_high = "ERROR"
                qstar_high_err = "ERROR"

        # Remove the existing high-q extrapolation plot if it exists and calculation was successful
        if self.high_extrapolation_plot and not high_calculation_pass:
            model_items: list[QtGui.QStandardItem] = GuiUtils.getChildrenFromItem(self._model_item)
            for item in model_items:
                if item.text() == self.high_extrapolation_plot.title:
                    reactor.callFromThread(self._manager.filesWidget.closePlotsForItem, item)
                    reactor.callFromThread(self._model_item.removeRow, item.row())
                    break
            self.high_extrapolation_plot = None

        reactor.callFromThread(self.update_model_from_thread, WIDGETS.D_HIGH_QSTAR, qstar_high)
        reactor.callFromThread(self.update_model_from_thread, WIDGETS.D_HIGH_QSTAR_ERR, qstar_high_err)

        # Q* Data calculations
        qstar_data: float | Literal["ERROR"]
        qstar_data_err: float | Literal["ERROR"]
        try:
            qstar_data, qstar_data_err = self._calculator.get_qstar_with_error()
        except Exception as ex:
            calculation_failed = True
            msg += f"Invariant calculation failed: {str(ex)}"
            qstar_data, qstar_data_err = "ERROR", "ERROR"

        reactor.callFromThread(self.update_model_from_thread, WIDGETS.D_DATA_QSTAR, qstar_data)
        reactor.callFromThread(self.update_model_from_thread, WIDGETS.D_DATA_QSTAR_ERR, qstar_data_err)

        # Volume Fraction calculations
        if self.rbContrast.isChecked() and self._contrast:
            volume_fraction: float | Literal["ERROR"]
            volume_fraction_error: float | Literal["ERROR"]
            try:
                volume_fraction, volume_fraction_error = self._calculator.get_volume_fraction_with_error(
                    self._contrast, contrast_err=self._contrast_err, extrapolation=extrapolation
                )
            except (ValueError, ZeroDivisionError) as ex:
                calculation_failed = True
                msg += f"Volume fraction calculation failed: {str(ex)}"
                volume_fraction, volume_fraction_error = "ERROR", "ERROR"

            reactor.callFromThread(self.update_model_from_thread, WIDGETS.W_VOLUME_FRACTION, volume_fraction)
            reactor.callFromThread(self.update_model_from_thread, WIDGETS.W_VOLUME_FRACTION_ERR, volume_fraction_error)

        # Contrast calculations
        if self.rbVolFrac.isChecked() and self._volfrac1:
            contrast_out: float | Literal["ERROR"]
            contrast_out_error: float | Literal["ERROR"]
            try:
                contrast_out, contrast_out_error = self._calculator.get_contrast_with_error(
                    self._volfrac1, volume_err=self._volfrac1_err, extrapolation=extrapolation
                )
            except (ValueError, ZeroDivisionError) as ex:
                calculation_failed: bool = True
                msg += f"Contrast calculation failed: {str(ex)}"
                contrast_out, contrast_out_error = "ERROR", "ERROR"

            reactor.callFromThread(self.update_model_from_thread, WIDGETS.W_CONTRAST_OUT, contrast_out)
            reactor.callFromThread(self.update_model_from_thread, WIDGETS.W_CONTRAST_OUT_ERR, contrast_out_error)

        # Surface Error calculations
        if self._porod and self._porod > 0:
            surface: float | Literal["ERROR"]
            surface_error: float | Literal["ERROR"]
            if self.rbContrast.isChecked():
                contrast_for_surface = self._contrast
                contrast_for_surface_err = self._contrast_err
            elif self.rbVolFrac.isChecked() and (contrast_out != "ERROR" and contrast_out_error != "ERROR"):
                contrast_for_surface = contrast_out
                contrast_for_surface_err = contrast_out_error

            try:
                surface, surface_error = self._calculator.get_surface_with_error(
                    contrast_for_surface,
                    self._porod,
                    contrast_err=contrast_for_surface_err,
                    porod_const_err=self._porod_err,
                )
            except (ValueError, ZeroDivisionError) as ex:
                calculation_failed: bool = True
                msg += f"Specific surface calculation failed: {str(ex)}"
                surface, surface_error = "ERROR", "ERROR"

            reactor.callFromThread(self.update_model_from_thread, WIDGETS.W_SPECIFIC_SURFACE, surface)
            reactor.callFromThread(self.update_model_from_thread, WIDGETS.W_SPECIFIC_SURFACE_ERR, surface_error)

        # Enable the status button
        self.cmdStatus.setEnabled(True)

        # Early exit if calculations failed
        if calculation_failed:
            self.cmdStatus.setEnabled(False)
            logger.warning(f"Calculation failed: {msg}")
            return self.model

        if low_calculation_pass:
            qmin_ext: float = float(self.extrapolation_parameters.ex_q_min)
            extrapolated_data = self._calculator.get_extra_data_low(self._low_points, q_start=qmin_ext)
            power_low: float | None = self._calculator.get_extrapolation_power(range="low")

            title = f"Low-Q extrapolation [{self._data.name}]"

            # Convert the data into plottable
            self.low_extrapolation_plot = self._manager.createGuiData(extrapolated_data)

            self.low_extrapolation_plot.name = title
            self.low_extrapolation_plot.title = title
            self.low_extrapolation_plot.symbol = "Line"
            self.low_extrapolation_plot.has_errors = False

            # copy labels and units of axes for plotting
            self.low_extrapolation_plot._xaxis = temp_data._xaxis
            self.low_extrapolation_plot._xunit = temp_data._xunit
            self.low_extrapolation_plot._yaxis = temp_data._yaxis
            self.low_extrapolation_plot._yunit = temp_data._yunit

            if self._low_fit:
                reactor.callFromThread(self.update_model_from_thread, WIDGETS.W_LOWQ_POWER_VALUE_EX, power_low)

        if high_calculation_pass:
            qmax_plot: float = float(self.extrapolation_parameters.point_3)

            power_high: float | None = self._calculator.get_extrapolation_power(range="high")
            high_out_data = self._calculator.get_extra_data_high(q_end=qmax_plot, npts=500)

            title = f"High-Q extrapolation [{self._data.name}]"

            # Convert the data into plottable
            self.high_extrapolation_plot = self._manager.createGuiData(high_out_data)
            self.high_extrapolation_plot.name = title
            self.high_extrapolation_plot.title = title
            self.high_extrapolation_plot.symbol = "Line"
            self.high_extrapolation_plot.has_errors = False

            # copy labels and units of axes for plotting
            self.high_extrapolation_plot._xaxis = temp_data._xaxis
            self.high_extrapolation_plot._xunit = temp_data._xunit
            self.high_extrapolation_plot._yaxis = temp_data._yaxis
            self.high_extrapolation_plot._yunit = temp_data._yunit

            if self._high_fit:
                reactor.callFromThread(self.update_model_from_thread, WIDGETS.W_HIGHQ_POWER_VALUE_EX, power_high)

        if qstar_high == "ERROR":
            qstar_high, qstar_high_err = 0.0, 0.0
        if qstar_low == "ERROR":
            qstar_low, qstar_low_err = 0.0, 0.0

        qstar_total = qstar_data + qstar_low + qstar_high
        qstar_total_error = np.sqrt(
            qstar_data_err * qstar_data_err + qstar_low_err * qstar_low_err + qstar_high_err * qstar_high_err
        )

        reactor.callFromThread(self.update_model_from_thread, WIDGETS.W_INVARIANT, qstar_total)
        reactor.callFromThread(self.update_model_from_thread, WIDGETS.W_INVARIANT_ERR, qstar_total_error)

        return self.model

    def update_model_from_thread(self, widget_id: int, value: float) -> None:
        """Update the model in the main thread."""
        try:
            # Use scientific notation for very small or very large values
            if abs(value) < 0.001 or abs(value) > 10000:
                formatted_value = f"{value:.4e}"
            else:
                formatted_value = f"{value:.3f}"
        except (TypeError, ValueError):
            formatted_value = str(value)

        item = QtGui.QStandardItem(formatted_value)
        self.model.setItem(widget_id, item)

        # Don't call mapper.toLast() if updating power values to avoid resetting radio button states
        if widget_id not in [WIDGETS.W_LOWQ_POWER_VALUE_EX, WIDGETS.W_HIGHQ_POWER_VALUE_EX]:
            self.mapper.toLast()

        # Update progress bars if updating Q* values
        if widget_id in [WIDGETS.D_DATA_QSTAR, WIDGETS.D_LOW_QSTAR, WIDGETS.D_HIGH_QSTAR]:
            self.update_progress_bars()

    def onStatus(self):
        """Display Invariant Details panel when clicking on Status button."""
        self.detailsDialog.setModel(self.model)
        self.detailsDialog.showDialog()
        self.cmdStatus.setEnabled(False)

    def onHelp(self):
        """Display help when clicking on Help button."""
        treeLocation: str = "/user/qtgui/Perspectives/Invariant/invariant_help.html"
        self.parent.showHelp(treeLocation)

    def setupSlots(self):
        """Setup slots for the buttons and checkboxes."""
        self.cmdCalculate.clicked.connect(self.calculate_invariant)
        self.cmdStatus.clicked.connect(self.onStatus)
        self.cmdHelp.clicked.connect(self.onHelp)

        # slots for the volume fraction and contrast radio buttons
        self.rbVolFrac.toggled.connect(self.contrast_volfrac_toggle)
        self.rbContrast.toggled.connect(self.contrast_volfrac_toggle)

        # group radio buttons to make them exclusive
        self.VolFracContrastGroup = QtWidgets.QButtonGroup(self)
        self.VolFracContrastGroup.addButton(self.rbVolFrac)
        self.VolFracContrastGroup.addButton(self.rbContrast)

        # update model from gui editing by users
        self.txtBackgd.textEdited.connect(self.updateFromGui)
        self.txtScale.textEdited.connect(self.updateFromGui)
        self.txtContrast.textEdited.connect(self.updateFromGui)
        self.txtContrastErr.textEdited.connect(self.updateFromGui)
        self.txtPorodCst.textEdited.connect(self.updateFromGui)
        self.txtPorodCstErr.textEdited.connect(self.updateFromGui)
        self.txtVolFrac1.textEdited.connect(self.updateFromGui)
        self.txtVolFrac1.editingFinished.connect(self.checkVolFrac)
        self.txtVolFrac1Err.textEdited.connect(self.updateFromGui)

        # Extrapolation parameters
        # Q range fields
        self.txtGuinierEnd_ex.textEdited.connect(self.on_extrapolation_text_editing)
        self.txtPorodStart_ex.textEdited.connect(self.on_extrapolation_text_editing)
        self.txtPorodEnd_ex.textEdited.connect(self.on_extrapolation_text_editing)
        self.txtGuinierEnd_ex.editingFinished.connect(self.on_extrapolation_text_edited)
        self.txtPorodStart_ex.editingFinished.connect(self.on_extrapolation_text_edited)
        self.txtPorodEnd_ex.editingFinished.connect(self.on_extrapolation_text_edited)
        self.enable_extrapolation_text(False)

        # Extrapolation Options
        self.chkLowQ_ex.stateChanged.connect(self.on_extrapolation_lowq_check_changed)
        self.chkHighQ_ex.stateChanged.connect(self.on_extrapolation_highq_check_changed)

        self.rbLowQGuinier_ex.toggled.connect(self.lowGuinierAndPowerToggle_ex)
        self.rbLowQPower_ex.toggled.connect(self.lowGuinierAndPowerToggle_ex)
        self.rbHighQFix_ex.toggled.connect(self.highFitAndFixToggle_ex)
        self.rbHighQFit_ex.toggled.connect(self.highFitAndFixToggle_ex)
        self.rbLowQFix_ex.toggled.connect(self.lowFitAndFixToggle_ex)
        self.rbLowQFit_ex.toggled.connect(self.lowFitAndFixToggle_ex)

        # Group buttons to make them exclusive
        self.LowQGroup: QtWidgets.QButtonGroup = QtWidgets.QButtonGroup(self)
        self.LowQPowerGroup: QtWidgets.QButtonGroup = QtWidgets.QButtonGroup(self)
        self.HighQGroup: QtWidgets.QButtonGroup = QtWidgets.QButtonGroup(self)

        self.LowQGroup.addButton(self.rbLowQGuinier_ex)
        self.LowQGroup.addButton(self.rbLowQPower_ex)
        self.LowQPowerGroup.addButton(self.rbLowQFix_ex)
        self.LowQPowerGroup.addButton(self.rbLowQFit_ex)
        self.HighQGroup.addButton(self.rbHighQFix_ex)
        self.HighQGroup.addButton(self.rbHighQFit_ex)

        self.txtLowQPower_ex.textEdited.connect(self.updateFromGui)
        self.txtHighQPower_ex.textEdited.connect(self.updateFromGui)

        # Slider values
        self.slider.valueEdited.connect(self.on_extrapolation_slider_changed)

    # Extrapolation Options
    def on_extrapolation_lowq_check_changed(self) -> None:
        """Handle the state change of the low Q extrapolation checkbox."""
        state: bool = self.chkLowQ_ex.isChecked()
        itemf: QtGui.QStandardItem = QtGui.QStandardItem(str(state).lower())
        self.model.setItem(WIDGETS.W_ENABLE_LOWQ_EX, itemf)

        if state:
            self.rbLowQPower_ex.setEnabled(True)
            self.rbLowQGuinier_ex.setEnabled(True)

            if not (self.rbLowQPower_ex.isChecked() or self.rbLowQGuinier_ex.isChecked()):
                self.rbLowQGuinier_ex.setChecked(True)

            if self.rbLowQPower_ex.isChecked():
                self.rbLowQFix_ex.setEnabled(True)
                self.rbLowQFit_ex.setEnabled(True)
                self.txtLowQPower_ex.setEnabled(
                    True
                ) if self.rbLowQFix_ex.isChecked() else self.txtLowQPower_ex.setEnabled(False)
            else:
                self.rbLowQFix_ex.setEnabled(False)
                self.rbLowQFit_ex.setEnabled(False)
                self.txtLowQPower_ex.setEnabled(False)

        else:
            self.rbLowQPower_ex.setEnabled(False)
            self.rbLowQGuinier_ex.setEnabled(False)
            self.txtLowQPower_ex.setEnabled(False)
            self.rbLowQFix_ex.setEnabled(False)
            self.rbLowQFit_ex.setEnabled(False)

        self.update_from_model()

    def on_extrapolation_highq_check_changed(self) -> None:
        """Handle the state change of the high Q extrapolation checkbox."""
        state: bool = self.chkHighQ_ex.isChecked()
        itemf: QtGui.QStandardItem = QtGui.QStandardItem(str(state).lower())
        self.model.setItem(WIDGETS.W_ENABLE_HIGHQ_EX, itemf)
        if state:
            self.rbHighQFix_ex.setEnabled(True)
            self.rbHighQFit_ex.setEnabled(True)

            if not (self.rbHighQFix_ex.isChecked() or self.rbHighQFit_ex.isChecked()):
                self.rbHighQFit_ex.setChecked(True)

            if self.rbHighQFix_ex.isChecked():
                self.txtHighQPower_ex.setEnabled(True)
            else:
                self.txtHighQPower_ex.setEnabled(False)
        else:
            self.rbHighQFix_ex.setEnabled(False)
            self.rbHighQFit_ex.setEnabled(False)
            self.txtHighQPower_ex.setEnabled(False)

        self.update_from_model()

    def lowGuinierAndPowerToggle_ex(self) -> None:
        """If Power is selected, Fit and Fix radio buttons are visible."""
        if self.rbLowQPower_ex.isChecked():
            self.enable_low_q_power_options(True)
            # Set default to Fit
            self.rbLowQFit_ex.setChecked(True)
        else:
            self.enable_low_q_power_options(False)

        # Update model to reflect the radio button states
        self.model.setItem(
            WIDGETS.W_LOWQ_GUINIER_EX, QtGui.QStandardItem(str(self.rbLowQGuinier_ex.isChecked()).lower())
        )
        self.model.setItem(WIDGETS.W_LOWQ_POWER_EX, QtGui.QStandardItem(str(self.rbLowQPower_ex.isChecked()).lower()))

        self.update_from_model()

    def enable_low_q_power_options(self, state: bool) -> None:
        """Show and enable the Fit and Fix options if Power is selected."""
        self.rbLowQFit_ex.setEnabled(state)
        self.rbLowQFix_ex.setEnabled(state)
        if self.rbLowQFix_ex.isChecked():
            self.txtLowQPower_ex.setEnabled(True)
        else:
            self.txtLowQPower_ex.setEnabled(False)

        self.update_from_model()

    def highFitAndFixToggle_ex(self) -> None:
        """Enable editing of power exponent if Fix for high Q is checked."""
        if self.rbHighQFix_ex.isChecked():
            self.txtHighQPower_ex.setEnabled(True)
        else:
            self.txtHighQPower_ex.setEnabled(False)

        # Update model to reflect the radio button states
        self.model.setItem(WIDGETS.W_HIGHQ_FIT_EX, QtGui.QStandardItem(str(self.rbHighQFit_ex.isChecked()).lower()))
        self.model.setItem(WIDGETS.W_HIGHQ_FIX_EX, QtGui.QStandardItem(str(self.rbHighQFix_ex.isChecked()).lower()))

        self.update_from_model()

    def lowFitAndFixToggle_ex(self) -> None:
        """Enable editing of power exponent if Fix for low Q is checked."""
        if self.rbLowQFix_ex.isChecked():
            self.txtLowQPower_ex.setEnabled(True)
        else:
            self.txtLowQPower_ex.setEnabled(False)

        # Update model to reflect the radio button states
        self.model.setItem(WIDGETS.W_LOWQ_FIT_EX, QtGui.QStandardItem(str(self.rbLowQFit_ex.isChecked()).lower()))
        self.model.setItem(WIDGETS.W_LOWQ_FIX_EX, QtGui.QStandardItem(str(self.rbLowQFix_ex.isChecked()).lower()))

        self.update_from_model()

    def on_extrapolation_slider_changed(self, state: ExtrapolationParameters) -> None:
        """Handle when user changes any of the extrapolation slider values."""
        format_string: str = "%.7g"
        self.model.setItem(WIDGETS.W_GUINIER_END_EX, QtGui.QStandardItem(format_string % state.point_1))
        self.model.setItem(WIDGETS.W_POROD_START_EX, QtGui.QStandardItem(format_string % state.point_2))
        self.model.setItem(WIDGETS.W_POROD_END_EX, QtGui.QStandardItem(format_string % state.point_3))
        self.correct_extrapolation_values()

    def on_extrapolation_text_editing(self) -> None:
        """Handle when user edits any of the extrapolation text boxes."""
        if self.extrapolation_parameters is None or self._data is None:
            return
        self.check_extrapolation_values()

    def on_extrapolation_text_edited(self) -> None:
        """Handle when user finishes editing any of the extrapolation text boxes."""
        # First update the model with new values
        self.apply_parameters_from_ui()
        # Then correct any invalid values
        self.correct_extrapolation_values()

    def format_sig_fig(self, value: float) -> str:
        """Format a float to 7 significant figures as a string."""
        return f"{value:.7g}"

    def _get_live_extrapolation_values(self) -> tuple[float, float, float]:
        """Read current text box values without correcting them."""
        return (
            safe_float(self.txtGuinierEnd_ex.text()),
            safe_float(self.txtPorodStart_ex.text()),
            safe_float(self.txtPorodEnd_ex.text()),
        )

    def check_extrapolation_values(self) -> None:
        """
        Check validity of extrapolation text boxes such that:
        data_q_min < point_1 < point_2 < point_3 < Q_MAXIMUM and point_2 < data_q_max.
        If invalid, set background color of text box to red.
        """
        # source of values: live text boxes
        p1, p2, p3 = self._get_live_extrapolation_values()

        data_q_min = float(self._data.x.min())  # Actual data min
        data_q_max = float(self._data.x.max())  # Actual data max
        qmax = Q_MAXIMUM  # Extrapolation maximum

        # Helper to test numeric presence
        has_p1 = not math.isnan(p1)
        has_p2 = not math.isnan(p2)
        has_p3 = not math.isnan(p3)

        invalid_p1_data_min: bool = has_p1 and p1 <= data_q_min
        invalid_p1_high: bool = has_p1 and has_p2 and p1 >= p2
        invalid_p2_data_min: bool = has_p2 and p2 <= data_q_min
        invalid_p2_data_max: bool = has_p2 and p2 >= data_q_max
        invalid_p3_low: bool = has_p3 and has_p2 and p3 <= p2
        invalid_p3_ex_max: bool = has_p3 and p3 > qmax

        # UI feedback:
        # - If a field has no numeric value (user still typing "1e-" or empty) keep default background.
        # - If the numeric check says invalid -> red
        self.txtGuinierEnd_ex.setStyleSheet(BG_RED if invalid_p1_data_min or invalid_p1_high else BG_DEFAULT)
        self.txtPorodStart_ex.setStyleSheet(BG_RED if invalid_p2_data_min or invalid_p2_data_max else BG_DEFAULT)
        self.txtPorodEnd_ex.setStyleSheet(BG_RED if invalid_p3_low or invalid_p3_ex_max else BG_DEFAULT)

        self.validity_flags = [
            invalid_p2_data_min,
            invalid_p1_data_min,
            invalid_p1_high,
            invalid_p2_data_max,
            invalid_p3_low,
            invalid_p3_ex_max,
        ]

        # Disable Calculate button if any invalid values
        if any(self.validity_flags):
            self.enable_calculation(False, "Calculate (Correct invalid extrapolation values)")
        else:
            self.check_status()

    def correct_extrapolation_values(self) -> None:
        """Correct invalid extrapolation text box values to nearest valid value."""
        # update validity flags first
        self.check_extrapolation_values()

        # if all values are valid, nothing to do
        if not any(self.validity_flags):
            return

        data_q_min = float(self.format_sig_fig(self._data.x.min()))  # Actual data min
        data_q_max = float(self.format_sig_fig(self._data.x.max()))  # Actual data max
        messages = []

        # block signals to avoid recursive calls
        with (
            QtCore.QSignalBlocker(self.txtGuinierEnd_ex),
            QtCore.QSignalBlocker(self.txtPorodStart_ex),
            QtCore.QSignalBlocker(self.txtPorodEnd_ex),
        ):
            # start by updating p2 as it is used in multiple checks
            if self.validity_flags[0]:  # point_2 <= data_q_min
                messages.append(f"The minimum Q value of the data is {data_q_min:.7g}.")
                new_p2: float = (data_q_min + data_q_max) / 2  # midpoint of data range
                self.txtPorodStart_ex.setText(self.format_sig_fig(new_p2))
                self.check_extrapolation_values()  # re-check validity after changing p2

            p2 = safe_float(self.txtPorodStart_ex.text())

            if self.validity_flags[1]:  # point_1 <= data_q_min
                messages.append(f"The minimum value is {data_q_min:.7g}.")
                new_p1: float = data_q_min + ADJUST_EPS
                self.txtGuinierEnd_ex.setText(self.format_sig_fig(new_p1))

            if self.validity_flags[2]:  # point_1 >= point_2
                new_p1: float = p2 - ADJUST_EPS
                messages.append(f"The Low-q end value must be less than the High-q start value ({p2:.7g}).")
                self.txtGuinierEnd_ex.setText(self.format_sig_fig(new_p1))

            if self.validity_flags[3]:  # point_2 >= data_q_max
                new_p2: float = data_q_max - ADJUST_EPS
                messages.append(f"The maximum Q value of the data is {data_q_max:.7g}.")
                self.txtPorodStart_ex.setText(self.format_sig_fig(new_p2))

            if self.validity_flags[4]:  # point_3 <= point_2
                new_p3: float = data_q_max + ADJUST_EPS  # just above data max to extrapoalate
                messages.append(f"The High-q end value must be greater than the High-q start value ({new_p3:.7g}).")
                self.txtPorodEnd_ex.setText(self.format_sig_fig(new_p3))

            if self.validity_flags[5]:  # point_3 > qmax
                qmax: float = Q_MAXIMUM
                messages.append(f"The maximum value is {qmax:.7g}.")
                self.txtPorodEnd_ex.setText(self.format_sig_fig(qmax))

        # update slider and model
        self.apply_parameters_from_ui()

        if messages:
            messages.append("Values have been adjusted to the nearest valid value.")
            QtWidgets.QMessageBox.warning(self, "Invalid Extrapolation Values", "\n".join(messages))

    def apply_parameters_from_ui(self):
        """Sets extrapolation parameters from the text boxes into the model and slider."""
        p1: str = self.txtGuinierEnd_ex.text()
        p2: str = self.txtPorodStart_ex.text()
        p3: str = self.txtPorodEnd_ex.text()

        if self.extrapolation_parameters is None:
            return
        # update the slider (this may emit a signal that will call on_extrapolation_slider_changed)
        self.slider.extrapolation_parameters = self.extrapolation_parameters._replace(
            point_1=safe_float(p1), point_2=safe_float(p2), point_3=safe_float(p3)
        )

        # update model item text too
        self.model.setItem(WIDGETS.W_GUINIER_END_EX, QtGui.QStandardItem(p1))
        self.model.setItem(WIDGETS.W_POROD_START_EX, QtGui.QStandardItem(p2))
        self.model.setItem(WIDGETS.W_POROD_END_EX, QtGui.QStandardItem(p3))

        # re-validate to update any UI flags
        self.check_extrapolation_values()

    def stateChanged(self) -> None:
        """Catch modifications from low- and high-Q extrapolation check boxes"""
        sender: QtWidgets.QWidget = self.sender()
        itemf: QtGui.QStandardItem = QtGui.QStandardItem(str(sender.isChecked()).lower())
        if sender.text() == "Enable Low-Q extrapolation":
            self.model.setItem(WIDGETS.W_ENABLE_LOWQ, itemf)

        if sender.text() == "Enable High-Q extrapolation":
            self.model.setItem(WIDGETS.W_ENABLE_HIGHQ, itemf)

    def checkQExtrapolatedData(self) -> None:
        """
        Match status of low or high-Q extrapolated data checkbox in
        DataExplorer with low or high-Q extrapolation checkbox in invariant
        panel.
        """
        # name to search in DataExplorer
        if "Low" in str(self.sender().text()):
            name: str = "Low-Q extrapolation"
        if "High" in str(self.sender().text()):
            name: str = "High-Q extrapolation"

        GuiUtils.updateModelItemStatus(self._manager.filesWidget.model, self._path, name, self.sender().checkState())

    def checkVolFrac(self) -> None:
        """Check if volfrac1 is strictly between 0 and 1."""
        if self.txtVolFrac1.text().strip() != "":
            try:
                vf1 = float(self.txtVolFrac1.text())
            except ValueError:
                self.txtVolFrac1.setStyleSheet(BG_RED)
                self.enable_calculation(False, "Calculate (Invalid volume fraction)")
                msg = "Volume fractions must be valid numbers."
                QtWidgets.QMessageBox.warning(self, "Invalid Volume Fraction", msg)
                return
            if 0 < vf1 < 1:
                self.txtVolFrac1.setStyleSheet(BG_DEFAULT)
                self.check_status()
            else:
                self.txtVolFrac1.setStyleSheet(BG_RED)
                self.enable_calculation(False, "Calculate (Invalid volume fraction)")
                msg = "Volume fraction must be between 0 and 1."
                QtWidgets.QMessageBox.warning(self, "Invalid Volume Fraction", msg)

    def updateFromGui(self) -> None:
        """Update model when new user inputs."""

        possible_senders: list[str] = [
            "txtBackgd",
            "txtContrast",
            "txtContrastErr",
            "txtPorodCst",
            "txtPorodCstErr",
            "txtScale",
            "txtVolFrac1",
            "txtVolFrac1Err",
            "txtLowQPower_ex",
            "txtHighQPower_ex",
        ]

        related_widgets: list[WIDGETS] = [
            WIDGETS.W_BACKGROUND,
            WIDGETS.W_CONTRAST,
            WIDGETS.W_CONTRAST_ERR,
            WIDGETS.W_POROD_CST,
            WIDGETS.W_POROD_CST_ERR,
            WIDGETS.W_SCALE,
            WIDGETS.W_VOLFRAC1,
            WIDGETS.W_VOLFRAC1_ERR,
            WIDGETS.W_LOWQ_POWER_VALUE_EX,
            WIDGETS.W_HIGHQ_POWER_VALUE_EX,
        ]

        sender_name = self.sender().objectName()
        text_value = self.sender().text()
        index_elt: int = possible_senders.index(sender_name)

        # Allow empty strings for optional fields like contrast and porod constant
        optional_fields: list[str] = [
            "txtContrast",
            "txtContrastErr",
            "txtPorodCst",
            "txtPorodCstErr",
            "txtVolFrac1",
            "txtVolFrac1Err",
            "txtLowQPower_ex",
            "txtHighQPower_ex",
        ]

        if text_value == "" and sender_name in optional_fields:
            # Set the corresponding attribute to None
            item = QtGui.QStandardItem("")
            self.model.setItem(related_widgets[index_elt], item)
            self.sender().setStyleSheet(BG_DEFAULT)

            # Map sender names to instance variable names
            sender_to_attr = {
                "txtContrast": "_contrast",
                "txtContrastErr": "_contrast_err",
                "txtPorodCst": "_porod",
                "txtPorodCstErr": "_porod_err",
                "txtVolFrac1": "_volfrac1",
                "txtVolFrac1Err": "_volfrac1_err",
                "txtLowQPower_ex": "_low_q_power_ex",
                "txtHighQPower_ex": "_high_q_power_ex",
            }
            if sender_name in sender_to_attr:
                setattr(self, sender_to_attr[sender_name], None)

            self.check_status()
            return

        # Set model item with the text value
        item: QtGui.QStandardItem = QtGui.QStandardItem(text_value)
        self.model.setItem(related_widgets[index_elt], item)

        try:
            new_value = float(text_value)
            self.sender().setStyleSheet(BG_DEFAULT)

            # Map sender names to instance variable names
            sender_to_attr = {
                "txtBackgd": "_background",
                "txtContrast": "_contrast",
                "txtContrastErr": "_contrast_err",
                "txtPorodCst": "_porod",
                "txtScale": "_scale",
                "txtVolFrac1": "_volfrac1",
                "txtVolFrac1Err": "_volfrac1_err",
                "txtLowQPower_ex": "_low_power_value",
                "txtHighQPower_ex": "_high_power_value",
            }

            if sender_name in sender_to_attr:
                setattr(self, sender_to_attr[sender_name], new_value)

            self.check_status()
        except (ValueError, TypeError):
            # empty field or invalid input, just skip
            self.sender().setStyleSheet(BG_RED)
            self.enable_calculation(False, "Calculate (Invalid input)")

    def contrast_volfrac_toggle(self) -> None:
        """Enable editing of the correct fields based on whether Contrast or VolFrac is selected."""
        use_contrast: bool = self.rbContrast.isChecked()

        # update model items
        self.model.setItem(WIDGETS.W_ENABLE_CONTRAST, QtGui.QStandardItem(str(self.rbContrast.isChecked()).lower()))
        self.model.setItem(WIDGETS.W_ENABLE_VOLFRAC, QtGui.QStandardItem(str(self.rbVolFrac.isChecked()).lower()))

        # Input fields
        self.txtContrast.setEnabled(use_contrast)
        self.txtContrastErr.setEnabled(use_contrast)
        self.txtVolFrac1.setEnabled(not use_contrast)
        self.txtVolFrac1Err.setEnabled(not use_contrast)

        # Output fields
        self.txtVolFract.setEnabled(use_contrast)
        self.txtVolFractErr.setEnabled(use_contrast)
        self.txtContrastOut.setEnabled(not use_contrast)
        self.txtContrastOutErr.setEnabled(not use_contrast)

        # allow calculation if the relevant fields are filled
        self.check_status()

    def update_progress_bars(self) -> None:
        """Update progress bars based on Q* values from the model."""

        def reset_progress_bars():
            """Helper to reset all progress bars to empty state."""
            for bar in (self.progressBarLowQ, self.progressBarData, self.progressBarHighQ):
                bar.setValue(0)
                bar.setFormat("")

        def get_qstar_value(widget_id: int) -> float:
            """Extract Q* value from model item, return 0.0 if invalid."""
            item = self.model.item(widget_id)
            if not item or not item.text() or item.text() == "ERROR":
                return 0.0
            try:
                return float(item.text())
            except (ValueError, TypeError):
                return 0.0

        def set_progress_bar(progress_bar: QtWidgets.QProgressBar, percent: float):
            """Set progress bar value and format string."""
            progress_bar.setValue(int(percent))
            progress_bar.setFormat("%6.2f %%" % percent)

        try:
            # Early validation checks
            if not self._data:
                reset_progress_bars()
                return

            qstar_total = get_qstar_value(WIDGETS.W_INVARIANT)
            if qstar_total <= 0:
                reset_progress_bars()
                return

            # Get Q* components
            qdata = get_qstar_value(WIDGETS.D_DATA_QSTAR)
            qstar_low = get_qstar_value(WIDGETS.D_LOW_QSTAR)
            qstar_high = get_qstar_value(WIDGETS.D_HIGH_QSTAR)

            # Calculate percentages
            data_percent = (qdata / qstar_total) * 100.0
            low_percent = (qstar_low / qstar_total) * 100.0
            high_percent = (qstar_high / qstar_total) * 100.0

            # Update all progress bars
            set_progress_bar(self.progressBarLowQ, low_percent)
            set_progress_bar(self.progressBarData, data_percent)
            set_progress_bar(self.progressBarHighQ, high_percent)

        except (ValueError, TypeError, AttributeError) as ex:
            logger.debug(f"Progress bar update failed: {ex}")
            reset_progress_bars()

    def setupModel(self) -> None:
        """Setup the model for the invariant panel."""
        # filename
        item: QtGui.QStandardItem = QtGui.QStandardItem(self._path)
        self.model.setItem(WIDGETS.W_NAME, item)

        # add Q parameters to the model
        qmin: float = 0.0
        item: QtGui.QStandardItem = QtGui.QStandardItem(str(qmin))
        self.model.setItem(WIDGETS.W_QMIN, item)
        qmax: float = 0.0
        item: QtGui.QStandardItem = QtGui.QStandardItem(str(qmax))
        self.model.setItem(WIDGETS.W_QMAX, item)

        # add custom input params
        item: QtGui.QStandardItem = QtGui.QStandardItem(str(self._background))
        self.model.setItem(WIDGETS.W_BACKGROUND, item)
        if self._contrast is not None:
            item: QtGui.QStandardItem = QtGui.QStandardItem(str(self._contrast))
        else:
            item: QtGui.QStandardItem = QtGui.QStandardItem("")
        self.model.setItem(WIDGETS.W_CONTRAST, item)
        item: QtGui.QStandardItem = QtGui.QStandardItem(str(self._contrast_err))
        self.model.setItem(WIDGETS.W_CONTRAST_ERR, item)
        item: QtGui.QStandardItem = QtGui.QStandardItem(str(self._scale))
        self.model.setItem(WIDGETS.W_SCALE, item)

        # leave line edit empty if value is not defined
        item: QtGui.QStandardItem = (
            QtGui.QStandardItem(str(self._porod)) if self._porod is not None else QtGui.QStandardItem("")
        )
        self.model.setItem(WIDGETS.W_POROD_CST, item)
        item: QtGui.QStandardItem = (
            QtGui.QStandardItem(str(self._porod_err)) if self._porod_err is not None else QtGui.QStandardItem("")
        )
        self.model.setItem(WIDGETS.W_POROD_CST_ERR, item)
        item: QtGui.QStandardItem = (
            QtGui.QStandardItem(str(self._contrast)) if self._contrast is not None else QtGui.QStandardItem("")
        )
        self.model.setItem(WIDGETS.W_CONTRAST, item)
        item: QtGui.QStandardItem = (
            QtGui.QStandardItem(str(self._contrast_err)) if self._contrast_err is not None else QtGui.QStandardItem("")
        )
        self.model.setItem(WIDGETS.W_CONTRAST_ERR, item)
        item: QtGui.QStandardItem = (
            QtGui.QStandardItem(str(self._volfrac1)) if self._volfrac1 is not None else QtGui.QStandardItem("")
        )
        self.model.setItem(WIDGETS.W_VOLFRAC1, item)
        item: QtGui.QStandardItem = (
            QtGui.QStandardItem(str(self._volfrac1_err)) if self._volfrac1_err is not None else QtGui.QStandardItem("")
        )
        self.model.setItem(WIDGETS.W_VOLFRAC1_ERR, item)

        # add enable contrast/volfrac to the model
        item: QtGui.QStandardItem = QtGui.QStandardItem("true")
        self.model.setItem(WIDGETS.W_ENABLE_CONTRAST, item)
        item: QtGui.QStandardItem = QtGui.QStandardItem("false")
        self.model.setItem(WIDGETS.W_ENABLE_VOLFRAC, item)

        # Extrapolation elements
        self.model.setItem(WIDGETS.W_GUINIER_END_EX, QtGui.QStandardItem(""))
        self.model.setItem(WIDGETS.W_POROD_START_EX, QtGui.QStandardItem(""))
        self.model.setItem(WIDGETS.W_POROD_END_EX, QtGui.QStandardItem(""))
        self.model.setItem(WIDGETS.W_LOWQ_POWER_VALUE_EX, QtGui.QStandardItem(str(DEFAULT_POWER_VALUE)))
        self.model.setItem(WIDGETS.W_HIGHQ_POWER_VALUE_EX, QtGui.QStandardItem(str(DEFAULT_POWER_VALUE)))
        self.model.setItem(WIDGETS.W_ENABLE_LOWQ_EX, QtGui.QStandardItem("false"))
        self.model.setItem(WIDGETS.W_ENABLE_HIGHQ_EX, QtGui.QStandardItem("false"))
        self.model.setItem(WIDGETS.W_LOWQ_GUINIER_EX, QtGui.QStandardItem("false"))
        self.model.setItem(WIDGETS.W_LOWQ_POWER_EX, QtGui.QStandardItem("false"))
        self.model.setItem(WIDGETS.W_LOWQ_FIT_EX, QtGui.QStandardItem("false"))
        self.model.setItem(WIDGETS.W_LOWQ_FIX_EX, QtGui.QStandardItem("false"))
        self.model.setItem(WIDGETS.W_HIGHQ_FIT_EX, QtGui.QStandardItem("false"))
        self.model.setItem(WIDGETS.W_HIGHQ_FIX_EX, QtGui.QStandardItem("false"))

    def setupMapper(self) -> None:
        """Set up the mapper."""
        self.mapper: QtWidgets.QDataWidgetMapper = QtWidgets.QDataWidgetMapper(self)
        self.mapper.setOrientation(QtCore.Qt.Vertical)
        self.mapper.setModel(self.model)

        # Filename
        self.mapper.addMapping(self.txtName, WIDGETS.W_NAME)
        self.mapper.addMapping(self.txtFileName, WIDGETS.W_NAME)

        # Qmin/Qmax
        self.mapper.addMapping(self.txtTotalQMin, WIDGETS.W_QMIN)
        self.mapper.addMapping(self.txtTotalQMax, WIDGETS.W_QMAX)

        # Background
        self.mapper.addMapping(self.txtBackgd, WIDGETS.W_BACKGROUND)

        # Scale
        self.mapper.addMapping(self.txtScale, WIDGETS.W_SCALE)

        # Contrast
        self.mapper.addMapping(self.txtContrast, WIDGETS.W_CONTRAST)
        self.mapper.addMapping(self.txtContrastErr, WIDGETS.W_CONTRAST_ERR)

        # Volume fraction
        self.mapper.addMapping(self.txtVolFrac1, WIDGETS.W_VOLFRAC1)
        self.mapper.addMapping(self.txtVolFrac1Err, WIDGETS.W_VOLFRAC1_ERR)

        # Porod constant
        self.mapper.addMapping(self.txtPorodCst, WIDGETS.W_POROD_CST)
        self.mapper.addMapping(self.txtPorodCstErr, WIDGETS.W_POROD_CST_ERR)

        # Output
        self.mapper.addMapping(self.txtVolFract, WIDGETS.W_VOLUME_FRACTION)
        self.mapper.addMapping(self.txtVolFractErr, WIDGETS.W_VOLUME_FRACTION_ERR)
        self.mapper.addMapping(self.txtContrastOut, WIDGETS.W_CONTRAST_OUT)
        self.mapper.addMapping(self.txtContrastOutErr, WIDGETS.W_CONTRAST_OUT_ERR)
        self.mapper.addMapping(self.txtSpecSurf, WIDGETS.W_SPECIFIC_SURFACE)
        self.mapper.addMapping(self.txtSpecSurfErr, WIDGETS.W_SPECIFIC_SURFACE_ERR)
        self.mapper.addMapping(self.txtInvariantTot, WIDGETS.W_INVARIANT)
        self.mapper.addMapping(self.txtInvariantTotErr, WIDGETS.W_INVARIANT_ERR)

        # Extrapolation tab
        self.mapper.addMapping(self.txtGuinierEnd_ex, WIDGETS.W_GUINIER_END_EX)
        self.mapper.addMapping(self.txtPorodStart_ex, WIDGETS.W_POROD_START_EX)
        self.mapper.addMapping(self.txtPorodEnd_ex, WIDGETS.W_POROD_END_EX)
        self.mapper.addMapping(self.txtLowQPower_ex, WIDGETS.W_LOWQ_POWER_VALUE_EX)
        self.mapper.addMapping(self.txtHighQPower_ex, WIDGETS.W_HIGHQ_POWER_VALUE_EX)

        self.mapper.addMapping(self.chkLowQ_ex, WIDGETS.W_ENABLE_LOWQ_EX)
        self.mapper.addMapping(self.chkHighQ_ex, WIDGETS.W_ENABLE_HIGHQ_EX)

        self.mapper.addMapping(self.rbLowQGuinier_ex, WIDGETS.W_LOWQ_GUINIER_EX)
        self.mapper.addMapping(self.rbLowQPower_ex, WIDGETS.W_LOWQ_POWER_EX)
        self.mapper.addMapping(self.rbLowQFit_ex, WIDGETS.W_LOWQ_FIT_EX)
        self.mapper.addMapping(self.rbLowQFix_ex, WIDGETS.W_LOWQ_FIX_EX)
        self.mapper.addMapping(self.rbHighQFit_ex, WIDGETS.W_HIGHQ_FIT_EX)
        self.mapper.addMapping(self.rbHighQFix_ex, WIDGETS.W_HIGHQ_FIX_EX)

        self.mapper.toFirst()

    def setData(self, data_item: QtGui.QStandardItem = None, is_batch: bool = False) -> None:
        """
        Obtain a QStandardItem object and dissect it to get Data1D/2D.
        Pass it over to the calculator.
        """
        assert data_item is not None

        if self.txtName.text() == data_item[0].text():
            msg = "This file is already loaded in Invariant panel."
            QtWidgets.QMessageBox.warning(self, "Invariant Panel", msg)
            return

        if not isinstance(data_item, list):
            msg = "Incorrect type passed to the Invariant Perspective."
            raise AttributeError(msg)

        if not isinstance(data_item[0], QtGui.QStandardItem):
            msg = "Incorrect type passed to the Invariant Perspective."
            raise AttributeError(msg)

        # Only 1 file can be loaded
        self._model_item = data_item[0]

        # Reset plots on data change
        self.low_extrapolation_plot = None
        self.high_extrapolation_plot = None

        # Extract data on 1st child - this is the Data1D/2D component
        data = GuiUtils.dataFromItem(self._model_item)
        self.model.item(WIDGETS.W_NAME).setData(self._model_item.text())

        # Enable text boxes in the extrapolation tab
        self.enable_extrapolation_text(True)

        log_data_min = np.log(safe_float(data.x.min()))
        log_data_max = np.log(safe_float(data.x.max()))

        def fractional_position(f):
            return np.exp(f * log_data_max + (1 - f) * log_data_min)

        self.model.setItem(WIDGETS.W_GUINIER_END_EX, QtGui.QStandardItem("%.7g" % fractional_position(0.15)))
        self.model.setItem(WIDGETS.W_POROD_START_EX, QtGui.QStandardItem("%.7g" % fractional_position(0.85)))
        self.model.setItem(WIDGETS.W_POROD_END_EX, QtGui.QStandardItem("%.7g" % Q_MAXIMUM))

        # update GUI and model with info from loaded data
        self.updateGuiFromFile(data=data)

        self.slider.extrapolation_parameters = self.extrapolation_parameters
        self.slider.setEnabled(True)

        self.check_status()

        self.tabWidget.setCurrentIndex(0)

        self._manager.filesWidget.newPlot()

        self.mapper.toFirst()

    def removeData(self, data_list: list | None = None) -> None:
        """Remove the existing data reference from the Invariant Perspective."""
        if not data_list or self._model_item not in data_list:
            return

        # close all plots associated with this data before clearing the item
        if self._model_item is not None:
            self._manager.filesWidget.closePlotsForItem(self._model_item)

        self._data = None
        self._model_item = None
        self.low_extrapolation_plot = None
        self.high_extrapolation_plot = None
        self._path = ""
        self.txtName.setText("")
        self.txtFileName.setText("")
        self._porod = None
        self._porod_err = None
        # Pass an empty dictionary to set all inputs to their default values
        self.updateFromParameters({})
        # Disable buttons to return to base state
        self.check_status()

    def updateGuiFromFile(self, data: Data1D = None) -> None:
        """Update display in GUI and plot."""
        self._data = data

        # plot loaded file
        if not isinstance(self._data, Data1D):
            msg: str = "Invariant cannot be computed with 2D data."
            raise ValueError(msg)

        try:
            name: str = data.name
        except (AttributeError, TypeError):
            msg: str = "No data name chosen."
            raise ValueError(msg)
        try:
            qmin: float = min(self._data.x)
            qmax: float = max(self._data.x)
        except (AttributeError, TypeError, ValueError):
            msg: str = "Unable to find q min/max of data named %s" % data.name
            raise ValueError(msg)

        # update model with input form files: name, qmin, qmax
        self.model.item(WIDGETS.W_NAME).setText(name)
        self.model.item(WIDGETS.W_QMIN).setText(str(qmin))
        self.model.item(WIDGETS.W_QMAX).setText(str(qmax))
        self._path = data.filename

        self._calculator = invariant.InvariantCalculator(
            data=self._data, background=self._background, scale=self._scale
        )

    def serializeAll(self) -> dict:
        """
        Serialize the invariant state so data can be saved.
        Invariant is not batch-ready so this will only effect a single page.
        :return: {data-id: {self.name: {invariant-state}}}
        """
        return self.serializeCurrentPage()

    def serializeCurrentPage(self) -> dict:
        """
        Serialize and return a dictionary of {data_id: invariant-state}.
        Return empty dictionary if no data.
        :return: {data-id: {self.name: {invariant-state}}}
        """
        state: dict = {}
        if self._data:
            tab_data: dict = self.serializePage()
            data_id: str = tab_data.pop("data_id", "")
            state[data_id] = {"invar_params": tab_data}
        return state

    def serializePage(self) -> dict:
        """
        Serializes full state of this invariant page.
        Called by Save Analysis.
        :return: {invariant-state}
        """
        # Get all parameters from page
        param_dict: dict = self.serializeState()
        if self._data:
            param_dict["data_name"] = str(self._data.name)
            param_dict["data_id"] = str(self._data.id)
        return param_dict

    def serializeState(self) -> dict:
        """
        Collects all active params into a dictionary of {name: value}.
        :return: {name: value}
        """
        # Be sure model has been updated
        self.update_from_model()
        return {
            "vol_fraction": self.txtVolFract.text(),
            "vol_fraction_err": self.txtVolFractErr.text(),
            "contrast_out": self.txtContrastOut.text(),
            "contrast_out_err": self.txtContrastOutErr.text(),
            "specific_surface": self.txtSpecSurf.text(),
            "specific_surface_err": self.txtSpecSurfErr.text(),
            "invariant_total": self.txtInvariantTot.text(),
            "invariant_total_err": self.txtInvariantTotErr.text(),
            "background": self.txtBackgd.text(),
            "contrast": self.txtContrast.text(),
            "contrast_err": self.txtContrastErr.text(),
            "scale": self.txtScale.text(),
            "porod": self.txtPorodCst.text(),
            "volfrac1": self.txtVolFrac1.text(),
            "volfrac1_err": self.txtVolFrac1Err.text(),
            "enable_contrast": self.rbContrast.isChecked(),
            "enable_volfrac": self.rbVolFrac.isChecked(),
            "total_q_min": self.txtTotalQMin.text(),
            "total_q_max": self.txtTotalQMax.text(),
            "guinier_end_low_q_ex": self.txtGuinierEnd_ex.text(),
            "porod_start_high_q_ex": self.txtPorodStart_ex.text(),
            "porod_end_high_q_ex": self.txtPorodEnd_ex.text(),
            "power_low_q_ex": self.txtLowQPower_ex.text(),
            "power_high_q_ex": self.txtHighQPower_ex.text(),
            "enable_low_q_ex": self.chkLowQ_ex.isChecked(),
            "enable_high_q_ex": self.chkHighQ_ex.isChecked(),
            "low_q_guinier_ex": self.rbLowQGuinier_ex.isChecked(),
            "low_q_power_ex": self.rbLowQPower_ex.isChecked(),
            "low_q_fit_ex": self.rbLowQFit_ex.isChecked(),
            "low_q_fix_ex": self.rbLowQFix_ex.isChecked(),
            "high_q_fit_ex": self.rbHighQFit_ex.isChecked(),
            "high_q_fix_ex": self.rbHighQFix_ex.isChecked(),
        }

    def updateFromParameters(self, params: dict) -> None:
        """
        Called by Open Project and Open Analysis.
        :param params: {param_name: value}
        :return: None
        """
        # Params should be a dictionary
        if not isinstance(params, dict):
            c_name = params.__class__.__name__
            msg = "Invariant.updateFromParameters expects a dictionary"
            raise TypeError(f"{msg}: {c_name} received")

        # Assign values to 'Invariant' tab inputs - use defaults if not found
        self.txtTotalQMin.setText(str(params.get("total_q_min", "0.0")))
        self.txtTotalQMax.setText(str(params.get("total_q_max", "0.0")))
        self.txtVolFract.setText(str(params.get("vol_fraction", "")))
        self.txtVolFractErr.setText(str(params.get("vol_fraction_err", "")))
        self.txtContrastOut.setText(str(params.get("contrast_out", "")))
        self.txtContrastOutErr.setText(str(params.get("contrast_out_err", "")))
        self.txtSpecSurf.setText(str(params.get("specific_surface", "")))
        self.txtSpecSurfErr.setText(str(params.get("specific_surface_err", "")))
        self.txtInvariantTot.setText(str(params.get("invariant_total", "")))
        self.txtInvariantTotErr.setText(str(params.get("invariant_total_err", "")))
        self.txtBackgd.setText(str(params.get("background", "0.0")))
        self.txtScale.setText(str(params.get("scale", "1.0")))
        self.txtContrast.setText(str(params.get("contrast", "")))
        self.txtContrastErr.setText(str(params.get("contrast_err", "0.0")))
        self.txtPorodCst.setText(str(params.get("porod", "0.0")))
        self.txtVolFrac1.setText(str(params.get("volfrac1", "0.0")))
        self.txtVolFrac1Err.setText(str(params.get("volfrac1_err", "0.0")))

        # Extrapolation tab - use new _ex suffix variables
        self.txtGuinierEnd_ex.setText(str(params.get("guinier_end_low_q_ex", "")))
        self.txtPorodStart_ex.setText(str(params.get("porod_start_high_q_ex", "")))
        self.txtPorodEnd_ex.setText(str(params.get("porod_end_high_q_ex", "")))
        self.txtLowQPower_ex.setText(str(params.get("power_low_q_ex", DEFAULT_POWER_VALUE)))
        self.txtHighQPower_ex.setText(str(params.get("power_high_q_ex", DEFAULT_POWER_VALUE)))
        self.chkLowQ_ex.setChecked(params.get("enable_low_q_ex", False))
        self.chkHighQ_ex.setChecked(params.get("enable_high_q_ex", False))
        self.rbLowQGuinier_ex.setChecked(params.get("low_q_guinier_ex", False))
        self.rbLowQPower_ex.setChecked(params.get("low_q_power_ex", False))
        self.rbLowQFit_ex.setChecked(params.get("low_q_fit_ex", False))
        self.rbLowQFix_ex.setChecked(params.get("low_q_fix_ex", False))
        self.rbHighQFit_ex.setChecked(params.get("high_q_fit_ex", False))
        self.rbHighQFix_ex.setChecked(params.get("high_q_fix_ex", False))

        # Update once all inputs are changed
        self.update_from_model()

    def allowBatch(self) -> bool:
        """Tell the caller that we don't accept multiple data instances."""
        return False

    def allowSwap(self) -> bool:
        """Tell the caller that we can't swap data."""
        return False

    def reset(self):
        """Reset the fitting perspective to an empty state."""
        self.removeData([self._model_item] if self._model_item else None)
