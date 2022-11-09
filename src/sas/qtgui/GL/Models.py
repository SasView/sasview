from typing import Sequence, Tuple, Union, Optional
from abc import abstractmethod

import numpy as np

from OpenGL.GL import *

from sas.qtgui.GL.Renderable import Renderable
from sas.qtgui.GL.Color import Color


class SolidModel(Renderable):
    """ Base class for the two solid models"""
    def __init__(self,
                 vertices: Sequence[Tuple[float, float, float]],
                 meshes: Sequence[Sequence[int]]):

        self.solid_render_enabled = False
        self.vertices = vertices
        self.meshes = meshes


class SolidVertexModel(SolidModel):
    def __init__(self,
                 vertices: Sequence[Tuple[float, float, float]],
                 meshes: Sequence[Sequence[int]],
                 vertex_colours: Optional[Union[Sequence[Color], Color]]):

        super().__init__(vertices, meshes)

        self.vertex_colours = vertex_colours

    def render_solid(self):
        pass


class SolidFaceModel(SolidModel):
    def __init__(self,
                 vertices: Sequence[Tuple[float, float, float]],
                 meshes: Sequence[Sequence[int]],
                 face_colours: Optional[Union[Sequence[Color], Color]]):

        super().__init__(vertices, meshes)

        self.face_colours = face_colours

    def render_solid(self):
        pass


class WireModel(Renderable):
    def __init__(self,
                 vertices: Sequence[Tuple[float, float, float]],
                 edges: Sequence[Tuple[int, int]],
                 edge_colors: Optional[Union[Sequence[Color], Color]]):

        self.wireframe_render_enabled = False
        self.edges = edges
        self.vertices = vertices
        self.edge_colors = edge_colors

    def render_wireframe(self):
        if self.wireframe_render_enabled:
            vertices = self.vertices
            colors = self.edge_colors

            if isinstance(colors, Color):

                glBegin(GL_LINES)
                colors.set()

                for edge in self.edges:
                    glVertex3f(*vertices[edge[0]])
                    glVertex3f(*vertices[edge[1]])

                glEnd()

            else:  # Assume here that the type is correctly specified, thus colors are a sequence

                glBegin(GL_LINES)
                for edge, color in zip(self.edges, colors):

                    color.set()

                    glVertex3f(*vertices[edge[0]])
                    glVertex3f(*vertices[edge[1]])

                glEnd()


class FullVertexModel(SolidVertexModel, WireModel):
    """ Model that has both wireframe and solid, vertex coloured rendering enabled"""
    def __init__(self,
                 vertices: Sequence[Tuple[float, float, float]],
                 edges: Sequence[Tuple[int, int]],
                 meshes: Sequence[Sequence[int]],
                 edge_colors: Optional[Union[Sequence[Color], Color]],
                 vertex_colors: Optional[Union[Sequence[Color], Color]]):

        SolidVertexModel.__init__(self,
                                  vertices=vertices,
                                  meshes=meshes,
                                  vertex_colours=vertex_colors)
        WireModel.__init__(self,
                           vertices=vertices,
                           edges=edges,
                           edge_colors=edge_colors)


class FullFaceModel(SolidFaceModel, WireModel):
    """ Model that has both wireframe and solid, face coloured rendering enabled"""

    def __init__(self,
                 vertices: Sequence[Tuple[float, float, float]],
                 edges: Sequence[Tuple[int, int]],
                 meshes: Sequence[Sequence[int]],
                 edge_colors: Optional[Union[Sequence[Color], Color]],
                 face_colors: Optional[Union[Sequence[Color], Color]]):

        SolidFaceModel.__init__(self,
                                vertices=vertices,
                                meshes=meshes,
                                face_colours=face_colors)
        WireModel.__init__(self,
                           vertices=vertices,
                           edges=edges,
                           edge_colors=edge_colors)