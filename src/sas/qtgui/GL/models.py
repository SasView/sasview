
"""
3D Model classes
"""


from typing import Sequence, Union, Optional

import numpy as np

from OpenGL.GL import *

from sas.qtgui.GL.renderable import Renderable
from sas.qtgui.GL.color import ColorSpecification, ColorSpecificationMethod

VertexData = Union[Sequence[tuple[float, float, float]], np.ndarray]
EdgeData = Union[Sequence[tuple[int, int]], np.ndarray]
TriangleMeshData = Union[Sequence[tuple[int, int, int]], np.ndarray]


class ModelBase(Renderable):
    """ Base class for all models"""

    def __init__(self, vertices: VertexData):
        self._vertices = vertices
        self._vertex_array = np.array(vertices, dtype=float)

    # Vertices set and got as sequences of tuples, but a list of
    @property
    def vertices(self):
        return self._vertices

    @vertices.setter
    def vertices(self, new_vertices: VertexData):
        self._vertices = new_vertices
        self._vertex_array = np.array(new_vertices, dtype=float)



class SolidModel(ModelBase):
    """ Base class for the solid models"""
    def __init__(self,
                 vertices: VertexData,
                 triangle_meshes: Sequence[TriangleMeshData]):

        ModelBase.__init__(self, vertices)

        self.solid_render_enabled = False

        self._triangle_meshes = triangle_meshes
        self._triangle_mesh_arrays = [np.array(x) for x in triangle_meshes]

    @property
    def triangle_meshes(self) -> Sequence[TriangleMeshData]:
        return self._triangle_meshes

    @triangle_meshes.setter
    def triangle_meshes(self, new_triangle_meshes: Sequence[TriangleMeshData]):
        self._triangle_meshes = new_triangle_meshes
        self._triangle_mesh_arrays = [np.array(x) for x in new_triangle_meshes]


class SolidVertexModel(SolidModel):
    def __init__(self,
                 vertices: VertexData,
                 triangle_meshes: Sequence[TriangleMeshData],
                 colors: Optional[ColorSpecification]):

        """


        :vertices: Sequence[tuple[float, float, float]], vertices of the model
        :triangle_meshes: Sequence[Sequence[tuple[int, int, int]]], sequence of triangle
                          meshes indices making up the shape
        :colors: Optional[Union[Sequence[Color], Color]], single color for shape, or array with a colour for
                 each mesh or vertex (color_by_mesh selects which of these it is)
        :color_by_mesh: bool = False, Colour in each mesh with a colour specified by colours

        """

        super().__init__(vertices, triangle_meshes)

        self.colors = colors

        self.solid_render_enabled = self.colors is not None


    def render_solid(self):
        if self.solid_render_enabled:

            if self.colors.method == ColorSpecificationMethod.UNIFORM:

                glEnableClientState(GL_VERTEX_ARRAY)
                glColor4f(*self.colors.data)

                glVertexPointerf(self._vertex_array)

                for triangle_mesh in self._triangle_mesh_arrays:
                    glDrawElementsui(GL_TRIANGLES, triangle_mesh)

                glDisableClientState(GL_VERTEX_ARRAY)

            elif self.colors.method == ColorSpecificationMethod.BY_COMPONENT:

                glEnableClientState(GL_VERTEX_ARRAY)

                glVertexPointerf(self._vertex_array)

                for triangle_mesh, color in zip(self._triangle_mesh_arrays, self.colors.data):
                    glColor4f(*color)
                    glDrawElementsui(GL_TRIANGLES, triangle_mesh)

                glDisableClientState(GL_VERTEX_ARRAY)

            elif self.colors.method == ColorSpecificationMethod.BY_VERTEX:

                glEnableClientState(GL_VERTEX_ARRAY)
                glEnableClientState(GL_COLOR_ARRAY)

                glVertexPointerf(self._vertex_array)
                glColorPointerf(self.colors.data)

                for triangle_mesh in self._triangle_mesh_arrays:
                    glDrawElementsui(GL_TRIANGLES, triangle_mesh)

                glDisableClientState(GL_COLOR_ARRAY)
                glDisableClientState(GL_VERTEX_ARRAY)


class WireModel(ModelBase):

    def __init__(self,
                 vertices: VertexData,
                 edges: EdgeData,
                 edge_colors: Optional[ColorSpecification]):

        """ Wireframe Model

        :vertices: Sequence[tuple[float, float, float]], vertices of the model
        :edges: Sequence[tuple[int, int]], indices of the points making up the edges
        :edge_colors: Optional[Union[Sequence[Color], Color]], color of the individual edges or a single color for them all
        """


        super().__init__(vertices)

        self.wireframe_render_enabled = edge_colors is not None
        self.edges = edges
        self.edge_colors = edge_colors

    def render_wireframe(self):
        if self.wireframe_render_enabled:
            vertices = self.vertices
            colors = self.edge_colors

            if colors.method == ColorSpecificationMethod.UNIFORM:

                glBegin(GL_LINES)
                glColor4f(*colors.data)

                for edge in self.edges:
                    glVertex3f(*vertices[edge[0]])
                    glVertex3f(*vertices[edge[1]])

                glEnd()

            elif colors.method == ColorSpecificationMethod.BY_COMPONENT:

                glBegin(GL_LINES)
                for edge, color in zip(self.edges, colors.data):

                    glColor4f(*color)

                    glVertex3f(*vertices[edge[0]])
                    glVertex3f(*vertices[edge[1]])

                glEnd()

            elif colors.method == ColorSpecificationMethod.BY_VERTEX:
                raise NotImplementedError("Vertex coloring of wireframe is currently not supported")

            else:
                raise ValueError(f"Unknown coloring method: {ColorSpecification.method}")


class FullModel(SolidVertexModel, WireModel):
    """ Model that has both wireframe and solid, vertex coloured rendering enabled,

    See SolidVertexModel and WireModel
    """
    def __init__(self,
                 vertices: VertexData,
                 edges: EdgeData,
                 triangle_meshes: Sequence[TriangleMeshData],
                 edge_colors: Optional[ColorSpecification],
                 colors: Optional[ColorSpecification]):

        SolidVertexModel.__init__(self,
                                  vertices=vertices,
                                  triangle_meshes=triangle_meshes,
                                  colors=colors)
        WireModel.__init__(self,
                           vertices=vertices,
                           edges=edges,
                           edge_colors=edge_colors)

