
from PySide6 import QtWidgets

from sas.qtgui.Perspectives.ParticleEditor.UI.RadiusSelectionUI import Ui_RadiusSelection


class RadiusSelection(QtWidgets.QWidget, Ui_RadiusSelection):
    def __init__(self, text: str | None=None, parent=None):
        super().__init__()

        self.setupUi(self)

        if text is not None:
            self.label.setText(text)


    def radius(self):
        return float(self.radiusField.value())
