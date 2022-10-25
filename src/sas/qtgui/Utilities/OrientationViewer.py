import numpy as np
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QSizePolicy
import pyqtgraph.opengl as gl
from pyqtgraph.Transform3D import Transform3D

from sas.qtgui.Utilities.OrientationViewerController import OrientationViewierController, Orientation

from sasmodels.sasmodels.jitter import Rx, Ry, Rz

class OrientationViewer(QtWidgets.QWidget):

    cuboid_scaling = [0.1, 0.4, 1.0]

    def __init__(self, parent=None):
        super().__init__()

        self.graph = gl.GLViewWidget()
        self.graph.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

        self.controller = OrientationViewierController()
        layout = QtWidgets.QVBoxLayout()

        layout.addWidget(self.graph)
        layout.addWidget(self.controller)
        self.setLayout(layout)


        self.cube = self.create_cube()



        xgrid = gl.GLGridItem()
        ygrid = gl.GLGridItem()
        zgrid = gl.GLGridItem()

        self.graph.addItem(self.cube)

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

        self.cube.setTransform(self.createTransform(0, 0, 0))

        self.controller.valueEdited.connect(self.on_angle_change)

    @staticmethod
    def hypercube(n):
        if n <= 1:
            return [[0], [1]]
        else:
            hypersquare = OrientationViewer.hypercube(n-1)
            return [[0] + vert for vert in hypersquare] + [[1] + vert for vert in hypersquare]


    @staticmethod
    def create_cube():
        # Sorry
        vertices = OrientationViewer.hypercube(3)

        faces_and_colors = []

        for fixed_dim in range(3):
            for zero_one in range(2):
                this_face = [(ind, v) for ind, v in enumerate(vertices) if v[fixed_dim] == zero_one]

                def sort_key(x):
                    _, v = x
                    other_dims = v[:fixed_dim] + v[fixed_dim+1:]
                    return (v[fixed_dim] - 0.5)*np.arctan2(other_dims[0]-0.5, other_dims[1]-0.5)

                this_face = sorted(this_face, key=sort_key)

                color = [0.6,0.6,0.6,1]
                color[fixed_dim]=0.4

                # faces_and_colors.append([[this_face[x][0] for x in range(4)], color])

                faces_and_colors.append(([this_face[x][0] for x in (0,1,2)], color))
                faces_and_colors.append(([this_face[x][0] for x in (2,3,0)], color))

        vertices = np.array(vertices, dtype=float) - 0.5
        faces = np.array([face for face, _ in faces_and_colors])
        colors = np.array([color for _, color in faces_and_colors])

        return gl.GLMeshItem(vertexes=vertices, faces=faces, faceColors=colors,
                             drawEdges=False, edgeColor=(0, 0, 0, 1), smooth=False)


    @staticmethod
    def createTransform(theta_deg: float, phi_deg: float, psi_deg: float) -> Transform3D:

        # Get rotation matrix
        r_mat = Rz(phi_deg)@Ry(theta_deg)@Rz(psi_deg)@np.diag(OrientationViewer.cuboid_scaling)

        # Get the 4x4 transformation matrix, by (1) padding by zeros (2) setting the corner element to 1
        trans_mat = np.pad(r_mat, ((0, 1), (0, 1)))
        trans_mat[-1, -1] = 1

        return Transform3D(trans_mat)


    def on_angle_change(self, orientation: Orientation):
        self.cube.setTransform(
            self.createTransform(
                orientation.theta,
                orientation.phi,
                orientation.psi))



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