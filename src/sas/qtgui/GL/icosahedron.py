
import numpy as np

from sas.qtgui.GL.color import ColorSpecification
from sas.qtgui.GL.models import FullModel

ico_ring_h = np.sqrt(1/5)
ico_ring_r = np.sqrt(4/5)


class Icosahedron(FullModel):
    """ Icosahedron centred at 0,0,0"""



    ico_vertices = \
        [(0.0, 0.0, 1.0)] + \
        [(ico_ring_r * np.cos(angle), ico_ring_r * np.sin(angle), ico_ring_h) for angle in 2*np.pi*np.arange(5)/5] + \
        [(ico_ring_r * np.cos(angle), ico_ring_r * np.sin(angle), -ico_ring_h) for angle in 2*np.pi*(np.arange(5)+0.5)/5] + \
        [(0.0, 0.0, -1.0)]

    ico_edges = [
        (0, 1), # Top converging
        (0, 2),
        (0, 3),
        (0, 4),
        (0, 5),
        (1, 2), # Top radial
        (2, 3),
        (3, 4),
        (4, 5),
        (5, 1), # Middle diagonals, advanced
        (1, 6),
        (2, 7),
        (3, 8),
        (4, 9),
        (5, 10),
        (1, 10), # Middle diagonals, delayed
        (2, 6),
        (3, 7),
        (4, 8),
        (5, 9),
        (6, 7), # Bottom radial
        (7, 8),
        (8, 9),
        (9, 10),
        (10, 6),
        (6, 11), # Bottom converging
        (7, 11),
        (8, 11),
        (9, 11),
        (10, 11),
    ]

    ico_triangles = [[
        (0, 1, 2), # Top cap
        (0, 2, 3),
        (0, 3, 4),
        (0, 4, 5),
        (0, 5, 1),
        (2, 1, 6), # Top middle ring
        (3, 2, 7),
        (4, 3, 8),
        (5, 4, 9),
        (1, 5, 10),
        (6, 10, 1), # Bottom middle ring
        (7, 6, 2),
        (8, 7, 3),
        (9, 8, 4),
        (10, 9, 5),
        (6, 7, 11), # Bottom cap
        (7, 8, 11),
        (8, 9, 11),
        (9, 10, 11),
        (10, 6, 11)
    ]]

    def __init__(self,
                 colors: ColorSpecification | None=None,
                 edge_colors: ColorSpecification | None=None):

        super().__init__(
            vertices=Icosahedron.ico_vertices,
            edges=Icosahedron.ico_edges,
            triangle_meshes=Icosahedron.ico_triangles,
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
