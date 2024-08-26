import logging
import numpy as np
import sys

from PySide6 import QtGui, QtCore, QtWidgets



# sas-global
import sas.qtgui.Utilities.GuiUtils as GuiUtils
import sas.qtgui.Plotting.PlotHelper as PlotHelper

# pr inversion GUI elements
from .InversionUtils import WIDGETS
from sas.qtgui.Perspectives.Inversion.UI.TabbedInversionUI import Ui_PrInversion
from .InversionLogic import InversionLogic

# pr inversion calculation elements
from sas.sascalc.pr.invertor import Invertor
from sas.qtgui.Plotting.PlotterData import Data1D, DataRole

# Batch calculation display
from sas.qtgui.Utilities.GridPanel import BatchInversionOutputPanel
from ...Plotting.Plotter import Plotter
import sas.qtgui.Plotting.PlotHelper as PlotHelper

#regeneration of documentation
from pathlib import Path
from sas.sascalc.doc_regen.makedocumentation import IMAGES_DIRECTORY_LOCATION, HELP_DIRECTORY_LOCATION


def is_float(value):
    """Converts text input values to floats. Empty strings throw ValueError"""
    try:
        return float(value)
    except ValueError:
        return 0.0


# Default Values for inputs
NUMBER_OF_TERMS = 10
REGULARIZATION = 0.0
BACKGROUND_INPUT = 0.0
Q_MIN_INPUT = 0.0
Q_MAX_INPUT = 0.0
MAX_DIST = 140.0

DICT_KEYS = ["Calculator", "PrPlot", "DataPlot"]

logger = logging.getLogger(__name__)


