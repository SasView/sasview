import logging

from PySide6 import QtGui, QtCore, QtWidgets

from sas.qtgui.Perspectives.SizeDistribution.UI.SizeDistributionUI import (
    Ui_SizeDistribution,
)
from sas.qtgui.Perspectives.perspective import Perspective
from sas.qtgui.Utilities import GuiUtils

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

        # The window should not close
        self._allowClose = False

        self._data = None
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
        self.mapper.toFirst()

    def setupModel(self):
        """
        Update boxes with initial values
        """
        pass

    def setupWindow(self):
        """Initialize base window state on init"""
        pass

    def setupValidators(self):
        """Apply validators to editable line edits"""
        pass

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

        model_item = data_item[0]
        data = GuiUtils.dataFromItem(model_item)
        self._data = data
        self._model_item = model_item

    def getState(self):
        """
        Collects all active params into a dictionary of {name: value}
        :return: {name: value}
        """
        return {}

    def removeData(self, data_list=None):
        """Remove the existing data reference from the Size Distribution Perspective"""
        if not data_list or self._model_item not in data_list:
            return
        self._data = None
        self._model_item = None
        # Pass an empty dictionary to set all inputs to their default values
        self.updateFromParameters({})

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
        pass
