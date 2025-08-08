from PySide6.QtWidgets import QWidget

from sas.qtgui.Perspectives.ParticleEditor.ParameterFunctionality.UI.ParameterTableButtonsUI import (
    Ui_ParameterTableButtons,
)


class ParameterTableButtons(QWidget, Ui_ParameterTableButtons):
    def __init__(self):
        super().__init__()

        self.setupUi(self)
