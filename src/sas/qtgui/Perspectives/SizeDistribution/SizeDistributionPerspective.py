import logging

from PySide6 import QtGui, QtCore, QtWidgets

from sas.qtgui.Perspectives.SizeDistribution.SizeDistributionLogic import (
    SizeDistributionLogic,
)
from sas.qtgui.Perspectives.SizeDistribution.UI.SizeDistributionUI import (
    Ui_SizeDistribution,
)
from sas.qtgui.Perspectives.perspective import Perspective
from sas.qtgui.Perspectives.SizeDistribution.SizeDistributionUtils import WIDGETS
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Utilities import GuiUtils


ASPECT_RATIO = 1.0
DIAMETER_MIN = 10.0
DIAMETER_MAX = 1000.0
NUM_DIAMETER_BINS = 100
LOG_BINNING = "true"
CONTRAST = 1.0
BACKGROUND = 0.0
SKY_BACKGROUND = 1e-6
SUBTRACT_LOW_Q = "false"
POWER_LOW_Q = 4
NUM_PTS_LOW_Q = 10
SCALE_LOW_Q = 1.0
NUM_ITERATIONS = 100

logger = logging.getLogger(__name__)


class SizeDistributionWindow(QtWidgets.QDialog, Ui_SizeDistribution, Perspective):
    """
    The main window for the Size Distribution perspective.
    """

    name = "SizeDistribution"
    ext = "ps"

    @property
    def title(self) -> str:
        """Window title"""
        return "Size Distribution Perspective"

    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)

        self.setWindowTitle(self.title)

        self._manager = parent
        self._parent = parent
        self._model_item = QtGui.QStandardItem()

        self.communicate = parent.communicator()
        self.communicate.dataDeletedSignal.connect(self.removeData)

        self.logic = SizeDistributionLogic()

        # The window should not close
        self._allowClose = False

        self._data = None
        self._path = ""
        self._calculator = None

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

    ######################################################################
    # Base Perspective Class Definitions

    def communicator(self):
        return self.communicate

    def allowBatch(self):
        return False

    def allowSwap(self):
        """
        Tell the caller we don't accept swapping data
        """
        return False

    def setClosable(self, value=True):
        """
        Allow outsiders close this widget
        """
        assert isinstance(value, bool)
        self._allowClose = value

    def isClosable(self):
        """
        Allow outsiders close this widget
        """
        return self._allowClose

    def isSerializable(self):
        """
        Tell the caller that this perspective writes its state
        """
        return True

    def closeEvent(self, event):
        """
        Overwrite QDialog close method to allow for custom widget close
        """
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

    ######################################################################
    # Initialization routines

    def setupSlots(self):
        """Connect the use controls to their appropriate methods"""
        self.helpButton.clicked.connect(self.help)
        self.quickFitButton.clicked.connect(self.onQuickFit)
        self.fullFitButton.clicked.connect(self.onFullFit)
        self.cmdReset.clicked.connect(self.onRangeReset)
        self.chkLowQ.stateChanged.connect(self.onLowQStateChanged)

    def setupMapper(self):
        # Set up the mapper.
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
        self.mapper.addMapping(self.txtNptsLowQ, WIDGETS.W_NUM_PTS_LOW_Q)
        self.mapper.addMapping(self.txtScaleLowQ, WIDGETS.W_SCALE_LOW_Q)
        self.mapper.addMapping(self.txtPowerLowQ, WIDGETS.W_POWER_LOW_Q)

        self.mapper.toFirst()

    def setupModel(self):
        """
        Update boxes with initial values
        """
        # filename
        item = QtGui.QStandardItem(self._path)
        self.model.setItem(WIDGETS.W_NAME, item)

        # add Q parameters to the model
        qmin = 0.0
        item = QtGui.QStandardItem(str(qmin))
        self.model.setItem(WIDGETS.W_QMIN, item)
        qmax = 0.0
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
        item = QtGui.QStandardItem(str(NUM_PTS_LOW_Q))
        self.model.setItem(WIDGETS.W_NUM_PTS_LOW_Q, item)
        item = QtGui.QStandardItem(str(POWER_LOW_Q))
        self.model.setItem(WIDGETS.W_POWER_LOW_Q, item)
        item = QtGui.QStandardItem(str(SCALE_LOW_Q))
        self.model.setItem(WIDGETS.W_SCALE_LOW_Q, item)

    def setupWindow(self):
        """Initialize base window state on init"""
        self.enableButtons()
        self.txtNptsLowQ.setEnabled(False)
        self.txtPowerLowQ.setEnabled(False)
        self.txtScaleLowQ.setEnabled(False)
        self.rbFitLowQ.setEnabled(False)
        self.rbFixLowQ.setEnabled(False)

    def setupValidators(self):
        """Apply validators to editable line edits"""
        self.txtAspectRatio.setValidator(GuiUtils.DoubleValidator())
        self.txtBackgd.setValidator(GuiUtils.DoubleValidator())
        self.txtBackgd.setValidator(GuiUtils.DoubleValidator())
        self.txtMinDiameter.setValidator(GuiUtils.DoubleValidator())
        self.txtMaxDiameter.setValidator(GuiUtils.DoubleValidator())
        self.txtBinsDiameter.setValidator(GuiUtils.DoubleValidator())
        self.txtContrast.setValidator(GuiUtils.DoubleValidator())
        self.txtSkyBackgd.setValidator(GuiUtils.DoubleValidator())
        self.txtIterations.setValidator(GuiUtils.DoubleValidator())
        self.txtNptsLowQ.setValidator(GuiUtils.DoubleValidator())
        self.txtPowerLowQ.setValidator(GuiUtils.DoubleValidator())
        self.txtScaleLowQ.setValidator(GuiUtils.DoubleValidator())

    ######################################################################
    # Methods for updating GUI

    def enableButtons(self):
        """
        Enable buttons when data is present, else disable them
        """
        self.quickFitButton.setEnabled(self.logic.data_is_loaded)
        self.fullFitButton.setEnabled(self.logic.data_is_loaded)
        self.boxWeighting.setEnabled(self.logic.data_is_loaded)
        # Weighting controls
        if self.logic.di_flag:
            self.rbWeighting2.setEnabled(True)
            self.rbWeighting2.setChecked(True)
            # self.onWeightingChoice(self.rbWeighting2)
        else:
            self.rbWeighting2.setEnabled(False)
            self.rbWeighting1.setChecked(True)
            # self.onWeightingChoice(self.rbWeighting1)

    ######################################################################
    # GUI Interaction Events

    def help(self):
        """
        Open the Size Distribution help
        """
        tree_location = (
            "/user/qtgui/Perspectives/SizeDistribution/sizedistribution_help.html"
        )
        self._manager.showHelp(tree_location)

    def onQuickFit(self):
        pass

    def onFullFit(self):
        pass

    def onRangeReset(self):
        """
        Callback for resetting qmin/qmax
        """
        qmin = 0.0
        qmax = 0.0
        if self.logic.data_is_loaded:
            qmin, qmax = self.logic.computeDataRange()
        self.updateQRange(qmin, qmax)

    def onLowQStateChanged(self, state):
        is_checked = state == QtCore.Qt.CheckState.Checked.value
        self.txtNptsLowQ.setEnabled(is_checked)
        self.txtPowerLowQ.setEnabled(is_checked)
        self.txtScaleLowQ.setEnabled(is_checked)
        self.rbFitLowQ.setEnabled(is_checked)
        self.rbFixLowQ.setEnabled(is_checked)

    ######################################################################
    # Response Actions

    def setData(self, data_item=None, is_batch=False):
        """
        Obtain a QStandardItem object and parse it to get Data1D/2D
        Pass it over to the calculator
        """
        assert data_item is not None

        if not isinstance(data_item, list):
            msg = "Incorrect type passed to the Size Distribution Perspective"
            raise AttributeError(msg)

        self._model_item = data_item[0]
        self.logic.data = GuiUtils.dataFromItem(self._model_item)
        self.model.item(WIDGETS.W_NAME).setData(self._model_item.text())

        if not isinstance(self.logic.data, Data1D):
            msg = "Size Distribution cannot be computed with 2D data."
            raise ValueError(msg)

        try:
            name = self.logic.data.name
        except AttributeError:
            msg = "No data name chosen."
            raise ValueError(msg)
        try:
            qmin = min(self.logic.data.x)
            qmax = max(self.logic.data.x)
        except (AttributeError, TypeError, ValueError):
            msg = "Unable to find q min/max of \n data named %s" % self.logic.data.name
            raise ValueError(msg)

        self.model.item(WIDGETS.W_NAME).setText(name)
        self.model.item(WIDGETS.W_QMIN).setText(str(qmin))
        self.model.item(WIDGETS.W_QMAX).setText(str(qmax))
        self._path = self.logic.data.filename

        self.enableButtons()

    def getState(self):
        """
        Collects all active params into a dictionary of {name: value}
        :return: {name: value}
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
            "num_pts_low_q": self.txtNptsLowQ.text(),
            "power_low_q": self.txtPowerLowQ.text(),
            "scale_low_q": self.txtScaleLowQ.txt(),
        }

    def removeData(self, data_list=None):
        """Remove the existing data reference from the Size Distribution Perspective"""
        if not data_list or self._model_item not in data_list:
            return
        self._data = None
        self._path = None
        self.txtName.setText("")
        self._model_item = None
        self.logic.data = None
        # Pass an empty dictionary to set all inputs to their default values
        self.updateFromParameters({})
        self.enableButtons()

    def serializeAll(self):
        """
        Serialize the size distribution state so data can be saved
        Size distribution is not batch-ready so this will only effect a single page
        :return: {data-id: {self.name: {inversion-state}}}
        """
        return self.serializeCurrentPage()

    def serializeCurrentPage(self):
        """
        Serialize and return a dictionary of {data_id: sizedistr-state}
        Return empty dictionary if no data
        :return: {data-id: {self.name: {invariant - state}}}
        """
        state = {}
        if self._data:
            tab_data = self.getPage()
            data_id = tab_data.pop("data_id", "")
            state[data_id] = {"sizedistr_params": tab_data}
        return state

    def getPage(self):
        """
        serializes full state of this fit page
        """
        # Get all parameters from page
        param_dict = self.getState()
        if self._data:
            param_dict["data_name"] = str(self._data.name)
            param_dict["data_id"] = str(self._data.id)
        return param_dict

    def updateFromParameters(self, params):
        """
        Called by Open Project, Open Analysis, and removeData
        :param params: {param_name: value} -> Default values used if not valid
        :return: None
        """
        # Params should be a dictionary
        if not isinstance(params, dict):
            c_name = params.__class__.__name__
            msg = "SizeDistribution.updateFromParameters expects a dictionary"
            raise TypeError(f"{msg}: {c_name} received")
        # Assign values to 'Parameters' tab inputs - use defaults if not found
        self.txtMinRange.setText(str(params.get("range_q_min", "0.0")))
        self.txtMaxRange.setText(str(params.get("range_q_max", "0.0")))
        self.txtAspectRatio.setText(str(params.get("aspect_ratio", str(ASPECT_RATIO))))
        self.txtMinDiameter.setText(str(params.get("d_min", str(DIAMETER_MIN))))
        self.txtMaxDiameter.setText(str(params.get("d_max", str(DIAMETER_MAX))))
        self.txtBinsDiameter.setText(
            str(params.get("num_d_bins", str(NUM_DIAMETER_BINS)))
        )
        self.chkLogBinning.setChecked(params.get("log_binning", True))
        self.txtContrast.setText(str(params.get("contrast", str(CONTRAST))))
        self.txtSkyBackgd.setText(
            str(params.get("sky_background", str(SKY_BACKGROUND)))
        )
        self.txtIterations.setText(
            str(params.get("num_iterations", str(NUM_ITERATIONS)))
        )
        self.txtBackgd.setText(str(params.get("background", str(BACKGROUND))))
        self.chkLowQ.setChecked(params.get("subtract_low_q", False))
        self.txtNptsLowQ.setText(str(params.get("num_pts_low_q", str(NUM_PTS_LOW_Q))))
        self.txtPowerLowQ.setText(str(params.get("power_low_q", str(POWER_LOW_Q))))
        self.txtScaleLowQ.setText(str(params.get("scale_low_q", str(SCALE_LOW_Q))))

    def updateQRange(self, q_range_min, q_range_max):
        """
        Update the local model based on calculated values
        """
        q_max = str(q_range_max)
        q_min = str(q_range_min)
        self.model.item(WIDGETS.W_QMIN).setText(q_min)
        self.model.item(WIDGETS.W_QMAX).setText(q_max)
