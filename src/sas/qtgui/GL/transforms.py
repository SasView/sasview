from typing import List

import numpy as np

from OpenGL.GL import *
from OpenGL.GLU import *

from sas.qtgui.GL.renderable import Renderable




class SceneGraphNode(Renderable):
    """
    General transform - also doubles as a scene graph node

    For the sake of speed, the transformation matrix shape is not checked.
    It should be a 4x4 transformation matrix
    """

    def __init__(self, *children: Renderable):
        super().__init__()
        self.children: List[Renderable] = list(children)
        self.solid_render_enabled = True
        self.wireframe_render_enabled = True


    def add_child(self, child: Renderable):
        """ Add a renderable object to this scene graph node"""
        self.children.append(child)

    def apply(self):
        pass

    def render_solid(self):
        if self.solid_render_enabled:

            # Apply transform
            glPushMatrix()
            self.apply()

            # Render children
            for child in self.children:
                child.render_solid()

            # Unapply
            glPopMatrix()


    def render_wireframe(self):

        if self.wireframe_render_enabled:
            # Apply transform
            glPushMatrix()
            self.apply()

            # Render children
            for child in self.children:
                child.render_wireframe()

            # unapply transform
            glPopMatrix()


class Rotation(SceneGraphNode):


    def __init__(self, angle, axis, *children: Renderable):
        """
        Rotate the children of this node

        :param angle: angle of rotation in TODO
        :param axis: axis for rotation
        """
        super().__init__(*children)
        self.angle = angle
        self.axis = axis

    def apply(self):
        pass



class Translation(SceneGraphNode):


    def __init__(self, x: float, y: float, z: float, *children: Renderable):
        """
        Translate the children of this node

        :param x: x translation
        :param y: y translation
        :param z: z translation
        """
        super().__init__(*children)
        self.x = x
        self.y = y
        self.z = z

    def apply(self):
        glTranslate(self.x, self.y, self.z)


class Scale(SceneGraphNode):

    def __init__(self, x: float, y: float, z: float, *children: Renderable):
        """
        Scale the children of this node

        :param x: x scale
        :param y: y scale
        :param z: z scale
        """

        super().__init__(*children)
        self.x = x
        self.y = y
        self.z = z

    def apply(self):
        glScale(self.x, self.y, self.z)

