from typing import Optional, List
import numpy as np

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtCore import Qt

import matplotlib as mpl

from sasmodels.core import load_model_info, build_model
from sasmodels.data import empty_data2D
from sasmodels.direct_model import DirectModel
from sasmodels.jitter import Rx, Ry, Rz

from sas.qtgui.GL.color import Color
from sas.qtgui.GL.scene import Scene
from sas.qtgui.GL.transforms import Rotation, Scaling, Translation
from sas.qtgui.GL.surface import Surface
from sas.qtgui.GL.cylinder import Cylinder
from sas.qtgui.GL.cone import Cone
from sas.qtgui.GL.cube import Cube

from sas.qtgui.Utilities.OrientationViewer.OrientationViewerController import OrientationViewierController, Orientation


def createCubeTransform(theta_deg: float, phi_deg: float, psi_deg: float, scaling: List[float]) -> np.ndarray:
    # Get rotation matrix
    r_mat = Rz(phi_deg) @ Ry(theta_deg) @ Rz(psi_deg) @ np.diag(scaling)

    # Get the 4x4 transformation matrix, by (1) padding by zeros (2) setting the corner element to 1
    trans_mat = np.pad(r_mat, ((0, 1), (0, 1)))
    trans_mat[-1, -1] = 1
    trans_mat[2, -1] = 2

    return trans_mat

class OrientationViewer(QtWidgets.QWidget):

    # Dimensions of scattering cuboid
    a = 0.1
    b = 0.4
    c = 1.0

    arrow_size = 0.2
    arrow_color = Color(0.9, 0.9, 0.9)
    ghost_color = Color(0.6, 0.6, 0.6)

    cuboid_scaling = [a, b, c]

    n_ghosts_per_perameter = 8
    n_q_samples = 128
    log_I_max = 10
    log_I_min = -3
    q_max = 0.5
    polydispersity_distribution = "gaussian"

    log_I_range = log_I_max - log_I_min

    def __init__(self, parent=None):
        super().__init__()

        self._colormap_name = 'viridis'

        self.parent = parent

        self.scene = Scene()

        self.scene.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.controller = OrientationViewierController()

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.scene)
        layout.addWidget(self.controller)
        self.setLayout(layout)

        self.arrow = Translation(0,0,1.5,
                         Rotation(180,0,1,0,
                             Scaling(
                                OrientationViewer.arrow_size,
                                OrientationViewer.arrow_size,
                                OrientationViewer.arrow_size,
                                Scaling(0.1, 0.1, 1,
                                    Cylinder(colors=OrientationViewer.arrow_color)),
                                Translation(0,0,1.3,
                                        Scaling(0.3, 0.3, 0.3,
                                            Cone(colors=OrientationViewer.arrow_color))))))

        self.scene.add(self.arrow)

        self.image_plane_coordinate_points = np.linspace(-3, 3, OrientationViewer.n_q_samples)

        # temporary plot data
        x, y = np.meshgrid(self.image_plane_coordinate_points, self.image_plane_coordinate_points)
        self.image_plane_data = np.zeros_like(x)

        self.surface = Surface(
                            self.image_plane_coordinate_points,
                            self.image_plane_coordinate_points,
                            self.image_plane_data,
                            edge_skip=8)

        self.surface.wireframe_render_enabled = False
        # self.surface.colormap = 'Greys'


        self.image_plane = Translation(0,0,-1, Scaling(0.5, 0.5, 0.5, self.surface))

        self.scene.add(self.image_plane)


        for a in np.linspace(-1, 1, OrientationViewer.n_ghosts_per_perameter):
            b_ghosts = []
            for b in np.linspace(-1, 1, OrientationViewer.n_ghosts_per_perameter):
                c_ghosts = []
                for c in np.linspace(-1, 1, OrientationViewer.n_ghosts_per_perameter):
                    ghost = Cube(edge_colors=OrientationViewer.ghost_color)



        self.first_rotation = Rotation(0,0,0,1,
                        Scaling(OrientationViewer.a,
                                OrientationViewer.b,
                                OrientationViewer.c,
                                Cube(edge_colors=Color(1,1,1), colors=Color(0,1,0))
                            ))

        self.second_rotation = Rotation(0,0,1,0,self.first_rotation)
        self.third_rotation = Rotation(0,0,0,1,self.second_rotation)

        self.cubes = Translation(0,0,0.5,self.third_rotation)

        self.scene.add(self.cubes)

        #

        #
        # for _, _, _, ghost in self.ghosts:
        #     ghost.setTransform(OrientationViewerGraphics.createCubeTransform(0, 0, 0, OrientationViewer.cuboid_scaling))
        #
        #
        self.controller.sliderSet.connect(self.on_angle_changed)
        self.controller.sliderMoved.connect(self.on_angle_changing)

        self.calculator = OrientationViewer.create_calculator()
        self.on_angle_changed(Orientation())

    @property
    def colormap(self) -> str:
        return self._colormap_name

    @colormap.setter
    def colormap(self, colormap_name: str):
        self._colormap_name = colormap_name
        self.surface.colormap = self._colormap_name

    def _set_image_data(self, orientation: Orientation):
        """ Set the data on the plot"""

        data = self.scatering_data(orientation)

        scaled_data = (np.log(data) - OrientationViewer.log_I_min) / OrientationViewer.log_I_range
        self.image_plane_data = np.clip(scaled_data, 0, 1)

        self.surface.set_z_data(self.image_plane_data)

        # self.surface.colormap = self.colormap

        self.scene.update()



    def on_angle_changed(self, orientation: Optional[Orientation]):

        """ Response to angle change"""

        if orientation is None:
            return


        #r_mat = Rz(phi_deg) @ Ry(theta_deg) @ Rz(psi_deg) @ np.diag(scaling)
        self.first_rotation.angle = orientation.psi
        self.second_rotation.angle = orientation.theta
        self.third_rotation.angle = orientation.phi

        # for a, b, c, ghost in self.ghosts:
        #
        #     ghost.setTransform(
        #         OrientationViewerGraphics.createCubeTransform(
        #             orientation.theta + 0.5*a*orientation.dtheta,
        #             orientation.phi + 0.5*b*orientation.dphi,
        #             orientation.psi + 0.5*c*orientation.dpsi,
        #             OrientationViewer.cuboid_scaling))

        self._set_image_data(orientation)


    def on_angle_changing(self, orientation: Optional[Orientation]):

        """ Response to angle change"""

        if orientation is None:
            return

        # self.surface.colormap = "Greys"

        #r_mat = Rz(phi_deg) @ Ry(theta_deg) @ Rz(psi_deg) @ np.diag(scaling)
        self.first_rotation.angle = orientation.psi
        self.second_rotation.angle = orientation.theta
        self.third_rotation.angle = orientation.phi

        # for a, b, c, ghost in self.ghosts:
        #
        #     ghost.setTransform(
        #         OrientationViewerGraphics.createCubeTransform(
        #             orientation.theta + 0.5*a*orientation.dtheta,
        #             orientation.phi + 0.5*b*orientation.dphi,
        #             orientation.psi + 0.5*c*orientation.dpsi,
        #             OrientationViewer.cuboid_scaling))

        self.scene.update()

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