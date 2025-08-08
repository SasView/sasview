import numpy as np

from sas.qtgui.GL.color import ColorSpecification
from sas.qtgui.GL.models import FullModel


class Cylinder(FullModel):
    """ Graphics primitive: Radius 1, Height 2 cone "centred" at (0,0,0)"""

    @staticmethod
    def cylinder_vertices(n) -> list[tuple[float, float, float]]:
        """ Helper function: Vertices of the cylinder primitive"""
        return [(0.0, 0.0, 1.0)] + \
               [ (np.sin(angle), np.cos(angle), 1.0) for angle in 2*np.pi*np.arange(0, n)/n] + \
               [(0.0, 0.0, -1.0)] + \
               [ (np.sin(angle), np.cos(angle), -1.0) for angle in 2*np.pi*np.arange(0, n)/n]


    @staticmethod
    def cylinder_edges(n):
        """ Helper function: Edges of the cylinder primitive"""
        return [(i+1, (i+1)%n+1) for i in range(n)] + \
               [(i + n + 2, (i+1)%n + n + 2) for i in range(n)] + \
               [(i+1, i + n + 2) for i in range(n)]

    @staticmethod
    def cylinder_face_triangles(n, offset) -> list[tuple[int, int, int]]:
        """ Helper function: Faces of the ends of cylinder primitive"""
        return [(i+offset + 1, (i + 1) % n + offset + 1, offset) for i in range(n)]

    @staticmethod
    def cylinder_side_triangles(n) -> list[tuple[int, int, int]]:
        """ Helper function: Faces of the sides of the cylinder primitive"""
        sides = []
        for i in range(n):
            # Squares into triangles

            # Bottom left, top right, bottom right
            sides.append((i + 1, (i + 1) % n + n + 2, (i + 1) % n + 1))
            # Top right, bottom left, top left
            sides.append(((i + 1) % n + n + 2, i + 1, i + n + 2))
        return sides

    @staticmethod
    def cylinder_triangles(n) -> list[list[tuple[int, int, int]]]:
        """ Helper function: All faces of the cylinder primitive"""
        return [
            Cylinder.cylinder_face_triangles(n, 0),
            Cylinder.cylinder_side_triangles(n),
            [tuple(reversed(x)) for x in Cylinder.cylinder_face_triangles(n, n+1)]
        ]

    def __init__(self,
                 n: int = 20,
                 colors: ColorSpecification | None=None,
                 edge_colors: ColorSpecification | None=None):

        super().__init__(
            vertices=Cylinder.cylinder_vertices(n),
            edges=Cylinder.cylinder_edges(n),
            triangle_meshes=Cylinder.cylinder_triangles(n),
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
