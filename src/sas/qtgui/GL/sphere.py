import numpy as np

from sas.qtgui.GL.color import ColorSpecification
from sas.qtgui.GL.models import FullModel


class Sphere(FullModel):
    @staticmethod
    def sphere_vertices(n_horizontal, n_segments):
        """ Helper function: Vertices of the UV sphere primitive"""
        vertices = [(0.0, 0.0, 1.0)]

        for theta in (np.pi/n_horizontal)*np.arange(0.5, n_horizontal):
            for phi in (2*np.pi/n_segments)*np.arange(n_segments):
                sin_theta = np.sin(theta)
                x = sin_theta * np.cos(phi)
                y = sin_theta * np.sin(phi)
                z = np.cos(theta)
                vertices.append((x,y,z))

        vertices.append((0.0, 0.0, -1.0))

        return vertices

    @staticmethod
    def sphere_edges(n_horizontal, n_segments, grid_gap):

        """ Helper function: Edges of the UV sphere primitive"""
        edges = []

        # Bands
        for i in range(0, n_horizontal, grid_gap):
            for j in range(n_segments):
                edges.append((i*n_segments + j + 1, i*n_segments + (j+1)%n_segments + 1))

        # Vertical lines
        for i in range(n_horizontal-1):
            for j in range(0, n_segments, grid_gap):
                edges.append((i*n_segments + j + 1, (i+1)*n_segments + j + 1))

        return edges

    @staticmethod
    def sphere_triangles(n_horizontal, n_segments):
        """ Helper function: Triangles of the UV sphere primitive"""
        triangles = []
        last_index = n_horizontal*n_segments + 1

        # Top cap
        for j in range(n_segments):
            triangles.append((j+1, (j+1)%n_segments + 1, 0))

        # Mid bands
        for i in range(n_horizontal-1):
            for j in range(n_segments):
                triangles.append((i*n_segments + j + 1, (i+1)*n_segments + (j+1)%n_segments + 1, (i+1)*n_segments + j+1))
                triangles.append(((i+1)*n_segments + (j+1)%n_segments + 1, i*n_segments + j + 1, i*n_segments + (j+1)%n_segments + 1))

        # Bottom cap
        for j in range(n_segments):
            triangles.append(((n_horizontal-1)*n_segments + j + 1, (n_horizontal-1)*n_segments + (j + 1) % n_segments + 1, last_index))

        return [triangles]

    def __init__(self,
                 n_horizontal: int = 21,
                 n_segments: int = 28,
                 grid_gap: int = 1,
                 colors: ColorSpecification | None=None,
                 edge_colors: ColorSpecification | None=None):

        """

        UV Sphere Primitive

        :param n_horizontal: Number of horizontal bands
        :param n_segments: Number of segments (angular)
        :param grid_gap: Coarse grain the wireframe by skipping every 'grid_gap' coordinates
        :param colors: List of colours for each vertex, or a single color for all
        :param edge_colors: List of colours for each edge, or a single color for all

        Note: For aesthetically pleasing results with `grid_gap`, `n_segments` should be a multiple
        of `grid_gap`, and `n_horizontal - 1` should be too.

        Default parameters should work with a grid gap of 2 or 4.
        """
        if n_segments < 3:
            raise ValueError(f"Sphere must have at least 3 segments, got {n_segments}")

        if n_horizontal < 2:
            raise ValueError(f"Sphere must have at least 2 horizontal strips, got {n_horizontal}")

        super().__init__(
            vertices=Sphere.sphere_vertices(n_horizontal, n_segments),
            edges=Sphere.sphere_edges(n_horizontal, n_segments, grid_gap),
            triangle_meshes=Sphere.sphere_triangles(n_horizontal, n_segments),
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
