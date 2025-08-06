import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt

from sas.qtgui.Perspectives.ParticleEditor.defaults import sld as default_sld
from sas.qtgui.Perspectives.ParticleEditor.function_processor import spherical_converter
from sas.qtgui.Perspectives.ParticleEditor.LabelledSlider import LabelledSlider
from sas.qtgui.Perspectives.ParticleEditor.RadiusSelection import RadiusSelection
from sas.qtgui.Perspectives.ParticleEditor.SLDMagnetismOption import SLDMagnetismOption
from sas.qtgui.Perspectives.ParticleEditor.ViewerButtons import AxisButtons, PlaneButtons


def rotation_matrix(alpha: float, beta: float):

    sa = np.sin(alpha)
    ca = np.cos(alpha)
    sb = np.sin(beta)
    cb = np.cos(beta)

    xz = np.array([
            [ ca, 0, -sa],
            [  0, 1,   0],
            [ sa, 0,  ca]])

    yz = np.array([
            [1,  0,   0 ],
            [0,  cb, -sb],
            [0,  sb,  cb]])

    return np.dot(xz, yz)
def cross_section_coordinates(radius: float, alpha: float, beta: float, plane_distance: float, n_points: int):

    xy_values = np.linspace(-radius, radius, n_points)

    x, y = np.meshgrid(xy_values, xy_values)
    x = x.reshape((-1, ))
    y = y.reshape((-1, ))

    z = np.zeros_like(x) + plane_distance

    xyz = np.vstack((x, y, z))

    r = rotation_matrix(alpha, beta)

    return np.dot(r, xyz).T

def draw_line_in_place(im, x0, y0, dx, dy, channel):
    """ Simple line drawing (otherwise need to import something heavyweight)"""

    length = np.sqrt(dx * dx + dy * dy)
    # print(x, y, dx, dy, length)

    if length == 0:
        return

    for i in range(int(length)):
        x = int(x0 + i * dx / length)
        y = int(y0 + i * dy / length)
        im[y, x, channel] = 255


