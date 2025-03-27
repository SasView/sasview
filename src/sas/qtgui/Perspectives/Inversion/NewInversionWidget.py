
from dataclasses import dataclass
from PySide6.QtWidgets import QWidget

from src.sas.qtgui.Perspectives.Inversion.InversionLogic import InversionLogic
from src.sas.qtgui.Perspectives.Inversion.UI.TabbedInversionUI import Ui_PrInversion
from src.sas.qtgui.Plotting.PlotterData import Data1D
from src.sas.sascalc.pr.invertor import Invertor

@dataclass
class InversionBatchResult:
    logic: InversionLogic
    calculator: Invertor
    pr_plot: Data1D
    data_plot: Data1D


class NewInversionWidget(QWidget, Ui_PrInversion):
    # The old class had 'name' and 'ext'. Since this class doesn't inherit from
    # perspective, I'm not convinced they are needed here.

    def __init__(self, parent=None, data=None, tab_id=1):
       super().__init__()

       self.parent = parent

       # We're going to use this structure even if we're just dealing with one
       # specific datum. Just that this dictionary would then have one item in
       # it.
       self.batchResults: list[InversionBatchResult] = []
