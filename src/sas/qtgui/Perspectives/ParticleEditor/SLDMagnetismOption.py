from PySide6 import QtWidgets

from sas.qtgui.Perspectives.ParticleEditor.UI.SLDMagOptionUI import Ui_SLDMagnetismOption


class SLDMagnetismOption(QtWidgets.QWidget, Ui_SLDMagnetismOption):
    def __init__(self, parent=None):
        super().__init__()

        self.setupUi(self)
