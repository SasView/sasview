
from dataclasses import dataclass
from PySide6.QtWidgets import QWidget

from src.sas.qtgui.Perspectives.Inversion.InversionLogic import InversionLogic
from src.sas.qtgui.Perspectives.Inversion.UI.TabbedInversionUI import Ui_PrInversion
from src.sas.qtgui.Plotting.PlotterData import Data1D
from src.sas.sascalc.pr.invertor import Invertor

@dataclass
class InversionResult:
    logic: InversionLogic
    calculator: Invertor
    pr_plot: Data1D | None
    data_plot: Data1D | None


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
        self.results: list[InversionResult] = [
            InversionResult(logic=InversionLogic(),
                            calculator=Invertor(),
                            pr_plot=None,
                            data_plot=None)
        ]

        self.isCalculating: bool = False

        self.setupUi(self)

    @property
    def is_batch(self) -> bool:
        return len(self.results) > 1

    @property
    def currentDataIndex(self) -> int:
        return self.dataList.currentIndex()

    @property
    def currentResult(self) -> InversionResult:
        return self.results[self.currentDataIndex]

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
