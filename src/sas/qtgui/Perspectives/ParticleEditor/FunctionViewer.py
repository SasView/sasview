import numpy as np

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontMetrics

def cross_section(particle: Particle, plane_origin: np.ndarray, plane_normal: np.ndarray):
    pass

class FunctionViewer(QtWidgets.QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.radius = 1
        self.sizePx = 500
        self.function = lambda x,y,z: np.ones_like(x)

        self.theta = 0.0
        self.phi = 0.0
        self.normal_offset = 0.0

        self.scene = QtWidgets.QGraphicsScene()
        self.setScene(self.scene)

        self.pixmap = QtGui.QPixmap(self.sizePx, self.sizePx)
        self.pixmap_item = self.scene.addPixmap(self.pixmap)


    def setRadius(self):
        pass
    def setSizePx(self, size):
        pass
    def setFunction(self, fun):

        # Set the function here

        self.updateImage()

    def updateImage(self):

        # Draw image

        self.drawScale()
        self.drawAxes()


    def drawScale(self):
        pass

    def drawAxes(self):
        pass


def main():
    """ Show a demo of the function viewer"""
    app = QtWidgets.QApplication([])
    viewer = FunctionViewer()
    viewer.show()
    app.exec_()


if __name__ == "__main__":
    main()
