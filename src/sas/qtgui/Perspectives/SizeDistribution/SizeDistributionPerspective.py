import logging
from types import TracebackType

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from sasdata.dataloader.data_info import Data1D as LoadData1D

from sas.qtgui.Perspectives.perspective import Perspective
from sas.qtgui.Perspectives.SizeDistribution.SizeDistributionLogic import (
    SizeDistributionLogic,
)
from sas.qtgui.Perspectives.SizeDistribution.SizeDistributionThread import (
    SizeDistributionThread,
)
from sas.qtgui.Perspectives.SizeDistribution.SizeDistributionUtils import (
    WIDGETS,
    MaxEntParameters,
    MaxEntResult,
    WeightType,
)
from sas.qtgui.Perspectives.SizeDistribution.UI.SizeDistributionUI import (
    Ui_SizeDistribution,
)
from sas.qtgui.Perspectives.UndoRedo import DictSnapshotCommand, UndoStack
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Utilities import GuiUtils

ASPECT_RATIO: float = 1.0
DIAMETER_MIN: float = 10.0
DIAMETER_MAX: float = 1000.0
NUM_DIAMETER_BINS: int = 100
LOG_BINNING: str = "true"
CONTRAST: float = 1.0
BACKGROUND: float = 1e-6
SKY_BACKGROUND: float = 1e-6
SUBTRACT_LOW_Q: str = "false"
POWER_LOW_Q: int = 4
SCALE_LOW_Q: float = 1.0
NUM_ITERATIONS: int = 100
WEIGHT_FACTOR: float = 1.0
WEIGHT_PERCENT: float = 1.0

logger = logging.getLogger(__name__)


