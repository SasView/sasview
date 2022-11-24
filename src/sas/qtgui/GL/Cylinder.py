from typing import Optional, Union, Sequence, List, Tuple

import numpy as np

from sas.qtgui.GL.Models import FullVertexModel, WireModel
from sas.qtgui.GL.Color import Color


class Cylinder(FullVertexModel):
    """ Graphics primitive: Radius 1, Height 2 cone "centred" at (0,0,0)"""

    @staticmethod
    def cylinder_vertices(n) -> List[Tuple[float, float, float]]:
        return [(0.0, 0.0, 1.0)] + \
               [ (np.sin(angle), np.cos(angle), 1.0) for angle in 2*np.pi*np.arange(0, n)/n] + \
               [(0.0, 0.0, -1.0)] + \
               [ (np.sin(angle), np.cos(angle), -1.0) for angle in 2*np.pi*np.arange(0, n)/n]


    @staticmethod
    def cylinder_edges(n):
        return [(i+1, (i+1)%n+1) for i in range(n)] + \
               [(i + n + 2, (i+1)%n + n + 2) for i in range(n)] + \
               [(i+1, i + n + 2) for i in range(n)]

    @staticmethod
    def cylinder_face_triangles(n, offset) -> List[Tuple[int, int, int]]:
        return [(i+offset + 1, (i + 1) % n + offset + 1, offset) for i in range(n)]

    @staticmethod
    def cylinder_side_triangles(n):
        pass

    @staticmethod
    def cylinder_triangles(n) -> List[List[Tuple[int, int, int]]]:
        return [
            Cylinder.cylinder_face_triangles(n, 0),
            [tuple(reversed(x)) for x in Cylinder.cylinder_face_triangles(n, n+1)]
        ]

    def __init__(self,
                 n: int = 20,
                 vertex_colors: Optional[Union[Sequence[Color], Color]]=None,
                 edge_colors: Optional[Union[Sequence[Color],Color]]=None):

        super().__init__(
            vertices=Cylinder.cylinder_vertices(n),
            edges=Cylinder.cylinder_edges(n),
            triangle_meshes=Cylinder.cylinder_triangles(n),
            edge_colors=edge_colors,
            vertex_colors=vertex_colors)

        if edge_colors is None:
            self.wireframe_render_enabled = False
            self.edge_colors = []
        else:
            self.wireframe_render_enabled = True
            self.edge_colors = edge_colors

        if vertex_colors is None:
            self.solid_render_enabled = False
            self.face_colors = []
        else:
            self.solid_render_enabled = True
            self.face_colors = vertex_colors
