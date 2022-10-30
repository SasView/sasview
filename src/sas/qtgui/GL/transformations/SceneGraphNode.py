from typing import List

import numpy as np

from OpenGL.GL import *
from OpenGL.GLU import *

from sas.qtgui.GL.Renderable import Renderable

class SceneGraphNode(Renderable):
    """
    General transform - also doubles as a scene graph node

    For the sake of speed, the transformation matrix shape is not checked.
    It should be a 4x4 transformation matrix
    """

    def __init__(self, matrix: np.ndarray, *children: Renderable):
        super().__init__()
        self.matrix = matrix
        self.children: List[Renderable] = list(children)

    def add_child(self, child: Renderable):
        self.children.append(child)


