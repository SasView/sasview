from typing import Optional
import numpy as np

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtCore import Qt

import matplotlib as mpl

import pyqtgraph.opengl as gl
from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt5.QtOpenGL import QGLWidget

from sasmodels.core import load_model_info, build_model
from sasmodels.data import empty_data2D
from sasmodels.direct_model import DirectModel

from sas.qtgui.Utilities.OrientationViewer.OrientationViewerController import OrientationViewierController, Orientation
from sas.qtgui.Utilities.OrientationViewer.OrientationViewerGraphics import OrientationViewerGraphics
from sas.qtgui.Utilities.OrientationViewer.FloodBarrier import FloodBarrier





class OrientationViewer(QtWidgets.QWidget):

    # Dimensions of scattering cuboid
    a = 0.1
    b = 0.4
    c = 1.0

    cuboid_scaling = [a, b, c]

    n_ghosts_per_perameter = 8
    n_q_samples = 256
    log_I_max = 10
    log_I_min = -3
    q_max = 0.5
    polydispersity_distribution = "gaussian"

    log_I_range = log_I_max - log_I_min

    def __init__(self, parent=None):
        super().__init__()

        self.parent = parent

        # Put a barrier that will stop a flood of events going to the calculator
        self.set_image_data = FloodBarrier[Orientation](self._set_image_data, Orientation(), 0.5)

        self.graph = gl.GLViewWidget()

        self.graph.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.controller = OrientationViewierController()

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.graph)
        layout.addWidget(self.controller)
        self.setLayout(layout)

        self.arrow = OrientationViewerGraphics.create_arrow()
        self.image_plane_coordinate_points = np.linspace(-3, 3, 256)

        # temporary plot data
        x, y = np.meshgrid(self.image_plane_coordinate_points, self.image_plane_coordinate_points)
        self.image_plane_data = np.zeros_like(x)

        self.colormap = mpl.colormaps["viridis"]

        self.image_plane_colors = self.colormap(self.image_plane_data)

        self.image_plane = gl.GLSurfacePlotItem(
            self.image_plane_coordinate_points,
            self.image_plane_coordinate_points,
            self.image_plane_data,
            self.image_plane_colors
        )

        ghost_alpha = 1/(OrientationViewer.n_ghosts_per_perameter**3)
        self.ghosts = []
        for a in np.linspace(-1, 1, OrientationViewer.n_ghosts_per_perameter):
            for b in np.linspace(-1, 1, OrientationViewer.n_ghosts_per_perameter):
                for c in np.linspace(-1, 1, OrientationViewer.n_ghosts_per_perameter):
                    ghost = OrientationViewerGraphics.create_cube(ghost_alpha)
                    self.graph.addItem(ghost)
                    self.ghosts.append((a, b, c, ghost))



        self.graph.addItem(self.arrow)
        self.graph.addItem(self.image_plane)

        self.arrow.rotate(180, 1, 0, 0)
        self.arrow.scale(0.05, 0.05, 0.05)
        self.arrow.translate(0,0,1)

        self.image_plane.translate(0,0,-0.5) # It's 1 unit thick, so half way

        for _, _, _, ghost in self.ghosts:
            ghost.setTransform(OrientationViewerGraphics.createCubeTransform(0, 0, 0, OrientationViewer.cuboid_scaling))


        self.controller.valueEdited.connect(self.on_angle_change)

        self.calculator = OrientationViewer.create_calculator()
        self.on_angle_change(Orientation())



    def _set_image_data(self, orientation: Orientation):

        data = self.scatering_data(orientation)

        scaled_data = (np.log(data) - OrientationViewer.log_I_min) / OrientationViewer.log_I_range
        self.image_plane_data = np.clip(scaled_data, 0, 1)

        self.image_plane_colors = self.colormap(self.image_plane_data)

        self.image_plane.setData(z=self.image_plane_data, colors=self.image_plane_colors)



    def on_angle_change(self, orientation: Optional[Orientation]):

        if orientation is None:
            return

        for a, b, c, ghost in self.ghosts:

            ghost.setTransform(
                OrientationViewerGraphics.createCubeTransform(
                    orientation.theta + 0.5*a*orientation.dtheta,
                    orientation.phi + 0.5*b*orientation.dphi,
                    orientation.psi + 0.5*c*orientation.dpsi,
                    OrientationViewer.cuboid_scaling))

        self.set_image_data(orientation)

    @staticmethod
    def create_calculator():
        """
        Make a parallelepiped model calculator for q range -qmax to qmax with n samples
        """

        model_info = load_model_info("parallelepiped")
        model = build_model(model_info)
        q = np.linspace(-OrientationViewer.q_max, OrientationViewer.q_max, OrientationViewer.n_q_samples)
        data = empty_data2D(q, q)
        calculator = DirectModel(data, model)

        return calculator


    def polydispersity_sample_count(self, orientation):
        """ Work out how many samples to do for the polydispersity"""
        polydispersity = [orientation.dtheta, orientation.dphi, orientation.dpsi]
        is_polydisperse = [1 if x > 0 else 0 for x in polydispersity]
        n_polydisperse = np.sum(is_polydisperse)

        samples = int(200 / (n_polydisperse**2.2 + 1)) #

        return (samples * x for x in is_polydisperse)

    def scatering_data(self, orientation: Orientation) -> np.ndarray:

        # add the orientation parameters to the model parameters

        theta_pd_n, phi_pd_n, psi_pd_n = self.polydispersity_sample_count(orientation)

        data = self.calculator(
            theta=orientation.theta,
            theta_pd=orientation.dtheta,
            theta_pd_type=OrientationViewer.polydispersity_distribution,
            theta_pd_n=theta_pd_n,
            phi=orientation.phi,
            phi_pd=orientation.dphi,
            phi_pd_type=OrientationViewer.polydispersity_distribution,
            phi_pd_n=phi_pd_n,
            psi=orientation.psi,
            psi_pd=orientation.dpsi,
            psi_pd_type=OrientationViewer.polydispersity_distribution,
            psi_pd_n=psi_pd_n,
            a=OrientationViewer.a,
            b=OrientationViewer.b,
            c=OrientationViewer.c,
            background=np.exp(OrientationViewer.log_I_min))

        return np.reshape(data, (OrientationViewer.n_q_samples, OrientationViewer.n_q_samples))



def main():

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