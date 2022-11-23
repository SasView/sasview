from typing import Optional, Tuple
import numpy as np

from matplotlib.colors import Colormap

from sas.qtgui.GL.Models import FullVertexModel, WireModel
from sas.qtgui.GL.Color import Color


class Surface(FullVertexModel):


    @staticmethod
    def calculate_edge_indices(nx, ny):
        all_edges = []
        for i in range(nx-1):
            for j in range(ny):
                all_edges.append((j*nx + i, j*nx + i + 1))

        for i in range(nx):
            for j in range(ny-1):
                all_edges.append((j*nx + i, (j+1)*nx + i))

        return all_edges

    @staticmethod
    def calculate_triangles(nx, ny):
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
                 colormap: Optional[Colormap]=None):

        """ Surface plot


        :param x_values: 1D array of x values
        :param y_values: 1D array of y values
        :param z_data: 2D array of z values
        :param colormap: Optional[Colormap] colour map

        """

        if colormap is None:
            pass

        self.x_data, self.y_data = np.meshgrid(x_values, y_values)
        self.z_data = z_data

        self.n_x = len(x_values)
        self.n_y = len(y_values)

        super().__init__(
            vertices=[(float(x), float(y), float(z)) for x, y, z in zip(np.nditer(self.x_data), np.nditer(self.y_data), np.nditer(self.z_data))],
            edges=Surface.calculate_edge_indices(self.n_x, self.n_y),
            triangle_meshes=[Surface.calculate_triangles(self.n_x, self.n_y)],
            edge_colors=Color(1.0,1.0,1.0),
            vertex_colors=Color(0.0,0.4,0.0)
            )

        self.wireframe_render_enabled = True
        self.solid_render_enabled = True


    # def _get_colors(self, z_values, colormap) -> Sequence[Color]:
    #     return []
    #
    # def set_z_data(self, z_data):
    #     pass