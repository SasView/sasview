import logging

import numpy as np

from sas.qtgui.GL.color import ColorMap, uniform_coloring
from sas.qtgui.GL.models import FullModel

logger = logging.getLogger("GL.Surface")

class Surface(FullModel):


    @staticmethod
    def calculate_edge_indices(nx, ny, gap=1):
        """ Helper function to calculate the indices of the edges"""
        all_edges = []
        for i in range(nx-1):
            for j in range(0, ny, gap):
                all_edges.append((j*nx + i, j*nx + i + 1))

        for i in range(0, nx, gap):
            for j in range(ny-1):
                all_edges.append((j*nx + i, (j+1)*nx + i))

        return all_edges

    @staticmethod
    def calculate_triangles(nx, ny):
        """ Helper function to calculate the indices of the triangles in the mesh"""
        triangles = []
        for i in range(nx-1):
            for j in range(ny-1):
                triangles.append((j*nx + i, (j+1)*nx+(i+1), j*nx + (i + 1)))
                triangles.append((j*nx + i, (j+1)*nx + i, (j+1)*nx + (i+1)))
        return triangles

    def __init__(self,
                 x_values: np.ndarray,
                 y_values: np.ndarray,
                 z_data: np.ndarray,
                 colormap: str= ColorMap._default_colormap,
                 c_range: tuple[float, float] = (0, 1),
                 edge_skip: int=1):

        """ Surface plot


        :param x_values: 1D array of x values
        :param y_values: 1D array of y values
        :param z_data: 2D array of z values
        :param colormap: name of a matplotlib colour map
        :param c_range: min and max values for the color map to span
        :param edge_skip: skip every `edge_skip` index when drawing wireframe
        """


        self.x_data, self.y_data = np.meshgrid(x_values, y_values)
        self.z_data = z_data

        self.n_x = len(x_values)
        self.n_y = len(y_values)

        self.c_range = c_range
        self._colormap_name = colormap
        self._colormap = ColorMap(colormap, min_value=c_range[0], max_value=c_range[1])

        self.x_flat = self.x_data.flatten()
        self.y_flat = self.y_data.flatten()
        self.z_flat = self.z_data.flatten()

        verts = np.vstack((self.x_flat, self.y_flat, self.z_flat)).T

        super().__init__(
            vertices=verts,
            edges=Surface.calculate_edge_indices(self.n_x, self.n_y, edge_skip),
            triangle_meshes=[Surface.calculate_triangles(self.n_x, self.n_y)],
            edge_colors=uniform_coloring(1.0,1.0,1.0),
            colors=self._colormap.vertex_coloring(self.z_flat)
            )

        self.wireframe_render_enabled = True
        self.solid_render_enabled = True


    def set_z_data(self, z_data):

        "Set the z data on this surface plot"

        self.z_data = z_data
        self.z_flat = z_data.flatten()

        self.vertices = np.vstack((self.x_flat, self.y_flat, self.z_flat)).T
        self.colors = self._colormap.vertex_coloring(self.z_flat)

    @property
    def colormap(self) -> str:
        """ Name of the colormap"""
        return self._colormap_name

    @colormap.setter
    def colormap(self, colormap: str):
        if self._colormap_name != colormap:
            self._colormap = ColorMap(colormap, min_value=self.c_range[0], max_value=self.c_range[1])
            self.colors = self._colormap.vertex_coloring(self.z_flat)
            self._colormap_name = colormap
