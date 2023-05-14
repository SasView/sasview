import numpy as np

from PySide6 import QtGui, QtWidgets, QtCore
from PySide6.QtCore import Qt


from sas.qtgui.Perspectives.ParticleEditor.LabelledSlider import LabelledSlider
from sas.qtgui.Perspectives.ParticleEditor.SLDMagnetismOption import SLDMagnetismOption
from sas.qtgui.Perspectives.ParticleEditor.ViewerButtons import AxisButtons, PlaneButtons

def rotation_matrix(theta: float, phi: float):

    st = np.sin(theta)
    ct = np.cos(theta)
    sp = np.sin(phi)
    cp = np.cos(phi)

    xz = np.array([
            [ ct, 0, -st],
            [  0, 1,   0],
            [ st, 0,  ct]])

    yz = np.array([
            [1,  0,   0 ],
            [0,  cp, -sp],
            [0,  sp,  cp]])

    return np.dot(xz, yz)
def cross_section_coordinates(radius: float, theta: float, phi: float, plane_distance: float, n_points: int):

    xy_values = np.linspace(-radius, radius, n_points)

    x, y = np.meshgrid(xy_values, xy_values)
    x = x.reshape((-1, ))
    y = y.reshape((-1, ))

    z = np.zeros_like(x) + plane_distance

    xyz = np.vstack((x, y, z))

    r = rotation_matrix(theta, phi)

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


class FunctionViewer(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.n_draw_layers = 99
        self.layer_size = 100
        self.radius = 1
        self.upscale = 2
        self._size_px = self.layer_size*self.upscale
        self.function = cube_function
        # self.function = lambda x,y,z: x
        self.coordinate_mapping = lambda x,y,z: (x,y,z)

        self.theta = 0.0
        self.phi = np.pi
        self.normal_offset = 0.0
        self.mag_theta = 0.0
        self.mag_phi = 0.0

        self._graphics_viewer_offset = 5

        #
        # Qt Setup
        #

        density_label = QtWidgets.QLabel("Projection")
        density_label.setAlignment(Qt.AlignCenter)

        self.densityViewer = QtWidgets.QGraphicsView()

        self.densityScene = QtWidgets.QGraphicsScene()
        self.densityViewer.setScene(self.densityScene)

        pixmap = QtGui.QPixmap(self._size_px, self._size_px)
        self.densityPixmapItem = self.densityScene.addPixmap(pixmap)

        self.densityViewer.setFixedWidth(self._size_px + self._graphics_viewer_offset)
        self.densityViewer.setFixedHeight(self._size_px + self._graphics_viewer_offset)
        self.densityViewer.setCursor(Qt.OpenHandCursor)

        slice_label = QtWidgets.QLabel("Slice")
        slice_label.setAlignment(Qt.AlignCenter)

        self.sliceViewer = QtWidgets.QGraphicsView()

        self.sliceScene = QtWidgets.QGraphicsScene()
        self.sliceViewer.setScene(self.sliceScene)

        pixmap = QtGui.QPixmap(self._size_px, self._size_px)
        self.slicePixmapItem = self.sliceScene.addPixmap(pixmap)

        self.sliceViewer.setFixedWidth(self._size_px + self._graphics_viewer_offset)
        self.sliceViewer.setFixedHeight(self._size_px + self._graphics_viewer_offset)
        self.sliceViewer.setCursor(Qt.OpenHandCursor)
        #
        # self.theta_slider = LabelledSlider("θ", -180, 180, 0)
        # self.theta_slider.valueChanged.connect(self.onThetaChanged)
        #
        # self.phi_slider = LabelledSlider("φ", 0, 180, 0)
        # self.phi_slider.valueChanged.connect(self.onPhiChanged)
        #
        # self.psi_slider = LabelledSlider("ψ", 0, 180, 0)
        # self.psi_slider.valueChanged.connect(self.onPsiChanged)

        self.plane_buttons = PlaneButtons(self.setAngles)

        self.depth_slider = LabelledSlider("Depth", -100, 100, 0, name_width=35, value_width=35, value_units="%")
        self.depth_slider.valueChanged.connect(self.onDepthChanged)

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


        spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)


        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(density_label)
        layout.addWidget(self.densityViewer)
        # layout.addWidget(self.theta_slider)
        # layout.addWidget(self.phi_slider)
        # layout.addWidget(self.psi_slider)
        layout.addWidget(slice_label)
        layout.addWidget(self.sliceViewer)
        layout.addWidget(self.plane_buttons)
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
        self.dPhidY = 0.01

        # Show images
        self.updateImage()
    def eventFilter(self, source, event):


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

                self.theta += self.dThetadX * dx
                self.phi += self.dPhidY * dy

                self.theta %= 2*np.pi
                self.phi %= 2*np.pi

                self.lastMouseX = x
                self.lastMouseY = y

                self.updateImage()

                return

        super().eventFilter(source, event)


    def setRadius(self):
        pass

    def setSizePx(self, size):
        pass

    def setFunction(self, fun):

        self.function = fun

        self.updateImage()

    def setCoordinateMapping(self, fun):
        self.coordinate_mapping = fun

    def onDisplayTypeSelected(self):
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
        self.mag_theta = np.pi*float(self.mag_theta_slider.value())/180
        self.updateImage(mag_only=True)
    def onMagPhiChanged(self):
        self.mag_phi = np.pi * float(self.mag_phi_slider.value()) / 180
        self.updateImage(mag_only=True)

    def onPsiChanged(self):
        self.psi = np.pi * float(self.psi_slider.value()) / 180
        self.updateImage()
    def onDepthChanged(self):
        self.normal_offset = self.radius * float(self.depth_slider.value()) / 100
        self.updateImage()

    def setAngles(self, theta_deg, phi_deg):
        
        self.theta = np.pi * theta_deg / 180
        self.phi = np.pi * (phi_deg + 180) / 180

        self.updateImage()

    def updateImage(self, mag_only=True):

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

        self.drawScale(image)
        self.drawAxes(image)

        # image = np.ascontiguousarray(np.flip(image, 0)) # Y is upside down

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

        # image = np.ascontiguousarray(np.flip(image, 0)) # Y is upside down

        height, width, channels = image.shape
        bytes_per_line = channels * width
        qimage = QtGui.QImage(image.data, width, height, bytes_per_line, QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap(qimage)
        self.slicePixmapItem.setPixmap(pixmap)



    def drawScale(self, im):
        pass

    def drawAxes(self, im):
        vectors = 20*rotation_matrix(self.theta, self.phi)

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
    viewer.setCoordinateMapping(spherical_converter)
    viewer.setFunction(pseudo_orbital)

    viewer.show()
    app.exec_()


if __name__ == "__main__":
    main()
