
import logging
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtGui import QIntValidator, QStandardItem
from PySide6.QtWidgets import QWidget

from sas.qtgui.Perspectives.Inversion.DMaxExplorerWidget import DmaxWindow
from sas.qtgui.Perspectives.Inversion.InversionLogic import InversionLogic
from sas.qtgui.Perspectives.Inversion.Thread import CalcBatchPr, CalcPr, EstimateNT
from sas.qtgui.Perspectives.Inversion.UI.TabbedInversionUI import Ui_PrInversion
from sas.qtgui.Plotting.PlotterData import Data1D, DataRole
from sas.qtgui.Utilities.GridPanel import BatchInversionOutputPanel
from sas.qtgui.Utilities.GuiUtils import (
    Communicate,
    DoubleValidator,
    HashableStandardItem,
    dataFromItem,
    updateModelItemWithPlot,
)
from sas.sascalc.pr.invertor import Invertor


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

def get_outputs(invertor: Invertor, elapsed: float):
    return CalculatedOutputs(
        invertor.rg(invertor.out),
        invertor.iq0(invertor.out),
        invertor.background,
        elapsed,
        invertor.chi2,
        invertor.oscillations(invertor.out),
        invertor.get_positive(invertor.out),
        invertor.get_pos_err(invertor.out, invertor.cov)
    )

@dataclass
class EstimatedParameters:
    reg_constant: float
    nterms: int

@dataclass
class InversionResult:
    logic: InversionLogic
    calculator: Invertor
    pr_plot: Data1D | None
    data_plot: Data1D | None
    outputs: CalculatedOutputs | None
    estimated_parameters: EstimatedParameters | None

def format_float(f: float):
    return f'{f:.3f}'

def format_float_scientific(f: float):
    """
    Formats a float in scientific notation with 3 significant figures.
    """
    return f'{f:.3g}' if f != 0 else '0.0'  # Avoids showing '0e+00' for zero values

# Default Values for inputs
NUMBER_OF_TERMS = 10
REGULARIZATION = 0.0
BACKGROUND_INPUT = 0.0
Q_MIN_INPUT = 0.0
Q_MAX_INPUT = 0.0
MAX_DIST = 140.0

logger = logging.getLogger(__name__)