class SizeDistributionWindow(QtWidgets.QDialog, Ui_SizeDistribution, Perspective):
    """The main window for the Size Distribution perspective."""

    name: str = "SizeDistribution"
    ext: str = "ps"

    @property
    def title(self) -> str:
        """Return the window title."""
        return "Size Distribution Perspective"

    fittingFinishedSignal = QtCore.Signal(MaxEntResult)
    data_plot_signal = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__()
        self.setupUi(self)

        self.setWindowTitle(self.title)

        self._manager = parent
        self._parent = parent
        self._model_item = QtGui.QStandardItem()

        self.communicator = GuiUtils.communicator
        self.communicator.dataDeletedSignal.connect(self.removeData)

        self.logic = SizeDistributionLogic()

        # The window should not close
        self._allowClose: bool = False

        # Undo/redo infrastructure
        self._undo_stack_obj = UndoStack(self)
        self._undo_baseline: dict | None = None

        self._data: LoadData1D | None = None
        self._path: str = ""
        self.fit_thread: SizeDistributionThread | None = None
        self.is_calculating: bool = False
        self.backgd_plot: Data1D | None = None
        self.backgd_subtr_plot: Data1D | None = None
        self.fit_plot: Data1D | None = None
        self.size_distr_plot: Data1D | None = None

        self.model = QtGui.QStandardItemModel(self)
        self.mapper = QtWidgets.QDataWidgetMapper(self)

        # Add validators
        self.setupValidators()
        # Link user interactions with methods
        self.setupSlots()
        # Set values
        self.setupModel()
        # Set up the Widget Map
        self.setupMapper()

        # Set base window state
        self.setupWindow()

        # Undo/redo: baseline after full initialization
        self._setupUndoConnections()
        self._rebaseline_undo_state()
        self._undo_stack_obj.clear()

    ######################################################################
    # Base Perspective Class Definitions

    def allowBatch(self) -> bool:
        """Tell the caller we don't accept batch data."""
        return False

    def allowSwap(self) -> bool:
        """Tell the caller we don't accept swapping data."""
        return False

    def setClosable(self, value: bool = True) -> None:
        """Allow outsiders close this widget."""
        assert isinstance(value, bool)
        self._allowClose = value

    def isClosable(self) -> bool:
        """Return whether this widget is currently closable."""
        return self._allowClose

    def isSerializable(self) -> bool:
        """Tell the caller that this perspective writes its state."""
        return True

    @property
    def undo_stack(self):
        """Return the undo stack for this perspective.

        Overrides ``Perspective.undo_stack`` (which returns ``None``).
        """
        return self._undo_stack_obj

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Overwrite QDialog close method to allow for custom widget close."""
        # Close report widgets before closing/minimizing main widget
        if self._allowClose:
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

    # ------------------------------------------------------------------
    # Undo/redo contract methods
    # ------------------------------------------------------------------

    def _get_parameter_dict(self) -> dict:
        """Capture current input-only state from widgets.

        Mirrors ``getState()`` but also includes weighting and power-fit
        radio buttons not captured by the existing serializer.
        """
        return {
            "range_q_min": self.txtMinRange.text(),
            "range_q_max": self.txtMaxRange.text(),
            "aspect_ratio": self.txtAspectRatio.text(),
            "d_min": self.txtMinDiameter.text(),
            "d_max": self.txtMaxDiameter.text(),
            "num_d_bins": self.txtBinsDiameter.text(),
            "log_binning": self.chkLogBinning.isChecked(),
            "contrast": self.txtContrast.text(),
            "sky_background": self.txtSkyBackgd.text(),
            "num_iterations": self.txtIterations.text(),
            "background": self.txtBackgd.text(),
            "subtract_low_q": self.chkLowQ.isChecked(),
            "power_low_q": self.txtPowerLowQ.text(),
            "scale_low_q": self.txtScaleLowQ.text(),
            "wgt_factor": self.txtWgtFactor.text(),
            "wgt_percent": self.txtWgtPercent.text(),
            "weight_1": self.rbWeighting1.isChecked(),
            "weight_2": self.rbWeighting2.isChecked(),
            "weight_3": self.rbWeighting3.isChecked(),
            "weight_4": self.rbWeighting4.isChecked(),
            "fit_power": self.rbFitPower.isChecked(),
            "fix_power": self.rbFixPower.isChecked(),
        }

    def _restore_parameter_values(self, state: dict) -> None:
        """Apply a state dict to all input widgets AND the underlying model.

        Must update model items because ``setText`` alone does not sync
        through a ``QDataWidgetMapper`` — the model must be explicitly
        updated for data-load paths to see the correct values.
        """
        with self._undo_stack_obj.suppressed():
            # Text widgets
            self.txtMinRange.setText(str(state.get("range_q_min", "0.0")))
            self.txtMaxRange.setText(str(state.get("range_q_max", "0.0")))
            self.txtAspectRatio.setText(str(state.get("aspect_ratio", str(ASPECT_RATIO))))
            self.txtMinDiameter.setText(str(state.get("d_min", str(DIAMETER_MIN))))
            self.txtMaxDiameter.setText(str(state.get("d_max", str(DIAMETER_MAX))))
            self.txtBinsDiameter.setText(str(state.get("num_d_bins", str(NUM_DIAMETER_BINS))))
            self.txtContrast.setText(str(state.get("contrast", str(CONTRAST))))
            self.txtSkyBackgd.setText(str(state.get("sky_background", str(SKY_BACKGROUND))))
            self.txtIterations.setText(str(state.get("num_iterations", str(NUM_ITERATIONS))))
            self.txtBackgd.setText(str(state.get("background", str(BACKGROUND))))
            self.txtPowerLowQ.setText(str(state.get("power_low_q", str(POWER_LOW_Q))))
            self.txtScaleLowQ.setText(str(state.get("scale_low_q", str(SCALE_LOW_Q))))
            self.txtWgtFactor.setText(str(state.get("wgt_factor", str(WEIGHT_FACTOR))))
            self.txtWgtPercent.setText(str(state.get("wgt_percent", str(WEIGHT_PERCENT))))

            # Checkboxes
            self.chkLogBinning.setChecked(bool(state.get("log_binning", True)))
            self.chkLowQ.setChecked(bool(state.get("subtract_low_q", False)))

            # Radio buttons (mutually exclusive groups)
            if bool(state.get("weight_1", True)):
                self.rbWeighting1.setChecked(True)
            elif bool(state.get("weight_2", False)):
                self.rbWeighting2.setChecked(True)
            elif bool(state.get("weight_3", False)):
                self.rbWeighting3.setChecked(True)
            elif bool(state.get("weight_4", False)):
                self.rbWeighting4.setChecked(True)

            if bool(state.get("fix_power", True)):
                self.rbFixPower.setChecked(True)
            elif bool(state.get("fit_power", False)):
                self.rbFitPower.setChecked(True)

            # Sync model items (QDataWidgetMapper is one-way, model not
            # updated by setText alone)
            self.model.item(WIDGETS.W_QMIN).setText(
                str(state.get("range_q_min", "0.0")))
            self.model.item(WIDGETS.W_QMAX).setText(
                str(state.get("range_q_max", "0.0")))
            self.model.item(WIDGETS.W_ASPECT_RATIO).setText(
                str(state.get("aspect_ratio", str(ASPECT_RATIO))))
            self.model.item(WIDGETS.W_DMIN).setText(
                str(state.get("d_min", str(DIAMETER_MIN))))
            self.model.item(WIDGETS.W_DMAX).setText(
                str(state.get("d_max", str(DIAMETER_MAX))))
            self.model.item(WIDGETS.W_DBINS).setText(
                str(state.get("num_d_bins", str(NUM_DIAMETER_BINS))))
            self.model.item(WIDGETS.W_CONTRAST).setText(
                str(state.get("contrast", str(CONTRAST))))
            self.model.item(WIDGETS.W_SKY_BACKGROUND).setText(
                str(state.get("sky_background", str(SKY_BACKGROUND))))
            self.model.item(WIDGETS.W_NUM_ITERATIONS).setText(
                str(state.get("num_iterations", str(NUM_ITERATIONS))))
            self.model.item(WIDGETS.W_BACKGROUND).setText(
                str(state.get("background", str(BACKGROUND))))
            self.model.item(WIDGETS.W_POWER_LOW_Q).setText(
                str(state.get("power_low_q", str(POWER_LOW_Q))))
            self.model.item(WIDGETS.W_SCALE_LOW_Q).setText(
                str(state.get("scale_low_q", str(SCALE_LOW_Q))))
            self.model.item(WIDGETS.W_WEIGHT_FACTOR).setText(
                str(state.get("wgt_factor", str(WEIGHT_FACTOR))))
            self.model.item(WIDGETS.W_WEIGHT_PERCENT).setText(
                str(state.get("wgt_percent", str(WEIGHT_PERCENT))))
            self.model.item(WIDGETS.W_LOG_BINNING).setText(
                str(state.get("log_binning", True)).lower())
            self.model.item(WIDGETS.W_SUBTRACT_LOW_Q).setText(
                str(state.get("subtract_low_q", False)).lower())

        # Update derived UI state (low Q enablement)
        self.onLowQStateChanged(
            QtCore.Qt.CheckState.Checked.value if bool(state.get("subtract_low_q", False))
            else QtCore.Qt.CheckState.Unchecked.value)

    def _captureUndoState(self, description: str = "Change") -> None:
        """Push a DictSnapshotCommand if current state differs from baseline."""
        if self._undo_baseline is None:
            return
        new_state = self._get_parameter_dict()
        if new_state != self._undo_baseline:
            self._undo_stack_obj.push(
                DictSnapshotCommand(self._undo_baseline, new_state, description)
            )
            self._undo_baseline = new_state

    def _rebaseline_undo_state(self) -> None:
        """Update undo baseline without pushing a command."""
        self._undo_baseline = self._get_parameter_dict()

    def _setupUndoConnections(self) -> None:
        """Connect undo-capture signals for user-editable input widgets."""
        # Text edits — editingFinished as commit boundary
        text_edits = [
            self.txtMinRange, self.txtMaxRange,
            self.txtAspectRatio, self.txtMinDiameter, self.txtMaxDiameter,
            self.txtBinsDiameter, self.txtContrast,
            self.txtSkyBackgd, self.txtIterations,
            self.txtBackgd, self.txtPowerLowQ, self.txtScaleLowQ,
            self.txtWgtFactor, self.txtWgtPercent,
        ]
        for te in text_edits:
            te.editingFinished.connect(
                lambda desc="Edit value": self._captureUndoState(desc))

        # Checkboxes
        self.chkLogBinning.toggled.connect(
            lambda _: self._captureUndoState("Toggle log binning"))
        self.chkLowQ.toggled.connect(
            lambda _: self._captureUndoState("Toggle subtract low-Q"))

        # Weighting radio buttons
        self.rbWeighting1.toggled.connect(
            lambda _: self._captureUndoState("Change weighting"))
        self.rbWeighting2.toggled.connect(
            lambda _: self._captureUndoState("Change weighting"))
        self.rbWeighting3.toggled.connect(
            lambda _: self._captureUndoState("Change weighting"))
        self.rbWeighting4.toggled.connect(
            lambda _: self._captureUndoState("Change weighting"))

        # Power fit/fix radio buttons
        self.rbFitPower.toggled.connect(
            lambda _: self._captureUndoState("Change power mode"))
        self.rbFixPower.toggled.connect(
            lambda _: self._captureUndoState("Change power mode"))

    ######################################################################
    # Initialization routines

    def setupSlots(self) -> None:
        """Connect the use controls to their appropriate methods."""
        # Buttons
        self.helpButton.clicked.connect(self.help)
        self.quickFitButton.clicked.connect(self.onQuickFit)
        self.fullFitButton.clicked.connect(self.onFullFit)
        self.cmdReset.clicked.connect(self.onRangeReset)
        self.cmdFitFlatBackground.clicked.connect(self.onFitFlatBackground)
        self.cmdFitPowerLaw.clicked.connect(self.onFitPowerLaw)

        # Checkboxes
        self.chkLowQ.stateChanged.connect(self.onLowQStateChanged)

        # Local signals
        self.fittingFinishedSignal.connect(self.fitComplete)

        # Event filters for plot background update
        background_update_widgets = [
            self.txtBackgd,
            self.txtScaleLowQ,
            self.txtPowerLowQ,
        ]
        for widget in background_update_widgets:
            widget.installEventFilter(self)

    def setupMapper(self) -> None:
        """Set up the mapper."""
        self.mapper.setOrientation(QtCore.Qt.Vertical)
        self.mapper.setModel(self.model)

        # Filename
        self.mapper.addMapping(self.txtName, WIDGETS.W_NAME)

        # Qmin/Qmax
        self.mapper.addMapping(self.txtMinRange, WIDGETS.W_QMIN)
        self.mapper.addMapping(self.txtMaxRange, WIDGETS.W_QMAX)

        # Model
        self.mapper.addMapping(self.txtAspectRatio, WIDGETS.W_ASPECT_RATIO)

        # Size distribution
        self.mapper.addMapping(self.txtMinDiameter, WIDGETS.W_DMIN)
        self.mapper.addMapping(self.txtMaxDiameter, WIDGETS.W_DMAX)
        self.mapper.addMapping(self.txtBinsDiameter, WIDGETS.W_DBINS)
        self.mapper.addMapping(self.chkLogBinning, WIDGETS.W_LOG_BINNING)
        self.mapper.addMapping(self.txtContrast, WIDGETS.W_CONTRAST)

        # Method parameters
        self.mapper.addMapping(self.txtSkyBackgd, WIDGETS.W_SKY_BACKGROUND)
        self.mapper.addMapping(self.txtIterations, WIDGETS.W_NUM_ITERATIONS)

        # Background
        self.mapper.addMapping(self.txtBackgd, WIDGETS.W_BACKGROUND)
        self.mapper.addMapping(self.chkLowQ, WIDGETS.W_SUBTRACT_LOW_Q)
        self.mapper.addMapping(self.txtScaleLowQ, WIDGETS.W_SCALE_LOW_Q)
        self.mapper.addMapping(self.txtPowerLowQ, WIDGETS.W_POWER_LOW_Q)

        # Weighting
        self.mapper.addMapping(self.txtWgtFactor, WIDGETS.W_WEIGHT_FACTOR)
        self.mapper.addMapping(self.txtWgtPercent, WIDGETS.W_WEIGHT_PERCENT)

        self.mapper.toFirst()

    def setupModel(self) -> None:
        """Update boxes with initial values."""
        # filename
        item = QtGui.QStandardItem(self._path)
        self.model.setItem(WIDGETS.W_NAME, item)

        # add Q parameters to the model
        qmin: float = 0.0
        item = QtGui.QStandardItem(str(qmin))
        self.model.setItem(WIDGETS.W_QMIN, item)
        qmax: float = 0.0
        item = QtGui.QStandardItem(str(qmax))
        self.model.setItem(WIDGETS.W_QMAX, item)

        # Model
        item = QtGui.QStandardItem(str(ASPECT_RATIO))
        self.model.setItem(WIDGETS.W_ASPECT_RATIO, item)

        # Size distribution parameters
        item = QtGui.QStandardItem(str(DIAMETER_MIN))
        self.model.setItem(WIDGETS.W_DMIN, item)
        item = QtGui.QStandardItem(str(DIAMETER_MAX))
        self.model.setItem(WIDGETS.W_DMAX, item)
        item = QtGui.QStandardItem(str(NUM_DIAMETER_BINS))
        self.model.setItem(WIDGETS.W_DBINS, item)
        item = QtGui.QStandardItem(str(LOG_BINNING))
        self.model.setItem(WIDGETS.W_LOG_BINNING, item)
        item = QtGui.QStandardItem(str(CONTRAST))
        self.model.setItem(WIDGETS.W_CONTRAST, item)

        # Method parameters
        item = QtGui.QStandardItem(str(SKY_BACKGROUND))
        self.model.setItem(WIDGETS.W_SKY_BACKGROUND, item)
        item = QtGui.QStandardItem(str(NUM_ITERATIONS))
        self.model.setItem(WIDGETS.W_NUM_ITERATIONS, item)

        # Background
        item = QtGui.QStandardItem(str(BACKGROUND))
        self.model.setItem(WIDGETS.W_BACKGROUND, item)
        item = QtGui.QStandardItem(str(SUBTRACT_LOW_Q))
        self.model.setItem(WIDGETS.W_SUBTRACT_LOW_Q, item)
        item = QtGui.QStandardItem(str(POWER_LOW_Q))
        self.model.setItem(WIDGETS.W_POWER_LOW_Q, item)
        item = QtGui.QStandardItem(str(SCALE_LOW_Q))
        self.model.setItem(WIDGETS.W_SCALE_LOW_Q, item)

        # Weighting
        item = QtGui.QStandardItem(str(WEIGHT_FACTOR))
        self.model.setItem(WIDGETS.W_WEIGHT_FACTOR, item)
        item = QtGui.QStandardItem(str(WEIGHT_PERCENT))
        self.model.setItem(WIDGETS.W_WEIGHT_PERCENT, item)

    def setupWindow(self) -> None:
        """Initialize base window state on startup."""
        self.enableButtons()
        self.txtPowerLowQ.setEnabled(False)
        self.txtScaleLowQ.setEnabled(False)
        self.rbFixPower.setChecked(True)

    def setupValidators(self) -> None:
        """Apply validators to editable line edits."""
        self.txtAspectRatio.setValidator(GuiUtils.DoubleValidator())
        self.txtBackgd.setValidator(GuiUtils.DoubleValidator())
        self.txtMinDiameter.setValidator(GuiUtils.DoubleValidator())
        self.txtMaxDiameter.setValidator(GuiUtils.DoubleValidator())
        self.txtBinsDiameter.setValidator(GuiUtils.DoubleValidator())
        self.txtContrast.setValidator(GuiUtils.DoubleValidator())
        self.txtSkyBackgd.setValidator(GuiUtils.DoubleValidator())
        self.txtIterations.setValidator(GuiUtils.DoubleValidator())
        self.txtPowerLowQ.setValidator(GuiUtils.DoubleValidator())
        self.txtScaleLowQ.setValidator(GuiUtils.DoubleValidator())
        self.txtWgtFactor.setValidator(GuiUtils.DoubleValidator())
        self.txtWgtPercent.setValidator(GuiUtils.DoubleValidator())
        self.txtBackgdQMin.setValidator(GuiUtils.DoubleValidator())
        self.txtBackgdQMax.setValidator(GuiUtils.DoubleValidator())

    ######################################################################
    # Methods for updating GUI

    def enableButtons(self) -> None:
        """Enable buttons when data is present, else disable them."""
        data_loaded = self.logic.data_is_loaded
        can_fit = data_loaded and not self.is_calculating

        self.quickFitButton.setEnabled(can_fit)
        self.fullFitButton.setEnabled(can_fit)

        self.boxWeighting.setEnabled(data_loaded)
        self.cmdFitFlatBackground.setEnabled(data_loaded)

        self.cmdFitPowerLaw.setEnabled(data_loaded and self.chkLowQ.isChecked())

    ######################################################################
    # GUI Interaction Events

    def help(self) -> None:
        """Open the Size Distribution help."""
        tree_location: str = "/user/qtgui/Perspectives/SizeDistribution/sizedistribution_help.html"
        self._manager.showHelp(tree_location)

    def onQuickFit(self) -> None:
        """Perform a quick fit of the size distribution."""
        self.is_calculating = True
        self._undo_stack_obj.set_enabled(False)
        self.enableButtons()

        params = self.getMaxEntParams()
        params.full_fit = False
        self.fit_thread = SizeDistributionThread(
            data=self.logic.data,
            background=self.logic.background,
            params=params,
            completefn=self.fittingCompleted,
            exception_handler=self.fittingError,
        )
        self.fit_thread.queue()

    def onFullFit(self) -> None:
        """Perform a full fit of the size distribution."""
        self.is_calculating = True
        self._undo_stack_obj.set_enabled(False)
        self.enableButtons()

        params = self.getMaxEntParams()
        params.full_fit = True
        self.fit_thread = SizeDistributionThread(
            data=self.logic.data,
            background=self.logic.background,
            params=params,
            completefn=self.fittingCompleted,
            exception_handler=self.fittingError,
        )
        self.fit_thread.queue()

    def onRangeReset(self) -> None:
        """Callback for resetting qmin/qmax."""
        qmin: float = 0.0
        qmax: float = 0.0
        if self.logic.data_is_loaded:
            qmin, qmax = self.logic.computeDataRange()
        with self._undo_stack_obj.suppressed():
            self.updateQRange(qmin, qmax)
        self._captureUndoState("Reset Q range")

    def onLowQStateChanged(self, state: int) -> None:
        """Slot for state change of the subtract power law checkbox."""
        is_checked: bool = state == QtCore.Qt.CheckState.Checked.value
        self.txtPowerLowQ.setEnabled(is_checked)
        self.txtScaleLowQ.setEnabled(is_checked)
        self.cmdFitPowerLaw.setEnabled(is_checked)
        if self.logic.data_is_loaded:
            self.updateBackground()
            self.plotData()

    def onFitFlatBackground(self) -> None:
        """Fit flat background and update plot."""
        qmin, qmax = self.getFlatBackgroundRange()
        fit_result = self.logic.fitBackground(power=0.0, qmin=qmin, qmax=qmax)
        if fit_result is None:
            return
        constant = fit_result[0]
        with self._undo_stack_obj.suppressed():
            self.txtBackgd.setText(f"{constant:5g}")
        self.updateBackground()
        self.plotData()
        self._captureUndoState("Fit flat background")

    def onFitPowerLaw(self) -> None:
        """Fit background power law and update plot."""
        qmin, qmax = self.getPowerLawBackgroundRange()
        if self.rbFitPower.isChecked():
            # if the power should be fit, pass None
            fit_result = self.logic.fitBackground(power=None, qmin=qmin, qmax=qmax)
            if fit_result is None:
                return
            scale, power_fit = fit_result
            # by convention, the power is shown without a minus sign
            power = -1.0 * power_fit
            with self._undo_stack_obj.suppressed():
                self.txtPowerLowQ.setText(f"{power:5g}")
        else:
            # if the power should be fixed, pass the value from the input box
            _, _, power_fixed = self.getBackgroundParams()
            fit_result = self.logic.fitBackground(power_fixed, qmin, qmax)
            if fit_result is None:
                return
            scale = fit_result[0]
        # update the scale
        with self._undo_stack_obj.suppressed():
            self.txtScaleLowQ.setText(f"{scale:5g}")
        self.updateBackground()
        self.plotData()
        self._captureUndoState("Fit power law background")

    def eventFilter(self, widget: QtCore.QObject, event: QtCore.QEvent) -> bool:
        """Catch enter key presses and update data plot."""
        if not self.logic.data_is_loaded:
            return False
        if widget.text() == "":
            return False
        # Update plot of data and background
        if event.type() == QtCore.QEvent.KeyPress:
            # check for Enter press
            if event.key() in [QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter]:
                self.updateBackground()
                self.plotData()
                return True
        return False

    ######################################################################
    # Response Actions

    def setData(self, data_item: list | None = None, is_batch: bool = False) -> None:
        """Obtain a QStandardItem object and parse it to get Data1D/2D
        Pass it over to the calculator
        """
        if not isinstance(data_item, list):
            msg = "Incorrect type passed to the Size Distribution Perspective"
            raise AttributeError(msg)

        if self.logic.data_is_loaded:
            # remove existing data and reset GUI
            self.resetWindow()

        self._model_item = data_item[0]
        logic_data = GuiUtils.dataFromItem(self._model_item)

        if not isinstance(logic_data, Data1D):
            msg = "Size Distribution cannot be computed with 2D data."
            raise ValueError(msg)

        self.logic.data = logic_data
        self.model.item(WIDGETS.W_NAME).setData(self._model_item.text())
        self.updateBackground()

        try:
            name: str = self.logic.data.name
        except AttributeError:
            msg = "No data name chosen."
            raise ValueError(msg)
        try:
            qmin: float = min(self.logic.data.x)
            qmax: float = max(self.logic.data.x)
        except (AttributeError, TypeError, ValueError):
            msg = "Unable to find q min/max of \n data named %s" % self.logic.data.name
            raise ValueError(msg)

        self.model.item(WIDGETS.W_NAME).setText(name)
        self.model.item(WIDGETS.W_QMIN).setText(str(qmin))
        self.model.item(WIDGETS.W_QMAX).setText(str(qmax))
        self._path = self.logic.data.filename

        # Set up default weighting controls
        self.rbWeighting2.setEnabled(self.logic.di_flag)
        self.rbWeighting2.setChecked(self.logic.di_flag)
        if not self.logic.di_flag:
            self.rbWeighting4.setChecked(True)

        self.enableButtons()

        self.plotData()

        # Clear undo stack + re-baseline for fresh data
        self._undo_stack_obj.clear()
        self._rebaseline_undo_state()

    def plotData(self) -> None:
        """Plot data, background and background subtracted data."""
        plots: list = [self._model_item]
        self.backgd_plot, self.backgd_subtr_plot, self.fit_plot = self.logic.newDataPlot()

        if self.backgd_plot is not None:
            title: str = self.backgd_plot.name
            GuiUtils.updateModelItemWithPlot(self._model_item, self.backgd_plot, title)
            plots.append(self.backgd_plot)

        if self.backgd_subtr_plot is not None:
            title = self.backgd_subtr_plot.name
            GuiUtils.updateModelItemWithPlot(self._model_item, self.backgd_subtr_plot, title)
            plots.append(self.backgd_subtr_plot)

        if self.fit_plot is not None:
            title = self.fit_plot.name
            GuiUtils.updateModelItemWithPlot(self._model_item, self.fit_plot, title)
            plots.append(self.fit_plot)

        self.communicator.plotRequestedSignal.emit(plots)

    def getState(self) -> dict[str, str | bool]:
        """
        Collects all active params into a dictionary.

        :return: a dictionary of {name: value}
        """
        return {
            "range_q_min": self.txtMinRange.text(),
            "range_q_max": self.txtMaxRange.text(),
            "aspect_ratio": self.txtAspectRatio.text(),
            "d_min": self.txtMinDiameter.text(),
            "d_max": self.txtMaxDiameter.text(),
            "num_d_bins": self.txtBinsDiameter.text(),
            "log_binning": self.chkLogBinning.isChecked(),
            "contrast": self.txtContrast.text(),
            "sky_background": self.txtSkyBackgd.text(),
            "num_iterations": self.txtIterations.text(),
            "background": self.txtBackgd.text(),
            "subtract_low_q": self.chkLowQ.isChecked(),
            "power_low_q": self.txtPowerLowQ.text(),
            "scale_low_q": self.txtScaleLowQ.text(),
        }

    def removeData(self, data_list: list | None = None) -> None:
        """Remove the existing data reference from the Size Distribution Perspective."""
        if not data_list or self._model_item not in data_list:
            return
        self.resetWindow()

    def resetWindow(self) -> None:
        """Reset the state of input widgets and data structures to default values."""
        self._data = None
        self._path = ""
        self.txtName.setText("")
        self.txtPowerLawQMin.setText("")
        self.txtPowerLawQMax.setText("")
        self.txtBackgdQMin.setText("")
        self.txtBackgdQMax.setText("")
        self._model_item = None
        self.logic.data = None
        self.logic.data_fit = None
        self.logic.background = None
        self.backgd_subtr_plot = None
        self.backgd_plot = None
        self.fit_plot = None
        self.size_distr_plot = None
        self.setupModel()
        self.enableButtons()
        self.clearStatistics()

        # Clear undo stack + re-baseline after data removal
        self._undo_stack_obj.clear()
        self._rebaseline_undo_state()

    def serializeAll(self) -> dict:
        """
        Serialize the size distribution state so data can be saved.
        Size distribution is not batch-ready so this will only effect a single page.

        :return: a dictionary of {data-id: {self.name: {inversion-state}}}
        """
        return self.serializeCurrentPage()

    def serializeCurrentPage(self) -> dict:
        """
        Serialize and return a dictionary representing the current state of the size distribution page.
        Return empty dictionary if no data.

        :return: a dictionary of {data-id: {self.name: {invariant - state}}}
        """
        state: dict = {}
        if self._data:
            tab_data = self.getPage()
            data_id: str | bool = tab_data.pop("data_id", "")
            state[data_id] = {"sizedistr_params": tab_data}
        return state

    def getPage(self) -> dict[str, str | bool]:
        """
        Serializes full state of this fit page into a dictionary.

        :return: a dictionary of {param_name: value}
        """
        # Get all parameters from page
        param_dict: dict[str, str | bool] = self.getState()
        if self._data:
            param_dict["data_name"] = str(self._data.name)
            param_dict["data_id"] = str(self._data.id)
        return param_dict

    def updateFromParameters(self, params: dict) -> None:
        """
        Update the GUI state based on a dictionary of parameters.
        Called by Open Project, Open Analysis, and removeData.

        :param params: a dictionary of {param_name: value}; default values used if not valid
        """
        # Params should be a dictionary
        if not isinstance(params, dict):
            c_name: str = params.__class__.__name__
            msg: str = "SizeDistribution.updateFromParameters expects a dictionary"
            raise TypeError(f"{msg}: {c_name} received")
        with self._undo_stack_obj.suppressed():
            # Assign values to 'Parameters' tab inputs - use defaults if not found
            self.txtMinRange.setText(str(params.get("range_q_min", "0.0")))
            self.txtMaxRange.setText(str(params.get("range_q_max", "0.0")))
            self.txtAspectRatio.setText(str(params.get("aspect_ratio", str(ASPECT_RATIO))))
            self.txtMinDiameter.setText(str(params.get("d_min", str(DIAMETER_MIN))))
            self.txtMaxDiameter.setText(str(params.get("d_max", str(DIAMETER_MAX))))
            self.txtBinsDiameter.setText(str(params.get("num_d_bins", str(NUM_DIAMETER_BINS))))
            self.chkLogBinning.setChecked(params.get("log_binning", True))
            self.txtContrast.setText(str(params.get("contrast", str(CONTRAST))))
            self.txtSkyBackgd.setText(str(params.get("sky_background", str(SKY_BACKGROUND))))
            self.txtIterations.setText(str(params.get("num_iterations", str(NUM_ITERATIONS))))
            self.txtBackgd.setText(str(params.get("background", str(BACKGROUND))))
            self.chkLowQ.setChecked(params.get("subtract_low_q", False))
            self.txtPowerLowQ.setText(str(params.get("power_low_q", str(POWER_LOW_Q))))
            self.txtScaleLowQ.setText(str(params.get("scale_low_q", str(SCALE_LOW_Q))))
        self._rebaseline_undo_state()

    def updateQRange(self, q_range_min: float, q_range_max: float) -> None:
        """Update the local model based on calculated values."""
        q_max: str = str(q_range_max)
        q_min: str = str(q_range_min)
        self.model.item(WIDGETS.W_QMIN).setText(q_min)
        self.model.item(WIDGETS.W_QMAX).setText(q_max)

    def fittingCompleted(self, result: MaxEntResult | None) -> None:
        """Send the finish message from calculate threads to main thread."""
        self.fittingFinishedSignal.emit(result)

    def fittingError(self, etype: type[BaseException], value: BaseException, traceback: TracebackType | None) -> None:
        """Handle error in the calculation thread."""
        # re-enable the fit buttons
        self.is_calculating = False
        self._undo_stack_obj.set_enabled(True)
        self._rebaseline_undo_state()
        self.enableButtons()
        logger.exception("Fitting failed", exc_info=(etype, value, traceback))

    def fitComplete(self, result: MaxEntResult) -> None:
        """
        Receive and display fitting results.

        :param result: MaxEnt fitting result object containing the calculated
            statistics and fitted data used to update the plots and output.
        """
        # re-enable the fit buttons
        self.is_calculating = False
        self._undo_stack_obj.set_enabled(True)
        self._rebaseline_undo_state()
        self.enableButtons()
        if result is None:
            msg = "Fitting failed."
            self.communicator.statusBarUpdateSignal.emit(msg)
            return

        # update the output box
        self.updateStatistics(result)

        # plot size distribution
        plots = [self._model_item]
        qmin_fit = float(self.txtMinRange.text())
        qmax_fit = float(self.txtMaxRange.text())

        self.size_distr_plot = self.logic.newSizeDistrPlot(result, qmin_fit, qmax_fit)
        if self.size_distr_plot is not None:
            # set the trust range for the size distribution plot
            self.size_distr_plot.show_trust_bar = True
            trust_range = self.logic.computeTrustRange(qmin_fit, qmax_fit)
            self.size_distr_plot.trust_range = {
                "d_low": trust_range[0],
                "d_high": trust_range[1],
            }

            title = self.size_distr_plot.name
            GuiUtils.updateModelItemWithPlot(self._model_item, self.size_distr_plot, title)
            plots.append(self.size_distr_plot)

        self.communicator.plotRequestedSignal.emit(plots)

        # add fit to data plot
        if isinstance(result.data_max_ent, LoadData1D):
            self.logic.data_fit = result.data_max_ent
            # TODO: q range sliders should not be reset here
            self.plotData()

    def getWeightType(self) -> WeightType | None:
        """Return the weight type based on the checked radio button."""
        weight_type_map = {
            self.rbWeighting1: WeightType.NONE,
            self.rbWeighting2: WeightType.DI,
            self.rbWeighting3: WeightType.SQRT_I,
            self.rbWeighting4: WeightType.PERCENT_I,
        }
        for button, weight_type in weight_type_map.items():
            if button.isChecked():
                return weight_type

    def getMaxEntParams(self) -> MaxEntParameters:
        """Collect Max Ent parameters from the GUI state."""
        return MaxEntParameters(
            qmin=float(self.txtMinRange.text()),
            qmax=float(self.txtMaxRange.text()),
            dmin=float(self.txtMinDiameter.text()),
            dmax=float(self.txtMaxDiameter.text()),
            num_bins=int(self.txtBinsDiameter.text()),
            log_binning=self.chkLogBinning.isChecked(),
            aspect_ratio=float(self.txtAspectRatio.text()),
            contrast=float(self.txtContrast.text()),
            sky_background=float(self.txtSkyBackgd.text()),
            max_iterations=int(self.txtIterations.text()),
            weight_factor=float(self.txtWgtFactor.text()),
            weight_percent=float(self.txtWgtPercent.text()),
            weight_type=self.getWeightType(),
        )

    def getBackgroundParams(self) -> tuple[float, float, float]:
        """Collect background parameters from the GUI state."""
        constant: float = float(self.txtBackgd.text())
        power_law: bool = self.chkLowQ.isChecked()
        power: float = -1.0 * float(self.txtPowerLowQ.text()) if power_law else 0.0
        scale: float = float(self.txtScaleLowQ.text()) if power_law else 0.0
        return constant, scale, power

    def getFlatBackgroundRange(self) -> tuple[float, float]:
        """Collect background range from the GUI state."""
        qmin, qmax = self.logic.computeDataRange()
        qmin_text = self.txtBackgdQMin.text()
        if qmin_text:
            qmin: float = float(qmin_text)
        qmax_text = self.txtBackgdQMax.text()
        if qmax_text:
            qmax: float = float(qmax_text)
        return qmin, qmax

    def getPowerLawBackgroundRange(self) -> tuple[float, float]:
        """Collect power law range from the GUI state."""
        qmin, qmax = self.logic.computeDataRange()
        qmin_text = self.txtPowerLawQMin.text()
        if qmin_text:
            qmin: float = float(qmin_text)
        qmax_text = self.txtPowerLawQMax.text()
        if qmax_text:
            qmax: float = float(qmax_text)
        return qmin, qmax

    def updateBackground(self) -> None:
        """Update the background data."""
        constant, scale, power = self.getBackgroundParams()
        self.logic.computeBackground(constant, scale, power)

    def updateStatistics(self, result: MaxEntResult) -> None:
        """Update the output box with statistics."""
        if all(result.convergences):
            if len(result.convergences) == 1:
                converge_msg = f"Quick fit converged after {result.num_iters[0]} iterations"
            else:
                converge_msg = f"Full fit converged after on average {np.mean(result.num_iters):.1f} iterations"
            self.lblConvergence.setStyleSheet("color: black;")
        else:
            converge_msg = "Not converged! Try increasing the weight factor."
            self.lblConvergence.setStyleSheet("color: red; font-weight: bold;")
        self.lblConvergence.setText(converge_msg)
        self.txtChiSq.setText(f"{result.chisq:.5g}")
        stats: dict[str, float] = result.statistics
        self.txtVolume.setText(f"{stats['volume']:.5g} +/- {stats['volume_err']:.5g}")
        self.txtDiameterMean.setText(f"{stats['mean']:.5g}")
        self.txtDiameterMedian.setText(f"{stats['median']:.5g}")
        self.txtDiameterMode.setText(f"{stats['mode']:.5g}")

    def clearStatistics(self) -> None:
        """Clear the output box."""
        self.lblConvergence.setText("")
        self.txtChiSq.setText("")
        self.txtVolume.setText("")
        self.txtDiameterMean.setText("")
        self.txtDiameterMode.setText("")
        self.txtDiameterMedian.setText("")

    def reset(self) -> None:
        """Reset the size distribution perspective to an empty state."""
        self.removeData([self._model_item] if self._model_item else None)
        self.resetWindow()
