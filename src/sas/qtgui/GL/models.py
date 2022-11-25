
"""
3D Model classes
"""


from typing import Sequence, Tuple, Union, Optional

import numpy as np

from OpenGL.GL import *

from sas.qtgui.GL.renderable import Renderable
from sas.qtgui.GL.color import Color

def color_sequence_to_array(colors: Union[Sequence[Color], Color]):
    if isinstance(colors, Color):
        return None
    else:
        return np.array([color.to_array for color in colors], dtype=float)


class ModelBase(Renderable):
    """ Base class for all models"""

    def __init__(self, vertices: Sequence[Tuple[float, float, float]]):
        self._vertices = vertices
        self._vertex_array = np.array(vertices, dtype=float)

    # Vertices set and got as sequences of tuples, but a list of
    @property
    def vertices(self):
        return self._vertices

    @vertices.setter
    def vertices(self, new_vertices):
        self._vertices = new_vertices
        self._vertex_array = np.array(new_vertices, dtype=float)



class SolidModel(ModelBase):
    """ Base class for the solid models"""
    def __init__(self,
                 vertices: Sequence[Tuple[float, float, float]],
                 triangle_meshes: Sequence[Sequence[Tuple[int, int, int]]]):

        ModelBase.__init__(self, vertices)

        self.solid_render_enabled = False

        self._triangle_meshes = triangle_meshes
        self._triangle_mesh_arrays = [np.array(x) for x in triangle_meshes]

    @property
    def triangle_meshes(self) -> Sequence[Sequence[Tuple[int, int, int]]]:
        return self._triangle_meshes

    @triangle_meshes.setter
    def triangle_meshes(self, new_triangle_meshes: Sequence[Sequence[int]]):
        self._triangle_meshes = new_triangle_meshes
        self._triangle_mesh_arrays = [np.array(x) for x in new_triangle_meshes]


class SolidVertexModel(SolidModel):
    def __init__(self,
                 vertices: Sequence[Tuple[float, float, float]],
                 triangle_meshes: Sequence[Sequence[Tuple[int, int, int]]],
                 colors: Optional[Union[Sequence[Color], Color]],
                 color_by_mesh: bool = False):

        """


        :vertices: Sequence[Tuple[float, float, float]], vertices of the model
        :triangle_meshes: Sequence[Sequence[Tuple[int, int, int]]], sequence of triangle
                          meshes indices making up the shape
        :colors: Optional[Union[Sequence[Color], Color]], single color for shape, or array with a colour for
                 each mesh or vertex (color_by_mesh selects which of these it is)
        :color_by_mesh: bool = False, Colour in each mesh with a colour specified by colours

        """

        super().__init__(vertices, triangle_meshes)

        self.color_by_mesh = color_by_mesh

        self._vertex_colors = colors
        self._vertex_color_array = None if isinstance(colors, Color) or color_by_mesh else np.array([color.to_array() for color in colors], dtype=float)

        self.solid_render_enabled = self.colors is not None

    @property
    def colors(self):
        return self._vertex_colors

    @colors.setter
    def colors(self, new_vertex_colors):
        self.colors = new_vertex_colors
        self._vertex_color_array = None if isinstance(new_vertex_colors, Color) else np.array([color.to_array() for color in new_vertex_colors], dtype=float)
        self.solid_render_enabled = self.colors is not None

    def render_solid(self):
        if self.solid_render_enabled:

            if isinstance(self._vertex_colors, Color):

                glEnableClientState(GL_VERTEX_ARRAY)
                self._vertex_colors.set()

                glVertexPointerf(self._vertex_array)

                for triangle_mesh in self._triangle_mesh_arrays:
                    glDrawElementsui(GL_TRIANGLES, triangle_mesh)


                glDisableClientState(GL_VERTEX_ARRAY)


            else:

                if self.color_by_mesh:

                    glEnableClientState(GL_VERTEX_ARRAY)

                    glVertexPointerf(self._vertex_array)

                    for triangle_mesh, color in zip(self._triangle_mesh_arrays, self.colors):
                        color.set()
                        glDrawElementsui(GL_TRIANGLES, triangle_mesh)

                    glDisableClientState(GL_VERTEX_ARRAY)

                else:
                    glEnableClientState(GL_VERTEX_ARRAY)
                    glEnableClientState(GL_COLOR_ARRAY)

                    glVertexPointerf(self._vertex_array)
                    glColorPointerf(self._vertex_color_array)

                    for triangle_mesh in self._triangle_mesh_arrays:
                        glDrawElementsui(GL_TRIANGLES, triangle_mesh)

                    glDisableClientState(GL_COLOR_ARRAY)
                    glDisableClientState(GL_VERTEX_ARRAY)


class WireModel(ModelBase):

    def __init__(self,
                 vertices: Sequence[Tuple[float, float, float]],
                 edges: Sequence[Tuple[int, int]],
                 edge_colors: Optional[Union[Sequence[Color], Color]]):

        """ Wireframe Model

        :vertices: Sequence[Tuple[float, float, float]], vertices of the model
        :edges: Sequence[Tuple[int, int]], indices of the points making up the edges
        :edge_colors: Optional[Union[Sequence[Color], Color]], color of the individual edges or a single color for them all
        """


        super().__init__(vertices)

        self.wireframe_render_enabled = False
        self.edges = edges
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

            else:  # Assume here that the correct type is supplied, thus colors are a sequence

                glBegin(GL_LINES)
                for edge, color in zip(self.edges, colors):

                    color.set()

                    glVertex3f(*vertices[edge[0]])
                    glVertex3f(*vertices[edge[1]])

                glEnd()


class FullModel(SolidVertexModel, WireModel):
    """ Model that has both wireframe and solid, vertex coloured rendering enabled,

    See SolidVertexModel and WireModel
    """
    def __init__(self,
                 vertices: Sequence[Tuple[float, float, float]],
                 edges: Sequence[Tuple[int, int]],
                 triangle_meshes: Sequence[Sequence[Tuple[int, int, int]]],
                 edge_colors: Optional[Union[Sequence[Color], Color]],
                 vertex_colors: Optional[Union[Sequence[Color], Color]],
                 color_by_mesh: bool = False):



        SolidVertexModel.__init__(self,
                                  vertices=vertices,
                                  triangle_meshes=triangle_meshes,
                                  colors=vertex_colors,
                                  color_by_mesh=color_by_mesh)
        WireModel.__init__(self,
                           vertices=vertices,
                           edges=edges,
                           edge_colors=edge_colors)

