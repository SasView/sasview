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
        self.setupLinks()
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

    def setupLinks(self):
        """Connect the use controls to their appropriate methods"""
        self.helpButton.clicked.connect(self.help)

    def setupMapper(self):
        # Set up the mapper.
        self.mapper.setOrientation(QtCore.Qt.Vertical)
        self.mapper.setModel(self.model)

        # Filename
        self.mapper.addMapping(self.txtName, WIDGETS.W_NAME)

        # Qmin/Qmax
        self.mapper.addMapping(self.txtTotalQMin, WIDGETS.W_QMIN)
        self.mapper.addMapping(self.txtTotalQMax, WIDGETS.W_QMAX)

        # Model
        self.mapper.addMapping(self.txtAspectRatio, WIDGETS.W_ASPECT_RATIO)

        # Size distribution
        self.mapper.addMapping(self.txtMinDiameter, WIDGETS.W_DMIN)
        self.mapper.addMapping(self.txtMaxDiameter, WIDGETS.W_DMAX)
        self.mapper.addMapping(self.txtBinsDiameter, WIDGETS.W_DBINS)

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
        d_min = 10.0
        item = QtGui.QStandardItem(str(d_min))
        self.model.setItem(WIDGETS.W_DMIN, item)
        d_max = 100.0
        item = QtGui.QStandardItem(str(d_max))
        self.model.setItem(WIDGETS.W_DMAX, item)
        n_bins = 100.0
        item = QtGui.QStandardItem(str(n_bins))
        self.model.setItem(WIDGETS.W_DBINS, item)

    def setupWindow(self):
        """Initialize base window state on init"""
        self.enableButtons()

    def setupValidators(self):
        """Apply validators to editable line edits"""
        self.txtAspectRatio.setValidator(GuiUtils.DoubleValidator())

    ######################################################################
    # Methods for updating GUI

    def enableButtons(self):
        """
        Enable buttons when data is present, else disable them
        """
        self.plotButton.setEnabled(self.logic.data_is_loaded)
        self.quickFitButton.setEnabled(self.logic.data_is_loaded)
        self.fullFitButton.setEnabled(self.logic.data_is_loaded)

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
            "total_q_min": self.txtTotalQMin.text(),
            "total_q_max": self.txtTotalQMax.text(),
            "aspect_ratio": self.txtAspectRatio.text(),
            "d_min": self.txtMinDiameter.text(),
            "d_max": self.txtMaxDiameter.text(),
            "num_d_bins": self.txtBinsDiameter.text(),
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
        self.txtTotalQMin.setText(str(params.get("total_q_min", "0.0")))
        self.txtTotalQMax.setText(str(params.get("total_q_max", "0.0")))
        self.txtAspectRatio.setText(str(params.get("aspect_ratio", "1.0")))
        self.txtMinDiameter.setText(str(params.get("d_min", "10.0")))
        self.txtMaxDiameter.setText(str(params.get("d_max", "100.0")))
        self.txtBinsDiameter.setText(str(params.get("num_d_bins", "100")))
