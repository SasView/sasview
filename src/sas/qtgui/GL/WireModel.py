from typing import Union, Tuple, Sequence

from abc import abstractmethod

import numpy as np

from OpenGL.GL import *
from OpenGL.GLU import *

from sas.qtgui.GL.Renderable import Renderable
from sas.qtgui.GL.Color import Color


class WireModel(Renderable):

    @property
    def wireframe_render_enabled(self) -> bool:
        return True

    @abstractmethod
    @property
    def vertices(self) -> Sequence[Tuple[float, float, float]]:
        pass

    @abstractmethod
    @property
    def edges(self) -> Sequence[Tuple[int, int]]:
        pass

    @abstractmethod
    @property
    def edge_colors(self) -> Union[Sequence[Color], Color]:
        pass

    @abstractmethod
    @property
    def render_wireframe(self):
        if self.wireframe_render_enabled:
            vertices = self.vertices
            colors = self.edge_colors

            if isinstance(colors, Color):

                glBegin(GL_LINES)
                colors.set()

                for edge in self.edges:
                    glVertex3f(vertices[edge[0]])
                    glVertex3f(vertices[edge[1]])

                glEnd(GL_LINES)

            else:  # Assume here that the type is correctly specified, thus colors are a sequence

                glBegin(GL_LINES)
                for edge, color in zip(self.edges, colors):

                    color.set()

                    glVertex3f(vertices[edge[0]])
                    glVertex3f(vertices[edge[1]])

                glEnd(GL_LINES)