class FunctionViewer(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.n_draw_layers = 99
        self.layer_size = 100
        self.radius = 1
        self.upscale = 2
        self._size_px = self.layer_size*self.upscale
        self.function = default_sld
        # self.function = lambda x,y,z: x
        self.coordinate_mapping = spherical_converter

        self.alpha = 0.0
        self.beta = np.pi
        self.normal_offset = 0.0
        self.mag_theta = 0.0
        self.mag_phi = 0.0

        self._graphics_viewer_offset = 5


        #
        # Qt Setup
        #

        # Density

        self.densityViewer = QtWidgets.QGraphicsView()

        self.densityScene = QtWidgets.QGraphicsScene()
        self.densityViewer.setScene(self.densityScene)

        pixmap = QtGui.QPixmap(self._size_px, self._size_px)
        self.densityPixmapItem = self.densityScene.addPixmap(pixmap)

        self.densityViewer.setFixedWidth(self._size_px + self._graphics_viewer_offset)
        self.densityViewer.setFixedHeight(self._size_px + self._graphics_viewer_offset)
        self.densityViewer.setCursor(Qt.OpenHandCursor)

        # Slice

        self.sliceViewer = QtWidgets.QGraphicsView()

        self.sliceScene = QtWidgets.QGraphicsScene()
        self.sliceViewer.setScene(self.sliceScene)

        pixmap = QtGui.QPixmap(self._size_px, self._size_px)
        self.slicePixmapItem = self.sliceScene.addPixmap(pixmap)

        self.sliceViewer.setFixedWidth(self._size_px + self._graphics_viewer_offset)
        self.sliceViewer.setFixedHeight(self._size_px + self._graphics_viewer_offset)
        self.sliceViewer.setCursor(Qt.OpenHandCursor)

        # General control

        self.radius_control = RadiusSelection("View Radius")
        self.radius_control.radiusField.valueChanged.connect(self.onRadiusChanged)

        self.plane_buttons = PlaneButtons(self.setAngles)

        self.depth_slider = LabelledSlider("Depth", -100, 100, 0, name_width=35, value_width=35, value_units="%")
        self.depth_slider.valueChanged.connect(self.onDepthChanged)

        # Magnetism controls

        self.sld_magnetism_option = SLDMagnetismOption()
        self.sld_magnetism_option.sldOption.clicked.connect(self.onDisplayTypeSelected)
        self.sld_magnetism_option.magnetismOption.clicked.connect(self.onDisplayTypeSelected)

        self.mag_theta_slider = LabelledSlider("θ", -180, 180, 0)
        self.mag_theta_slider.valueChanged.connect(self.onMagThetaChanged)

        self.mag_phi_slider = LabelledSlider("φ", 0, 180, 0)
        self.mag_phi_slider.valueChanged.connect(self.onMagPhiChanged)

        self.mag_buttons = AxisButtons(lambda x,y: None)

        magLayout = QtWidgets.QVBoxLayout()

        magGroup = QtWidgets.QGroupBox("B Field (display)")
        magGroup.setLayout(magLayout)

        magLayout.addWidget(self.mag_theta_slider)
        magLayout.addWidget(self.mag_phi_slider)
        magLayout.addWidget(self.mag_buttons)

        # Main layout

        spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        layout = QtWidgets.QVBoxLayout()

        layout.addWidget(self.densityViewer)
        layout.addWidget(self.plane_buttons)
        layout.addWidget(self.radius_control)
        layout.addWidget(self.sliceViewer)
        layout.addWidget(self.depth_slider)
        layout.addItem(spacer)
        layout.addWidget(self.sld_magnetism_option)
        layout.addWidget(magGroup)

        self.setLayout(layout)

        self.setFixedWidth(self._size_px + 20) # Perhaps a better way of keeping the viewer width small?

        # Mouse response
        self.densityViewer.viewport().installEventFilter(self)
        self.sliceViewer.viewport().installEventFilter(self)

        self.lastMouseX = 0
        self.lastMouseY = 0
        self.dThetadX = 0.01
        self.dPhidY = -0.01

        self.radius = self.radius_control.radius()

        # Show images
        self.updateImage()
    def eventFilter(self, source, event):
        """ Event filter intercept, grabs mouse drags on the images"""

        if event.type() == QtCore.QEvent.MouseButtonPress:

            if (source is self.densityViewer.viewport()) or \
                (source is self.sliceViewer.viewport()):

                x, y = event.pos().x(), event.pos().y()
                self.lastMouseX = x
                self.lastMouseY = y

                return

        elif event.type() == QtCore.QEvent.MouseMove:
            if (source is self.densityViewer.viewport()) or \
                (source is self.sliceViewer.viewport()):

                x, y = event.pos().x(), event.pos().y()
                dx = x - self.lastMouseX
                dy = y - self.lastMouseY

                self.alpha += self.dThetadX * dx
                self.beta += self.dPhidY * dy

                self.alpha %= 2 * np.pi
                self.beta %= 2 * np.pi

                self.lastMouseX = x
                self.lastMouseY = y

                self.updateImage()

                return

        super().eventFilter(source, event)


    def onRadiusChanged(self):
        """ Draw radius changed """
        self.radius = self.radius_control.radius()
        self.updateImage()

    def setSLDFunction(self, fun, coordinate_mapping):
        """ Set the function to be plotted """
        self.function = fun
        self.coordinate_mapping = coordinate_mapping

        self.updateImage()

    def onDisplayTypeSelected(self):
        """ Switch between SLD and magnetism view """

        if self.sld_magnetism_option.magnetismOption.isChecked():
            print("Magnetic view selected")
        if self.sld_magnetism_option.sldOption.isChecked():
            print("SLD view selected")

    # def onThetaChanged(self):
    #     self.theta = np.pi*float(self.theta_slider.value())/180
    #     self.updateImage()
    # def onPhiChanged(self):
    #     self.phi = np.pi * float(self.phi_slider.value()) / 180
    #     self.updateImage()

    def onMagThetaChanged(self):
        """ Magnetic field theta angle changed """

        self.mag_theta = np.pi*float(self.mag_theta_slider.value())/180
        self.updateImage(mag_only=True)
    def onMagPhiChanged(self):
        """ Magnetic field phi angle changed """
        self.mag_phi = np.pi * float(self.mag_phi_slider.value()) / 180
        self.updateImage(mag_only=True)

    def onDepthChanged(self):
        """ Callback for cross section depth slider """
        self.normal_offset = self.radius * float(self.depth_slider.value()) / 100
        self.updateImage()

    def setAngles(self, alpha_deg, beta_deg):
        """ Set the viewer angles """
        self.alpha = np.pi * alpha_deg / 180
        self.beta = np.pi * (beta_deg + 180) / 180

        self.updateImage()

    def updateImage(self, mag_only=True):

        """ Update the images in the viewer"""

        # Draw density plot

        bg_values = None
        for depth in np.linspace(-self.radius, self.radius, self.n_draw_layers+2)[1:-1]:
            sampling = cross_section_coordinates(self.radius, self.alpha, self.beta, depth, self.layer_size)
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

        self.drawScale(image)
        self.drawAxes(image)

        height, width, channels = image.shape
        bytes_per_line = channels * width
        qimage = QtGui.QImage(image.data, width, height, bytes_per_line, QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap(qimage)
        self.densityPixmapItem.setPixmap(pixmap)


        # Cross section image

        sampling = cross_section_coordinates(self.radius, self.alpha, self.beta, self.normal_offset, self._size_px)
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
        """ Draw a scalebar """
        pass

    def drawAxes(self, im):
        """ Draw a small xyz axis on an image"""
        vectors = 20*rotation_matrix(self.alpha, self.beta)

        y = self._size_px - 30
        x = 30

        # xy coordinates
        for i in range(1):
            for j in range(1):

                draw_line_in_place(im, x+i, y+j, vectors[0, 0], vectors[0, 1], 0)
                draw_line_in_place(im, x+i, y+j, vectors[1, 0], vectors[1, 1], 1)
                draw_line_in_place(im, x+i, y+j, vectors[2, 0], vectors[2, 1], 2)
                draw_line_in_place(im, x+i, y+j, vectors[2, 0], vectors[2, 1], 1) # Blue is hard to see, make it cyan

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
    viewer.setSLDFunction(pseudo_orbital, spherical_converter)

    viewer.show()
    app.exec_()


if __name__ == "__main__":
    main()
