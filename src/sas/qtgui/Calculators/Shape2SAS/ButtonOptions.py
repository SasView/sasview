# Global
from PySide6.QtWidgets import QWidget

# Local Perspectives
from sas.qtgui.Calculators.Shape2SAS.UI.ButtonOptionsUI import Ui_ButtonOptions


class ButtonOptions(QWidget, Ui_ButtonOptions):
    """close, reset and help options"""
    def __init__(self, parent=None):
        super().__init__()

        self.setupUi(self)

