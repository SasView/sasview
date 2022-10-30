import numpy as np
from sas.qtgui.GL.transformations.SceneGraphNode import SceneGraphNode
from sas.qtgui.GL.Renderable import Renderable

from OpenGL.GL import *
from OpenGL.GLU import *

class Scale(SceneGraphNode):
    """
    General transform - also doubles as a scene graph node

    For the sake of speed, the transformation matrix shape is not checked.
    It should be a 3 element vector
    """

    def __init__(self, scale: np.ndarray, *children: Renderable):
        super().__init__(*children)
        self.scale = scale

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


