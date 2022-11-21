from typing import Optional, Tuple
import numpy as np

from matplotlib import cm as ColorMap

from Models import FullVertexModel


class Surface(FullVertexModel):

    """ Surface plot


    x_values: 1D array of x values
    y_values: 1D array of y values
    z_data: 2D array of z values
    colormap: Optional colour map

    """

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

    def __init__(self,
                 x_values: np.ndarray,
                 y_values: np.ndarray,
                 z_data: np.ndarray,
                 colormap: Optional[ColorMap]=None):


        self.x_data, self.y_data = np.meshgrid(x_values, y_values)
        self.z_data = z_data

        super().__init__(
            vertices=Cube.cube_vertices,
            edges=self.calculate_edge_indices(len(x_values), len(y_values)),
            triangle_meshes=Cube.cube_triangles,
            edge_colors=edge_colors,
            vertex_colors=self._get_colors(z_data, colormap))

    def _get_colors(self, z_values, colormap) -> Sequence[Color]:
        return []

    def set_z_data(self, z_data):
        pass