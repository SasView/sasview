
from dataclasses import dataclass
from PySide6.QtWidgets import QWidget

from src.sas.qtgui.Perspectives.Inversion.InversionLogic import InversionLogic
from src.sas.qtgui.Perspectives.Inversion.UI.TabbedInversionUI import Ui_PrInversion
from src.sas.qtgui.Plotting.PlotterData import Data1D
from src.sas.qtgui.Utilities import GuiUtils
from src.sas.sascalc.pr.NewInvertor import NewInvertor

@dataclass
class InversionResult:
    logic: InversionLogic
    calculator: NewInvertor
    pr_plot: Data1D | None
    data_plot: Data1D | None


# Default Values for inputs
NUMBER_OF_TERMS = 10
REGULARIZATION = 0.0
BACKGROUND_INPUT = 0.0
Q_MIN_INPUT = 0.0
Q_MAX_INPUT = 0.0
MAX_DIST = 140.0


class NewInversionWidget(QWidget, Ui_PrInversion):
    # The old class had 'name' and 'ext'. Since this class doesn't inherit from
    # perspective, I'm not convinced they are needed here.

    def __init__(self, parent=None, data=None, tab_id=1, tab_name=''):
        super(NewInversionWidget, self).__init__()

        self.parent = parent
        self.tab_name = tab_name
        self.tab_id = tab_id
        self._data: Data1D | None
        self.data = data



        # We're going to use this structure even if we're just dealing with one
        # specific datum. Just that this dictionary would then have one item in
        # it.
        self.results: list[InversionResult] = [
            InversionResult(logic=InversionLogic(),
                            calculator=NewInvertor(),
                            pr_plot=None,
                            data_plot=None)
        ]

        self.isCalculating: bool = False
        self.calculator  = NewInvertor()

        self.setupUi(self)
        self.updateGuiValues()

    # TODO: Need to verify type hint for data.
    def updateTab(self, data: Data1D, tab_id: int):
        self.data = data
        self.tab_id = tab_id
        self.updateGuiValues()

    @property
    def data(self) -> Data1D | None:
        return self._data

    @data.setter
    def data(self, value: GuiUtils.HashableStandardItem):
        self._data = GuiUtils.dataFromItem(value)

    @property
    def is_batch(self) -> bool:
        return len(self.results) > 1

    @property
    def currentDataIndex(self) -> int:
        return self.dataList.currentIndex()

    @property
    def currentResult(self) -> InversionResult:
        return self.results[self.currentDataIndex]

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
        if self.data is None:
            self.dataList.setCurrentText('')
        else:
            # TODO: Will have multiple values when batch is implemented.
            self.dataList.addItem(self.data.name)
            self.dataList.setCurrentIndex(0)


        # TODO: This won't work for batch at the moment.
        current_calculator = self.currentResult.calculator

        self.noOfTermsInput.setText(str(current_calculator.noOfTerms))
        self.regularizationConstantInput.setText(str(current_calculator.alpha))
        self.maxDistanceInput.setText(str(current_calculator.dmax))

        # TODO: Maybe don't see the others until they've been calculated.

    def acceptsData(self) -> bool:
        # TODO: Temporary
        return True
