#Global
from PySide6.QtWidgets import QWidget

#Local Perspectives
from sas.qtgui.Calculators.Shape2SAS.UI.ViewerButtonsUI import Ui_ViewerButtons
from sas.qtgui.Calculators.Shape2SAS.UI.ViewerModelRadiusUI import Ui_ViewerModelRadius


class ViewerButtons(QWidget, Ui_ViewerButtons):
    """XY, XZ, YZ view axis buttons"""
    def __init__(self, parent=None):
        super().__init__()

        self.setupUi(self)


class ViewerModelRadius(QWidget, Ui_ViewerModelRadius):
    """Model radius view"""
    def __init__(self, parent=None):
        super().__init__()

        self.setupUi(self)