class InversionWidget(QtWidgets.QWidget, Ui_PrInversion):
    """
    The main Interface for the P(r) Inversion perspective.
    This Class is responsible for displaying the component within the Inversion Tab
    """

    name = "Inversion"
    ext = "pr"  # Extension used for saving analyse

    estimateSignal = QtCore.Signal(tuple)
    estimateNTSignal = QtCore.Signal(tuple)
    estimateDynamicNTSignal = QtCore.Signal(tuple)
    estimateDynamicSignal = QtCore.Signal(tuple)
    calculateSignal = QtCore.Signal(tuple)

    plotUpdateSignal = QtCore.Signal(list)
    forcePlotDisplaySignal = QtCore.Signal(list)



    def __init__(self, parent=None, data=None, tab_id=1):
        super(InversionWidget, self).__init__()

        # Necessary globals
        self.parent = parent


        self.plot_widgets = {}
        self.active_plots = {}


        ########################################
        
        # Which tab is this widget displayed in?
        self.tab_id = tab_id


        # data index for the batch set
        self.data_index = 0
        self.tab_name = None

        self.setupUi(self)

        self.setWindowTitle("P(r) Inversion Perspective")

        #  set parent window and connect communicator
        self.communicate = self.parent.communicator()
        #self.communicator = self.parent.communicator()
        self.communicate.dataDeletedSignal.connect(self.removeData)
        self.batchResults = {}

        self.logic = InversionLogic()

        # current QStandardItem showing on the panel
        self.data = None

        if data is not None:
            self.data = data
            if isinstance(data, list):
                self.data = data

        # Reference to Dmax window for self.data
        self.dmaxWindow = None

        # p(r) calculator for self.data
        self._calculator = Invertor()

        # Default to background estimate
        self._calculator.est_bck = True

        # plots of self.data
        self.prPlot = None
        self.dataPlot = None
        self.plot1D = Plotter(quickplot=True)

        # suggested nTerms
        self.nTermsSuggested = NUMBER_OF_TERMS
        # suggested alpha
        self._calculator.alpha = REGULARIZATION
        


        self.maxIndex = 1

        # Calculation threads used by all data items
        self.calcThread = None
        self.estimationThread = None
        self.estimationThreadNT = None
        self.isCalculating = False

        # Dictionary mapping data to all parameters
        self.dataDictionary = {}


        # Mapping for all data items
        self.model = QtGui.QStandardItemModel(self)
        self.mapper = QtWidgets.QDataWidgetMapper(self)

        # Batch fitting parameters
        self.batchComplete = []
        self.is_batch = False
        self.batchResultsWindow = None
        self._allowPlots = False
        self.q_min = 0.0    
        self.q_max = np.inf

        if self.logic.data_is_loaded:
            self.q_min, self.q_max = self.logic.computeDataRange()         


        # Add validators
        self.setupValidators()

        # Link user interactions with methods
        self.setupLinks()

        # Set values
        self.setupModel()

        # Set up the Widget Map
        self.setupMapper()

        self.setupWindow()
        self.updateQRange(self.q_min, self.q_max)
        self.maxQInput.setText(str(self.q_max))
        self.minQInput.setText(str(self.q_min))

    ######################################################################
    # Base Perspective Class Definitions



    def setPlotable(self, value=True):
        """
        Let Plots to be displayable - needed so batch mode is not clutter with plots
        """
        assert isinstance(value, bool)
        self._allowPlots = value

    def isSerializable(self):
        """
        Tell the caller that this perspective writes its state
        """
        return True

    def closeDMax(self):
        if self.dmaxWindow is not None:
            self.dmaxWindow.close()

    def closeBatchResults(self):
        if self.batchResultsWindow is not None:
            self.batchResultsWindow.close()

    ######################################################################
    # Initialization routines

    def setupLinks(self):
        """Connect the use controls to their appropriate methods"""
        self.dataList.currentIndexChanged.connect(self.displayChange)
        self.calculateAllButton.clicked.connect(self.startThreadAll)
        self.calculateThisButton.clicked.connect(self.startThreadThis)
        self.stopButton.clicked.connect(self.stopCalculation)
        self.removeButton.clicked.connect(self.removeData)
        self.showResultsButton.clicked.connect(self.showBatchOutput)
        self.helpButton.clicked.connect(self.help)
        self.estimateBgd.toggled.connect(self.toggleBgd)
        self.manualBgd.toggled.connect(self.toggleBgd)
        self.regConstantSuggestionButton.clicked.connect(self.acceptAlpha)
        self.noOfTermsSuggestionButton.clicked.connect(self.acceptNoTerms)
        self.explorerButton.clicked.connect(self.openExplorerWindow)

        self.backgroundInput.textChanged.connect(
            lambda: self.set_background(self.backgroundInput.text()))
        self.noOfTermsInput.textChanged.connect(
            lambda: self.set_nTermsSuggested(self.noOfTermsInput.text()))
        self.regularizationConstantInput.textChanged.connect(
            lambda: self._calculator.set_alpha(is_float(self.regularizationConstantInput.text())))
        self.maxDistanceInput.textChanged.connect(
            lambda: self._calculator.set_dmax(is_float(self.maxDistanceInput.text())))
        

        # Signals asking for replot
        self.maxQInput.editingFinished.connect(
            lambda: self.updateMaxQ(is_float(self.maxQInput.text())))
        self.minQInput.editingFinished.connect(
            lambda: self.updateMinQ(is_float(self.minQInput.text())))
        self.slitHeightInput.textChanged.connect(
            lambda: self._calculator.set_slit_height(is_float(self.slitHeightInput.text())))
        self.slitWidthInput.textChanged.connect(
            lambda: self._calculator.set_slit_width(is_float(self.slitWidthInput.text())))


        #self.model.itemChanged.connect(self.model_changed) # disabled because it causes dataList to be set to prevous item. further debuging required.
        self.estimateNTSignal.connect(self._estimateNTUpdate)
        self.estimateDynamicNTSignal.connect(self._estimateDynamicNTUpdate)
        self.estimateDynamicSignal.connect(self._estimateDynamicUpdate)
        self.estimateSignal.connect(self._estimateUpdate)
        self.calculateSignal.connect(self._calculateUpdate)
        
        self.maxDistanceInput.textEdited.connect(self.performEstimateDynamic)
        



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

        # q_min/q_max
        self.mapper.addMapping(self.minQInput, WIDGETS.W_Q_MIN)
        self.mapper.addMapping(self.maxQInput, WIDGETS.W_Q_MAX)

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
        self.mapper.addMapping(self.showResultsButton, WIDGETS.W_CALCULATE_VISIBLE)
        self.mapper.addMapping(self.helpButton, WIDGETS.W_HELP)

        self.mapper.toFirst()

    def setupModel(self):
        """
        Update boxes with initial values
        """
        bgd_item = QtGui.QStandardItem(str(BACKGROUND_INPUT))
        self.model.setItem(WIDGETS.W_BACKGROUND_INPUT, bgd_item)
        q_min_item = QtGui.QStandardItem(str(Q_MIN_INPUT))
        self.model.setItem(WIDGETS.W_Q_MIN, q_min_item)
        q_max_item = QtGui.QStandardItem(str(Q_MAX_INPUT))
        self.model.setItem(WIDGETS.W_Q_MAX, q_max_item)
        blank_item = QtGui.QStandardItem("")
        self.model.setItem(WIDGETS.W_SLIT_WIDTH, blank_item)
        blank_item = QtGui.QStandardItem("")
        self.model.setItem(WIDGETS.W_SLIT_HEIGHT, blank_item)
        no_terms_item = QtGui.QStandardItem(str(NUMBER_OF_TERMS))
        self.model.setItem(WIDGETS.W_NO_TERMS, no_terms_item)
        reg_item = QtGui.QStandardItem(str(REGULARIZATION))
        self.model.setItem(WIDGETS.W_REGULARIZATION, reg_item)
        max_dist_item = QtGui.QStandardItem(str(MAX_DIST))
        self.model.setItem(WIDGETS.W_MAX_DIST, max_dist_item)
        blank_item = QtGui.QStandardItem("")
        self.model.setItem(WIDGETS.W_RG, blank_item)
        blank_item = QtGui.QStandardItem("")
        self.model.setItem(WIDGETS.W_I_ZERO, blank_item)
        bgd_item = QtGui.QStandardItem(str(BACKGROUND_INPUT))
        self.model.setItem(WIDGETS.W_BACKGROUND_OUTPUT, bgd_item)
        blank_item = QtGui.QStandardItem("")
        self.model.setItem(WIDGETS.W_COMP_TIME, blank_item)
        blank_item = QtGui.QStandardItem("")
        self.model.setItem(WIDGETS.W_CHI_SQUARED, blank_item)
        blank_item = QtGui.QStandardItem("")
        self.model.setItem(WIDGETS.W_OSCILLATION, blank_item)
        blank_item = QtGui.QStandardItem("")
        self.model.setItem(WIDGETS.W_POS_FRACTION, blank_item)
        blank_item = QtGui.QStandardItem("")
        self.model.setItem(WIDGETS.W_SIGMA_POS_FRACTION, blank_item)


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
        self.calculateAllButton.setEnabled(not self.isCalculating
                                           and self.logic.data_is_loaded and self.is_batch)
        self.calculateThisButton.setEnabled(self.logic.data_is_loaded
                                            and not self.isCalculating and not self.is_batch)
        self.calculateThisButton.setVisible(not self.is_batch and not self.isCalculating)
        self.calculateAllButton.setVisible(self.is_batch and not self.isCalculating)
        
        self.showResultsButton.setEnabled(self.logic.data_is_loaded
                                          and self.is_batch
                                          and not self.isCalculating and self.batchResultsWindow is not None)
        self.removeButton.setEnabled(self.logic.data_is_loaded and not self.isCalculating)
        self.explorerButton.setEnabled(self.logic.data_is_loaded and not self.isCalculating)
        self.stopButton.setVisible(self.isCalculating)
        self.regConstantSuggestionButton.setEnabled(self.logic.data_is_loaded and not self.isCalculating)
        self.noOfTermsSuggestionButton.setEnabled(self.logic.data_is_loaded and not self.isCalculating)



    def populateDataComboBox(self, name, data_ref):
        """
        Append a new name to the data combobox
        :param name: data name
        :param data_ref: QStandardItem reference for data set to be added
        """
        self.dataList.addItem(name, data_ref)

    def swapDataComboBox(self, name, data_ref):
        """
        Append a new name to the data combobox
        :param name: data name
        :param data_ref: QStandardItem reference for data set to be added
        """
        index = self.dataList.count()
        # if some data already in the box
        if index > 0: 
            self.dataList.clear()
        self.dataList.addItem(name, data_ref)

    def acceptNoTerms(self):
        """Send estimated no of terms to input"""
        self.model.setItem(WIDGETS.W_NO_TERMS, QtGui.QStandardItem(
            self.noOfTermsSuggestionButton.text()))

    def acceptAlpha(self):
        """Send estimated alpha to input"""
        self.model.setItem(WIDGETS.W_REGULARIZATION, QtGui.QStandardItem(
            self.regConstantSuggestionButton.text()))

    def acceptsData(self):
        """ Tells the caller this widget can accept new dataset """
        return not self.logic.data_is_loaded

    def displayChange(self, data_index = None):
        """Switch to another item in the data list"""
        if isinstance(self.data, list):
            return
        try:
            self.updateDataList(self.data)
            self.setCurrentData(self.dataList.itemData(data_index)) 
            self.updateDynamicGuiValues(data_index)
            self.updateGuiValues(data_index)
            self.enableButtons()
        except KeyError:
            # Data might be removed
            return

    def setQ(self):
        """calculate qmin and qmax values and update calculator accordingly"""
        if self.logic.data_is_loaded:
            self.q_min, self.q_max = self.logic.computeDataRange()               
              
        self.updateMinQ(self.q_min)
        self.updateMaxQ(self.q_max)

    def updateTab(self, data = None, tab_index=None):
        self.logic.data = GuiUtils.dataFromItem(data)
        self.swapDataComboBox(self.logic.data.name, data)        


    #1D data                     
        self.logic.add_errors()    
        self.setQ()
        self.updateDynamicGuiValues()
        self.updateGuiValues()
        self.enableButtons()
        self.calculateAllButton.setVisible(False)
        self.showResultsButton.setVisible(False)


    def addPlot(self, new_plot): 
        title = str(PlotHelper.idOfPlot(new_plot))
        new_plot.setWindowTitle(title)

        # Set the object name to satisfy the Squish object picker
        new_plot.setObjectName(title)

        # Add the plot to the workspace
        plot_widget = self.parent.workspace().addSubWindow(new_plot)
        #if sys.platform == 'darwin':
        workspace_height = int(float(self.parent.workspace().sizeHint().height()) / 2)
        workspace_width = int(float(self.parent.workspace().sizeHint().width()) / 2)
        plot_widget.resize(workspace_width, workspace_height)

        # Show the plot
        new_plot.show()
        new_plot.canvas.draw()

        # Update the plot widgets dict
        self.plot_widgets[title] = plot_widget

        # Update the active chart list
        self.active_plots[new_plot.data[0].name] = new_plot
        
    ######################################################################
    # GUI Interaction Events

    def updateCalculator(self):
        """Update all p(r) params"""
        self._calculator.set_x(self.logic.data.x)
        self._calculator.set_y(self.logic.data.y)   
        self.logic.data.dy = self.logic.add_errors()        
        self._calculator.set_err(self.logic.data.dy)
        #self.q_min, self.q_max = self.logic.computeDataRange() 
        self.updateMinQ(self.q_min)
        self.updateMaxQ(self.q_max)
        self.set_background(self.backgroundInput.text())
        self.set_nTermsSuggested(self.noOfTermsInput.text())
        self._calculator.set_alpha(is_float(self.regularizationConstantInput.text()))
        self._calculator.set_dmax(is_float(self.maxDistanceInput.text()))

    def set_background(self, value):
        """sets background"""
        if value and (isinstance(value, (float, str))):
            self._calculator.background = float(value)
 
    def set_nTermsSuggested(self, value):
        """noOfTerms"""
        if value and (isinstance(value, (float, str))):
            self.nTermsSuggested = float(value)       



    def model_changed(self):
        """Update the values when user makes changes"""
        if not self.mapper:
            msg = "Unable to update P{r}. The connection between the main GUI "
            msg += "and P(r) was severed. Attempting to restart P(r)."
            logger.warning(msg)
            self.setClosable(True)
            self.close()
            InversionWidget.__init__(self.parent(), list(self.dataDictionary.keys()))
            exit(0)
        if self.dmaxWindow is not None:
            self.dmaxWindow.nfunc = self.getNFunc()
            self.dmaxWindow.pr_state = self._calculator
        self.mapper.toLast()

    def help(self):
        """
        Open the P(r) Inversion help browser
        """
        tree_location = "/user/qtgui/Perspectives/Inversion/pr_help.html"

        # Actual file anchor will depend on the combo box index
        # Note that we can be clusmy here, since bad current_fitter_id
        # will just make the page displayed from the top
        self.parent.showHelp(tree_location)

    def toggleBgd(self):
        """
        Toggle the background between manual and estimated
        """
        self.model.blockSignals(True)
        value = 1 if self.estimateBgd.isChecked() else 0
        itemt = QtGui.QStandardItem(str(value == 1).lower())
        self.model.setItem(WIDGETS.W_ESTIMATE, itemt)
        itemt = QtGui.QStandardItem(str(value == 0).lower())
        self.model.setItem(WIDGETS.W_MANUAL_INPUT, itemt)
        self._calculator.set_est_bck(value)
        self.backgroundInput.setEnabled(self._calculator.est_bck == 0)
        self.model.blockSignals(False)

    def openExplorerWindow(self):
        """
        Open the Explorer window to see correlations between params and results
        """
        from .DMaxExplorerWidget import DmaxWindow
        self.dmaxWindow = DmaxWindow(pr_state=self._calculator,
                                     nfunc=self.getNFunc(),
                                     parent=self)
        #Do the inversion to get the parameters
        self.startThread()
        self.dmaxWindow.show()

    def showBatchOutput(self):
        """
        Display the batch output in tabular form
        :param output_data: Dictionary mapping name -> P(r) instance
         """

        # if batch results window is not initialized yet, then create a new table.
        # else add to the tabs.
        if self.batchResultsWindow is None:
            self.batchResultsWindow = BatchInversionOutputPanel(
                parent=self,
                output_data=self.batchResults)
        else:
            self.batchResultsWindow.newTableTab(data=self.batchResults)
        self.batchResultsWindow.show()

    def stopCalculation(self):
        """ Stop all threads, return to the base state and update GUI """
        self.stopCalcThread()
        self.stopEstimationThread()
        self.stopEstimateNTThread()
        self.updateGuiValues()
        
        self.isCalculating = False
        
        self.enableButtons()
        # Show any batch calculations that successfully completed
        if self.is_batch and self.batchResultsWindow is not None:                    
            #self.showBatchOutput()
            self.calculateAllButton.setText("Calculate All")
            self.updateGuiValues(index=self.dataList.currentIndex())
            self.updateDynamicGuiValues(index=self.dataList.currentIndex())
        
    def onHelp(self):
        """
        Show the "Inversion" section of help
        """
        regen_in_progress = False
        help_location = self.getHelpLocation(HELP_DIRECTORY_LOCATION)
        if regen_in_progress is False:
            self.parent.showHelp(help_location)

            
    def getHelpLocation(self, tree_base) -> Path:
        # Actual file will depend on the current tab
        tree_location = tree_base / "user" / "qtgui" / "Perspectives" / "Inversion"
        return tree_location / "pr_help.html"


    def updateMinQ(self, q_value=None):
        """ Validate the low q value """
        if q_value is None:
            q_value = self.q_min
       
        q_min = float(q_value) 
        self.q_min = q_min
        if self._calculator is not None:    
            self._calculator.set_q_min(q_min)

        self.minQInput.setText(f"{float(q_min):.3}") 
        self.model.setItem(WIDGETS.W_Q_MIN, QtGui.QStandardItem("{:.4g}".format(q_min)))
        
    def updateMaxQ(self, q_value=None ):
        """ Validate the value of high q """
        if q_value is None:
           q_value = self.q_max
        q_max = float(q_value)                       

        self.q_max = q_max
        if self._calculator is not None:    
            self._calculator.set_q_max(q_max)
        self.maxQInput.setText(f"{float(q_max):.3}") 
        self.model.setItem(WIDGETS.W_Q_MAX, QtGui.QStandardItem("{:.4g}".format(q_max)))


    def updateQRange(self, q_range_min, q_range_max):
        """
        Update the local model based on calculated values
        """
        if q_range_max is not None:
            self.q_max = q_range_max
        else:
            self.q_max = np.inf
        if q_range_min is not None:
            self.q_min = q_range_min
        else:
            self.q_min = 0.0    
        if self._calculator is not None:    
            self._calculator.set_q_min(self.q_min)
            self._calculator.set_q_max(self.q_max)
        self.maxQInput.setText(f"{float(self.q_max):.3}") 
        self.minQInput.setText(f"{float(self.q_min):.3}") 

    ######################################################################
    # Response Actions

    def updateDataList(self, dataRef):
        """Save the current data state of the window into self.data_list"""
        if dataRef is None:
            return
        self.saveParameters()
        self.dataDictionary[dataRef] = {
            DICT_KEYS[0]: self._calculator,
            DICT_KEYS[1]: self.prPlot,
            DICT_KEYS[2]: self.dataPlot
        }

    def saveToBatchResults(self):
        """Save the current data state of the window into the batchResults"""
        try:
            self.batchResults[self.logic.data.name] = {
            DICT_KEYS[0]: self._calculator,
            DICT_KEYS[1]: self.prPlot,
            DICT_KEYS[2]: self.dataPlot
        }
        except TypeError:
            logging.error("Failed to save data for batch results.")

    def saveParameters(self):
        """Save any parameters set by the user"""
        # remove the need for the extra noOfTerms regConst and maxDist
        self._calculator.noOfTerms = int(self.getNFunc())
        self._calculator.regConst = is_float(self.regularizationConstantInput.text())
        self._calculator.maxDist = is_float(self.maxDistanceInput.text())
        self._calculator.background = is_float(self.backgroundInput.text())
        self._calculator.set_slit_height(is_float(self.slitHeightInput.text()))
        self._calculator.set_slit_width(is_float(self.slitWidthInput.text()))
        self._calculator.set_q_min(is_float(self.minQInput.text()))
        self._calculator.set_q_max(is_float(self.maxQInput.text()))

    def setParameters(self):
        try:
            """ sets parameters previously saved with saveParameters """
            self.noOfTermsInput.setText(str(self.dataDictionary[self.data].get(DICT_KEYS[0]).noOfTerms))
            self.regularizationConstantInput.setText(str(self.dataDictionary[self.data].get(DICT_KEYS[0]).regConst))
            self.maxDistanceInput.setText(str(self.dataDictionary[self.data].get(DICT_KEYS[0]).maxDist))
            self.backgroundInput.setText(str(self.dataDictionary[self.data].get(DICT_KEYS[0]).background))
            self.minQInput.setText(str(self.dataDictionary[self.data].get(DICT_KEYS[0]).q_min))
            self.maxQInput.setText(str(self.dataDictionary[self.data].get(DICT_KEYS[0]).q_max))
            self.slitHeightInput.setText(str(self.dataDictionary[self.data].get(DICT_KEYS[0]).slit_height))
            self.slitWidthInput.setText(str(self.dataDictionary[self.data].get(DICT_KEYS[0]).slit_width))
            
        except:
            # Data might be removed
            self.setDefaultParameters()

    def setDefaultParameters(self):        
        """ sets to default parameters  """
        self.noOfTermsInput.setText(str(NUMBER_OF_TERMS))
        self.regularizationConstantInput.setText(str(REGULARIZATION))
        self.maxDistanceInput.setText(str(MAX_DIST))
        self.backgroundInput.setText(str(BACKGROUND_INPUT))
        self.computationTimeValue.setText("")
        self.minQInput.setText(str(Q_MIN_INPUT))
        self.maxQInput.setText(str(Q_MAX_INPUT))
        self.slitHeightInput.setText("")
        self.slitWidthInput.setText("")



    def resetCalcPrams(self):
        " resets the calibration prams """
        self._calculator.nfunc = self._calculator.nfunc
        self._calculator.set_alpha(self._calculator.regConst)
        self._calculator.set_dmax(self._calculator.d_max)

        self.updateCalculator()  # sets Background

    def getState(self):
        """
        Collects all active params into a dictionary of {name: value}
        :return: {name: value}
        """
        # If no measurement performed, calculate using base params
        if self.chiDofValue.text() == '':
            self._calculator.out, self._calculator.cov = self._calculator.invert()
        return {
            'alpha': self._calculator.alpha,
            'background': self._calculator.background,
            'chi2': self._calculator.chi2,
            'cov': self._calculator.cov,
            'd_max': self._calculator.d_max,
            'elapsed': self._calculator.elapsed,
            'err': self._calculator.err,
            'est_bck': self._calculator.est_bck,
            'iq0': self._calculator.iq0(self._calculator.out),
            'nerr': self._calculator.nerr,
            'nfunc': self.getNFunc(),
            'npoints': self._calculator.npoints,
            'ny': self._calculator.ny,
            'out': self._calculator.out,
            'oscillations': self._calculator.oscillations(self._calculator.out),
            'pos_frac': self._calculator.get_positive(self._calculator.out),
            'pos_err': self._calculator.get_pos_err(self._calculator.out,
                                                    self._calculator.cov),
            'q_max': self._calculator.q_max,
            'q_min': self._calculator.q_min,
            'rg': self._calculator.rg(self._calculator.out),
            'slit_height': self._calculator.slit_height,
            'slit_width': self._calculator.slit_width,
            'suggested_alpha': self._calculator.suggested_alpha,
            'x': self._calculator.x,
            'y': self._calculator.y,
        }

    def getNFunc(self):
        """Get the n_func value from the GUI object"""
        try:
            nfunc = int(self.noOfTermsInput.text())
        except ValueError:
            logger.error("Incorrect number of terms specified: %s" % self.noOfTermsInput.text())
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
        self.data = data_ref
        self.setParameters()
        self.logic.data = GuiUtils.dataFromItem(data_ref)
        self.resetCalcPrams()
        self._calculator = self.dataDictionary[data_ref].get(DICT_KEYS[0])
        self.prPlot = self.dataDictionary[data_ref].get(DICT_KEYS[1])
        self.dataPlot = self.dataDictionary[data_ref].get(DICT_KEYS[2])
        

    def updateDynamicGuiValues(self, index=None):
        """update gui with suggested parameters"""
        if index is not None and index>0:
            self.logic.data = GuiUtils.dataFromItem(self.dataList.itemData(index))
            pr = self.batchResults[self.logic.data.name].get(DICT_KEYS[0]) 
            alpha = self.batchResults[self.logic.data.name].get(DICT_KEYS[0]).suggested_alpha
        else:    
            pr = self._calculator
            alpha = self._calculator.suggested_alpha
        self.model.setItem(WIDGETS.W_MAX_DIST,
                           QtGui.QStandardItem("{:.4g}".format(pr.get_dmax())))
        self.regConstantSuggestionButton.setText("{:-3.2g}".format(alpha))
        self.noOfTermsSuggestionButton.setText(
            "{:n}".format(self.nTermsSuggested))

        self.enableButtons()

    def updateGuiValues(self, index=None):
        
        if index is not None and index>=0:
            self.logic.data = GuiUtils.dataFromItem(self.dataList.itemData(index))
            pr = self.batchResults[self.logic.data.name].get(DICT_KEYS[0])

        else:    
            pr = self._calculator
            
        out = pr.out
        cov = pr.cov
        elapsed = pr.elapsed
        alpha = pr.suggested_alpha
        self.updateMaxQ(pr.get_q_max())
        self.updateMinQ(pr.get_q_min())

        self.model.setItem(WIDGETS.W_Q_MIN, QtGui.QStandardItem("{:.3g}".format(pr.get_q_min())))
        self.model.setItem(WIDGETS.W_Q_MAX, QtGui.QStandardItem("{:.3g}".format(pr.get_q_max())))

        self.model.setItem(WIDGETS.W_BACKGROUND_INPUT,
                           QtGui.QStandardItem("{:.3g}".format(pr.background)))
        self.model.setItem(WIDGETS.W_BACKGROUND_OUTPUT,
                           QtGui.QStandardItem("{:.3g}".format(pr.background)))
        self.model.setItem(WIDGETS.W_COMP_TIME,
                           QtGui.QStandardItem("{:.4g}".format(elapsed)))
        self.model.setItem(WIDGETS.W_MAX_DIST,
                           QtGui.QStandardItem("{:.4g}".format(pr.get_dmax())))
        self.regConstantSuggestionButton.setText("{:.2g}".format(alpha))

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
        if self.prPlot is not None:        
            try:
                title = self.prPlot.name
                self.prPlot.plot_role = DataRole.ROLE_STAND_ALONE
                GuiUtils.updateModelItemWithPlot(self.data, self.prPlot, title)
                self.communicate.plotRequestedSignal.emit([self.data, self.prPlot], None)
            except AssertionError:
                pass
        
        if self.dataPlot is not None:
            try:
                title = self.dataPlot.name
                self.dataPlot.plot_role = DataRole.ROLE_DEFAULT
                self.dataPlot.symbol = "Line"
                self.dataPlot.show_errors = False
                GuiUtils.updateModelItemWithPlot(self.data, self.dataPlot, title)
                self.communicate.plotRequestedSignal.emit([self.data, self.dataPlot], None)
            except AssertionError:
                pass
        self.enableButtons()

    def removeData(self, data_list=None):
        """Remove the existing data reference from the P(r) Persepective"""
        self.batchResults = {}
        if self.is_batch:
            self.prPlot = None
            self.dataPlot = None
            self.dataList.removeItem(self.dataList.currentIndex())
            self._allowPlots = True
        if not data_list:
            data_list = [self.data]
        self.closeDMax()
        for data in data_list:
            self.dataDictionary.pop(data, None)
        if self.dataPlot:
            # Reset dataplot sliders
            self.dataPlot.slider_low_q_input = []
            self.dataPlot.slider_high_q_input = []
            self.dataPlot.slider_low_q_setter = []
            self.dataPlot.slider_high_q_setter = []
        self.data = None
        length = len(data_list)
        for index in reversed(range(length)):
            if self.dataList.itemData(index) in data_list:
                self.dataList.removeItem(index)
        # Last file removed
        self.dataDeleted = False
        if len(self.dataDictionary) == 0:
            self.prPlot = None
            self.dataPlot = None
            self.logic.data = None
            self._calculator = Invertor()
            self.closeBatchResults()
            self.nTermsSuggested = NUMBER_OF_TERMS
            self._calculator.suggested_alpha = REGULARIZATION
            self.noOfTermsSuggestionButton.setText("{:n}".format(
                self.nTermsSuggested))
            self.regConstantSuggestionButton.setText("{:-3.2g}".format(
                self._calculator.suggested_alpha))
            self.updateGuiValues()
            self.setupModel()
            
        else:
            self.dataList.setCurrentIndex(0)
            self.prPlot = None
            self.dataPlot = None
            self.updateGuiValues(index=0)



    def currentTabName(self):
        """
        Returns the name of the current tab
        """
        tab_name = []
        if self.tab_name is not None:
            tab_name.append(str(self.tab_name))
        return tab_name

    def getPage(self):
        """
        serializes full state of this fit page
        """
        # Get all parameters from page
        param_dict = self.getState()
        param_dict['data_name'] = str(self.logic.data.name)
        param_dict['data_id'] = str(self.logic.data.id)
        param_dict['tab_id'] = self.currentTabDataId()
        param_dict['tab_name'] = self.currentTabName()
        return param_dict

    def updateFromParameters(self, params):
        """
        Updates the calculator page with the given parameters
        """
        self.updateMaxQ(self._calculator.get_q_max())
        self._calculator.q_max = params['q_max']
        self.updateMinQ(self._calculator.get_q_min())
        self._calculator.q_min = params['q_min']        
        self._calculator.alpha = params['alpha']
        self._calculator.suggested_alpha = params['suggested_alpha']
        self._calculator.d_max = params['d_max']
        self._calculator.nfunc = params['nfunc']
        self.nTermsSuggested = self._calculator.nfunc

        # self.acceptAlpha() // suggested values have been disabled to avoid inference with batch
        # self.acceptNoTerms()
        self._calculator.background = params['background']
        self._calculator.chi2 = params['chi2']
        self._calculator.cov = params['cov']
        self._calculator.elapsed = params['elapsed']
        self._calculator.err = params['err']
        self._calculator.set_est_bck = bool(params['est_bck'])
        self._calculator.nerr = params['nerr']
        self._calculator.npoints = params['npoints']
        self._calculator.ny = params['ny']
        self._calculator.out = params['out']
        self._calculator.slit_height = params['slit_height']
        self._calculator.slit_width = params['slit_width']
        self._calculator.x = params['x']
        self._calculator.y = params['y']
        self.updateGuiValues()
        self.updateDynamicGuiValues()

    ######################################################################
    # Thread Creators

    def startThreadAll(self):
        """
        Batch Process all items in DropDown Menu
        """
        if not isinstance(self.logic.data, Data1D):
            return
            
        self.isCalculating = True
        self.is_batch = True
        self._allowPlots = False
        self.batchComplete = []
        self.calculateAllButton.setText("Calculating...")
        self.startThread()


    def startThreadThis(self):
        """
        Calculate the data for the Current Item in the prespective.
        """
        self._allowPlots = True
        self.startThread()

    def startNextBatchItem(self):
        """
        Calculate the data for the Next Item in the dropdown list.
        calculate until all items are in the batchComplete list.
        """
        self.is_batch = False
        
        for index in range(len(self.dataDictionary)):

            if index not in self.batchComplete:
                self.dataList.setCurrentIndex(index)
                self.displayChange(index)
                self.batchComplete.append(index)
                self.is_batch = True
                break
        if not isinstance(self.logic.data, Data1D):
            return
        elif self.is_batch:
            self.startThread()

        else:
            # If no data sets left, end batch calculation
            self.isCalculating = False
            self.is_batch = True
            self.batchComplete = []
            self.updateGuiValues(index=self.dataList.currentIndex())
            self.updateDynamicGuiValues(index=self.dataList.currentIndex())
            self.calculateAllButton.setText("Calculate All")
            self.enableButtons()
            self.showBatchOutput()
            

    def startThread(self):
        """
            Start a calculation thread
        """
        from .Thread import CalcPr

        # Set data before running the calculations
        self.isCalculating = True
        self.enableButtons()
        
        # Disable calculation buttons to prevent thread interference

        # If the thread is already started, stop it
        #self.stopCalcThread()

        pr = self._calculator.clone()
        self.updateCalculator()
        # Making sure that nfunc and alpha parameters are correctly initialized
        pr.suggested_alpha = self._calculator.alpha
        self.calcThread = CalcPr(pr, self.getNFunc(),tab_id=[[self.tab_id]],
                                 error_func=self._threadError,
                                 completefn=self._calculateCompleted,
                                 updatefn=None)
        self.calcThread.queue()
        self.calcThread.ready(2.5)

    def stopCalcThread(self):
        """ Stops a thread if it exists and is running """
        if self.calcThread is not None and self.calcThread.isrunning():
            self.calcThread.stop()

    def performEstimateNT(self):
        """
        Perform parameter estimation
        """
        from .Thread import EstimateNT

        self.updateCalculator()

        # If a thread is already started, stop it
        self.stopEstimateNTThread()

        pr = self._calculator.clone()
        # Skip the slit settings for the estimation
        # It slows down the application and it doesn't change the estimates
        pr.slit_height = 0.0
        pr.slit_width = 0.0
        nfunc = self.getNFunc()
        pr.suggested_alpha = self._calculator.alpha
        self.estimationThreadNT = EstimateNT(pr, nfunc,
                                             error_func=self._threadError,
                                             completefn=self._estimateNTCompleted,
                                             updatefn=None)
        self.estimationThreadNT.queue()
        self.estimationThreadNT.ready(2.5)

    def performEstimateDynamicNT(self):
        """
        Perform parameter estimation
        """
        from .Thread import EstimateNT

        self.updateCalculator()

        # If a thread is already started, stop it
        self.stopEstimateNTThread()

        pr = self._calculator.clone()
        # Skip the slit settings for the estimation
        # It slows down the application and it doesn't change the estimates
        pr.slit_height = 0.0
        pr.slit_width = 0.0
        nfunc = self.getNFunc()
        pr.suggested_alpha = self._calculator.alpha
        self.estimationThreadNT = EstimateNT(pr, nfunc,
                                             error_func=self._threadError,
                                             completefn=self._estimateDynamicNTCompleted,
                                             updatefn=None)
        self.estimationThreadNT.queue()
        self.estimationThreadNT.ready(2.5)

    def stopEstimateNTThread(self):
        if (self.estimationThreadNT is not None and
                self.estimationThreadNT.isrunning()):
            self.estimationThreadNT.stop()

    def performEstimate(self):
        """
            Perform parameter estimation
        """
        from .Thread import EstimatePr

        # If a thread is already started, stop it
        self.stopEstimationThread()

        self.estimationThread = EstimatePr(self._calculator.clone(),
                                           self.getNFunc(),
                                           error_func=self._threadError,
                                           completefn=self._estimateCompleted,
                                           updatefn=None)
        self.estimationThread.queue()
        self.estimationThread.ready(2.5)

    def performEstimateDynamic(self):
        """
            Perform parameter estimation
        """
        from .Thread import EstimatePr

        # If a thread is already started, stop it
        self.stopEstimationThread()

        self.estimationThread = EstimatePr(self._calculator.clone(),
                                           self.getNFunc(),
                                           error_func=self._threadError,
                                           completefn=self._estimateDynamicCompleted,
                                           updatefn=None)
        self.estimationThread.queue()
        self.estimationThread.ready(2.5)

    def stopEstimationThread(self):
        """ Stop the estimation thread if it exists and is running """
        if (self.estimationThread is not None and
                self.estimationThread.isrunning()):
            self.estimationThread.stop()

    ######################################################################
    # Thread Complete

    def _estimateCompleted(self, alpha, message, elapsed):
        ''' Send a signal to the main thread for model update'''
        self.estimateSignal.emit((alpha, message, elapsed))

    def _estimateDynamicCompleted(self, alpha, message, elapsed):
        ''' Send a signal to the main thread for model update'''
        self.estimateDynamicSignal.emit((alpha, message, elapsed))

    def _estimateUpdate(self, output_tuple):
        """
        Parameter estimation completed,
        display the results to the user

        :param alpha: estimated best alpha
        :param elapsed: computation time
        """
        alpha, message, elapsed = output_tuple
        self._calculator.alpha = alpha
        self._calculator.elapsed += self._calculator.elapsed
        if message:
            logger.info(message)
        self.performEstimateNT()
        self.performEstimateDynamicNT()

    def _estimateDynamicUpdate(self, output_tuple):
        """
        Parameter estimation completed,
        display the results to the user

        :param alpha: estimated best alpha
        :param elapsed: computation time
        """
        alpha, message, elapsed = output_tuple
        self._calculator.alpha = alpha
        self._calculator.elapsed += self._calculator.elapsed
        if message:
            logger.info(message)
        self.performEstimateDynamicNT()

    def _plotUpdate(self):
        print("Plotting update")

    def _estimateNTCompleted(self, nterms, alpha, message, elapsed):
        ''' Send a signal to the main thread for model update'''
        self.estimateNTSignal.emit((nterms, alpha, message, elapsed))

    def _estimateDynamicNTCompleted(self, nterms, alpha, message, elapsed):
        ''' Send a signal to the main thread for model update'''
        self.estimateDynamicNTSignal.emit((nterms, alpha, message, elapsed))

    def _estimateNTUpdate(self, output_tuple):
        """
        Parameter estimation completed,
        display the results to the user

        :param alpha: estimated best alpha
        :param nterms: estimated number of terms
        :param elapsed: computation time
        """
        nterms, alpha, message, elapsed = output_tuple
        self._calculator.elapsed += elapsed
        self._calculator.alpha = alpha
        self.nTermsSuggested = nterms
        # Save useful info
        self.updateGuiValues()
        if message:
            logger.info(message)
        if self.is_batch:
            self.acceptAlpha()
            self.acceptNoTerms()
            self.startThread()
            self.updateDynamicGuiValues()


    def _estimateDynamicNTUpdate(self, output_tuple):
        """
        Parameter estimation completed,
        display the results to the user

        :param alpha: estimated best alpha
        :param nterms: estimated number of terms
        :param elapsed: computation time
        """
        nterms, alpha, message, elapsed = output_tuple
        self._calculator.elapsed += elapsed
        self._calculator.suggested_alpha = alpha
        self.nTermsSuggested = nterms
        # Save useful info
        self.updateDynamicGuiValues()
        if message:
            logger.info(message)
        if self.is_batch:
            self.acceptAlpha()
            self.acceptNoTerms()
            self.acceptNoTerms()
            self.updateGuiValues()
            self.startThread()

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

        # Update P(r) and fit plots
        # do not show/update plot if batch (Clutters and slows down interface)
        if self._allowPlots:
            self.prPlot = self.logic.newPRPlot(out, self._calculator, cov)
            self.prPlot.show_yzero = True
            self.prPlot.filename = self.logic.data.filename
            dataPlot = self.logic.new1DPlot(self.tab_id, out, self._calculator)
            dataPlot.filename = self.logic.data.filename

            dataPlot.show_q_range_sliders = True
            dataPlot.slider_update_on_move = False
            dataPlot.slider_perspective_name = "Inversion"
            dataPlot.slider_tab_name = self.currentTabName()
            dataPlot.slider_low_q_input = ['minQInput']
            dataPlot.slider_low_q_setter = ['updateMinQ']
            dataPlot.slider_high_q_input = ['maxQInput']
            dataPlot.slider_high_q_setter = ['updateMaxQ']
            self.dataPlot = dataPlot 
            #new_plots = [dataPlot]
            #for plot in new_plots:
            #    self.communicate.plotUpdateSignal.emit([plot])
            #    QtWidgets.QApplication.processEvents()
            
            # Udpate internals and GUI
        self.updateDataList(self.data)  
        
        
        self.saveToBatchResults()
        if self.is_batch:
            self.batchComplete.append(self.dataList.currentIndex())
            self.startNextBatchItem()
        else:
            self.updateGuiValues()
            self.isCalculating = False
            self.enableButtons()


    def _threadError(self, error):
        """
            Call-back method for calculation errors
        """
        logger.error(error)
        self.stopCalculation()


    def sendToInversion(self, items):
        """
        Send `items` to the Inversion perspective, in either single fit or batch mode
        """
        # if perspective is correct, otherwise complain
        if self.parent._current_perspective.name != 'Inversion':
            msg = "Please change current perspective to Inversion."
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIcon(QtWidgets.QMessageBox.Critical)
            msgbox.setText(msg)
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            _ = msgbox.exec_()
            return
        # icky way to go up the tree
        self.parent._current_perspective.setData(data_item=items, is_batch=True)








def debug(checkpoint):
    print(" - - - - - - - - [ DEBUG :: Checkpoint {} ] - - - - - - - - ".format(checkpoint))
