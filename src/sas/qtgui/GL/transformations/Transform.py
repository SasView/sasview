import numpy as np

from OpenGL.GL import *
from OpenGL.GLU import *

from sas.qtgui.GL.Renderable import Renderable
from sas.qtgui.GL.transformations.SceneGraphNode import SceneGraphNode


class Transform(SceneGraphNode):
    """
    General transform - also doubles as a scene graph node

    For the sake of speed, the transformation matrix shape is not checked.
    It should be a 4x4 transformation matrix
    """

    def __init__(self, matrix: np.ndarray, *children: Renderable):
        super().__init__(*children)
        self.matrix = matrix

    def render_solid(self):
        # Apply transform

        for child in self.children:
            child.render_solid()

        # unapply transform

    def render_wireframe(self):
        # Apply transform

        for child in self.children:
            child.render_wireframe()

        # unapply transform


