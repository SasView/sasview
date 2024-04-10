from typing import Callable

from PySide6 import QtWidgets
from sas.qtgui.Perspectives.ParticleEditor.UI.AxisButtonsUI import Ui_AxisSelection
from sas.qtgui.Perspectives.ParticleEditor.UI.PlaneButtonsUI import Ui_PlaneSelection

x_angles = (90, 0)
y_angles = (0, 90)
z_angles = (0, 0)


class PlaneButtons(QtWidgets.QWidget, Ui_PlaneSelection):
    """ XY, XZ, YZ plane selection buttons, sets angles """

    def __init__(self, set_angles_function: Callable[[float, float], None]):
        super().__init__()
        self.setupUi(self)

        self.setAngles = set_angles_function

        self.cmdSelectXY.clicked.connect(lambda: self.setAngles(*z_angles))
        self.cmdSelectYZ.clicked.connect(lambda: self.setAngles(*x_angles))
        self.cmdSelectXZ.clicked.connect(lambda: self.setAngles(*y_angles))



class AxisButtons(QtWidgets.QWidget, Ui_AxisSelection):
    """ X, Y, Z axis selection buttons, sets angles """

    def __init__(self, set_angles_function: Callable[[float, float], None]):
        super().__init__()
        self.setupUi(self)

        self.setAngles = set_angles_function

        self.cmdSelectX.clicked.connect(lambda: self.setAngles(*x_angles))
        self.cmdSelectY.clicked.connect(lambda: self.setAngles(*y_angles))
        self.cmdSelectZ.clicked.connect(lambda: self.setAngles(*z_angles))

