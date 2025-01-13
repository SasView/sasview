#Global
from PySide6.QtWidgets import QApplication, QWidget

#Local Perspectives
from UI.ViewerButtonsUI import Ui_ViewerButtons
from UI.ViewerModelRadiusUI import Ui_ViewerModelRadius


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



