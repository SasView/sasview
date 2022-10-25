
from PyQt5 import QtWidgets
import pyqtgraph.opengl as gl


class OrientationViewer(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__()

        self.resize(600, 700)

        self.graph = gl.GLViewWidget()
        layout = QtWidgets.QVBoxLayout()

        # Add widgets to the layout
        layout.addWidget(self.graph)
        layout.addWidget(QtWidgets.QPushButton("Top"))
        layout.addWidget(QtWidgets.QPushButton("Center"))
        layout.addWidget(QtWidgets.QPushButton("Bottom"))
        # Set the layout on the application's window
        self.setLayout(layout)

        ## create three grids, add each to the view
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
    app.exec_()


if __name__ == "__main__":
    main()