""" As close a thing as there are to tests for GL"""

from typing import Optional, Tuple, List, Callable
import numpy as np

from PyQt5 import QtWidgets, Qt, QtGui, QtOpenGL, QtCore

from sas.qtgui.GL.scene import GraphWidget
from sas.qtgui.GL.models import ModelBase
from sas.qtgui.GL.color import Color
from sas.qtgui.GL.surface import Surface
from sas.qtgui.GL.cone import Cone
from sas.qtgui.GL.cube import Cube
from sas.qtgui.GL.cylinder import Cylinder
from sas.qtgui.GL.icosahedron import Icosahedron
from sas.qtgui.GL.sphere import Sphere
from sas.qtgui.GL.transforms import SceneGraphNode, Translation, Rotation, Scale

def transform_tests():
    """ Shows all the existing primitives that can be rendered, press a key to go through them

    1) 4 shapes in a vertical 2 unit x 2 unit grid - as cylinder and cone have r=1, they should touch
    2) 27 cubes in 3x3x3 grid, with scaling changing (1/2, 1, 2) in the same dimension as the translation
    3)
    
    """

    import os

    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    app = QtWidgets.QApplication([])

    cube = Cube(edge_colors=Color(1, 1, 1), face_colors=Color(0.7, 0.2, 0))
    cone = Cone(edge_colors=Color(1, 1, 1), vertex_colors=Color(0, 0.7, 0.2))
    cylinder = Cylinder(edge_colors=Color(1, 1, 1), vertex_colors=Color(0, 0.2, 0.7))
    icos = Icosahedron(edge_colors=Color(1, 1, 1), vertex_colors=Color(0.7, 0, 0.7))


    # Translations
    translate_test = \
        SceneGraphNode(
            Translation(0,0,1,
                        Translation(0,-1,0,cube),
                        Translation(0,1,0,cone)),
            Translation(0,0,-1,
                        Translation(0,-1,0,cylinder),
                        Translation(0,1,0,icos)))

    # Scaling
    scaling_components = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                components = Translation(-2*(i-1), -2*(j-1), -2*(k-1), Scale(2**(i-1), 2**(j-1), 2**(k-1), cube))
                scaling_components.append(components)

    scaling_test = Scale(0.5, 0.5, 0.5, *scaling_components)


    item_list = [
        translate_test,
        scaling_test
    ]

    # Turn off all of them
    for item in item_list:
        item.solid_render_enabled = False
        item.wireframe_render_enabled = False


    # Thing for going through each of the draw types of the primatives

    def item_states(item: ModelBase):

        item.solid_render_enabled = True
        item.wireframe_render_enabled = True

        yield None

        item.solid_render_enabled = False
        item.wireframe_render_enabled = False

    def scan_states():
        while True:
            for item in item_list:
                for _ in item_states(item):
                    yield None

    state = scan_states()
    next(state)


    mainWindow = QtWidgets.QMainWindow()
    viewer = GraphWidget(parent=mainWindow)

    # Keyboard callback
    def enable_disable(key):
        next(state)
        viewer.update()

    viewer.on_key = enable_disable

    for item in item_list:
        viewer.add(item)

    mainWindow.setCentralWidget(viewer)

    mainWindow.show()

    mainWindow.resize(600, 600)
    app.exec_()


if __name__ == "__main__":
    transform_tests()