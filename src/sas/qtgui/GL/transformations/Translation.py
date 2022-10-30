import numpy as np
from sas.qtgui.GL.Renderable import Renderable
from sas.qtgui.GL.transformations.SceneGraphNode import SceneGraphNode

from OpenGL.GL import *
from OpenGL.GLU import *

class Translation(SceneGraphNode):
    """
    General transform - also doubles as a scene graph node

    For the sake of speed, the rotation matrix shape is not checked.
    It should be a 3 element vector
    """

    def __init__(self, rotation: np.ndarray, *children: Renderable):
        super().__init__(*children)
        self.rotation = rotation

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


