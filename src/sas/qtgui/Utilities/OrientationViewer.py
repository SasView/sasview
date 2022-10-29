import numpy as np

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtCore import Qt

import matplotlib as mpl

import pyqtgraph.opengl as gl
from pyqtgraph.Transform3D import Transform3D
from OpenGL.GL import *

from sasmodels.core import load_model_info, build_model
from sasmodels.data import empty_data2D
from sasmodels.direct_model import DirectModel
from sasmodels.jitter import Rx, Ry, Rz

from sas.qtgui.Utilities.OrientationViewerController import OrientationViewierController, Orientation
from sas.qtgui.Utilities.OrientationViewerGraphics import OrientationViewerGraphics






class OrientationViewer(QtWidgets.QWidget):

    cuboid_scaling = [0.1, 0.4, 1.0]
    n_ghosts_per_perameter = 10
    log_I_max = 3
    log_I_min = -3

    @staticmethod
    def colormap_scale(data):
        x = data.copy()
        x -= np.min(x)
        x /= np.max(x)
        return x

    def __init__(self, parent=None):
        super().__init__()


        self.graph = gl.GLViewWidget()
        #
        # glBegin(GL_VERTEX_ARRAY)
        #
        # glEnd()
        #
        # glBlendFunc(GL_ONE_MINUS_SRC_ALPHA, GL_SRC_ALPHA)
        # glEnable(GL_COLOR_MATERIAL)
        # glEnable(GL_BLEND)


        self.graph.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.controller = OrientationViewierController()

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.graph)
        layout.addWidget(self.controller)
        self.setLayout(layout)

        self.arrow = self.create_arrow()
        self.image_plane_coordinate_points = np.linspace(-2, 2, 256)

        # temporary plot data
        X, Y = np.meshgrid(self.image_plane_coordinate_points, self.image_plane_coordinate_points)

        R2 = (X**2 + Y**2)

        self.image_plane_data = 0.5*(1+np.cos(5*np.sqrt(R2))) / (5*R2+1)

        self.colormap = mpl.colormaps["viridis"]
        # for i in range(101):
        #     print(self.colormap(i))

        self.image_plane_colors = self.colormap(OrientationViewer.colormap_scale(self.image_plane_data))

        self.image_plane = gl.GLSurfacePlotItem(
            self.image_plane_coordinate_points,
            self.image_plane_coordinate_points,
            self.image_plane_data,
            self.image_plane_colors
        )


        ghost_alpha = 1/(OrientationViewer.n_ghosts_per_perameter**3) #0.9**(1/(OrientationViewer.n_ghosts_per_perameter**3))
        self.ghosts = []
        for a in np.linspace(-1, 1, OrientationViewer.n_ghosts_per_perameter):
            for b in np.linspace(-1, 1, OrientationViewer.n_ghosts_per_perameter):
                for c in np.linspace(-1, 1, OrientationViewer.n_ghosts_per_perameter):
                    ghost = OrientationViewerGraphics.create_cube(ghost_alpha)
                    self.graph.addItem(ghost)
                    self.ghosts.append((a, b, c, ghost))



        # self.graph.addItem(self.arrow)
        # self.graph.addItem(self.image_plane)

        self.arrow.rotate(180, 1, 0, 0)
        self.arrow.scale(0.05, 0.05, 0.2)

        for _, _, _, ghost in self.ghosts:
            ghost.setTransform(OrientationViewerGraphics.createTransform(0, 0, 0, OrientationViewer.cuboid_scaling))

        self.image_plane.translate(0,0,-2)

        self.controller.valueEdited.connect(self.on_angle_change)




    def on_angle_change(self, orientation: Orientation):

        for a, b, c, ghost in self.ghosts:

            ghost.setTransform(
                OrientationViewerGraphics.createTransform(
                    orientation.theta + 0.5*a*orientation.dtheta,
                    orientation.phi + 0.5*b*orientation.dphi,
                    orientation.psi + 0.5*c*orientation.dpsi,
                    OrientationViewer.cuboid_scaling))

    @staticmethod
    def create_calculator(n=256, qmax=0.5):
        """
        Make a parallelepiped model calculator for q range -qmax to qmax with n samples
        """

        model_info = load_model_info("parallelepiped")
        model = build_model(model_info)
        q = np.linspace(-qmax, qmax, n)
        data = empty_data2D(q, q)
        calculator = DirectModel(data, model)

        return calculator


def main():
    """ Show a demo of the slider """
    import os

    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    app = QtWidgets.QApplication([])

    app.setAttribute(Qt.AA_EnableHighDpiScaling)
    app.setAttribute(Qt.AA_ShareOpenGLContexts)


    mainWindow = QtWidgets.QMainWindow()
    viewer = OrientationViewer(mainWindow)

    mainWindow.setCentralWidget(viewer)

    mainWindow.show()

    mainWindow.resize(600, 600)
    app.exec_()


if __name__ == "__main__":
    main()