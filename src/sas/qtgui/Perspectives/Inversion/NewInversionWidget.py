
from dataclasses import dataclass
import logging
from PySide6.QtCore import Signal
from PySide6.QtGui import QStandardItem
from PySide6.QtWidgets import QWidget

from sas.qtgui.Perspectives.Inversion.DMaxExplorerWidget import DmaxWindow
from src.sas.qtgui.Perspectives.Inversion.InversionLogic import InversionLogic
from src.sas.qtgui.Perspectives.Inversion.Thread import CalcPr, EstimateNT
from src.sas.qtgui.Perspectives.Inversion.UI.TabbedInversionUI import Ui_PrInversion
from sas.qtgui.Plotting.PlotterData import Data1D, DataRole
from src.sas.qtgui.Utilities.GuiUtils import updateModelItemWithPlot, HashableStandardItem, Communicate, dataFromItem
from src.sas.sascalc.pr.NewInvertor import NewInvertor

@dataclass
class CalculatedOutputs:
    rg: float
    iq0: float
    background: float
    calc_time: float
    chi2: float
    oscillations: float
    pos_frac: float
    pos_err: float

@dataclass
class EstimatedParameters:
    reg_constant: float
    nterms: int

@dataclass
class InversionResult:
    logic: InversionLogic
    calculator: NewInvertor
    pr_plot: Data1D | None
    data_plot: Data1D | None
    outputs: CalculatedOutputs | None
    estimated_parameters: EstimatedParameters | None

def format_float(f: float):
    return f'{f:.3f}'


# Default Values for inputs
NUMBER_OF_TERMS = 10
REGULARIZATION = 0.0
BACKGROUND_INPUT = 0.0
Q_MIN_INPUT = 0.0
Q_MAX_INPUT = 0.0
MAX_DIST = 140.0

logger = logging.getLogger(__name__)

