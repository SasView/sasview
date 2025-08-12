from typing import NamedTuple

from PySide6 import QtWidgets
from PySide6.QtCore import Signal

from sas.qtgui.Utilities.OrientationViewer.UI.OrientationViewerControllerUI import Ui_OrientationViewierControllerUI


class Orientation(NamedTuple):
    """ Data sent when updating the plot"""
    theta: int = 0
    phi: int = 0
    psi: int = 0
    dtheta: int = 0
    dphi: int = 0
    dpsi: int = 0



class OrientationViewierController(QtWidgets.QDialog, Ui_OrientationViewierControllerUI):

    """ Widget that controls the orientation viewer"""

    sliderSet = Signal(Orientation, name='sliderSet')
    sliderMoved = Signal(Orientation, name='sliderMoved')

    def __init__(self, parent=None):
        super().__init__()

        self.setupUi(self)

        self.setLabels(Orientation())

        # All sliders emit the same signal - the angular coordinates in degrees
        self.thetaSlider.sliderReleased.connect(self.onSliderSet)
        self.phiSlider.sliderReleased.connect(self.onSliderSet)
        self.psiSlider.sliderReleased.connect(self.onSliderSet)
        self.deltaTheta.sliderReleased.connect(self.onSliderSet)
        self.deltaPhi.sliderReleased.connect(self.onSliderSet)
        self.deltaPsi.sliderReleased.connect(self.onSliderSet)

        self.thetaSlider.valueChanged.connect(self.onSliderMoved)
        self.phiSlider.valueChanged.connect(self.onSliderMoved)
        self.psiSlider.valueChanged.connect(self.onSliderMoved)
        self.deltaTheta.valueChanged.connect(self.onSliderMoved)
        self.deltaPhi.valueChanged.connect(self.onSliderMoved)
        self.deltaPsi.valueChanged.connect(self.onSliderMoved)

    def setLabels(self, orientation: Orientation):

        self.thetaNumber.setText(f"{orientation.theta}°")
        self.phiNumber.setText(f"{orientation.phi}°")
        self.psiNumber.setText(f"{orientation.psi}°")

        self.deltaThetaNumber.setText(f"{orientation.dtheta}°")
        self.deltaPhiNumber.setText(f"{orientation.dphi}°")
        self.deltaPsiNumber.setText(f"{orientation.dpsi}°")


    def onSliderSet(self):
        theta = self.thetaSlider.value()
        phi = self.phiSlider.value()
        psi = self.psiSlider.value()

        dtheta = self.deltaTheta.value()
        dphi = self.deltaPhi.value()
        dpsi = self.deltaPsi.value()

        orientation = Orientation(theta, phi, psi, dtheta, dphi, dpsi)
        self.sliderSet.emit(orientation)
        self.setLabels(orientation)

    def onSliderMoved(self):

        theta = self.thetaSlider.value()
        phi = self.phiSlider.value()
        psi = self.psiSlider.value()

        dtheta = self.deltaTheta.value()
        dphi = self.deltaPhi.value()
        dpsi = self.deltaPsi.value()

        orientation = Orientation(theta, phi, psi, dtheta, dphi, dpsi)
        self.sliderMoved.emit(orientation)
        self.setLabels(orientation)




def main():
    """ Show a demo of the slider """
    app = QtWidgets.QApplication([])

    mainWindow = QtWidgets.QMainWindow()
    viewer = OrientationViewierController(mainWindow)

    mainWindow.setCentralWidget(viewer)

    mainWindow.show()

    mainWindow.resize(700, 100)
    app.exec_()


if __name__ == "__main__":
    main()
