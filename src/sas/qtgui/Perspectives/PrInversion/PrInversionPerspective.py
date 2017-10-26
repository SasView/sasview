import logging

from PyQt4 import QtGui, QtCore, QtWebKit

# sas-global
import sas.qtgui.Utilities.GuiUtils as GuiUtils

# pr inversion gui elements
from PrInversionUtils import WIDGETS
from UI.TabbedPrInversionUI import Ui_PrInversion

class PrInversionWindow(QtGui.QTabWidget, Ui_PrInversion):
    """
    """

    name = "PrInversion"

    def __init__(self, parent=None, data=None):
        super(PrInversionWindow, self).__init__()
        self.setupUi(self)

        self.setWindowTitle("P(r) Inversion Perspective")

        self._manager = parent
        self._model_item = QtGui.QStandardItem()
        self._helpView = QtWebKit.QWebView()
        self._data = data

        # The tabs need to be closeable
        self._allow_close = False

        # Set initial values
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
        logging.debug("P(r) Inversion Perspective loaded")

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

    def setupLinks(self):
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
        self.mapper.addMapping(self.dataFileName, WIDGETS.W_FILENAME)
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
        self.mapper.addMapping(self.regularizationConstantInput, WIDGETS.W_REGULARIZATION)
        self.mapper.addMapping(self.regConstantSuggestionButton, WIDGETS.W_REGULARIZATION_SUGGEST)
        self.mapper.addMapping(self.explorerButton, WIDGETS.W_EXPLORE)
        self.mapper.addMapping(self.maxDistanceInput, WIDGETS.W_MAX_DIST)
        self.mapper.addMapping(self.noOfTermsInput, WIDGETS.W_NO_TERMS)
        self.mapper.addMapping(self.noOfTermsSuggestionButton, WIDGETS.W_NO_TERMS_SUGGEST)

        # Output
        self.mapper.addMapping(self.rgValue, WIDGETS.W_RG)
        self.mapper.addMapping(self.iQ0Value, WIDGETS.W_I_ZERO)
        self.mapper.addMapping(self.backgroundValue, WIDGETS.W_BACKGROUND)
        self.mapper.addMapping(self.computationTimeValue, WIDGETS.W_COMP_TIME)
        self.mapper.addMapping(self.chiDofValue, WIDGETS.W_CHI_SQUARED)
        self.mapper.addMapping(self.oscillationValue, WIDGETS.W_OSCILLATION)
        self.mapper.addMapping(self.posFractionValue, WIDGETS.W_POS_FRACTION)
        self.mapper.addMapping(self.sigmaPosFractionValue, WIDGETS.W_SIGMA_POS_FRACTION)

        # Main Buttons
        self.mapper.addMapping(self.calculateButton, WIDGETS.W_CALCULATE)
        self.mapper.addMapping(self.statusButton, WIDGETS.W_STATUS)
        self.mapper.addMapping(self.helpButton, WIDGETS.W_HELP)

        self.mapper.toFirst()

    def setupModel(self):
        """
        Update boxes with latest values
        """
        item = QtGui.QStandardItem(self._path)
        self.model.setItem(WIDGETS.W_FILENAME, item)
        item = QtGui.QStandardItem(self._background)
        self.model.setItem(WIDGETS.W_BACKGROUND, item)
        self.estimateBgd.click()
        self.backgroundInput.setEnabled(self._bgd_input)
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

    # GUI Actions
    def calculatePrInversion(self):
        pass

    def status(self):
        pass

    def help(self):
        pass

    def toggleBgd(self, item):
        pass

    def openExplorerWindow(self):
        # TODO: This depends on SVCC-45
        pass