class NewInversionWidget(QWidget, Ui_PrInversion):
    # The old class had 'name' and 'ext'. Since this class doesn't inherit from
    # perspective, I'm not convinced they are needed here.

    calculationComplete = Signal()
    estimationComplete = Signal()
    changeBackgroundMode = Signal()

    def __init__(self, parent=None, data=None, tab_id=1, tab_name=''):
        super(NewInversionWidget, self).__init__()

        self.parent = parent
        self.tab_name = tab_name
        self.tab_id = tab_id

        self.communicator: Communicate  = self.parent.communicator()

        # We're going to use this structure even if we're just dealing with one
        # specific datum. Just that this dictionary would then have one item in
        # it.
        self.results: list[InversionResult] = [self.initResult()]

        self.setupUi(self)

        self.currentData = data
        self.isCalculating: bool = False

        self.dmaxWindow: DmaxWindow | None = None

        self.updateGuiValues()
        self.events()

    def initResult(self) -> InversionResult:
        logic = InversionLogic()
        return InversionResult(
            logic=logic,
            calculator=NewInvertor(logic),
            pr_plot=None,
            data_plot=None,
            outputs=None,
            estimated_parameters=None
        )

    # TODO: What is this function normally called?
    def events(self):
        self.calculateThisButton.clicked.connect(self.startThread)
        self.calculationComplete.connect(self.updateGuiValues)
        self.estimationComplete.connect(self.estimateAvailable)
        self.noOfTermsSuggestionButton.clicked.connect(self.applyNumTermsEstimate)
        self.regConstantSuggestionButton.clicked.connect(self.applyRegConstantEstimate)
        self.explorerButton.clicked.connect(self.openExplorerWindow)
        self.estimateBgd.pressed.connect(self.handleBackgroundModeChange)
        self.manualBgd.pressed.connect(self.handleBackgroundModeChange)

    # TODO: Need to verify type hint for data.
    def updateTab(self, data: Data1D, tab_id: int):
        self.currentData = data
        self.tab_id = tab_id
        self.updateGuiValues()
        self.enableButtons()
        self.startEstimateParameters()

    @property
    def is_batch(self) -> bool:
        return len(self.results) > 1

    @property
    def currentDataIndex(self) -> int:
        return self.dataList.currentIndex()

    @property
    def currentResult(self) -> InversionResult:
        return self.results[self.currentDataIndex]

    @property
    def currentData(self) -> Data1D | None:
        return self.currentResult.logic.data

    @property
    def currentDataItem(self) -> QStandardItem | None:
        return self.currentResult.logic.data_item

    @currentData.setter
    def currentData(self, value: HashableStandardItem | None):
        self.currentResult.logic.data = value
        if not value is None:
            # FIXME: This mutates the data even for other perspectives.
            self.currentResult.logic.add_errors()


    # TODO: I don't know if 'float' is the right type hint.
    @property
    def q_max(self) -> float:
        return self.currentResult.calculator.q_max

    @property
    def q_min(self) -> float:
        return self.currentResult.calculator.q_min

    # TODO: Probably change this name.
    def enableButtons(self):
        """
        Enable buttons when data is present, else disable them
        """
        self.calculateAllButton.setEnabled(not self.isCalculating
                                           and self.currentResult.logic.data_is_loaded and self.is_batch)
        self.calculateThisButton.setEnabled(self.currentResult.logic.data_is_loaded
                                            and not self.isCalculating and not self.is_batch)
        self.calculateThisButton.setVisible(not self.is_batch and not self.isCalculating)
        self.calculateAllButton.setVisible(self.is_batch and not self.isCalculating)

        self.showResultsButton.setEnabled(self.currentResult.logic.data_is_loaded
                                          and self.is_batch
                                          # FIXME: I will probably change how
                                          # batchResultsWindow is going to work.
                                          # This will need to change.
                                          and not self.isCalculating and self.batchResultsWindow is not None)
        self.removeButton.setEnabled(self.currentResult.logic.data_is_loaded and not self.isCalculating)
        self.explorerButton.setEnabled(self.currentResult.logic.data_is_loaded and not self.isCalculating)
        self.stopButton.setVisible(self.isCalculating)
        self.regConstantSuggestionButton.setEnabled(self.currentResult.logic.data_is_loaded and not self.isCalculating)
        self.noOfTermsSuggestionButton.setEnabled(self.currentResult.logic.data_is_loaded and not self.isCalculating)

    def updateGuiValues(self):
        self.dataList.clear()
        if self.currentData is None:
            self.dataList.setCurrentText('')
        else:
            # TODO: Will have multiple values when batch is implemented.
            self.dataList.addItem(self.currentData.name)
            self.dataList.setCurrentIndex(0)


        # TODO: This won't work for batch at the moment.
        current_calculator = self.currentResult.calculator

        # Checks if there is an estimation available.
        if not self.currentResult.estimated_parameters is None:
            self.noOfTermsSuggestionButton.setText(str(self.currentResult.estimated_parameters.nterms))
            self.regConstantSuggestionButton.setText("{:-3.2g}".format(self.currentResult.estimated_parameters.reg_constant))

        self.noOfTermsInput.setText(str(current_calculator.noOfTerms))
        self.regularizationConstantInput.setText(str(current_calculator.alpha))
        self.maxDistanceInput.setText(str(current_calculator.dmax))

        # Options tab
        if current_calculator.est_bck:
            self.estimateBgd.setChecked(True)
        else:
            self.manualBgd.setChecked(True)
        self.minQInput.setText(str(current_calculator.q_min))
        self.maxQInput.setText(str(current_calculator.q_max))
        self.slitHeightInput.setText(str(current_calculator.slit_height))
        self.slitWidthInput.setText(str(current_calculator.slit_width))

        # This checks to see if there is a calculation available.
        out = self.currentResult.outputs
        if not out is None:
            # TODO: It might be good to have a separate data class for these
            # values that are calculated.
            self.rgValue.setText(format_float(out.rg))
            self.iQ0Value.setText(format_float(out.iq0))
            self.backgroundValue.setText(format_float(out.background))
            if current_calculator.est_bck:
                self.backgroundInput.setText(format_float(out.background))
            self.computationTimeValue.setText(format_float(out.calc_time))
            self.chiDofValue.setText(format_float(out.chi2[0]))
            self.oscillationValue.setText(format_float(out.oscillations))
            self.posFractionValue.setText(format_float(out.pos_frac))
            self.sigmaPosFractionValue.setText(format_float(out.pos_err))

    def updateGuiSuggested(self, nterms, alpha):
        self.noOfTermsSuggestionButton.setText(str(nterms))
        self.regConstantSuggestionButton.setText(str(alpha))

    def acceptsData(self) -> bool:
        # TODO: Temporary
        return True

    def threadError(self, error: str):
        logger.error(error)
        # TODO: No function to stop calculation yet.

    # TODO: These parameters should really be type hinted (or rolled into a dataclass?)
    def calculationCompleted(self, out, cov, pr, elapsed):
        # TODO: Placeholder. Just output the numbers for now. Later the result
        # should be plotted.
        self.isCalculating = False
        self.enableButtons()
        calculator = self.currentResult.calculator
        # TODO: Some of these probably don't need to be here.
        self.currentResult.outputs = CalculatedOutputs(
            calculator.rg(out),
            calculator.iq0(out),
            calculator.background,
            elapsed,
            calculator.chi2,
            calculator.oscillations(out),
            calculator.get_positive(out),
            calculator.get_pos_err(out, cov)
        )
        # Previously called these events directly without a signal but it led to
        # QT segfaulting.
        self.calculationComplete.emit()
        self.makePlots(out, cov, pr, elapsed)
        self.showCurrentPlots()

    def makePlots(self, out, cov, pr, elapsed):
        # PR Plot
        self.currentResult.pr_plot = self.currentResult.logic.newPRPlot(out, pr, cov)
        self.currentResult.pr_plot.show_yzero = True
        self.currentResult.pr_plot.filename = self.currentResult.logic.data.filename
        self.currentResult.pr_plot.plot_role = DataRole.ROLE_STAND_ALONE

        # Data Plot
        data_plot = self.currentResult.logic.new1DPlot(self.tab_id, out, self.currentResult.calculator)
        data_plot.filename = self.currentResult.logic.data.filename

        data_plot.show_q_range_sliders = True
        data_plot.slider_update_on_move = False
        data_plot.slider_perspective_name = "Inversion"
        data_plot.slider_tab_name = self.tab_name
        data_plot.slider_low_q_input = ['minQInput']
        data_plot.slider_low_q_setter = ['updateMinQ']
        data_plot.slider_high_q_input = ['maxQInput']
        data_plot.slider_high_q_setter = ['updateMaxQ']
        data_plot.symbol = 'Line'
        data_plot.show_errors = False
        data_plot.plot_role = DataRole.ROLE_DEFAULT
        self.currentResult.data_plot = data_plot

    def showCurrentPlots(self):
        plots = [self.currentResult.pr_plot, self.currentResult.data_plot]
        for plot in plots:
            if not plot is None:
                updateModelItemWithPlot(self.currentDataItem, plot, plot.name)
                self.communicator.plotRequestedSignal.emit([self.currentDataItem, plot], None)

    def updateParams(self):
        # TODO: No validators so this will break if they can't be converted to
        # numbers.
        current_calculator = self.currentResult.calculator
        current_calculator.noOfTerms = int(self.noOfTermsInput.text())
        current_calculator.alpha = float(self.regularizationConstantInput.text())
        current_calculator.dmax = float(self.maxDistanceInput.text())

        # Options tab
        if self.estimateBgd.isChecked():
            current_calculator.est_bck = True
        else:
            current_calculator.est_bck = False
            current_calculator.background = float(self.backgroundInput.text())
        current_calculator.q_min = float(self.minQInput.text())
        current_calculator.q_max = float(self.maxQInput.text())
        current_calculator.slit_height = float(self.slitHeightInput.text())
        current_calculator.slit_width = float(self.slitWidthInput.text())


    def startThread(self):
        self.updateParams()
        self.isCalculating = True
        self.enableButtons()

        # TODO: Calc thread should be declared beforehand.
        self.calcThread = CalcPr(
            self.currentResult.calculator,
            # TODO: no of terms should be somewhere else
            self.currentResult.calculator.noOfTerms,
            tab_id=[[self.tab_id]],
            error_func=self.threadError,
            completefn=self.calculationCompleted,
            updatefn=None
        )

        self.calcThread.queue()
        # TODO: Why are we doing this?
        self.calcThread.ready(2.5)

    def estimateAvailable(self):
        self.updateGuiValues()

    def endEstimateParameters(self, nterms, alpha, message, elapsed):
        self.currentResult.estimated_parameters = EstimatedParameters(alpha, nterms)
        self.estimationComplete.emit()

    def applyRegConstantEstimate(self):
        self.currentResult.calculator.alpha = self.currentResult.estimated_parameters.reg_constant
        self.updateGuiValues()

    def applyNumTermsEstimate(self):
        self.currentResult.calculator.noOfTerms = self.currentResult.estimated_parameters.nterms
        self.updateGuiValues()

    def startEstimateParameters(self):
        estimation_thread = EstimateNT(
            self.currentResult.calculator,
            self.currentResult.calculator.nfunc,
            error_func=self.threadError,
            completefn=self.endEstimateParameters
        )
        estimation_thread.queue()
        estimation_thread.ready(2.5)

    def openExplorerWindow(self):
        self.dmaxWindow = DmaxWindow(
            pr_state=self.currentResult.calculator,
            nfunc=self.currentResult.calculator.nfunc,
            parent=self
        )
        self.dmaxWindow.show()

    def handleBackgroundModeChange(self):
        if self.estimateBgd.isChecked():
            self.backgroundInput.setEnabled(True)
        elif self.manualBgd.isChecked():
            self.backgroundInput.setEnabled(False)
