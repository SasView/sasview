
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QSizePolicy
import pyqtgraph.opengl as gl

from sas.qtgui.Utilities.OrientationViewerController import OrientationViewierController


class OrientationViewer(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__()

        self.graph = gl.GLViewWidget()
        self.graph.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

        self.controller = OrientationViewierController()
        layout = QtWidgets.QVBoxLayout()

        layout.addWidget(self.graph)
        layout.addWidget(self.controller)
        self.setLayout(layout)







        xgrid = gl.GLGridItem()
        ygrid = gl.GLGridItem()
        zgrid = gl.GLGridItem()
        self.graph.addItem(xgrid)
        self.graph.addItem(ygrid)
        self.graph.addItem(zgrid)

        ## rotate x and y grids to face the correct direction
        xgrid.rotate(90, 0, 1, 0)
        ygrid.rotate(90, 1, 0, 0)

        ## scale each grid differently
        xgrid.scale(0.2, 0.1, 0.1)
        ygrid.scale(0.2, 0.1, 0.1)
        zgrid.scale(0.1, 0.2, 0.1)



def main():
    """ Show a demo of the slider """
    app = QtWidgets.QApplication([])

    mainWindow = QtWidgets.QMainWindow()
    viewer = OrientationViewer(mainWindow)

    mainWindow.setCentralWidget(viewer)

    mainWindow.show()

    mainWindow.resize(700, 700)
    app.exec_()


if __name__ == "__main__":
    main()