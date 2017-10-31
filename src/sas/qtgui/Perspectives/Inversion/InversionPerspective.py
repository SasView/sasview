import sys
import logging
import pylab
import numpy as np

from PyQt4 import QtGui, QtCore, QtWebKit
from twisted.internet import reactor

# sas-global
import sas.qtgui.Utilities.GuiUtils as GuiUtils

# pr inversion GUI elements
from InversionUtils import WIDGETS
import UI.TabbedInversionUI
from UI.TabbedInversionUI import Ui_PrInversion
from InversionLogic import InversionLogic

# pr inversion calculation elements
from sas.sascalc.dataloader.data_info import Data1D
from sas.sascalc.pr.invertor import Invertor

def is_float(value):
    """Converts text input values to floats. Empty strings throw ValueError"""
    try:
        return float(value)
    except ValueError:
        return 0.0


# TODO: Remove data
# TODO: Modify plot references, don't just send new
# TODO: Explorer button - link to PR from AW
# TODO: Update help with batch capabilities
# TODO: Window should not be fixed size
# TODO: Easy way to scroll through results - no tabs in window(?) - 'spreadsheet'
# TODO: Method to export results in some meaningful way
class InversionWindow(QtGui.QTabWidget, Ui_PrInversion):
    """
    The main window for the P(r) Inversion perspective.
    """

    name = "Inversion"

    def __init__(self, parent=None, data=None):
        super(InversionWindow, self).__init__()
        self.setupUi(self)

        self.setWindowTitle("P(r) Inversion Perspective")

        self._manager = parent
        self._model_item = QtGui.QStandardItem()
        self._helpView = QtWebKit.QWebView()

        self.communicate = GuiUtils.Communicate()

        self.logic = InversionLogic()

        # The window should not close
        self._allow_close = False

        # current QStandardItem showing on the panel
        self._data = None
        # current Data1D as referenced by self._data
        self._data_set = None

        # p(r) calculator
        self._calculator = Invertor()
        self._last_calculator = None
        self.calc_thread = None
        self.estimation_thread = None

        # Current data object in view
        self._data_index = 0
        # list mapping data to p(r) calculation
        self._data_list = {}
        if not isinstance(data, list):
            data_list = [data]
        if data is not None:
            for datum in data_list:
                self._data_list[datum] = self._calculator.clone()

        # plots for current data
        self.pr_plot = None
        self.data_plot = None
        # plot references for all data in perspective
        self.pr_plot_list = {}
        self.data_plot_list = {}

        self.model = QtGui.QStandardItemModel(self)
        self.mapper = QtGui.QDataWidgetMapper(self)
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
        """Connect the use controls to their appropriate methods"""
        self.dataList.currentIndexChanged.connect(self.displayChange)
        self.calculateAllButton.clicked.connect(self.startThreadAll)
        self.calculateThisButton.clicked.connect(self.startThread)
        self.helpButton.clicked.connect(self.help)
        self.estimateBgd.toggled.connect(self.toggleBgd)
        self.manualBgd.toggled.connect(self.toggleBgd)
        self.regConstantSuggestionButton.clicked.connect(self.acceptAlpha)
        self.noOfTermsSuggestionButton.clicked.connect(self.acceptNoTerms)
        self.explorerButton.clicked.connect(self.openExplorerWindow)
        self.backgroundInput.textChanged.connect(
            lambda: self._calculator.set_est_bck(int(is_float(
                str(self.backgroundInput.text())))))
        self.minQInput.textChanged.connect(
            lambda: self._calculator.set_qmin(is_float(
                str(self.minQInput.text()))))
        self.regularizationConstantInput.textChanged.connect(
            lambda: self._calculator.set_alpha(is_float(
                str(self.regularizationConstantInput.text()))))
        self.maxDistanceInput.textChanged.connect(
            lambda: self._calculator.set_dmax(is_float(
                str(self.maxDistanceInput.text()))))
        self.maxQInput.textChanged.connect(
            lambda: self._calculator.set_qmax(is_float(
                str(self.maxQInput.text()))))
        self.slitHeightInput.textChanged.connect(
            lambda: self._calculator.set_slit_height(is_float(
                str(self.slitHeightInput.text()))))
        self.slitWidthInput.textChanged.connect(
            lambda: self._calculator.set_slit_width(is_float(
                str(self.slitHeightInput.text()))))
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
        self.mapper.addMapping(self.calculateAllButton, WIDGETS.W_CALCULATE_ALL)
        self.mapper.addMapping(self.calculateThisButton,
                               WIDGETS.W_CALCULATE_VISIBLE)
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

    def setupWindow(self):
        """Initialize base window state on init"""
        self.setTabPosition(0)
        self.enableButtons()
        self.estimateBgd.setChecked(True)

    ######################################################################
    # Methods for updating GUI

    def enableButtons(self):
        """
        Enable buttons when data is present, else disable them
        """
        self.explorerButton.setEnabled(self.logic.data_is_loaded)
        self.calculateAllButton.setEnabled(self.logic.data_is_loaded)
        self.calculateThisButton.setEnabled(self.logic.data_is_loaded)

    def populateDataComboBox(self, filename, data_ref):
        """
        Append a new file name to the data combobox
        :param data: Data1D object
        """
        qt_item = QtCore.QString.fromUtf8(filename)
        ref = QtCore.QVariant(data_ref)
        self.dataList.addItem(qt_item, ref)

    def acceptNoTerms(self):
        """Send estimated no of terms to input"""
        self.model.setItem(WIDGETS.W_NO_TERMS, QtGui.QStandardItem(
            self.noOfTermsSuggestionButton.text()))

    def acceptAlpha(self):
        """Send estimated alpha to input"""
        self.model.setItem(WIDGETS.W_REGULARIZATION, QtGui.QStandardItem(
            self.regConstantSuggestionButton.text()))

    def displayChange(self):
        variant_ref = self.dataList.itemData(self.dataList.currentIndex())
        self.setCurrentData(variant_ref.toPyObject())

    ######################################################################
    # GUI Interaction Events

    def update_calculator(self):
        """Update all p(r) params"""
        self._calculator.set_x(self._data_set.x)
        self._calculator.set_y(self._data_set.y)
        self._calculator.set_err(self._data_set.dy)

    def model_changed(self):
        """Update the values when user makes changes"""
        if not self.mapper:
            msg = "Unable to update P{r}. The connection between the main GUI "
            msg += "and P(r) was severed. Attempting to restart P(r)."
            logging.warning(msg)
            self.setClosable(True)
            self.close()
            InversionWindow.__init__(self.parent(), self._data_list.keys())
            exit(0)
        # TODO: Only send plot first time - otherwise, update in complete
        if self.pr_plot is not None:
            title = self.pr_plot.name
            GuiUtils.updateModelItemWithPlot(
                self._data, QtCore.QVariant(self.pr_plot), title)
        if self.data_plot is not None:
            title = self.data_plot.name
            GuiUtils.updateModelItemWithPlot(
                self._data, QtCore.QVariant(self.data_plot), title)
        self.mapper.toFirst()

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

    def toggleBgd(self):
        """
        Toggle the background between manual and estimated
        """
        sender = self.sender()
        if sender is self.estimateBgd:
            self.backgroundInput.setEnabled(False)
        else:
            self.backgroundInput.setEnabled(True)

    def openExplorerWindow(self):
        """
        Open the Explorer window to see correlations between params and results
        """
        # TODO: Link Invertor() and DmaxWindow so window updates when recalculated
        from dmax import DmaxWindow
        self.dmaxWindow = DmaxWindow(self._calculator, self.getNFunc(), self)
        self.dmaxWindow.show()

    ######################################################################
    # Response Actions

    def setData(self, data_item=None, is_batch=False):
        """
        Assign new data set(s) to the P(r) perspective
        Obtain a QStandardItem object and parse it to get Data1D/2D
        Pass it over to the calculator
        """
        assert data_item is not None

        if not isinstance(data_item, list):
            msg = "Incorrect type passed to the P(r) Perspective"
            raise AttributeError, msg

        for data in data_item:
            # Create initial internal mappings
            self._data_list[data] = self._calculator.clone()
            self._data_set = GuiUtils.dataFromItem(data)
            self.data_plot_list[data] = self.data_plot
            self.pr_plot_list[data] = self.pr_plot
            ref_var = QtCore.QVariant(data)
            self.populateDataComboBox(self._data_set.filename, ref_var)
            self.setCurrentData(data)

            # Estimate initial values from data
            self.performEstimate()
            self.logic = InversionLogic(self._data_set)

            # Estimate q range
            qmin, qmax = self.logic.computeDataRange()
            self.model.setItem(WIDGETS.W_QMIN, QtGui.QStandardItem(
                "{:.4g}".format(qmin)))
            self.model.setItem(WIDGETS.W_QMAX, QtGui.QStandardItem(
                "{:.4g}".format(qmax)))

        self.enableButtons()

    def getNFunc(self):
        """Get the n_func value from the GUI object"""
        return int(UI.TabbedInversionUI._fromUtf8(self.noOfTermsInput.text()))

    def setCurrentData(self, data_ref):
        """Get the current data and display as necessary"""

        if not isinstance(data_ref, QtGui.QStandardItem):
            msg = "Incorrect type passed to the P(r) Perspective"
            raise AttributeError, msg

        # Data references
        self._data = data_ref
        self._data_set = GuiUtils.dataFromItem(data_ref)
        self._calculator = self._data_list[data_ref]
        self.pr_plot = self.pr_plot_list[data_ref]
        self.data_plot = self.data_plot_list[data_ref]

    ######################################################################
    # Thread Creators

    # TODO: Move to individual class(?)

    def startThreadAll(self):
        for data_ref, pr in self._data_list.items():
            self._data_set = GuiUtils.dataFromItem(data_ref)
            self._calculator = pr
            self.startThread()

    def startThread(self):
        """
            Start a calculation thread
        """
        from Thread import CalcPr

        # Set data before running the calculations
        self.update_calculator()

        # If a thread is already started, stop it
        if self.calc_thread is not None and self.calc_thread.isrunning():
            self.calc_thread.stop()
        pr = self._calculator.clone()
        nfunc = self.getNFunc()
        self.calc_thread = CalcPr(pr, nfunc,
                                  error_func=self._threadError,
                                  completefn=self._completed, updatefn=None)
        self.calc_thread.queue()
        self.calc_thread.ready(2.5)

    def performEstimateNT(self):
        """
            Perform parameter estimation
        """
        from Thread import EstimateNT

        # If a thread is already started, stop it
        if (self.estimation_thread is not None and
                self.estimation_thread.isrunning()):
            self.estimation_thread.stop()
        pr = self._calculator.clone()
        # Skip the slit settings for the estimation
        # It slows down the application and it doesn't change the estimates
        pr.slit_height = 0.0
        pr.slit_width = 0.0
        nfunc = self.getNFunc()
        self.estimation_thread = EstimateNT(pr, nfunc,
                                            error_func=self._threadError,
                                            completefn=self._estimateNTCompleted,
                                            updatefn=None)
        self.estimation_thread.queue()
        self.estimation_thread.ready(2.5)

    def performEstimate(self):
        """
            Perform parameter estimation
        """
        from Thread import EstimatePr

        self.startThread()

        # If a thread is already started, stop it
        if (self.estimation_thread is not None and
                self.estimation_thread.isrunning()):
            self.estimation_thread.stop()
        pr = self._calculator.clone()
        nfunc = self.getNFunc()
        self.estimation_thread = EstimatePr(pr, nfunc,
                                            error_func=self._threadError,
                                            completefn=self._estimateCompleted,
                                            updatefn=None)
        self.estimation_thread.queue()
        self.estimation_thread.ready(2.5)

    ######################################################################
    # Thread Complete

    def _estimateCompleted(self, alpha, message, elapsed):
        """
        Parameter estimation completed,
        display the results to the user

        :param alpha: estimated best alpha
        :param elapsed: computation time
        """
        # Save useful info
        self.model.setItem(WIDGETS.W_COMP_TIME,
                           QtGui.QStandardItem(str(elapsed)))
        self.regConstantSuggestionButton.setText(QtCore.QString(str(alpha)))
        self.regConstantSuggestionButton.setEnabled(True)
        if message:
            logging.info(message)
        self.performEstimateNT()

    def _estimateNTCompleted(self, nterms, alpha, message, elapsed):
        """
        Parameter estimation completed,
        display the results to the user

        :param alpha: estimated best alpha
        :param nterms: estimated number of terms
        :param elapsed: computation time

        """
        # Save useful info
        self.noOfTermsSuggestionButton.setText(QtCore.QString(
            "{:n}".format(nterms)))
        self.noOfTermsSuggestionButton.setEnabled(True)
        self.regConstantSuggestionButton.setText(QtCore.QString(
            "{:.3g}".format(alpha)))
        self.regConstantSuggestionButton.setEnabled(True)
        self.model.setItem(WIDGETS.W_COMP_TIME,
                           QtGui.QStandardItem(str(elapsed)))
        self.PrTabWidget.setCurrentIndex(0)
        if message:
            logging.info(message)

    def _completed(self, out, cov, pr, elapsed):
        """
        Method called with the results when the inversion is done

        :param out: output coefficient for the base functions
        :param cov: covariance matrix
        :param pr: Invertor instance
        :param elapsed: time spent computing

        """
        # Save useful info
        cov = np.ascontiguousarray(cov)
        pr.cov = cov
        pr.out = out
        pr.elapsed = elapsed

        # Show result on control panel

        # TODO: Connect self._calculator to GUI - two-to-one connection possible?
        self.model.setItem(WIDGETS.W_RG, QtGui.QStandardItem(str(pr.rg(out))))
        self.model.setItem(WIDGETS.W_I_ZERO,
                           QtGui.QStandardItem(str(pr.iq0(out))))
        self.model.setItem(WIDGETS.W_BACKGROUND_INPUT,
                           QtGui.QStandardItem("{:.3f}".format(pr.background)))
        self.model.setItem(WIDGETS.W_BACKGROUND_OUTPUT,
                           QtGui.QStandardItem(str(pr.background)))
        self.model.setItem(WIDGETS.W_CHI_SQUARED,
                           QtGui.QStandardItem(str(pr.chi2[0])))
        self.model.setItem(WIDGETS.W_COMP_TIME,
                           QtGui.QStandardItem(str(elapsed)))
        self.model.setItem(WIDGETS.W_OSCILLATION,
                           QtGui.QStandardItem(str(pr.oscillations(out))))
        self.model.setItem(WIDGETS.W_POS_FRACTION,
                           QtGui.QStandardItem(str(pr.get_positive(out))))
        self.model.setItem(WIDGETS.W_SIGMA_POS_FRACTION,
                           QtGui.QStandardItem(str(pr.get_pos_err(out, cov))))

        # Display results tab
        self.PrTabWidget.setCurrentIndex(1)
        # Save Pr invertor
        self._calculator = pr
        # Append data to data list
        self._data_list[self._data] = self._calculator.clone()

        # Create new P(r) and fit plots
        if self.pr_plot is None:
            self.pr_plot = self.logic.newPRPlot(out, self._calculator, cov)
            self.pr_plot_list[self._data] = self.pr_plot
        else:
            # FIXME: this should update the existing plot, not create a new one
            self.pr_plot = self.logic.newPRPlot(out, self._calculator, cov)
            self.pr_plot_list[self._data] = self.pr_plot
        if self.data_plot is None:
            self.data_plot = self.logic.new1DPlot(out, self._calculator)
            self.data_plot_list[self._data] = self.data_plot
        else:
            # FIXME: this should update the existing plot, not create a new one
            self.data_plot = self.logic.new1DPlot(out, self._calculator)
            self.data_plot_list[self._data] = self.data_plot

    def _threadError(self, error):
        """
            Call-back method for calculation errors
        """
        logging.warning(error)
