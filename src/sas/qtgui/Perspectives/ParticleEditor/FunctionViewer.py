import numpy as np

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontMetrics

def rotation_matrix(theta: float, phi: float):

    st = np.sin(theta)
    ct = np.cos(theta)
    sp = np.sin(phi)
    cp = np.cos(phi)

    r = np.array([
        [st*cp, ct*cp, -sp],
        [st*sp, ct*sp,  cp],
        [ct,   -st,    0]]).T

    return r
def cross_section_coordinates(radius: float, theta: float, phi: float, plane_distance: float, n_points: int):

    xy_values = np.linspace(-radius, radius, n_points)

    x, y = np.meshgrid(xy_values, xy_values)
    x = x.reshape((-1, ))
    y = y.reshape((-1, ))

    z = np.zeros_like(x) - plane_distance

    xyz = np.vstack((x, z, y))

    r = rotation_matrix(theta, phi)

    return np.dot(r, xyz).T


class FunctionViewer(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.n_draw_layers = 99
        self.layer_size = 100
        self.radius = 1
        self.upscale = 2
        self._size_px = self.layer_size*self.upscale
        self.function = lambda x,y,z: np.ones_like(x)
        self.coordinate_mapping = lambda x,y,z: (x,y,z)

        self.theta = 0.0
        self.phi = 0.0
        self.normal_offset = 0.0

        self._graphics_viewer_offset = 5

        self.densityViewer = QtWidgets.QGraphicsView()

        self.densityScene = QtWidgets.QGraphicsScene()
        self.densityViewer.setScene(self.densityScene)

        pixmap = QtGui.QPixmap(self._size_px, self._size_px)
        self.densityPixmapItem = self.densityScene.addPixmap(pixmap)
        self.densityViewer.setFixedWidth(self._size_px + self._graphics_viewer_offset)
        self.densityViewer.setFixedHeight(self._size_px + self._graphics_viewer_offset)

        self.sliceViewer = QtWidgets.QGraphicsView()

        self.sliceScene = QtWidgets.QGraphicsScene()
        self.sliceViewer.setScene(self.sliceScene)

        pixmap = QtGui.QPixmap(self._size_px, self._size_px)
        self.slicePixmapItem = self.sliceScene.addPixmap(pixmap)
        self.sliceViewer.setFixedWidth(self._size_px + self._graphics_viewer_offset)
        self.sliceViewer.setFixedHeight(self._size_px + self._graphics_viewer_offset)

        self.theta_slider = QtWidgets.QSlider(Qt.Horizontal)
        self.theta_slider.setRange(0, 180)
        self.theta_slider.setTickInterval(15)
        self.theta_slider.valueChanged.connect(self.onThetaChanged)

        self.phi_slider = QtWidgets.QSlider(Qt.Horizontal)
        self.phi_slider.setRange(-180, 180)
        self.phi_slider.setTickInterval(15)
        self.phi_slider.valueChanged.connect(self.onPhiChanged)

        self.depth_slider = QtWidgets.QSlider(Qt.Horizontal)
        self.depth_slider.setRange(-100, 100)
        self.depth_slider.setTickInterval(10)
        self.depth_slider.valueChanged.connect(self.onDepthChanged)

        projection_label = QtWidgets.QLabel("Projection")
        projection_label.setAlignment(Qt.AlignCenter)

        slice_label = QtWidgets.QLabel("Slice")
        slice_label.setAlignment(Qt.AlignCenter)

        spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(projection_label)
        layout.addWidget(self.densityViewer)
        layout.addWidget(self.theta_slider)
        layout.addWidget(self.phi_slider)
        layout.addWidget(slice_label)
        layout.addWidget(self.sliceViewer)
        layout.addWidget(self.depth_slider)
        layout.addItem(spacer)

        self.setLayout(layout)

        self.setFixedWidth(self._size_px + 20) # Perhaps a better way of keeping the viewer width small?


    def setRadius(self):
        pass

    def setSizePx(self, size):
        pass

    def setFunction(self, fun):

        self.function = fun

        self.updateImage()

    def setCoordinateMapping(self, fun):
        self.coordinate_mapping = fun

    def onThetaChanged(self):
        self.theta = np.pi*float(self.theta_slider.value())/180
        self.updateImage()
    def onPhiChanged(self):
        self.phi = np.pi * float(self.phi_slider.value()) / 180
        self.updateImage()
    def onDepthChanged(self):
        self.normal_offset = self.radius * float(self.depth_slider.value()) / 100
        self.updateImage()

    def updateImage(self):

        # Draw image

        bg_values = None
        for depth in np.linspace(-self.radius, self.radius, self.n_draw_layers+2)[1:-1]:
            sampling = cross_section_coordinates(self.radius, self.theta, self.phi, depth, self.layer_size)
            a, b, c = self.coordinate_mapping(sampling[:, 0], sampling[:, 1], sampling[:, 2])

            values = self.function(a, b, c)  # TODO: Need to handle parameters properly

            if bg_values is None:
                bg_values = values
            else:
                bg_values += values

        min_value = np.min(bg_values)
        max_value = np.max(bg_values)

        if min_value == max_value:
            bg_values = np.ones_like(bg_values) * 0.5
        else:
            diff = max_value - min_value
            bg_values -= min_value
            bg_values *= (1/diff)

        bg_values = bg_values.reshape((self.layer_size, self.layer_size, 1))
        bg_image_values = np.array(bg_values * 255, dtype=np.uint8)

        bg_image_values = bg_image_values.repeat(self.upscale, axis=0).repeat(self.upscale, axis=1)

        image = np.concatenate((bg_image_values, bg_image_values, bg_image_values), axis=2)

        height, width, channels = image.shape
        bytes_per_line = channels * width
        qimage = QtGui.QImage(image.data, width, height, bytes_per_line, QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap(qimage)
        self.densityPixmapItem.setPixmap(pixmap)


        # Cross section

        sampling = cross_section_coordinates(self.radius, self.theta, self.phi, self.normal_offset, self._size_px)
        a,b,c = self.coordinate_mapping(sampling[:, 0], sampling[:, 1], sampling[:, 2])

        values = self.function(a,b,c) # TODO: Need to handle parameters properly

        values = values.reshape((self._size_px, self._size_px, 1))

        min_value = np.min(values)
        max_value = np.max(values)

        if min_value == max_value:
            values = np.zeros_like(values)
        else:
            diff = max_value - min_value
            values -= min_value
            values *= (1/diff)

        image_values = np.array(values*255, dtype=np.uint8)

        image = np.concatenate((image_values, image_values, image_values), axis=2)

        self.drawScale(image)
        self.drawAxes(image)


        height, width, channels = image.shape
        bytes_per_line = channels * width
        qimage = QtGui.QImage(image.data, width, height, bytes_per_line, QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap(qimage)
        self.slicePixmapItem.setPixmap(pixmap)



    def drawScale(self, im):
        pass

    def drawAxes(self, im):
        # in top 100 pixels
        pass

def main():
    """ Show a demo of the function viewer"""

    from sas.qtgui.Perspectives.ParticleEditor.function_processor import spherical_converter
    def micelle(r, theta, phi):
        out = np.zeros_like(r)
        out[r<1] = 4
        out[r<0.8] = 1
        return out

    def cube_function(x, y, z):

        inside = np.logical_and(np.abs(x) <= 0.5,
                       np.logical_and(
                           np.abs(y) <= 0.5,
                           np.abs(z) <= 0.5 ))
        #
        # print(cube_function)
        # print(np.any(inside), np.any(np.logical_not(inside)))

        out = np.zeros_like(x)
        out[inside] = 1.0

        return out

    def pseudo_orbital(r, theta, phi):
        return np.exp(-6*r)*r*np.abs(np.cos(2*theta))

    app = QtWidgets.QApplication([])
    viewer = FunctionViewer()
    viewer.setCoordinateMapping(spherical_converter)
    viewer.setFunction(pseudo_orbital)

    viewer.show()
    app.exec_()


if __name__ == "__main__":
    main()
