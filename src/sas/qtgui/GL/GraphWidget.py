from typing import Optional, Tuple
import numpy as np

from PyQt5 import QtWidgets, Qt, QtGui, QtOpenGL, QtCore

from OpenGL.GL import *
from OpenGL.GLU import *
class GraphWidget(QtOpenGL.QGLWidget):


    def __init__(self, parent):
        super().__init__(parent)
        self.setMinimumSize(640, 480)

        self.view_azimuth = 0.0
        self.view_elevation = 0.0
        self.view_distance = 5.0
        self.view_centre = (0.0, 0.0, 0.0)
        self.view_fov = 60

        self.background_color = (0, 0, 0, 0)

        # Mouse control settings
        self.mouse_sensitivity_azimuth = 0.01
        self.mouse_sensitivity_elevation = 0.01
        self.mouse_sensitivity_distance = 1.0
        self.mouse_sensitivity_position = 1.0

        # Mouse control variables
        self.mouse_position = None
        self.view_centre_difference = None
        self.view_azimuth_difference = None
        self.view_elevation_difference = None

    def test_paint(self):
        glTranslatef(-2.5, 0.5, -6.0)
        glColor3f( 1.0, 1.5, 0.0 )
        glPolygonMode(GL_FRONT, GL_FILL)
        glBegin(GL_TRIANGLES)
        glVertex3f(2.0,-1.2,0.0)
        glVertex3f(2.6,0.0,0.0)
        glVertex3f(2.9,-1.2,0.0)
        glEnd()
        glFlush()

    def initializeGL(self):
        glClearDepth(1.0)
        glDepthFunc(GL_LESS)
        glEnable(GL_DEPTH_TEST)
        glShadeModel(GL_SMOOTH)

    def default_viewport(self):
        return 0, 0, int(self.width() * self.devicePixelRatioF()), int(self.height() * self.devicePixelRatioF())

    def paintGL(self):
        """
        Paint the GL viewport
        """

        self.set_projection()
        self.set_model_view()

        glClearColor(*self.background_color)
        glClear( GL_DEPTH_BUFFER_BIT | GL_COLOR_BUFFER_BIT )

        self.test_paint()


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
        gluPerspective(45.0,1.33,0.1, 100.0)
        # glLoadMatrixf(np.array(self.projection_matrix().data(), dtype=np.float32))

    def view_matrix(self):
        tr = QtGui.QMatrix4x4()
        tr.translate(0.0, 0.0, -self.view_distance)

        azimuth = self.view_azimuth + 90
        elevation = self.view_elevation - 90

        if self.view_azimuth_difference is not None:
            azimuth += self.view_azimuth_difference

        if self.view_elevation_difference is not None:
            elevation += self.view_elevation_difference

        tr.rotate(elevation, 1, 0, 0)
        tr.rotate(azimuth, 0, 0, -1)
        tr.translate(*self.view_centre)
        return tr

    def set_model_view(self):
        glMatrixMode(GL_MODELVIEW)
        glLoadMatrixf(np.array(self.view_matrix().data(), dtype=np.float32))

    def mousePressEvent(self, ev):
        self.mouse_position = ev.localPos()

    def mouseMoveEvent(self, ev):
        new_mouse_position = ev.localPos()
        diff = new_mouse_position - self.mouse_position

        if ev.buttons() == QtCore.Qt.MouseButton.LeftButton:
            self.view_azimuth_difference = self.mouse_sensitivity_azimuth * diff.x()
            self.view_elevation_difference = self.mouse_sensitivity_elevation * diff.y()

        elif ev.buttons() == QtCore.Qt.MouseButton.RightButton:
            self.view_centre_difference = [self.mouse_sensitivity_position * diff.x(), 0,
                                           self.mouse_sensitivity_position * diff.y()]

        self.update()
    def mouseReleaseEvent(self, ev):
        # Mouse released, add dragging offset the view variables

        # self.view_centre += np.array(self.view_centre_difference)
        # self.view_elevation += self.view_elevation_difference
        # self.view_azimuth += self.view_azimuth_difference

        self.view_centre_difference = None
        self.view_azimuth_difference = None
        self.view_elevation_difference = None

        self.update()

def main():
    """ Show a demo of the opengl window """
    import os

    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    app = QtWidgets.QApplication([])

    mainWindow = QtWidgets.QMainWindow()
    viewer = GraphWidget(mainWindow)

    mainWindow.setCentralWidget(viewer)

    mainWindow.show()

    mainWindow.resize(600, 600)
    app.exec_()


if __name__ == "__main__":
    main()