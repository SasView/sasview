# global
import copy
import logging

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets
from twisted.internet import reactor, threads

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Plotting import PlotterData
from sas.qtgui.Plotting.PlotterData import Data1D, DataRole
from sas.qtgui.Utilities.ExtrapolationSlider import ExtrapolationSlider

# sas-global
from sas.sascalc.invariant import invariant
from sas.sascalc.util import ExtrapolationParameters

# local
from ..perspective import Perspective
from .InvariantDetails import DetailsDialog
from .InvariantUtils import WIDGETS, safe_float
from .UI.TabbedInvariantUI import Ui_tabbedInvariantUI

# The minimum q-value to be used when extrapolating
Q_MINIMUM = 1e-5
# The maximum q-value to be used when extrapolating
Q_MAXIMUM = 10
# Default number of points of interpolation: high and low range
NPOINTS_Q_INTERP = 10
# Default power law for interpolation
DEFAULT_POWER_VALUE = 4

# Background of line edits if settings OK or wrong
BG_DEFAULT = ""
BG_RED = "background-color: rgb(244, 170, 164);"

logger = logging.getLogger(__name__)


class InvariantWindow(QtWidgets.QDialog, Ui_tabbedInvariantUI, Perspective):
    # The controller which is responsible for managing signal slots connections
    # for the gui and providing an interface to the data model.

    name = "Invariant"
    ext = "inv"

    @property
    def title(self):
        """Perspective name"""
        return "Invariant Perspective"

    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)

        self.setWindowTitle(self.title)

        # GUI components
        self.parent = parent
        self._manager = parent
        self._reactor: reactor = reactor
        self._model_item: QtGui.QStandardItem = QtGui.QStandardItem()
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

        # Initial input params
        self._background: float = 0.0
        self._scale: float = 1.0
        self._contrast: float | None = None
        self._porod: float | None = None
        self._volfrac1: float | None = None
        self._volfrac2: float | None = None

        # New extrapolation options
        self._low_extrapolate: bool = False
        self._low_guinier: bool = True
        self._low_fit: bool = False
        self._low_points: int = NPOINTS_Q_INTERP
        self._low_power_value: float = DEFAULT_POWER_VALUE
        self._high_extrapolate: bool = False
        self._high_fit: bool = False
        self._high_points: int = NPOINTS_Q_INTERP
        self._high_power_value: float | None = DEFAULT_POWER_VALUE

        # Define plots
        self.high_extrapolation_plot: PlotterData | None = None
        self.low_extrapolation_plot: PlotterData | None = None
        self.no_extrapolation_plot: PlotterData | None = None

        # Slider
        self.slider = ExtrapolationSlider(lower_label="Low-Q", upper_label="High-Q")
        self.sliderLayout.insertWidget(1, self.slider)

        # no reason to have this widget resizable
        self.resize(self.minimumSizeHint())

        # Modify font in order to display Angstrom symbol correctly
        new_font = 'font-family: -apple-system, "Helvetica Neue", "Ubuntu";'
        self.lblTotalQUnits.setStyleSheet(new_font)
        self.lblSpecificSurfaceUnits.setStyleSheet(new_font)
        self.lblInvariantTotalQUnits.setStyleSheet(new_font)
        self.lblContrastUnits.setStyleSheet(new_font)
        self.lblPorodCstUnits.setStyleSheet(new_font)
        self.lblBackgroundUnits.setStyleSheet(new_font)

        # To remove blue square around line edits
        self.txtBackgd.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)
        self.txtContrast.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)
        self.txtScale.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)
        self.txtPorodCst.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)

        # Let's choose the Standard Item Model
        self.model = QtGui.QStandardItemModel(self)

        # Connect buttons to slots
        # Needs to be done early so default values propagate properly
        self.setupSlots()

        # Set up the model
        self.setupModel()

        # Set up the mapper
        self.setupMapper()

        # Default enablement
        self.cmdCalculate.setEnabled(False)

        # Validator: double
        self.txtBackgd.setValidator(GuiUtils.DoubleValidator())
        self.txtContrast.setValidator(GuiUtils.DoubleValidator())
        self.txtScale.setValidator(GuiUtils.DoubleValidator())
        self.txtVolFrac1.setValidator(GuiUtils.DoubleValidator())
        self.txtVolFrac2.setValidator(GuiUtils.DoubleValidator())

        # Start with all Extrapolation options disabled
        self.enable_extrapolation_options(False)

        # Set progress bars to 0
        self.update_progress_bars()

        # Default to using contrast for volume fraction
        self.rbContrast.setChecked(True)
        self.contrastToggle(True)

        self.tabWidget.setCurrentIndex(0)

        # Allow calculation if there is data
        self.allow_calculation()

        # Go to the first data item
        self.mapper.toFirst()

    @property
    def extrapolation_parameters(self) -> ExtrapolationParameters | None:
        if self._data is not None:
            return ExtrapolationParameters(
                safe_float(Q_MINIMUM),
                safe_float(self.model.item(WIDGETS.W_GUINIER_END_EX).text()),
                safe_float(self.model.item(WIDGETS.W_POROD_START_EX).text()),
                safe_float(self.model.item(WIDGETS.W_POROD_END_EX).text()),
                safe_float(Q_MAXIMUM),
            )
        else:
            return None

    def enable_extrapolation_text(self, state: bool) -> None:
        """Enable or disable the text fields in the extrapolation tab"""
        self.txtGuinierEnd_ex.setEnabled(state)
        self.txtPorodStart_ex.setEnabled(state)
        self.txtPorodEnd_ex.setEnabled(state)

    def enable_extrapolation_options(self, state: bool) -> None:
        """Enable or disable the options in the extrapolation tab"""
        self.rbLowQGuinier_ex.setEnabled(state)
        self.rbLowQPower_ex.setEnabled(state)
        self.rbLowQFit_ex.setEnabled(state)
        self.rbLowQFix_ex.setEnabled(state)
        self.rbHighQFit_ex.setEnabled(state)
        self.rbHighQFix_ex.setEnabled(state)
        self.txtLowQPower_ex.setEnabled(self.rbLowQFix_ex.isChecked())
        self.txtHighQPower_ex.setEnabled(self.rbHighQFix_ex.isChecked())

    def get_low_q_extrapolation_upper_limit(self):
        q_value = self._data.x[int(self._low_points) - 1]
        return q_value

    def set_low_q_extrapolation_upper_limit(self, value):
        self._low_points = (np.abs(self._data.x - value)).argmin() + 1

    def get_high_q_extrapolation_lower_limit(self):
        q_value = self._data.x[len(self._data.x) - int(self._high_points) - 1]
        return q_value

    def set_high_q_extrapolation_lower_limit(self, value):
        self._high_points = len(self._data.x) - (np.abs(self._data.x - value)).argmin() + 1

    def enableStatus(self) -> None:
        """Enable the status button"""
        self.cmdStatus.setEnabled(True)

    def setClosable(self, value: bool = True) -> None:
        """Allow outsiders close this widget"""
        self._allow_close = value

    def isSerializable(self):
        """
        Tell the caller that this perspective writes its state
        """
        return True

    def closeEvent(self, event):
        """
        Overwrite QDialog close method to allow for custom widget close
        """
        if self._allow_close:
            # reset the closability flag
            self.setClosable(value=False)
            # Tell the MdiArea to close the container if it is visible
            if self.parentWidget():
                self.parentWidget().close()
            event.accept()
        else:
            event.ignore()
            # Maybe we should just minimize
            self.setWindowState(QtCore.Qt.WindowMinimized)

    def update_from_model(self) -> None:
        """Update the globals based on the data in the model"""
        self._background = float(self.model.item(WIDGETS.W_BACKGROUND).text())
        if self.model.item(WIDGETS.W_CONTRAST).text() != "None" and self.model.item(WIDGETS.W_CONTRAST).text() != "":
            self._contrast = float(self.model.item(WIDGETS.W_CONTRAST).text())
        self._scale = float(self.model.item(WIDGETS.W_SCALE).text())
        if self.model.item(WIDGETS.W_POROD_CST).text() != "None" and self.model.item(WIDGETS.W_POROD_CST).text() != "":
            self._porod = float(self.model.item(WIDGETS.W_POROD_CST).text())
        if self.model.item(WIDGETS.W_VOLFRAC1).text() != "None" and self.model.item(WIDGETS.W_VOLFRAC1).text() != "":
            self._volfrac1 = float(self.model.item(WIDGETS.W_VOLFRAC1).text())
        if self.model.item(WIDGETS.W_VOLFRAC2).text() != "None" and self.model.item(WIDGETS.W_VOLFRAC2).text() != "":
            self._volfrac2 = float(self.model.item(WIDGETS.W_VOLFRAC2).text())

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
        self.cmdCalculate.setText("Calculating...")
        self.cmdCalculate.setEnabled(False)

        # Send the calculations to separate thread.
        d = threads.deferToThread(self.calculate_thread, extrapolation)

        # Add deferred callback for call return
        d.addCallback(self.deferredPlot)
        d.addErrback(self.on_calculation_failed)

    def on_calculation_failed(self, reason: Exception) -> None:
        """Handle calculation failure"""
        logger.error(f"calculation failed: {reason}")
        self.allow_calculation()

    def deferredPlot(self, model: QtGui.QStandardItemModel) -> None:
        """Run the GUI/model update in the main thread"""
        reactor.callFromThread(lambda: self.plot_result(model))
        self.allow_calculation()

    def allow_calculation(self) -> None:
        """Enable the calculate button if either volume fraction or contrast is selected"""
        if self._data is None:
            self.cmdCalculate.setEnabled(False)
            self.cmdCalculate.setText("Calculate (No data)")
            return

        if self.rbVolFrac.isChecked() and self.txtVolFrac1.text() != "":
            self.cmdCalculate.setEnabled(True)
            self.cmdCalculate.setText("Calculate")
        elif self.rbContrast.isChecked() and self.txtContrast.text() != "":
            self.cmdCalculate.setEnabled(True)
            self.cmdCalculate.setText("Calculate")
        else:
            self.cmdCalculate.setEnabled(False)
            self.cmdCalculate.setText("Calculate (Enter volume fraction or contrast)")

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
            self.low_extrapolation_plot.slider_low_q_input = self.extrapolation_parameters.data_q_min
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
        """On demand update of the details widget"""
        if self.detailsDialog.isVisible():
            self.onStatus()

    def calculate_thread(self, extrapolation: str) -> None:
        """Perform Invariant calculations."""
        # Get most recent values from GUI and model
        self.update_from_model()

        # Define base message
        msg = ""

        # Set base Q* values to 0.0
        qstar_low: float | None = 0.0
        qstar_low_err: float = 0.0
        qstar_high: float | None = 0.0
        qstar_high_err: float = 0.0

        temp_data = copy.deepcopy(self._data)

        calculation_failed: bool = False
        low_calculation_pass: bool = False
        high_calculation_pass: bool = False

        # Update calculator with background, scale, and data values
        self._calculator.background = self._background
        self._calculator.scale = self._scale
        self._calculator.set_data(temp_data)

        # Low Q extrapolation calculations
        if self._low_extrapolate:
            function_low = "power_law"
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
                if self._data and self.txtGuinierEnd_ex.text():
                    # Get the Q value where Guinier extrapolation should end
                    q_end_val = float(self.txtGuinierEnd_ex.text())

                    # Find the index of the data point closest to q_end_val
                    n_pts = int(np.abs(self._data.x - q_end_val).argmin()) + 1

                    # Ensure n_pts is within valid bounds
                    n_pts = max(1, min(n_pts, len(self._data.x)))

                    if n_pts != self._low_points:
                        self._low_points = n_pts

            except (ValueError, AttributeError, TypeError) as ex:
                logger.warning(f"Low-q Guinier end calculation failed: {str(ex)}")

            self._calculator.set_extrapolation(
                range="low", npts=int(self._low_points), function=function_low, power=self._low_power_value
            )

            try:
                qmin_ext = float(self.extrapolation_parameters.point_1)
                qmin = None if qmin_ext > self._data.x[0] else qmin_ext
                qstar_low, qstar_low_err = self._calculator.get_qstar_low(qmin)
                low_calculation_pass = True
            except Exception as ex:
                logger.warning(f"Low-q calculation failed: {str(ex)}")
                qstar_low = "ERROR"
                qstar_low_err = "ERROR"

        if self.low_extrapolation_plot and not low_calculation_pass:
            # Remove the existing extrapolation plot
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

            # Convert slider/q-value (Porod start) to number of points if available
            try:
                if self._data and self.txtPorodStart_ex.text():
                    # Get the Q value where Porod extrapolation should start
                    q_start_val = float(self.txtPorodStart_ex.text())

                    # Find the index of the data point closest to q_start_val
                    idx = int((np.abs(self._data.x - q_start_val)).argmin())

                    # Compute number of points from that index to the end
                    n_pts_high: int = len(self._data.x) - idx

                    # Ensure n_pts_high is within valid bounds
                    n_pts_high = max(1, min(n_pts_high, len(self._data.x)))

                    if n_pts_high != self._high_points:
                        self._high_points = n_pts_high

            except (ValueError, AttributeError, TypeError) as ex:
                logger.debug(f"Could not convert Porod start to n_pts_high: {ex}")

            self._calculator.set_extrapolation(
                range="high", npts=int(self._high_points), function=function_high, power=self._high_power_value
            )

            try:
                qmax_ext: float = float(self.extrapolation_parameters.point_3)
                qmax: float | None = None if qmax_ext < self._data.x[int(len(self._data.x) - 1)] else qmax_ext
                qstar_high, qstar_high_err = self._calculator.get_qstar_high(qmax)
                high_calculation_pass: bool = True
            except Exception as ex:
                logger.warning(f"High-q calculation failed: {str(ex)}")
                qstar_high = "ERROR"
                qstar_high_err = "ERROR"

        if self.high_extrapolation_plot and not high_calculation_pass:
            # Remove the existing extrapolation plot
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
        try:
            qstar_data, qstar_data_err = self._calculator.get_qstar_with_error()
        except Exception as ex:
            msg += str(ex)
            calculation_failed: bool = True
            qstar_data: float | str = "ERROR"
            qstar_data_err: float | str = "ERROR"
        reactor.callFromThread(self.update_model_from_thread, WIDGETS.D_DATA_QSTAR, qstar_data)
        reactor.callFromThread(self.update_model_from_thread, WIDGETS.D_DATA_QSTAR_ERR, qstar_data_err)

        # Volume Fraction calculations
        volume_fraction = ""
        volume_fraction_error = ""

        if self.rbContrast.isChecked() and self._contrast:
            try:
                volume_fraction, volume_fraction_error = self._calculator.get_volume_fraction_with_error(
                    self._contrast, extrapolation=extrapolation
                )
            except (ValueError, ZeroDivisionError, RuntimeError, AttributeError, TypeError) as ex:
                calculation_failed = True
                msg += str(ex)
                volume_fraction = "ERROR"
                volume_fraction_error = "ERROR"

        reactor.callFromThread(self.update_model_from_thread, WIDGETS.W_VOLUME_FRACTION, volume_fraction)
        reactor.callFromThread(self.update_model_from_thread, WIDGETS.W_VOLUME_FRACTION_ERR, volume_fraction_error)

        # Contrast calculations
        contrast_out: float | str = ""
        contrast_out_error: float | str = ""

        if self.rbVolFrac.isChecked() and self._volfrac1:
            try:
                contrast_out, contrast_out_error = self._calculator.get_contrast_with_error(
                    self._volfrac1, extrapolation=extrapolation
                )
            except (ValueError, ZeroDivisionError, RuntimeError, AttributeError, TypeError) as ex:
                calculation_failed: bool = True
                msg += str(ex)
                contrast_out: float | str = "ERROR"
                contrast_out_error: float | str = "ERROR"

        reactor.callFromThread(self.update_model_from_thread, WIDGETS.W_CONTRAST_OUT, contrast_out)
        reactor.callFromThread(self.update_model_from_thread, WIDGETS.W_CONTRAST_OUT_ERR, contrast_out_error)

        # Surface Error calculations
        surface: float | str | None = ""
        surface_error: float | str | None = ""

        if self._porod:
            # Use calculated contrast if in volume fraction mode, otherwise use input contrast
            contrast_for_surface = contrast_out if self.rbVolFrac.isChecked() and self._volfrac1 else self._contrast
            if contrast_for_surface:
                try:
                    surface, surface_error = self._calculator.get_surface_with_error(contrast_for_surface, self._porod)
                except (ValueError, ZeroDivisionError, RuntimeError, AttributeError, TypeError) as ex:
                    calculation_failed: bool = True
                    msg += str(ex)
                    surface: float | str = "ERROR"
                    surface_error: float | str = "ERROR"

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
            qmin_ext: float = float(self.extrapolation_parameters.data_q_min)
            extrapolated_data = self._calculator.get_extra_data_low(self._low_points, q_start=qmin_ext)
            power_low: float | None = self._calculator.get_extrapolation_power(range="low")

            # Plot the chart
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
            # for presentation in InvariantDetails
            qmax_plot: float = float(self.extrapolation_parameters.point_3)

            power_high: float | None = self._calculator.get_extrapolation_power(range="high")
            high_out_data = self._calculator.get_extra_data_high(q_end=qmax_plot, npts=500)

            # Plot the chart
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
            qstar_high: float | None = 0.0
            qstar_high_err: float = 0.0
        if qstar_low == "ERROR":
            qstar_low: float | None = 0.0
            qstar_low_err: float = 0.0
        qstar_total: float = qstar_data + qstar_low + qstar_high
        qstar_total_error: float = np.sqrt(
            qstar_data_err * qstar_data_err + qstar_low_err * qstar_low_err + qstar_high_err * qstar_high_err
        )
        reactor.callFromThread(self.update_model_from_thread, WIDGETS.W_INVARIANT, qstar_total)
        reactor.callFromThread(self.update_model_from_thread, WIDGETS.W_INVARIANT_ERR, qstar_total_error)

        return self.model

    def update_model_from_thread(self, row: int, value: float) -> None:
        """Update the model in the main thread"""
        try:
            # Use scientific notation for very small or very large values
            if abs(value) < 0.001 or abs(value) > 10000:
                formatted_value: str = f"{value:.4e}"
            else:
                formatted_value: str = str(round(value, 3))
        except (TypeError, ValueError):
            formatted_value: str = str(value)

        item = QtGui.QStandardItem(formatted_value)
        self.model.setItem(row, item)

        # Don't call mapper.toLast() if we're updating power values
        # as this can reset radio button states
        if row not in [WIDGETS.W_LOWQ_POWER_VALUE_EX, WIDGETS.W_HIGHQ_POWER_VALUE_EX]:
            self.mapper.toLast()

        # Update progress bars if we're updating Q* values
        if row in [WIDGETS.D_DATA_QSTAR, WIDGETS.D_LOW_QSTAR, WIDGETS.D_HIGH_QSTAR]:
            self.update_progress_bars()

    def onStatus(self):
        """Display Invariant Details panel when clicking on Status button"""
        self.detailsDialog.setModel(self.model)
        self.detailsDialog.showDialog()
        self.cmdStatus.setEnabled(False)

    def onHelp(self):
        """Display help when clicking on Help button"""
        treeLocation: str = "/user/qtgui/Perspectives/Invariant/invariant_help.html"
        self.parent.showHelp(treeLocation)

    def setupSlots(self):
        """Setup slots for the buttons and checkboxes"""
        self.cmdCalculate.clicked.connect(self.calculate_invariant)
        self.cmdStatus.clicked.connect(self.onStatus)
        self.cmdHelp.clicked.connect(self.onHelp)

        # slots for the volume fraction and contrast radio buttons
        self.rbVolFrac.toggled.connect(self.volFracToggle)
        self.rbContrast.toggled.connect(self.contrastToggle)

        # update model from gui editing by users
        self.txtBackgd.editingFinished.connect(self.updateFromGui)
        self.txtScale.editingFinished.connect(self.updateFromGui)
        self.txtContrast.editingFinished.connect(self.updateFromGui)
        self.txtPorodCst.editingFinished.connect(self.updateFromGui)
        self.txtVolFrac1.editingFinished.connect(self.updateFromGui)
        self.txtVolFrac1.editingFinished.connect(self.checkVolFrac)
        self.txtVolFrac2.editingFinished.connect(self.updateFromGui)

        # Extrapolation parameters
        # Q range fields
        self.txtGuinierEnd_ex.editingFinished.connect(self.on_extrapolation_text_changed_1)
        self.txtPorodStart_ex.editingFinished.connect(self.on_extrapolation_text_changed_2)
        self.txtPorodEnd_ex.editingFinished.connect(self.on_extrapolation_text_changed_3)
        self.txtGuinierEnd_ex.setValidator(GuiUtils.DoubleValidator())
        self.txtPorodStart_ex.setValidator(GuiUtils.DoubleValidator())
        self.txtPorodEnd_ex.setValidator(GuiUtils.DoubleValidator())
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

        # Slider values
        self.slider.valueEdited.connect(self.on_extrapolation_slider_changed)

    # Extrapolation Options
    def on_extrapolation_lowq_check_changed(self) -> None:
        """Handle the state change of the low Q extrapolation checkbox"""
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
        """Handle the state change of the high Q extrapolation checkbox"""
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
        """If Power is selected, Fit and Fix radio buttons are visible"""
        if self.rbLowQPower_ex.isChecked():
            self.showLowQPowerOptions(True)
            # Set default to Fit
            self.rbLowQFit_ex.setChecked(True)
        else:
            self.showLowQPowerOptions(False)

        # Update model to reflect the radio button states
        self.model.setItem(
            WIDGETS.W_LOWQ_GUINIER_EX, QtGui.QStandardItem(str(self.rbLowQGuinier_ex.isChecked()).lower())
        )
        self.model.setItem(WIDGETS.W_LOWQ_POWER_EX, QtGui.QStandardItem(str(self.rbLowQPower_ex.isChecked()).lower()))

        self.update_from_model()

    def showLowQPowerOptions(self, state: bool) -> None:
        """Show and enable the Fit and Fix options if Power is selected"""
        self.rbLowQFit_ex.setEnabled(state)
        self.rbLowQFix_ex.setEnabled(state)
        if self.rbLowQFix_ex.isChecked():
            self.txtLowQPower_ex.setEnabled(True)
        else:
            self.txtLowQPower_ex.setEnabled(False)

        self.update_from_model()

    def highFitAndFixToggle_ex(self) -> None:
        """Enable editing of power exponent if Fix for high Q is checked"""
        if self.rbHighQFix_ex.isChecked():
            self.txtHighQPower_ex.setEnabled(True)
        else:
            self.txtHighQPower_ex.setEnabled(False)

        # Update model to reflect the radio button states
        self.model.setItem(WIDGETS.W_HIGHQ_FIT_EX, QtGui.QStandardItem(str(self.rbHighQFit_ex.isChecked()).lower()))
        self.model.setItem(WIDGETS.W_HIGHQ_FIX_EX, QtGui.QStandardItem(str(self.rbHighQFix_ex.isChecked()).lower()))

        self.update_from_model()

    def lowFitAndFixToggle_ex(self) -> None:
        """Enable editing of power exponent if Fix for high Q is checked"""
        if self.rbLowQFix_ex.isChecked():
            self.txtLowQPower_ex.setEnabled(True)
        else:
            self.txtLowQPower_ex.setEnabled(False)

        # Update model to reflect the radio button states
        self.model.setItem(WIDGETS.W_LOWQ_FIT_EX, QtGui.QStandardItem(str(self.rbLowQFit_ex.isChecked()).lower()))
        self.model.setItem(WIDGETS.W_LOWQ_FIX_EX, QtGui.QStandardItem(str(self.rbLowQFix_ex.isChecked()).lower()))

        self.update_from_model()

    def on_extrapolation_slider_changed(self, state: ExtrapolationParameters) -> None:
        format_string: str = "%.7g"
        self.model.setItem(WIDGETS.W_GUINIER_END_EX, QtGui.QStandardItem(format_string % state.point_1))
        self.model.setItem(WIDGETS.W_POROD_START_EX, QtGui.QStandardItem(format_string % state.point_2))
        self.model.setItem(WIDGETS.W_POROD_END_EX, QtGui.QStandardItem(format_string % state.point_3))
        self.notify_extrapolation_text_box_validity(state, show_dialog=True)

    def on_extrapolation_text_changed_1(self) -> None:
        value: str = self.txtGuinierEnd_ex.text()
        params = self.extrapolation_parameters._replace(point_1=safe_float(value))
        self.slider.extrapolation_parameters = params
        self.notify_extrapolation_text_box_validity(params, show_dialog=True)

    def on_extrapolation_text_changed_2(self) -> None:
        value: str = self.txtPorodStart_ex.text()
        params = self.extrapolation_parameters._replace(point_2=safe_float(value))
        self.slider.extrapolation_parameters = params
        self.notify_extrapolation_text_box_validity(params, show_dialog=True)

    def on_extrapolation_text_changed_3(self) -> None:
        value: str = self.txtPorodEnd_ex.text()
        params = self.extrapolation_parameters._replace(point_3=safe_float(value))
        self.slider.extrapolation_parameters = params
        self.notify_extrapolation_text_box_validity(params, show_dialog=True)

    def notify_extrapolation_text_box_validity(
        self, params: ExtrapolationParameters, show_dialog: bool = False
    ) -> None:
        # Round values to 8 significant figures to avoid floating point precision issues
        p1: float = float(f"{params.point_1:.7g}")  # Guinier end
        p2: float = float(f"{params.point_2:.7g}")  # Porod start
        p3: float = float(f"{params.point_3:.7g}")  # Porod end
        data_q_min: float = float(f"{self._data.x.min():.7g}")  # Actual data min
        data_q_max: float = float(f"{self._data.x.max():.7g}")  # Actual data max
        qmax: float = Q_MAXIMUM

        # Determine validity flags such that data_q_min < point_1 < point_2 < point_3 < qmax
        # Also p2 < data_q_max so that Porod start is within data range
        invalid_1: bool = p1 <= data_q_min or p1 >= p2
        invalid_2: bool = p2 <= p1 or p2 >= p3 or p2 >= data_q_max
        invalid_3: bool = p3 <= p2 or p3 > qmax

        # Make the background red if the text box is invalid
        self.txtGuinierEnd_ex.setStyleSheet(BG_RED if invalid_1 else BG_DEFAULT)
        self.txtPorodStart_ex.setStyleSheet(BG_RED if invalid_2 else BG_DEFAULT)
        self.txtPorodEnd_ex.setStyleSheet(BG_RED if invalid_3 else BG_DEFAULT)

        # If requested, show dialog if values are out of range
        if show_dialog and (p1 <= data_q_min or p3 > qmax):
            msg = "The slider values are out of range.\n"
            msg += f"The minimum value is {data_q_min:.7g} and the maximum value is {qmax:.7g}"
            dialog = QtWidgets.QMessageBox(self, text=msg)
            dialog.setWindowTitle("Value out of range")
            dialog.setStandardButtons(QtWidgets.QMessageBox.Ok)
            dialog.exec_()
            if p1 < data_q_min:
                self.txtGuinierEnd_ex.setText(f"{data_q_min + 1e-7:.7g}")
                self.on_extrapolation_text_changed_1()
            if p3 > qmax:
                self.txtPorodEnd_ex.setText(f"{qmax:.7g}")
                self.on_extrapolation_text_changed_3()

        # Show dialog if p2 is greater than data max
        if show_dialog and (p2 > data_q_max):
            msg = "The High-Q start value cannot be greater than the maximum Q value of the data.\n"
            msg += f"The maximum Q value of the data is {data_q_max:.7g}"
            dialog = QtWidgets.QMessageBox(self, text=msg)
            dialog.setWindowTitle("Invalid High-Q Start Value")
            dialog.setStandardButtons(QtWidgets.QMessageBox.Ok)
            dialog.exec_()
            self.txtPorodStart_ex.setText(str(data_q_max - 1e-7))
            self.on_extrapolation_text_changed_2()

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
        panel
        """
        # name to search in DataExplorer
        if "Low" in str(self.sender().text()):
            name: str = "Low-Q extrapolation"
        if "High" in str(self.sender().text()):
            name: str = "High-Q extrapolation"

        GuiUtils.updateModelItemStatus(self._manager.filesWidget.model, self._path, name, self.sender().checkState())

    def checkVolFrac(self) -> None:
        """Check if volfrac1, volfrac2 are strictly between 0 and 1, and volfrac1 + volfrac2 = 1"""
        if self.txtVolFrac1.text() and self.txtVolFrac2.text():
            try:
                vf1 = float(self.txtVolFrac1.text())
                vf2 = float(self.txtVolFrac2.text())
            except ValueError:
                self.txtVolFrac1.setStyleSheet(BG_RED)
                self.txtVolFrac2.setStyleSheet(BG_RED)
                self.cmdCalculate.setEnabled(False)
                msg = "Volume fractions must be valid numbers."
                dialog = QtWidgets.QMessageBox(self, text=msg)
                dialog.setWindowTitle("Invalid Volume Fraction")
                dialog.setIcon(QtWidgets.QMessageBox.Warning)
                dialog.setStandardButtons(QtWidgets.QMessageBox.Ok)
                dialog.exec_()
                return
            if 0 < vf1 < 1 and 0 < vf2 < 1 and round(vf1 + vf2, 3) == 1.0:
                self.txtVolFrac1.setStyleSheet(BG_DEFAULT)
                self.txtVolFrac2.setStyleSheet(BG_DEFAULT)
                self.allow_calculation()
            else:
                self.txtVolFrac1.setStyleSheet(BG_RED)
                self.txtVolFrac2.setStyleSheet(BG_RED)
                self.cmdCalculate.setEnabled(False)
                msg = "Volume fractions must be between 0 and 1, and their sum must equal 1."
                dialog = QtWidgets.QMessageBox(self, text=msg)
                dialog.setWindowTitle("Invalid Volume Fraction")
                dialog.setIcon(QtWidgets.QMessageBox.Warning)
                dialog.setStandardButtons(QtWidgets.QMessageBox.Ok)
                dialog.exec_()

    def updateFromGui(self) -> None:
        """Update model when new user inputs"""

        possible_senders: list[str] = [
            "txtBackgd",
            "txtContrast",
            "txtPorodCst",
            "txtScale",
            "txtVolFrac1",
            "txtVolFrac2",
            "txtLowQPower_ex",
            "txtHighQPower_ex",
        ]

        related_widgets: list[WIDGETS] = [
            WIDGETS.W_BACKGROUND,
            WIDGETS.W_CONTRAST,
            WIDGETS.W_POROD_CST,
            WIDGETS.W_SCALE,
            WIDGETS.W_VOLFRAC1,
            WIDGETS.W_VOLFRAC2,
            WIDGETS.W_LOWQ_POWER_VALUE_EX,
            WIDGETS.W_HIGHQ_POWER_VALUE_EX,
        ]

        sender_name = self.sender().objectName()
        text_value = self.sender().text()
        index_elt: int = possible_senders.index(sender_name)

        # Allow empty strings for optional fields like contrast and porod constant
        optional_fields: list[str] = ["txtContrast", "txtPorodCst"]

        if text_value == "" and sender_name in optional_fields:
            # Set the corresponding attribute to None
            item = QtGui.QStandardItem("")
            self.model.setItem(related_widgets[index_elt], item)
            self.sender().setStyleSheet(BG_DEFAULT)

            # Map sender names to instance variable names
            sender_to_attr = {
                "txtContrast": "_contrast",
                "txtPorodCst": "_porod",
            }
            if sender_name in sender_to_attr:
                setattr(self, sender_to_attr[sender_name], None)

            self.allow_calculation()
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
                "txtPorodCst": "_porod",
                "txtScale": "_scale",
                "txtVolFrac1": "_volfrac1",
                "txtVolFrac2": "_volfrac2",
                "txtLowQPower_ex": "_low_power_value",
                "txtHighQPower_ex": "_high_power_value",
            }

            if sender_name in sender_to_attr:
                setattr(self, sender_to_attr[sender_name], new_value)

            # Auto-set _volfrac2 to 1 - _volfrac1 when txtVolFrac1 changes
            if sender_name == "txtVolFrac1":
                self.txtVolFrac2.setEnabled(False)
                self._volfrac2 = round(1 - self._volfrac1, 3)
                # Update the model and UI for volfrac2
                volfrac2_item = QtGui.QStandardItem(str(self._volfrac2))
                self.model.setItem(WIDGETS.W_VOLFRAC2, volfrac2_item)
                self.txtVolFrac2.setText(str(self._volfrac2))

            self.allow_calculation()
        except ValueError:
            # empty field, just skip
            self.sender().setStyleSheet(BG_RED)
            self.cmdCalculate.setEnabled(False)

    def contrastToggle(self, toggle: bool) -> None:
        """
        Enable editing of contrast and disable editing of volume fraction if Contrast is selected
        """
        self._update_contrast_volfrac_state(use_contrast=toggle)

    def volFracToggle(self, toggle: bool) -> None:
        """
        Enable editing of volume fraction and disable editing of contrast if VolFrac is selected
        """
        self._update_contrast_volfrac_state(use_contrast=not toggle)

    def _update_contrast_volfrac_state(self, use_contrast: bool) -> None:
        """
        Update the enabled state of contrast and volume fraction fields.
        
        Args:
            use_contrast: If True, contrast is input and volume fraction is output.
                          If False, volume fraction is input and contrast is output.
        """
        # Update model items
        self.model.setItem(WIDGETS.W_ENABLE_CONTRAST, QtGui.QStandardItem(str(use_contrast).lower()))
        self.model.setItem(WIDGETS.W_ENABLE_VOLFRAC, QtGui.QStandardItem(str(not use_contrast).lower()))

        # Input fields
        self.txtContrast.setEnabled(use_contrast)
        self.txtVolFrac1.setEnabled(not use_contrast)
        self.txtVolFrac2.setEnabled(not use_contrast)

        # Output fields (grey out the one that's being used as input)
        self.txtVolFract.setEnabled(use_contrast)
        self.txtVolFractErr.setEnabled(use_contrast)
        self.txtContrastOut.setEnabled(not use_contrast)
        self.txtContrastOutErr.setEnabled(not use_contrast)

    def update_progress_bars(self) -> None:
        """Update progress bars based on Q* values from the model"""

        def reset_progress_bars():
            """Helper to reset all progress bars to empty state"""
            self.progressBarData.setValue(0)
            self.progressBarData.setFormat("")
            self.progressBarLowQ.setValue(0)
            self.progressBarLowQ.setFormat("")
            self.progressBarHighQ.setValue(0)
            self.progressBarHighQ.setFormat("")

        def get_qstar_value(widget_id: int) -> float:
            """Extract Q* value from model item, return 0.0 if invalid"""
            item = self.model.item(widget_id)
            if not item or not item.text() or item.text() == "ERROR":
                return 0.0
            try:
                return float(item.text())
            except (ValueError, TypeError):
                return 0.0

        def set_progress_bar(progress_bar, percent: float):
            """Set progress bar value and format string"""
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
            qstar_low = get_qstar_value(WIDGETS.D_LOW_QSTAR)
            qstar_high = get_qstar_value(WIDGETS.D_HIGH_QSTAR)

            # Calculate percentages
            low_percent = (qstar_low / qstar_total) * 100.0
            high_percent = (qstar_high / qstar_total) * 100.0
            data_percent = 100.0 - low_percent - high_percent

            # Update all progress bars
            set_progress_bar(self.progressBarLowQ, low_percent)
            set_progress_bar(self.progressBarData, data_percent)
            set_progress_bar(self.progressBarHighQ, high_percent)

        except (ValueError, TypeError, AttributeError) as ex:
            logger.debug(f"Progress bar update failed: {ex}")
            reset_progress_bars()

    def setupModel(self) -> None:
        """ """
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
        item: QtGui.QStandardItem = QtGui.QStandardItem(str(self._scale))
        self.model.setItem(WIDGETS.W_SCALE, item)
        # leave line edit empty if Porod constant not defined
        if self._porod is not None:
            item: QtGui.QStandardItem = QtGui.QStandardItem(str(self._porod))
        else:
            item: QtGui.QStandardItem = QtGui.QStandardItem("")
        self.model.setItem(WIDGETS.W_POROD_CST, item)

        # add volume fraction to the model
        item: QtGui.QStandardItem = QtGui.QStandardItem(str(self._volfrac1))
        self.model.setItem(WIDGETS.W_VOLFRAC1, item)
        item: QtGui.QStandardItem = QtGui.QStandardItem(str(self._volfrac2))
        self.model.setItem(WIDGETS.W_VOLFRAC2, item)

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
        # Set up the mapper.
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

        # Porod constant
        self.mapper.addMapping(self.txtPorodCst, WIDGETS.W_POROD_CST)

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
        Obtain a QStandardItem object and dissect it to get Data1D/2D
        Pass it over to the calculator
        """
        assert data_item is not None

        if self.txtName.text() == data_item[0].text():
            logger.info("This file is already loaded in Invariant panel.")
            return

        if not isinstance(data_item, list):
            msg = "Incorrect type passed to the Invariant Perspective"
            raise AttributeError(msg)

        if not isinstance(data_item[0], QtGui.QStandardItem):
            msg = "Incorrect type passed to the Invariant Perspective"
            raise AttributeError(msg)

        # only 1 file can be loaded
        self._model_item = data_item[0]

        # Reset plots on data change
        self.low_extrapolation_plot = None
        self.high_extrapolation_plot = None
        self.no_extrapolation_plot = None

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

        self.allow_calculation()

        self.tabWidget.setCurrentIndex(0)

        self._manager.filesWidget.newPlot()

        self.mapper.toFirst()

    def removeData(self, data_list: list | None = None) -> None:
        """Remove the existing data reference from the Invariant Perspective"""
        if not data_list or self._model_item not in data_list:
            return

        # close all plots associated with this data before clearing the item
        if self._model_item is not None:
            self._manager.filesWidget.closePlotsForItem(self._model_item)

        self._data = None
        self._model_item = None
        self.low_extrapolation_plot = None
        self.high_extrapolation_plot = None
        self.no_extrapolation_plot = None
        self._path = ""
        self.txtName.setText("")
        self.txtFileName.setText("")
        self._porod = None
        # Pass an empty dictionary to set all inputs to their default values
        self.updateFromParameters({})
        # Disable buttons to return to base state
        self.cmdCalculate.setEnabled(False)

    def updateGuiFromFile(self, data: Data1D = None) -> None:
        """Update display in GUI and plot"""
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
        Serialize the invariant state so data can be saved
        Invariant is not batch-ready so this will only effect a single page
        :return: {data-id: {self.name: {invariant-state}}}
        """
        return self.serializeCurrentPage()

    def serializeCurrentPage(self) -> dict:
        """
        Serialize and return a dictionary of {data_id: invariant-state}
        Return empty dictionary if no data
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
        Serializes full state of this invariant page
        Called by Save Analysis
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
        Collects all active params into a dictionary of {name: value}
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
            "scale": self.txtScale.text(),
            "porod": self.txtPorodCst.text(),
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
        Called by Open Project and Open Analysis
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
        self.txtPorodCst.setText(str(params.get("porod", "0.0")))

        # Extrapolation tab
        self.txtGuinierEnd_ex.setText(str(params.get("qmax_lowq", "")))
        self.txtPorodStart_ex.setText(str(params.get("qmin_highq", "")))
        self.txtPorodEnd_ex.setText(str(params.get("qmax_highq", "")))
        self.txtLowQPower_ex.setText(str(params.get("lowQPower", DEFAULT_POWER_VALUE)))
        self.txtHighQPower_ex.setText(str(params.get("highQPower", DEFAULT_POWER_VALUE)))
        self.chkLowQ_ex.setChecked(params.get("lowQ", False))
        self.chkHighQ_ex.setChecked(params.get("highQ", False))
        self.rbLowQGuinier_ex.setChecked(params.get("lowQGuinier", False))
        self.rbLowQPower_ex.setChecked(params.get("lowQPower", False))
        self.rbLowQFit_ex.setChecked(params.get("lowQFit", False))
        self.rbLowQFix_ex.setChecked(params.get("lowQFix", False))
        self.rbHighQFit_ex.setChecked(params.get("highQFit", False))
        self.rbHighQFix_ex.setChecked(params.get("highQFix", False))

        # Update once all inputs are changed
        self.update_from_model()
        self.plot_result(self.model)

    def allowBatch(self) -> bool:
        """
        Tell the caller that we don't accept multiple data instances
        """
        return False

    def allowSwap(self) -> bool:
        """
        Tell the caller that we can't swap data
        """
        return False

    def reset(self):
        """
        Reset the fitting perspective to an empty state
        """
        self.removeData([self._model_item] if self._model_item else None)
