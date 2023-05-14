from PySide6 import QtWidgets

from sas.qtgui.Perspectives.ParticleEditor.UI.CodeToolBarUI import Ui_CodeToolBar

class RadiusSelection(QtWidgets.QWidget, Ui_CodeToolBar):
    def __init__(self, parent=None):
        super().__init__()

        self.setupUi(self)