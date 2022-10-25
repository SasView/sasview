from PyQt5 import QtWidgets

from sas.qtgui.Utilities.UI.OrientationViewerControllerUI import Ui_OrientationViewierControllerUI


class AddMultEditor(QtWidgets.QDialog, Ui_OrientationViewierControllerUI):
    def __init__(self, parent=None):
        super().__init__()

