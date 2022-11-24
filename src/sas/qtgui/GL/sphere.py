from typing import Optional, Union, Sequence

from sas.qtgui.GL.color import Color


class UVSphere():

    def __init__(self,
                 n_horizontal: int = 5,
                 n_segments: int = 5,
                 face_colors: Optional[Union[Sequence[Color],Color]]=None,
                 edge_colors: Optional[Union[Sequence[Color],Color]]=None):

        super().__init__(
            vertices=Cube.cube_vertices,
            edges=Cube.cube_edges,
            triangle_meshes=Cube.cube_triangles,
            edge_colors=edge_colors,
            vertex_colors=face_colors)

        self.vertices = Cube.cube_vertices
        self.edges = Cube.cube_edges

        if edge_colors is None:
            self.wireframe_render_enabled = False
            self.edge_colors = []
        else:
            self.wireframe_render_enabled = True
            self.edge_colors = edge_colors

        if face_colors is None:
            self.solid_render_enabled = False
            self.face_colors = []
        else:
            self.solid_render_enabled = True
            self.face_colors = face_colors
