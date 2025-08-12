import logging

import numpy as np
from OpenGL import GL

from sas.qtgui.GL.renderable import Renderable

logger = logging.getLogger("GL.transforms")

class SceneGraphNode(Renderable):
    """
    General transform - also doubles as a scene graph node

    For the sake of speed, the transformation matrix shape is not checked.
    It should be a 4x4 transformation matrix
    """

    def __init__(self, *children: Renderable):
        super().__init__()
        self.children: list[Renderable] = list(children)
        self.solid_render_enabled = True
        self.wireframe_render_enabled = True


    def add_child(self, child: Renderable):
        """ Add a renderable object to this scene graph node"""
        self.children.append(child)

    def apply(self):
        """ GL operations needed to apply any transformations associated with this node """

    def render_solid(self):
        if self.solid_render_enabled:

            # Apply transform
            GL.glPushMatrix()
            self.apply()

            # Check stack
            if GL.glGetIntegerv(GL.GL_MODELVIEW_STACK_DEPTH) >= 16:
                logger.info("GL Stack size utilisation {glGetIntegerv(GL_MODELVIEW_STACK_DEPTH))}, the limit could be as low as is 16")

            # Render children
            for child in self.children:
                child.render_solid()

            # Unapply
            GL.glPopMatrix()


    def render_wireframe(self):

        if self.wireframe_render_enabled:
            # Apply transform
            GL.glPushMatrix()
            self.apply()

            # Check stack
            if GL.glGetIntegerv(GL.GL_MODELVIEW_STACK_DEPTH) >= 16:
                logger.info("GL Stack size utilisation {glGetIntegerv(GL_MODELVIEW_STACK_DEPTH))}, the limit could be as low as is 16")


            # Render children
            for child in self.children:
                child.render_wireframe()

            # unapply transform
            GL.glPopMatrix()


class Rotation(SceneGraphNode):


    def __init__(self, angle, x, y, z, *children: Renderable):
        """
        Rotate the children of this node

        :param angle: angle of rotation in degrees
        :param axis: axis for rotation
        """
        super().__init__(*children)
        self.angle = angle
        self.x = x
        self.y = y
        self.z = z

    def apply(self):
        GL.glRotate(self.angle, self.x, self.y, self.z)


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
        GL.glTranslate(self.x, self.y, self.z)


class Scaling(SceneGraphNode):

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
        GL.glScale(self.x, self.y, self.z)

class MatrixTransform(SceneGraphNode):

    def __init__(self, matrix: np.ndarray, *children: Renderable):
        """

        Apply a 4x4 transformation matrix to the children of this node

        :param matrix: a 4x4 transformation matrix

        """

        super().__init__(*children)

        self.matrix = matrix

    def apply(self):
        GL.glMultMatrixd(self.matrix)
