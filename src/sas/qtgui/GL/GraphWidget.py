from typing import Optional, Tuple, List, Callable
import numpy as np

from PyQt5 import QtWidgets, Qt, QtGui, QtOpenGL, QtCore

from OpenGL.GL import *
from OpenGL.GLU import *

from sas.qtgui.GL.Renderable import Renderable
from sas.qtgui.GL.Color import Color
from sas.qtgui.GL.Surface import Surface
from sas.qtgui.GL.Cone import Cone

class GraphWidget(QtOpenGL.QGLWidget):


    def __init__(self, on_key: Callable[[int], None] = lambda x: None, parent=None):

        super().__init__(parent)
        self.setMinimumSize(640, 480)

        self.view_azimuth = 0.0
        self.view_elevation = 0.0
        self.view_distance = 5.0
        self.view_centre = np.array([0.0, 0.0, 0.0])
        self.view_fov = 60

        self.background_color = (0, 0, 0, 0)

        self.min_distance = 0.1
        self.max_distance = 250

        # Mouse control settings
        self.mouse_sensitivity_azimuth = 0.2
        self.mouse_sensitivity_elevation = 0.5
        self.mouse_sensitivity_distance = 1.0
        self.mouse_sensitivity_position = 0.01
        self.scroll_sensitivity = 0.0005

        # Mouse control variables
        self.mouse_position = None
        self.view_centre_difference = np.array([0.0, 0.0, 0.0])
        self.view_azimuth_difference = 0.0
        self.view_elevation_difference = 0.0

        self._items: List[Renderable] = []

        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)

        # Save the on_key callback
        self.on_key = on_key


    def initializeGL(self):
        glClearDepth(1.0)
        glDepthFunc(GL_LESS)
        glEnable(GL_DEPTH_TEST)
        glShadeModel(GL_SMOOTH)

    def default_viewport(self):
        x = int(self.width() * self.devicePixelRatioF())
        y = int(self.height() * self.devicePixelRatioF())
        # return -x//2, -y//2, x//2, y//2
        # return -y//2, -x//2, x, y
        return 0, 0, x, y


    def paintGL(self):
        """
        Paint the GL viewport
        """

        glViewport(*self.default_viewport())
        self.set_projection()

        glClearColor(*self.background_color)
        glClear( GL_DEPTH_BUFFER_BIT | GL_COLOR_BUFFER_BIT )

        self.set_model_view()

        # self.test_paint()
        glEnable(GL_POLYGON_OFFSET_FILL)

        for item in self._items:
            glPolygonOffset(0.0, 20.0)
            item.render_solid()
            glPolygonOffset(0.0, 0.0)
            item.render_wireframe()

        glPolygonOffset(0.0, 0.0)


    def projection_matrix(self):
        x0, y0, w, h = self.default_viewport()
        dist = self.view_distance
        nearClip = dist * 0.001
        farClip = dist * 1000.

        r = nearClip * np.tan(0.5 * np.radians(self.view_fov))
        t = r * h / w

        tr = QtGui.QMatrix4x4()
        tr.frustum(-r, r, -t, t, nearClip, farClip)
        return tr

    def set_projection(self):

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        # gluPerspective(45.0,1.33,0.1, 100.0)
        glLoadMatrixf(np.array(self.projection_matrix().data(), dtype=np.float32))

    def set_model_view(self):


        tr = QtGui.QMatrix4x4()
        # tr.translate(0.0, 0.0, -self.view_distance)
        tr.translate(0.0,0.0,-self.view_distance)


        azimuth = np.radians(self.view_azimuth + self.view_azimuth_difference)
        elevation = np.radians(np.clip(self.view_elevation + self.view_elevation_difference, -90, 90))
        centre = self.view_centre + self.view_centre_difference

        x = centre[0] + self.view_distance*np.cos(azimuth)*np.cos(elevation)
        y = centre[1] - self.view_distance*np.sin(azimuth)*np.cos(elevation)
        z = centre[2] + self.view_distance*np.sin(elevation)

        gluLookAt(
            x, y, z,
            centre[0], centre[1], centre[2],
            0.0, 0.0, 1.0)

    def mousePressEvent(self, ev):
        self.mouse_position = ev.localPos()

    def mouseMoveEvent(self, ev):
        new_mouse_position = ev.localPos()
        diff = new_mouse_position - self.mouse_position

        if ev.buttons() == QtCore.Qt.MouseButton.LeftButton:
            self.view_azimuth_difference = self.mouse_sensitivity_azimuth * diff.x()
            self.view_elevation_difference = self.mouse_sensitivity_elevation * diff.y()

        elif ev.buttons() == QtCore.Qt.MouseButton.RightButton:
            self.view_centre_difference = np.array([self.mouse_sensitivity_position * diff.x(), 0,
                                           self.mouse_sensitivity_position * diff.y()])

        self.update()
    def mouseReleaseEvent(self, ev):
        # Mouse released, add dragging offset the view variables

        self.view_centre += np.array(self.view_centre_difference)
        self.view_elevation += self.view_elevation_difference
        self.view_azimuth += self.view_azimuth_difference

        self.view_centre_difference = np.array([0.0,0.0,0.0])
        self.view_azimuth_difference = 0.0
        self.view_elevation_difference = 0.0

        self.update()

    def wheelEvent(self, event: QtGui.QWheelEvent):
        scroll_amount = event.angleDelta().y()

        self.view_distance *= np.exp(scroll_amount * self.scroll_sensitivity)

        if self.view_distance < self.min_distance:
            self.view_distance = self.min_distance

        if self.view_distance > self.max_distance:
            self.view_distance = self.max_distance

        event.accept()

        self.update()

    def add(self, item: Renderable):
        self._items.append(item)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        self.on_key(event.key())

def main():
    """ Show a demo of the opengl window """
    import os

    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    app = QtWidgets.QApplication([])

    mainWindow = QtWidgets.QMainWindow()
    viewer = GraphWidget(mainWindow)

    x = np.linspace(-1, 1, 101)
    y = np.linspace(-1, 1, 101)
    x_grid, y_grid = np.meshgrid(x, y)

    r_sq = x_grid**2 + y_grid**2
    z = np.cos(np.sqrt(r_sq))/(r_sq+1)

    viewer.add(Surface(x, y, z, edge_skip=4))

    mainWindow.setCentralWidget(viewer)

    mainWindow.show()

    mainWindow.resize(600, 600)
    app.exec_()


if __name__ == "__main__":
    main()