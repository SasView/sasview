from typing import Optional, Union, Sequence, List, Tuple

import numpy as np

from sas.qtgui.GL.models import FullVertexModel, WireModel
from sas.qtgui.GL.color import Color


class Cone(FullVertexModel):
    """ Graphics primitive: Radius 1, Height 2 cone "centred" at (0,0,0)"""

    @staticmethod
    def cone_vertices(n) -> List[Tuple[float, float, float]]:
        return [(0.0, 0.0, 1.0)] + [
            (np.sin(angle), np.cos(angle), -1.0)
            for angle in 2*np.pi*np.arange(0, n)/n] + [(0.0, 0.0, -1.0)]

    @staticmethod
    def cone_edges(n):
        return [(0, i+1) for i in range(n)] + [(i+1, (i+1)%n+1) for i in range(n)]

    @staticmethod
    def cone_tip_triangles(n) -> List[Tuple[int, int, int]]:
        return [(0, i + 1, (i + 1) % n + 1) for i in range(n)]

    @staticmethod
    def cone_base_triangles(n) -> List[Tuple[int, int, int]]:
        return [((i + 1) % n + 1, i + 1, n+1) for i in range(n)]

    @staticmethod
    def cone_triangles(n) -> List[List[Tuple[int, int, int]]]:
        return [Cone.cone_base_triangles(n),
                Cone.cone_tip_triangles(n)]

    def __init__(self,
                 n: int = 20,
                 vertex_colors: Optional[Union[Sequence[Color], Color]]=None,
                 edge_colors: Optional[Union[Sequence[Color],Color]]=None):

        super().__init__(
            vertices=Cone.cone_vertices(n),
            edges=Cone.cone_edges(n),
            triangle_meshes=Cone.cone_triangles(n),
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
