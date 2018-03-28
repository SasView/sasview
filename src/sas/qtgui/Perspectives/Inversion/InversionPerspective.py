import sys
import logging
import pylab
import numpy as np

from PyQt5 import QtGui, QtCore, QtWidgets

# sas-global
import sas.qtgui.Utilities.GuiUtils as GuiUtils

# pr inversion GUI elements
from .InversionUtils import WIDGETS
from .UI.TabbedInversionUI import Ui_PrInversion
from .InversionLogic import InversionLogic

# pr inversion calculation elements
from sas.sascalc.pr.invertor import Invertor

def is_float(value):
    """Converts text input values to floats. Empty strings throw ValueError"""
    try:
        return float(value)
    except ValueError:
        return 0.0

NUMBER_OF_TERMS = 10
REGULARIZATION = 0.0001
BACKGROUND_INPUT = 0.0
MAX_DIST = 140.0
DICT_KEYS = ["Calculator", "PrPlot", "DataPlot", "DMaxWindow", "NFuncEst"]


# TODO: Explore window not working
# TODO: Update help with batch capabilities
# TODO: Method to export results in some meaningful way
class InversionWindow(QtWidgets.QDialog, Ui_PrInversion):
    """
    The main window for the P(r) Inversion perspective.
    """

    name = "Inversion"
    estimateSignal = QtCore.pyqtSignal(tuple)
    estimateNTSignal = QtCore.pyqtSignal(tuple)
    calculateSignal = QtCore.pyqtSignal(tuple)

    def __init__(self, parent=None, data=None):
        super(InversionWindow, self).__init__()
        self.setupUi(self)

        self.setWindowTitle("P(r) Inversion Perspective")

        self._manager = parent
        self.communicate = GuiUtils.Communicate()

        self.logic = InversionLogic()

        # The window should not close
        self._allow_close = False

        # Visible data set items
        # current QStandardItem showing on the panel
        self._data = None
        # current Data1D as referenced by self._data
        self._data_set = None
        # Reference to Dmax window for self._data
        self.dmaxWindow = None
        # p(r) calculator for self._data
        self._calculator = Invertor()
        # Default to background estimate
        self._calculator.set_est_bck(True)
        # plots of self._data
        self.pr_plot = None
        self.data_plot = None
        # suggested nTerms
        self.nTermsSuggested = NUMBER_OF_TERMS

        # Calculation threads used by all data items
        self.calc_thread = None
        self.estimation_thread = None

        # Mapping for all data items
        # list mapping data to all parameters
        self._data_list = {}
        if not isinstance(data, list):
            data_list = [data]
        if data is not None:
            for datum in data_list:
                self.updateDataList(datum)

        self.enableButtons()

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
            # Tell the MdiArea to close the container
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
        self.dataList.currentIndexChanged.connect(self.displayChange)
        self.calculateAllButton.clicked.connect(self.startThreadAll)
        self.calculateThisButton.clicked.connect(self.startThread)
        self.removeButton.clicked.connect(self.removeData)
        self.helpButton.clicked.connect(self.help)
        self.estimateBgd.toggled.connect(self.toggleBgd)
        self.manualBgd.toggled.connect(self.toggleBgd)
        self.regConstantSuggestionButton.clicked.connect(self.acceptAlpha)
        self.noOfTermsSuggestionButton.clicked.connect(self.acceptNoTerms)
        self.explorerButton.clicked.connect(self.openExplorerWindow)

        self.backgroundInput.editingFinished.connect(
            lambda: self._calculator.set_background(is_float(self.backgroundInput.text())))
        self.minQInput.editingFinished.connect(
            lambda: self._calculator.set_qmin(is_float(self.minQInput.text())))
        self.regularizationConstantInput.editingFinished.connect(
            lambda: self._calculator.set_alpha(is_float(self.regularizationConstantInput.text())))
        self.maxDistanceInput.editingFinished.connect(
            lambda: self._calculator.set_dmax(is_float(self.maxDistanceInput.text())))
        self.maxQInput.editingFinished.connect(
            lambda: self._calculator.set_qmax(is_float(self.maxQInput.text())))
        self.slitHeightInput.editingFinished.connect(
            lambda: self._calculator.set_slit_height(is_float(self.slitHeightInput.text())))
        self.slitWidthInput.editingFinished.connect(
            lambda: self._calculator.set_slit_width(is_float(self.slitHeightInput.text())))

        self.model.itemChanged.connect(self.model_changed)
        self.estimateNTSignal.connect(self._estimateNTUpdate)
        self.estimateSignal.connect(self._estimateUpdate)
        self.calculateSignal.connect(self._calculateUpdate)

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
        self.mapper.addMapping(self.regularizationConstantInput, WIDGETS.W_REGULARIZATION)
        self.mapper.addMapping(self.regConstantSuggestionButton, WIDGETS.W_REGULARIZATION_SUGGEST)
        self.mapper.addMapping(self.explorerButton, WIDGETS.W_EXPLORE)
        self.mapper.addMapping(self.maxDistanceInput, WIDGETS.W_MAX_DIST)
        self.mapper.addMapping(self.noOfTermsInput, WIDGETS.W_NO_TERMS)
        self.mapper.addMapping(self.noOfTermsSuggestionButton, WIDGETS.W_NO_TERMS_SUGGEST)

        # Output
        self.mapper.addMapping(self.rgValue, WIDGETS.W_RG)
        self.mapper.addMapping(self.iQ0Value, WIDGETS.W_I_ZERO)
        self.mapper.addMapping(self.backgroundValue, WIDGETS.W_BACKGROUND_OUTPUT)
        self.mapper.addMapping(self.computationTimeValue, WIDGETS.W_COMP_TIME)
        self.mapper.addMapping(self.chiDofValue, WIDGETS.W_CHI_SQUARED)
        self.mapper.addMapping(self.oscillationValue, WIDGETS.W_OSCILLATION)
        self.mapper.addMapping(self.posFractionValue, WIDGETS.W_POS_FRACTION)
        self.mapper.addMapping(self.sigmaPosFractionValue, WIDGETS.W_SIGMA_POS_FRACTION)

        # Main Buttons
        self.mapper.addMapping(self.removeButton, WIDGETS.W_REMOVE)
        self.mapper.addMapping(self.calculateAllButton, WIDGETS.W_CALCULATE_ALL)
        self.mapper.addMapping(self.calculateThisButton, WIDGETS.W_CALCULATE_VISIBLE)
        self.mapper.addMapping(self.helpButton, WIDGETS.W_HELP)

        self.mapper.toFirst()

    def setupModel(self):
        """
        Update boxes with initial values
        """
        item = QtGui.QStandardItem(str(BACKGROUND_INPUT))
        self.model.setItem(WIDGETS.W_BACKGROUND_INPUT, item)
        item = QtGui.QStandardItem("")
        self.model.setItem(WIDGETS.W_QMIN, item)
        item = QtGui.QStandardItem("")
        self.model.setItem(WIDGETS.W_QMAX, item)
        item = QtGui.QStandardItem("")
        self.model.setItem(WIDGETS.W_SLIT_WIDTH, item)
        item = QtGui.QStandardItem("")
        self.model.setItem(WIDGETS.W_SLIT_HEIGHT, item)
        item = QtGui.QStandardItem(str(NUMBER_OF_TERMS))
        self.model.setItem(WIDGETS.W_NO_TERMS, item)
        item = QtGui.QStandardItem(str(REGULARIZATION))
        self.model.setItem(WIDGETS.W_REGULARIZATION, item)
        item = QtGui.QStandardItem(str(MAX_DIST))
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
        self.enableButtons()
        self.estimateBgd.setChecked(True)

    def setupValidators(self):
        """Apply validators to editable line edits"""
        self.noOfTermsInput.setValidator(QtGui.QIntValidator())
        self.regularizationConstantInput.setValidator(GuiUtils.DoubleValidator())
        self.maxDistanceInput.setValidator(GuiUtils.DoubleValidator())
        self.minQInput.setValidator(GuiUtils.DoubleValidator())
        self.maxQInput.setValidator(GuiUtils.DoubleValidator())
        self.slitHeightInput.setValidator(GuiUtils.DoubleValidator())
        self.slitWidthInput.setValidator(GuiUtils.DoubleValidator())

    ######################################################################
    # Methods for updating GUI

    def enableButtons(self):
        """
        Enable buttons when data is present, else disable them
        """
        self.calculateAllButton.setEnabled(self.logic.data_is_loaded)
        self.calculateThisButton.setEnabled(self.logic.data_is_loaded)
        self.removeButton.setEnabled(self.logic.data_is_loaded)
        self.explorerButton.setEnabled(self.logic.data_is_loaded)
        self.regConstantSuggestionButton.setEnabled(
            self._calculator.suggested_alpha != self._calculator.alpha)
        self.noOfTermsSuggestionButton.setEnabled(
            self._calculator.nfunc != self.nTermsSuggested)

    def populateDataComboBox(self, filename, data_ref):
        """
        Append a new file name to the data combobox
        :param filename: data filename
        :param data_ref: QStandardItem reference for data set to be added
        """
        self.dataList.addItem(filename, data_ref)

    def acceptNoTerms(self):
        """Send estimated no of terms to input"""
        self.model.setItem(WIDGETS.W_NO_TERMS, QtGui.QStandardItem(
            self.noOfTermsSuggestionButton.text()))

    def acceptAlpha(self):
        """Send estimated alpha to input"""
        self.model.setItem(WIDGETS.W_REGULARIZATION, QtGui.QStandardItem(
            self.regConstantSuggestionButton.text()))

    def displayChange(self):
        """Switch to another item in the data list"""
        ref_item = self.dataList.itemData(self.dataList.currentIndex())
        self.updateDataList(ref_item)
        self.setCurrentData(ref_item)

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
            InversionWindow.__init__(self.parent(), list(self._data_list.keys()))
            exit(0)
        if self.pr_plot is not None:
            title = self.pr_plot.name
            GuiUtils.updateModelItemWithPlot(self._data, self.pr_plot, title)
        if self.data_plot is not None:
            title = self.data_plot.name
            GuiUtils.updateModelItemWithPlot(self._data, self.data_plot, title)
        if self.dmaxWindow is not None:
            self.dmaxWindow.pr_state = self._calculator
            self.dmaxWindow.nfunc = self.getNFunc()
            self.dmaxWindow.modelChanged()
        self.mapper.toFirst()

    def help(self):
        """
        Open the P(r) Inversion help browser
        """
        tree_location = "/user/sasgui/perspectives/pr/pr_help.html"

        # Actual file anchor will depend on the combo box index
        # Note that we can be clusmy here, since bad current_fitter_id
        # will just make the page displayed from the top
        self._manager.showHelp(tree_location)

    def toggleBgd(self):
        """
        Toggle the background between manual and estimated
        """
        sender = self.sender()
        if sender is self.estimateBgd:
            self.backgroundInput.setEnabled(False)
            self._calculator.set_est_bck = True
        else:
            self.backgroundInput.setEnabled(True)
            self._calculator.set_est_bck = False

    def openExplorerWindow(self):
        """
        Open the Explorer window to see correlations between params and results
        """
        from .DMaxExplorerWidget import DmaxWindow
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
            raise AttributeError(msg)

        for data in data_item:
            if data in self._data_list.keys():
                # Don't add data if it's already in
                return
            # Create initial internal mappings
            self._data_set = GuiUtils.dataFromItem(data)
            self.logic = InversionLogic(self._data_set)
            self.populateDataComboBox(self._data_set.filename, data)
            # Estimate q range
            qmin, qmax = self.logic.computeDataRange()
            self._calculator.set_qmin(qmin)
            self._calculator.set_qmax(qmax)
            self.updateDataList(data)
            self.setCurrentData(data)
            # Estimate initial values from data
            self.performEstimate()
        self.updateGuiValues()

    def updateDataList(self, dataRef):
        """Save the current data state of the window into self._data_list"""
        if dataRef is None:
            return
        self._data_list[dataRef] = {
            DICT_KEYS[0]: self._calculator,
            DICT_KEYS[1]: self.pr_plot,
            DICT_KEYS[2]: self.data_plot,
            DICT_KEYS[3]: self.dmaxWindow,
            DICT_KEYS[4]: self.nTermsSuggested
        }

    def getNFunc(self):
        """Get the n_func value from the GUI object"""
        try:
            nfunc = int(self.noOfTermsInput.text())
        except ValueError:
            logging.error("Incorrect number of terms specified: %s" %self.noOfTermsInput.text())
            self.noOfTermsInput.setText(str(NUMBER_OF_TERMS))
            nfunc = NUMBER_OF_TERMS
        return nfunc

    def setCurrentData(self, data_ref):
        """Get the data by reference and display as necessary"""
        if data_ref is None:
            return
        if not isinstance(data_ref, QtGui.QStandardItem):
            msg = "Incorrect type passed to the P(r) Perspective"
            raise AttributeError(msg)
        # Data references
        self._data = data_ref
        self._data_set = GuiUtils.dataFromItem(data_ref)
        self._calculator = self._data_list[data_ref].get(DICT_KEYS[0])
        self.pr_plot = self._data_list[data_ref].get(DICT_KEYS[1])
        self.data_plot = self._data_list[data_ref].get(DICT_KEYS[2])
        self.dmaxWindow = self._data_list[data_ref].get(DICT_KEYS[3])
        self.nTermsSuggested = self._data_list[data_ref].get(DICT_KEYS[4])
        self.logic.set_data = self._data_set
        self.updateGuiValues()

    def updateGuiValues(self):
        pr = self._calculator
        out = self._calculator.out
        cov = self._calculator.cov
        elapsed = self._calculator.elapsed
        alpha = self._calculator.suggested_alpha
        nterms = self._calculator.nfunc
        self.model.setItem(WIDGETS.W_QMIN,
                           QtGui.QStandardItem("{:.4g}".format(pr.get_qmin())))
        self.model.setItem(WIDGETS.W_QMAX,
                           QtGui.QStandardItem("{:.4g}".format(pr.get_qmax())))
        self.model.setItem(WIDGETS.W_BACKGROUND_INPUT,
                           QtGui.QStandardItem("{:.3f}".format(pr.background)))
        self.model.setItem(WIDGETS.W_BACKGROUND_OUTPUT,
                           QtGui.QStandardItem("{:.3g}".format(pr.background)))
        self.model.setItem(WIDGETS.W_COMP_TIME,
                           QtGui.QStandardItem("{:.4g}".format(elapsed)))
        self.regConstantSuggestionButton.setText("{:-3.2g}".format(alpha))
        self.noOfTermsSuggestionButton.setText(
            "{:n}".format(self.nTermsSuggested))
        self.model.setItem(WIDGETS.W_COMP_TIME,
                           QtGui.QStandardItem("{:.2g}".format(elapsed)))

        if isinstance(pr.chi2, np.ndarray):
            self.model.setItem(WIDGETS.W_CHI_SQUARED,
                               QtGui.QStandardItem("{:.3g}".format(pr.chi2[0])))
        if out is not None:
            self.model.setItem(WIDGETS.W_RG,
                               QtGui.QStandardItem("{:.3g}".format(pr.rg(out))))
            self.model.setItem(WIDGETS.W_I_ZERO,
                               QtGui.QStandardItem(
                                   "{:.3g}".format(pr.iq0(out))))
            self.model.setItem(WIDGETS.W_OSCILLATION, QtGui.QStandardItem(
                "{:.3g}".format(pr.oscillations(out))))
            self.model.setItem(WIDGETS.W_POS_FRACTION, QtGui.QStandardItem(
                "{:.3g}".format(pr.get_positive(out))))
            if cov is not None:
                self.model.setItem(WIDGETS.W_SIGMA_POS_FRACTION,
                                   QtGui.QStandardItem(
                                       "{:.3g}".format(
                                           pr.get_pos_err(out, cov))))
        self.enableButtons()

    def removeData(self):
        """Remove the existing data reference from the P(r) Persepective"""
        if self.dmaxWindow is not None:
            self.dmaxWindow.done()
            self.dmaxWindow = None
        self.dataList.removeItem(self.dataList.currentIndex())
        self._data_list.pop(self._data)
        # Last file removed
        if len(self._data_list) == 0:
            self._data = None
            self._data_set = None
            self.pr_plot = None
            self.data_plot = None
            self._calculator = Invertor()
            self.logic.data = self._data_set
            self.nTermsSuggested = NUMBER_OF_TERMS
            self.noOfTermsSuggestionButton.setText("{:n}".format(
                self.nTermsSuggested))
            self.regConstantSuggestionButton.setText("{:-3.2g}".format(
                REGULARIZATION))
            self.enableButtons()
            self.setupModel()
        else:
            self.dataList.setCurrentIndex(0)
            self.updateGuiValues()

    ######################################################################
    # Thread Creators
    def startThreadAll(self):
        for data_ref in self._data_list.keys():
            self.setCurrentData(data_ref)
            self.startThread()

    def startThread(self):
        """
            Start a calculation thread
        """
        from .Thread import CalcPr

        # Set data before running the calculations
        self.update_calculator()

        # If a thread is already started, stop it
        if self.calc_thread is not None and self.calc_thread.isrunning():
            self.calc_thread.stop()
        pr = self._calculator.clone()
        nfunc = self.getNFunc()
        self.calc_thread = CalcPr(pr, nfunc,
                                  error_func=self._threadError,
                                  completefn=self._calculateCompleted,
                                  updatefn=None)
        self.calc_thread.queue()
        self.calc_thread.ready(2.5)

    def performEstimateNT(self):
        """
        Perform parameter estimation
        """
        from .Thread import EstimateNT

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
        from .Thread import EstimatePr

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
        ''' Send a signal to the main thread for model update'''
        self.estimateSignal.emit((alpha, message, elapsed))

    def _estimateUpdate(self, output_tuple):
        """
        Parameter estimation completed,
        display the results to the user

        :param alpha: estimated best alpha
        :param elapsed: computation time
        """
        alpha, message, elapsed = output_tuple
        if message:
            logging.info(message)
        self.performEstimateNT()

    def _estimateNTCompleted(self, nterms, alpha, message, elapsed):
        ''' Send a signal to the main thread for model update'''
        self.estimateNTSignal.emit((nterms, alpha, message, elapsed))

    def _estimateNTUpdate(self, output_tuple):
        """
        Parameter estimation completed,
        display the results to the user

        :param alpha: estimated best alpha
        :param nterms: estimated number of terms
        :param elapsed: computation time
        """
        nterms, alpha, message, elapsed = output_tuple
        self._calculator.elapsed = elapsed
        self._calculator.suggested_alpha = alpha
        self.nTermsSuggested = nterms
        # Save useful info
        self.updateGuiValues()
        if message:
            logging.info(message)

    def _calculateCompleted(self, out, cov, pr, elapsed):
        ''' Send a signal to the main thread for model update'''
        self.calculateSignal.emit((out, cov, pr, elapsed))

    def _calculateUpdate(self, output_tuple):
        """
        Method called with the results when the inversion is done

        :param out: output coefficient for the base functions
        :param cov: covariance matrix
        :param pr: Invertor instance
        :param elapsed: time spent computing
        """
        out, cov, pr, elapsed = output_tuple
        # Save useful info
        cov = np.ascontiguousarray(cov)
        pr.cov = cov
        pr.out = out
        pr.elapsed = elapsed

        # Save Pr invertor
        self._calculator = pr

        # Create new P(r) and fit plots
        if self.pr_plot is None:
            self.pr_plot = self.logic.newPRPlot(out, self._calculator, cov)
        if self.data_plot is None:
            self.data_plot = self.logic.new1DPlot(out, self._calculator)
        self.updateDataList(self._data)
        self.updateGuiValues()

    def _threadError(self, error):
        """
            Call-back method for calculation errors
        """
        logging.warning(error)