class InversionWidget(QWidget, Ui_PrInversion):
    calculationComplete = Signal()
    batchCalculationOutput = Signal(object)
    estimationComplete = Signal()
    changeBackgroundMode = Signal()

    def __init__(self, window, parent=None, data=None, tab_id=1, tab_name=''):
        super(InversionWidget, self).__init__()

        self.parent = parent
        self.window = window
        self.tab_name = tab_name
        self.tab_id = tab_id

        self.communicator: Communicate  = self.parent.communicator()

        # We're going to use this structure even if we're just dealing with one specific datum. Just that this list
        # would then have one item in it.
        self.results: list[InversionResult] = [self.initResult()]

        self.setupUi(self)
        self.setupValidators()

        self.isCalculating: bool = False

        self.dmaxWindow: DmaxWindow | None = None

        self.batchResultsWindow: BatchInversionOutputPanel | None = None
        self.batch_dict: dict[str, Any] | None = None

        self.input_boxes = [self.noOfTermsInput, self.regularizationConstantInput, self.maxDistanceInput,
                             self.minQInput, self.maxQInput, self.slitHeightInput, self.slitHeightInput]

        self.updateGuiValues()
        self.events()

    def initResult(self) -> InversionResult:
        logic = InversionLogic()
        return InversionResult(
            logic=logic,
            calculator=Invertor(logic),
            pr_plot=None,
            data_plot=None,
            outputs=None,
            estimated_parameters=None
        )

    def events(self):
        self.calculateThisButton.clicked.connect(self.startThread)
        self.calculateAllButton.clicked.connect(self.startThreadAll)
        self.batchCalculationOutput.connect(self.showBatchCalculationWindow)
        self.calculationComplete.connect(self.updateGuiValues)
        self.estimationComplete.connect(self.estimateAvailable)
        self.noOfTermsSuggestionButton.clicked.connect(self.applyNumTermsEstimate)
        self.regConstantSuggestionButton.clicked.connect(self.applyRegConstantEstimate)
        self.explorerButton.clicked.connect(self.openExplorerWindow)
        self.estimateBgd.pressed.connect(self.handleBackgroundModeChange)
        self.manualBgd.pressed.connect(self.handleBackgroundModeChange)
        self.dataList.currentIndexChanged.connect(self.handleCurrentDataChanged)
        self.helpButton.clicked.connect(self.onHelp)
        self.removeButton.clicked.connect(self.handleRemove)
        self.showResultsButton.clicked.connect(self.handleShowResults)

        for input_box in self.input_boxes:
            input_box.editingFinished.connect(self.startEstimateParameters)

    def handleRemove(self):
        if self.currentResult.data_plot:
            self.currentResult.data_plot.slider_low_q_input = []
            self.currentResult.data_plot.slider_low_q_setter = []
            self.currentResult.data_plot.slider_high_q_input = []
            self.currentResult.data_plot.slider_high_q_setter = []

        to_remove = self.dataList.currentIndex()
        self.dataList.removeItem(to_remove)
        _ = self.results.pop(to_remove)
        # If there's no results left, we need an empty one.
        if len(self.results) == 0:
            self.results.append(self.initResult())
            self.clearGuiValues()
        self.enableButtons()
        self.updateGuiValues()

    def handleCurrentDataChanged(self):
        # This event might get called before there is anything in the results list. But we can't update the GUI without
        # errors.
        if len(self.results) != 0:
            self.updateGuiValues()
            self.startEstimateParameters()

    # TODO: Need to verify type hint for data.
    def updateTab(self, data: HashableStandardItem | list[HashableStandardItem], tab_id: int):
        self.tab_id = tab_id
        if isinstance(data, list):
            self.results = []
            self.dataList.clear()
            for datum_item in data:
                new_result = self.initResult()
                new_result.logic.data = datum_item
                datum = dataFromItem(datum_item)
                self.dataList.addItem(datum.name)
                self.results.append(new_result)
        else:
            self.currentData = data
            self.dataList.clear()
            self.dataList.addItem(self.currentData.name)
        self.dataList.setCurrentIndex(0)
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
        if value is not None:
            self.onNewData()


    # TODO: I don't know if 'float' is the right type hint.
    @property
    def q_max(self) -> float:
        return self.currentResult.calculator.q_max

    @property
    def q_min(self) -> float:
        return self.currentResult.calculator.q_min

    def onNewData(self):
        # FIXME: This mutates the data even for other perspectives.
        self.currentResult.logic.add_errors()
        qmin, qmax = self.currentResult.logic.computeDataRange()
        self.currentResult.calculator.q_min = qmin
        self.currentResult.calculator.q_max = qmax

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
                                          and not self.isCalculating and self.batchResultsWindow is not None)
        self.removeButton.setEnabled(self.currentResult.logic.data_is_loaded and not self.isCalculating)
        self.explorerButton.setEnabled(self.currentResult.logic.data_is_loaded and not self.isCalculating)
        self.stopButton.setVisible(self.isCalculating)
        self.regConstantSuggestionButton.setEnabled(self.currentResult.logic.data_is_loaded and not self.isCalculating)
        self.noOfTermsSuggestionButton.setEnabled(self.currentResult.logic.data_is_loaded and not self.isCalculating)

    def updateGuiValues(self):
        # TODO: This won't work for batch at the moment.
        current_calculator = self.currentResult.calculator

        # Checks if there is an estimation available.
        if self.currentResult.estimated_parameters is not None:
            self.noOfTermsSuggestionButton.setText(str(self.currentResult.estimated_parameters.nterms))
            self.regConstantSuggestionButton.setText(f"{self.currentResult.estimated_parameters.reg_constant:.2g}")

        self.noOfTermsInput.setText(str(current_calculator.noOfTerms))
        self.regularizationConstantInput.setText(f"{current_calculator.alpha:.2g}")
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
        if out is not None:
            # TODO: It might be good to have a separate data class for these
            # values that are calculated.
            self.rgValue.setText(format_float(out.rg))
            self.iQ0Value.setText(format_float(out.iq0))
            self.backgroundValue.setText(format_float(out.background))
            if current_calculator.est_bck:
                self.backgroundInput.setText(format_float(out.background))
            self.computationTimeValue.setText(format_float(out.calc_time))
            self.chiDofValue.setText(format_float_scientific(out.chi2[0]))
            self.oscillationValue.setText(format_float(out.oscillations))
            self.posFractionValue.setText(format_float(out.pos_frac))
            self.sigmaPosFractionValue.setText(format_float(out.pos_err))

    def clearGuiValues(self):

        value_text_boxes = [*self.input_boxes, self.rgValue, self.iQ0Value, self.backgroundValue, self.backgroundInput,
                            self.computationTimeValue, self.chiDofValue, self.oscillationValue, self.posFractionValue,
                            self.sigmaPosFractionValue]

        for text_box in value_text_boxes:
            text_box.setText("")

    def setupValidators(self):
        """Apply validators to editable line edits"""
        self.noOfTermsInput.setValidator(QIntValidator())
        self.regularizationConstantInput.setValidator(DoubleValidator())
        self.maxDistanceInput.setValidator(DoubleValidator())
        self.minQInput.setValidator(DoubleValidator())
        self.maxQInput.setValidator(DoubleValidator())
        self.slitHeightInput.setValidator(DoubleValidator())
        self.slitWidthInput.setValidator(DoubleValidator())

    def updateGuiSuggested(self, nterms, alpha):
        self.noOfTermsSuggestionButton.setText(str(nterms))
        self.regConstantSuggestionButton.setText(str(alpha))

    def acceptsData(self) -> bool:
        return self.currentData is None

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
        self.currentResult.outputs = get_outputs(calculator, elapsed)
        # Previously called these events directly without a signal but it led to
        # QT segfaulting.
        self.calculationComplete.emit()
        self.makePlots(out, cov, pr, elapsed)
        self.showCurrentPlots()

    def makePlots(self, out, cov, pr, elapsed, result=None):
        if result is None:
            result = self.currentResult
        # PR Plot
        result.pr_plot = result.logic.newPRPlot(out, pr, cov)
        result.pr_plot.show_yzero = True
        result.pr_plot.filename = result.logic.data.filename
        result.pr_plot.plot_role = DataRole.ROLE_STAND_ALONE

        # Data Plot
        data_plot = result.logic.new1DPlot(self.tab_id, out, pr)
        data_plot.filename = result.logic.data.filename

        data_plot.show_q_range_sliders = True
        data_plot.slider_update_on_move = False
        data_plot.slider_perspective_name = "Inversion"
        data_plot.slider_tab_name = self.tab_name
        data_plot.slider_low_q_input = ['currentTab', 'minQInput']
        data_plot.slider_low_q_setter = ['currentTab', 'updateMinQ']
        data_plot.slider_high_q_input = ['currentTab', 'maxQInput']
        data_plot.slider_high_q_setter = ['currentTab', 'updateMaxQ']
        data_plot.symbol = 'Line'
        data_plot.show_errors = False
        data_plot.plot_role = DataRole.ROLE_DEFAULT
        result.data_plot = data_plot

    def showPlots(self, result: InversionResult):
        plots = [result.pr_plot, result.data_plot]
        for plot in plots:
            if plot is not None:
                updateModelItemWithPlot(result.logic._data_item, plot, plot.name)
                self.communicator.plotRequestedSignal.emit([result.logic._data_item, plot], None)

    def showCurrentPlots(self):
        self.showPlots(self.currentResult)

    def updateMinQ(self, new_q_min: float):
        calculator = self.currentResult.calculator
        new_q_min = max([min(calculator.x), new_q_min])
        calculator.q_min = new_q_min
        self.updateGuiValues()

    def updateMaxQ(self, new_q_max: float):
        calculator = self.currentResult.calculator
        new_q_max = min([max(calculator.x), new_q_max])
        calculator.q_max = new_q_max
        self.updateGuiValues()

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

    def startThreadAll(self):
        self.updateParams()
        self.isCalculating = True
        self.enableButtons()

        self.dataList.setCurrentIndex(0)
        self.calcThread = CalcBatchPr(
            prs=[result.calculator for result in self.results],
            nfuncs=[result.calculator.noOfTerms for result in self.results],
            error_func=self.threadError,
            completefn=self.batchCalculationComplete
        )
        self.calcThread.queue()
        self.calcThread.ready(2.5)

    def batchCalculationComplete(self, totalElapsed):
        self.isCalculating = False
        self.enableButtons()

        self.calculationComplete.emit()
        self.batch_dict = {}
        for result in self.results:
            # TODO: Calculate elapsed properly.
            result.outputs = get_outputs(result.calculator, totalElapsed)
            self.makePlots(result.calculator.out, result.calculator.cov, result.calculator, totalElapsed, result)
            self.batch_dict[result.logic.data.filename] = {
                'Calculator': result.calculator,
                'PrPlot': result.pr_plot,
                'DataPlot': result.data_plot,
                'Result': result
            }
        self.batchCalculationOutput.emit(self.batch_dict)

    def showBatchCalculationWindow(self, batch_dict):
        self.batchResultsWindow = BatchInversionOutputPanel(
            parent=self,
            output_data=batch_dict
        )
        self.batchResultsWindow.show()
        self.enableButtons()

    def handleShowResults(self):
        self.batchCalculationOutput.emit(self.batch_dict)

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
        if not self.currentResult.logic.data_is_loaded:
            return
        self.updateParams()
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

    def serialiseResult(self, result: InversionResult) -> dict[str, Any]:
        return {
            'data_id': result.logic.data.id,
            'alpha': result.calculator.alpha,
            'background': result.calculator.background,
            'chi2': result.calculator.chi2,
            'cov': result.calculator.cov,
            'd_max': result.calculator.dmax,
            'elapsed': result.calculator.elapsed,
            'err': result.calculator.err,
            'est_bck': result.calculator.est_bck,
            'iq0': result.calculator.iq0(result.calculator.out),
            'out': result.calculator.out,
            'oscillations': result.calculator.oscillations(result.calculator.out),
            'pos_frac': result.calculator.get_positive(result.calculator.out),
            'pos_err': result.outputs.pos_err if result.outputs is not None else None,
            'q_max': result.calculator.q_max,
            'q_min': result.calculator.q_min,
            'rg': result.calculator.rg(result.calculator.out),
            'slit_height': result.calculator.slit_height,
            'slit_width': result.calculator.slit_width,
            'suggested_alpha': result.calculator.suggested_alpha,
            'x': result.calculator.x,
            'y': result.calculator.y
        }

    def updateFromParameters(self, params: dict[str, Any]):
        result = self.currentResult
        result.calculator.alpha = params['alpha']
        result.calculator.background = params['background']
        result.calculator.chi2 = params['chi2']
        result.calculator.cov = params['cov']
        result.calculator.dmax = params['d_max']
        result.calculator.elapsed = params['elapsed']
        result.calculator.est_bck = params['est_bck']
        result.calculator.out = params['out']
        result.calculator.q_max = params['q_max']
        result.calculator.q_min = params['q_min']
        result.calculator.slit_height = params['slit_height']
        result.calculator.slit_width = params['slit_width']
        result.calculator.suggested_alpha = params['suggested_alpha']
        result.outputs = get_outputs(result.calculator, params['elapsed'])

    def getPage(self) -> dict[str, Any]:
        # FIXME: Doesn't work on batch.
        return self.serialiseResult(self.currentResult)

    def onHelp(self):
        self.window.help()
