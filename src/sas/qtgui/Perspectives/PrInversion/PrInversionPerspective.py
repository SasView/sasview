import numpy as np

from PyQt4 import QtGui, QtCore, QtWebKit

# sas-global
import sas.qtgui.Utilities.GuiUtils as GuiUtils

# pr inversion gui elements
from PrInversionUtils import WIDGETS
import UI.TabbedPrInversionUI
from UI.TabbedPrInversionUI import Ui_PrInversion

# pr inversion calculation elements
from sas.sascalc.pr.invertor import Invertor
from sas.sasgui.perspectives.pr import pr_thread as pr_thread


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

        self.communicate = GuiUtils.Communicate()

        # The window should not close
        self._allow_close = False

        # is there data
        self._has_data = False

        # Current data object in view
        self._data_index = 0
        # list mapping data to p(r) calculation
        self._data_list = []
        if not isinstance(data, list):
            data = [data]
        for datum in data:
            self._data_list.append({datum : None})

        # p(r) calculator
        self._calculator = Invertor()

        self.model = QtGui.QStandardItemModel(self)
        self.mapper = QtGui.QDataWidgetMapper(self)
        # Link user interactions with methods
        self.setupLinks()
        # Set values
        self.setupModel()
        # Set up the Widget Map
        self.setupMapper()

    ######################################################################
    # Base Perspective Class Definitions

    def allowBatch(self):
        return False

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
        """Connect the use controls to their appropriate methods"""
        self.enableButtons()
        self.checkBgdClicked(False)
        # TODO: enable the drop down box once batch is working
        self.dataList.setEnabled(False)
        # TODO: enable displayChange once batch is working
        # self.dataList.currentIndexChanged.connect(self.displayChange)
        self.calculateButton.clicked.connect(self._calculation)
        self.statusButton.clicked.connect(self.status)
        self.helpButton.clicked.connect(self.help)
        self.estimateBgd.toggled.connect(self.toggleBgd)
        self.manualBgd.toggled.connect(self.toggleBgd)
        self.explorerButton.clicked.connect(self.openExplorerWindow)
        self.model.itemChanged.connect(self.model_changed)

    def setupMapper(self):
        # Set up the mapper.
        self.mapper.setOrientation(QtCore.Qt.Vertical)
        self.mapper.setModel(self.model)

        # Filename
        self.mapper.addMapping(self.dataList, WIDGETS.W_FILENAME)
        # Background
        self.mapper.addMapping(self.backgroundInput, WIDGETS.W_BACKGROUND_INPUT)
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
        self.mapper.addMapping(self.backgroundValue, WIDGETS.W_BACKGROUND_OUTPUT)
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

    def setupModel(self):
        """
        Update boxes with initial values
        """
        item = QtGui.QStandardItem("")
        self.model.setItem(WIDGETS.W_FILENAME, item)
        item = QtGui.QStandardItem('0.0')
        self.model.setItem(WIDGETS.W_BACKGROUND_INPUT, item)
        item = QtGui.QStandardItem("")
        self.model.setItem(WIDGETS.W_QMIN, item)
        item = QtGui.QStandardItem("")
        self.model.setItem(WIDGETS.W_QMAX, item)
        item = QtGui.QStandardItem("")
        self.model.setItem(WIDGETS.W_SLIT_WIDTH, item)
        item = QtGui.QStandardItem("")
        self.model.setItem(WIDGETS.W_SLIT_HEIGHT, item)
        item = QtGui.QStandardItem("10")
        self.model.setItem(WIDGETS.W_NO_TERMS, item)
        item = QtGui.QStandardItem("0.0001")
        self.model.setItem(WIDGETS.W_REGULARIZATION, item)
        item = QtGui.QStandardItem("140.0")
        self.model.setItem(WIDGETS.W_MAX_DIST, item)
        item = QtGui.QStandardItem("")
        self.model.setItem(WIDGETS.W_RG, item)
        item = QtGui.QStandardItem("")
        self.model.setItem(WIDGETS.W_I_ZERO, item)
        item = QtGui.QStandardItem("")
        self.model.setItem(WIDGETS.W_BACKGROUND_OUTPUT, item)
        item = QtGui.QStandardItem("")
        self.model.setItem(WIDGETS.W_COMP_TIME, item)
        item = QtGui.QStandardItem("")
        self.model.setItem(WIDGETS.W_CHI_SQUARED, item)
        item = QtGui.QStandardItem("")
        self.model.setItem(WIDGETS.W_OSCILLATION, item)
        item = QtGui.QStandardItem("")
        self.model.setItem(WIDGETS.W_POS_FRACTION, item)
        item = QtGui.QStandardItem("")
        self.model.setItem(WIDGETS.W_SIGMA_POS_FRACTION, item)

    ######################################################################
    # Methods for updating GUI

    def enableButtons(self):
        """
        Enable buttons when data is present, else disable them
        """
        if self._has_data:
            self.statusButton.setEnabled(True)
            self.explorerButton.setEnabled(True)
            self.calculateButton.setEnabled(True)
        else:
            self.calculateButton.setEnabled(False)
            self.explorerButton.setEnabled(False)
            self.statusButton.setEnabled(False)

    def populateDataComboBox(self, filename):
        """
        Append a new file name to the data combobox
        :param data: Data1D object
        """
        qt_item = QtCore.QString.fromUtf8(filename)
        self.dataList.addItem(qt_item)

    ######################################################################
    # GUI Actions

    def _calculation(self):
        """
        Calculate the P(r) for every data set in the data list
        """
        # TODO: Run the calculations
        pass

    def model_changed(self):
        """Update the values when user makes changes"""
        if not self.mapper:
            return
        self.mapper.toFirst()
        # TODO: Update plots, etc.

    def status(self):
        """
        Show the status of the calculations
        """
        # TODO: Status - is this even needed/wanted?
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
        else:
            self.estimateBgd.setChecked(True)
            self.toggleBgd(self.estimateBgd)

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

        for data in data_item:
            data_object = GuiUtils.dataFromItem(data)
            self._data_list.append({data_object: None})
            self._has_data = True
            self.enableButtons()
            self.populateDataComboBox(data_object.filename)
            self.model.setItem(WIDGETS.W_QMIN,
                               QtGui.QStandardItem(str(data_object.x.min())))
            self.model.setItem(WIDGETS.W_QMAX,
                               QtGui.QStandardItem(str(data_object.x.max())))

            # TODO: Get value estimates
            no_terms, alpha, _ = self._calculator.estimate_numterms(
                self._calculator)
            self.noOfTermsSuggestionButton.setText(
                QtCore.QString(str(no_terms)))
            self.noOfTermsSuggestionButton.setEnabled(True)
            self.regConstantSuggestionButton.setText(QtCore.QString(str(alpha)))
            self.regConstantSuggestionButton.setEnabled(True)

            # TODO: Only load in the 1st data until batch mode is working
            break
