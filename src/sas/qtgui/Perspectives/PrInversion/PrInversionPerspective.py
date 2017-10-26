import numpy as np

from PyQt4 import QtGui, QtCore, QtWebKit

# sas-global
import sas.qtgui.Utilities.GuiUtils as GuiUtils

# pr inversion gui elements
from PrInversionUtils import WIDGETS
from UI.TabbedPrInversionUI import Ui_PrInversion

class PrInversionWindow(QtGui.QTabWidget, Ui_PrInversion):
    """
    The main window for the P(r) Inversion perspective.
    """

    name = "PrInversion"

    def __init__(self, parent=None, data=None):
        super(PrInversionWindow, self).__init__()
        self.setupUi(self)

        self.setWindowTitle("P(r) Inversion Perspective")

        self._manager = parent
        self._model_item = QtGui.QStandardItem()
        self._helpView = QtWebKit.QWebView()

        if not isinstance(data, list):
            data = [data]
        self._data = data

        # The tabs need to be closeable
        self._allow_close = False

        # Set initial values
        self._data_index = 0
        self._path = ""
        self._background = 0.0
        self._qmin = 0.0
        self._qmax = 1.0
        self._slit_height = 0.0
        self._slit_width = 0.0
        self._terms = 10
        self._regularization = 0.0001
        self._max_distance = 140
        self._bgd_input = False
        self._terms_button = False
        self._reg_button = False
        self._terms_label = ""
        self._reg_label = ""
        # Set results
        self._rg = 0.0
        self._i_0 = 0.0
        self._comp_time = 0.0
        self._chi_dof = 0.0
        self._oscillations = 0.0
        self._pos_fraction = 0.0
        self._sigma_pos_fraction = 0.0

        # Let's choose the Standard Item Model.
        self.model = QtGui.QStandardItemModel(self)
        # Set up the Widget Map
        self.setupMapper()
        # Set values
        self.setupModel()
        # Link user interactions with methods
        self.setupLinks()

        self.communicate = GuiUtils.Communicate()

    ######################################################################
    # Base Perspective Class Definitions

    def allowBatch(self):
        return True

    def setClosable(self, value=True):
        """
        Allow outsiders close this widget
        """
        assert isinstance(value, bool)
        self._allow_close = value

    def closeEvent(self, event):
        """
        Overwrite QDialog close method to allow for custom widget close
        """
        if self._allow_close:
            # reset the closability flag
            self.setClosable(value=False)
            event.accept()
        else:
            event.ignore()
            # Maybe we should just minimize
            self.setWindowState(QtCore.Qt.WindowMinimized)

    ######################################################################
    # Initialization routines

    def setupLinks(self):
        self.dataList.currentIndexChanged.connect(self.displayChange)
        self.calculateButton.clicked.connect(self.calculatePrInversion)
        self.statusButton.clicked.connect(self.status)
        self.helpButton.clicked.connect(self.help)
        self.estimateBgd.toggled.connect(self.toggleBgd)
        self.manualBgd.toggled.connect(self.toggleBgd)
        self.explorerButton.clicked.connect(self.openExplorerWindow)
        pass

    def setupMapper(self):
        # Set up the mapper.
        self.mapper = QtGui.QDataWidgetMapper(self)
        self.mapper.setOrientation(QtCore.Qt.Vertical)
        self.mapper.setModel(self.model)

        # Filename
        self.mapper.addMapping(self.dataList, WIDGETS.W_FILENAME)
        # Background
        self.mapper.addMapping(self.backgroundInput, WIDGETS.W_BACKGROUND)
        self.mapper.addMapping(self.estimateBgd, WIDGETS.W_ESTIMATE)
        self.mapper.addMapping(self.manualBgd, WIDGETS.W_MANUAL_INPUT)

        # Qmin/Qmax
        self.mapper.addMapping(self.minQInput, WIDGETS.W_QMIN)
        self.mapper.addMapping(self.maxQInput, WIDGETS.W_QMAX)

        # Slit Parameter items
        self.mapper.addMapping(self.slitWidthInput, WIDGETS.W_SLIT_WIDTH)
        self.mapper.addMapping(self.slitHeightInput, WIDGETS.W_SLIT_HEIGHT)

        # Parameter Items
        self.mapper.addMapping(self.regularizationConstantInput,
                               WIDGETS.W_REGULARIZATION)
        self.mapper.addMapping(self.regConstantSuggestionButton,
                               WIDGETS.W_REGULARIZATION_SUGGEST)
        self.mapper.addMapping(self.explorerButton, WIDGETS.W_EXPLORE)
        self.mapper.addMapping(self.maxDistanceInput, WIDGETS.W_MAX_DIST)
        self.mapper.addMapping(self.noOfTermsInput, WIDGETS.W_NO_TERMS)
        self.mapper.addMapping(self.noOfTermsSuggestionButton,
                               WIDGETS.W_NO_TERMS_SUGGEST)

        # Output
        self.mapper.addMapping(self.rgValue, WIDGETS.W_RG)
        self.mapper.addMapping(self.iQ0Value, WIDGETS.W_I_ZERO)
        self.mapper.addMapping(self.backgroundValue, WIDGETS.W_BACKGROUND)
        self.mapper.addMapping(self.computationTimeValue, WIDGETS.W_COMP_TIME)
        self.mapper.addMapping(self.chiDofValue, WIDGETS.W_CHI_SQUARED)
        self.mapper.addMapping(self.oscillationValue, WIDGETS.W_OSCILLATION)
        self.mapper.addMapping(self.posFractionValue, WIDGETS.W_POS_FRACTION)
        self.mapper.addMapping(self.sigmaPosFractionValue,
                               WIDGETS.W_SIGMA_POS_FRACTION)

        # Main Buttons
        self.mapper.addMapping(self.calculateButton, WIDGETS.W_CALCULATE)
        self.mapper.addMapping(self.statusButton, WIDGETS.W_STATUS)
        self.mapper.addMapping(self.helpButton, WIDGETS.W_HELP)

        self.mapper.toFirst()

    ######################################################################
    # Methods for updating GUI

    def setupModel(self):
        """
        Update boxes with latest values
        """
        item = QtGui.QStandardItem(self._path)
        self.model.setItem(WIDGETS.W_FILENAME, item)
        item = QtGui.QStandardItem(self._background)
        self.model.setItem(WIDGETS.W_BACKGROUND, item)
        self.checkBgdClicked(self._bgd_input)
        item = QtGui.QStandardItem(self._qmin)
        self.model.setItem(WIDGETS.W_QMIN, item)
        item = QtGui.QStandardItem(self._qmax)
        self.model.setItem(WIDGETS.W_QMAX, item)
        item = QtGui.QStandardItem(self._slit_width)
        self.model.setItem(WIDGETS.W_SLIT_WIDTH, item)
        item = QtGui.QStandardItem(self._slit_height)
        self.model.setItem(WIDGETS.W_SLIT_HEIGHT, item)
        item = QtGui.QStandardItem(self._terms)
        self.model.setItem(WIDGETS.W_NO_TERMS, item)
        item = QtGui.QStandardItem(self._regularization)
        self.model.setItem(WIDGETS.W_REGULARIZATION, item)
        item = QtGui.QStandardItem(self._max_distance)
        self.model.setItem(WIDGETS.W_MAX_DIST, item)
        item = QtGui.QStandardItem(self._rg)
        self.model.setItem(WIDGETS.W_RG, item)
        item = QtGui.QStandardItem(self._i_0)
        self.model.setItem(WIDGETS.W_I_ZERO, item)
        item = QtGui.QStandardItem(self._background)
        self.model.setItem(WIDGETS.W_BACKGROUND, item)
        item = QtGui.QStandardItem(self._comp_time)
        self.model.setItem(WIDGETS.W_COMP_TIME, item)
        item = QtGui.QStandardItem(self._chi_dof)
        self.model.setItem(WIDGETS.W_CHI_SQUARED, item)
        item = QtGui.QStandardItem(self._oscillations)
        self.model.setItem(WIDGETS.W_OSCILLATION, item)
        item = QtGui.QStandardItem(self._pos_fraction)
        self.model.setItem(WIDGETS.W_POS_FRACTION, item)
        item = QtGui.QStandardItem(self._sigma_pos_fraction)
        self.model.setItem(WIDGETS.W_SIGMA_POS_FRACTION, item)
        self.enableButtons()

    def enableButtons(self):
        """
        Disable buttons when no data present, else enable them
        """
        if self._path == "" and len(self._data) == 1:
            self.calculateButton.setEnabled(False)
            self.explorerButton.setEnabled(False)
            self.statusButton.setEnabled(False)
        else:
            self.statusButton.setEnabled(True)
            self.explorerButton.setEnabled(True)
            self.calculateButton.setEnabled(True)

    def reDraw(self):
        """
        Redraws the window with any and all necessary updates.
        """
        self.populateDataComboBox()
        self.dataList.setCurrentIndex(self._data_index)
        self._get_data_from_data_set()

    def populateDataComboBox(self):
        string_list = QtCore.QStringList()
        for item in self._path:
            qt_item = QtCore.QString.fromUtf8(item)
            string_list.append(qt_item)
        self.dataList.addItems(string_list)

    def _addPr(self, data_list):
        """
        Add a new data set to the P(r) window and updates as needed.
        :param data_list: List of data sent from the data manager
        """
        assert data_list is not None
        for data in data_list:
            # TODO: Get get object via GuiUtils
            self._data.append(None)
        self.reDraw()

    def _get_data_from_data_set(self):
        data = self._data[self._data_index]
        # TODO: Get all items from data
        # self._qmin = data.qmin
        # self._qmax = data.qmax
        self.setupModel()

    ######################################################################
    # GUI Actions

    def calculatePrInversion(self):
        """
        Calculate the P(r) for every data set in the data list
        """
        pass

    def status(self):
        """
        Show the status of the calculations
        """
        pass

    def help(self):
        """
        Open the P(r) Inversion help browser
        """
        tree_location = (GuiUtils.HELP_DIRECTORY_LOCATION +
                         "user/sasgui/perspectives/pr/pr_help.html")

        # Actual file anchor will depend on the combo box index
        # Note that we can be clusmy here, since bad current_fitter_id
        # will just make the page displayed from the top
        self._helpView.load(QtCore.QUrl(tree_location))
        self._helpView.show()

    def checkBgdClicked(self, boolean=None):
        if boolean or self.manualBgd.isChecked():
            self.manualBgd.setChecked(True)
            self.toggleBgd(self.manualBgd)
            self._bgd_input = True
        else:
            self.estimateBgd.setChecked(True)
            self.toggleBgd(self.estimateBgd)
            self._bgd_input = False

    def toggleBgd(self, item=None):
        """
        Toggle the background between manual and estimated
        :param item: gui item that was triggered
        """
        if not item:
            self.checkBgdClicked()
        elif isinstance(item, QtGui.QRadioButton):
            if item is self.estimateBgd:
                self.backgroundInput.setEnabled(False)
            else:
                self.backgroundInput.setEnabled(True)

    def openExplorerWindow(self):
        """
        Open the Explorer window to see correlations between params and results
        """
        # TODO: This depends on SVCC-45
        pass

    def displayChange(self):
        """
        Display the values of the data set selected from the data combo box
        """
        self._data_index = self.dataList.currentIndex()
        self.setupModel()

    ######################################################################
    # Response Actions

    def setData(self, data_item=None, is_batch=False):
        """
        Assign new data set or sets to the P(r) perspective
        Obtain a QStandardItem object and dissect it to get Data1D/2D
        Pass it over to the calculator
        """
        assert data_item is not None

        if not isinstance(data_item, list):
            msg = "Incorrect type passed to the P(r) Perspective"
            raise AttributeError, msg

        if not isinstance(data_item[0], QtGui.QStandardItem):
            msg = "Incorrect type passed to the P(r) Perspective"
            raise AttributeError, msg

        self._addPr(data_item)
