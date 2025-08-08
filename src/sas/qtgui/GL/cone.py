import numpy as np

from sas.qtgui.GL.color import ColorSpecification
from sas.qtgui.GL.models import FullModel


class Cone(FullModel):
    """ Graphics primitive: Radius 1, Height 2 cone "centred" at (0,0,0)"""

    @staticmethod
    def cone_vertices(n) -> list[tuple[float, float, float]]:
        """ Helper function: Vertices of the cone primitive"""
        return [(0.0, 0.0, 1.0)] + [
            (np.sin(angle), np.cos(angle), -1.0)
            for angle in 2*np.pi*np.arange(0, n)/n] + [(0.0, 0.0, -1.0)]

    @staticmethod
    def cone_edges(n):
        """ Helper function: Edges of the cone primitive"""
        return [(0, i+1) for i in range(n)] + [(i+1, (i+1)%n+1) for i in range(n)]

    @staticmethod
    def cone_tip_triangles(n) -> list[tuple[int, int, int]]:
        """ Helper function: Triangles in tip of the cone primitive"""
        return [(0, i + 1, (i + 1) % n + 1) for i in range(n)]

    @staticmethod
    def cone_base_triangles(n) -> list[tuple[int, int, int]]:
        """ Helper function: Triangles in base the cone primitive"""
        return [((i + 1) % n + 1, i + 1, n+1) for i in range(n)]

    @staticmethod
    def cone_triangles(n) -> list[list[tuple[int, int, int]]]:
        """ Helper function: The two separate meshes for triangles of the cone primitive"""
        return [Cone.cone_base_triangles(n),
                Cone.cone_tip_triangles(n)]

    def __init__(self,
                 n: int = 20,
                 colors: ColorSpecification | None=None,
                 edge_colors: ColorSpecification | None=None):

        super().__init__(
            vertices=Cone.cone_vertices(n),
            edges=Cone.cone_edges(n),
            triangle_meshes=Cone.cone_triangles(n),
            edge_colors=edge_colors,
            colors=colors)

        if edge_colors is None:
            self.wireframe_render_enabled = False
            self.edge_colors = []
        else:
            self.wireframe_render_enabled = True
            self.edge_colors = edge_colors

        if colors is None:
            self.solid_render_enabled = False
            self.face_colors = []
        else:
            self.solid_render_enabled = True
            self.face_colors = colors
