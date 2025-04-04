
from dataclasses import dataclass
import logging
from PySide6.QtWidgets import QWidget

from src.sas.qtgui.Perspectives.Inversion.InversionLogic import InversionLogic
from src.sas.qtgui.Perspectives.Inversion.Thread import CalcPr
from src.sas.qtgui.Perspectives.Inversion.UI.TabbedInversionUI import Ui_PrInversion
from src.sas.qtgui.Plotting.PlotterData import Data1D
from src.sas.qtgui.Utilities import GuiUtils
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
class InversionResult:
    logic: InversionLogic
    calculator: NewInvertor
    pr_plot: Data1D | None
    data_plot: Data1D | None
    outputs: CalculatedOutputs | None

def format_float(f: float):
    return f'{f:.2f}'


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

    def __init__(self, parent=None, data=None, tab_id=1, tab_name=''):
        super(NewInversionWidget, self).__init__()

        self.parent = parent
        self.tab_name = tab_name
        self.tab_id = tab_id



        # We're going to use this structure even if we're just dealing with one
        # specific datum. Just that this dictionary would then have one item in
        # it.
        self.results: list[InversionResult] = [self.initResult()]

        self.setupUi(self)

        self.currentData = data
        self.isCalculating: bool = False

        self.updateGuiValues()
        self.events()

    def initResult(self) -> InversionResult:
        logic = InversionLogic()
        return InversionResult(
            logic=logic,
            calculator=NewInvertor(logic),
            pr_plot=None,
            data_plot=None,
            outputs=None
        )

    # TODO: What is this function normally called?
    def events(self):
        self.calculateThisButton.clicked.connect(self.startThread)

    # TODO: Need to verify type hint for data.
    def updateTab(self, data: Data1D, tab_id: int):
        self.currentData = data
        self.tab_id = tab_id
        self.updateGuiValues()
        self.enableButtons()

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

    @currentData.setter
    def currentData(self, value: GuiUtils.HashableStandardItem):
        self.currentResult.logic.data = GuiUtils.dataFromItem(value)


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

        self.noOfTermsInput.setText(str(current_calculator.noOfTerms))
        self.regularizationConstantInput.setText(str(current_calculator.alpha))
        self.maxDistanceInput.setText(str(current_calculator.dmax))

        # This checks to see if there is a calculation available.
        out = self.currentResult.outputs
        if not out is None:
            # TODO: It might be good to have a separate data class for these
            # values that are calculated.
            self.rgValue.setText(format_float(out.rg))
            self.iQ0Value.setText(format_float(out.iq0))
            self.backgroundValue.setText(format_float(out.background))
            self.computationTimeValue.setText(format_float(out.calc_time))
            self.chiDofValue.setText(format_float(out.chi2[0]))
            self.oscillationValue.setText(format_float(out.oscillations))
            self.posFractionValue.setText(format_float(out.pos_frac))
            self.sigmaPosFractionValue.setText(format_float(out.pos_err))

    def acceptsData(self) -> bool:
        # TODO: Temporary
        return True

    def threadError(self, error: str):
        logger.error(error)
        # TODO: No function to stop calculation yet.

    def calculationCompleted(self, out, cov, pr, elapsed):
        # TODO: Placeholder. Just output the numbers for now. Later the result
        # should be plotted.
        logging.info(f'{out} {cov} {pr} {elapsed}')
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
        self.updateGuiValues()

    def startThread(self):
        self.isCalculating = True
        self.enableButtons()

        # TODO: Calc thread should be declared beforehand.
        self.calcThread = CalcPr(
            self.currentResult.calculator,
            # TODO: no of terms should be somewhere else
            self.currentResult.calculator.noOfTerms,
            tab_id=[[self.tab_id]],
            error_func=self.threadError,
            completefn=self.calculationCompleted, # TODO: Implement
            updatefn=None
        )

        self.calcThread.queue()
        # TODO: Why are we doing this?
        self.calcThread.ready(2.5)
