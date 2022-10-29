from typing import List

import numpy as np

import pyqtgraph.opengl as gl
from pyqtgraph.Transform3D import Transform3D
from OpenGL.GL import *

from sasmodels.jitter import Rx, Ry, Rz


class OrientationViewerGraphics:

    @staticmethod
    def hypercube(n):
        """ Coordinates of a hypercube in with 'binary' ordering"""
        if n <= 0:
            return [[]]
        else:
            hypersquare = OrientationViewerGraphics.hypercube(n-1)
            return [[0] + vert for vert in hypersquare] + [[1] + vert for vert in hypersquare]


    @staticmethod
    def create_cube(alpha=1.0):
        """ Mesh for the main cuboid"""
        # Sorry
        vertices = OrientationViewerGraphics.hypercube(3)

        faces_and_colors = []

        for fixed_dim in range(3):
            for zero_one in range(2):
                this_face = [(ind, v) for ind, v in enumerate(vertices) if v[fixed_dim] == zero_one]

                def sort_key(x):
                    _, v = x
                    other_dims = v[:fixed_dim] + v[fixed_dim+1:]
                    return (v[fixed_dim] - 0.5)*np.arctan2(other_dims[0]-0.5, other_dims[1]-0.5)

                this_face = sorted(this_face, key=sort_key)

                color = [255,255,255,255] #[0.6,0.6,0.6,alpha]
                color[fixed_dim]=0.4

                # faces_and_colors.append([[this_face[x][0] for x in range(4)], color])

                faces_and_colors.append(([this_face[x][0] for x in (0,1,2)], color))
                faces_and_colors.append(([this_face[x][0] for x in (2,3,0)], color))

        vertices = np.array(vertices, dtype=float) - 0.5
        faces = np.array([face for face, _ in faces_and_colors])
        colors = np.array([color for _, color in faces_and_colors])

        return gl.GLMeshItem(vertexes=vertices, faces=faces, faceColors=colors,
                             drawEdges=False, edgeColor=(0, 0, 0, 1), smooth=False)

    @staticmethod
    def create_arrow(n: int = 30, tail_length=10, tail_width=0.6):
        """ Mesh for an arrow """
        # Thanks, I hate it.

        # top and tail
        points = [[0, 0, 1], [0, 0, -tail_length]]
        faces = []
        colors = []

        # widest ring
        for angle in 2 * np.pi * np.arange(0, n) / n:
            points.append([np.sin(angle), np.cos(angle), 0])

        # middle ring
        for angle in 2 * np.pi * np.arange(0, n) / n:
            points.append([tail_width*np.sin(angle), tail_width*np.cos(angle), 0])

        # bottom ring
        for angle in 2 * np.pi * np.arange(0, n) / n:
            points.append([tail_width*np.sin(angle), tail_width*np.cos(angle), -tail_length])

        for i in range(n):
            # laterial indices
            j = (i+1) % n

            # Pointy bit
            faces.append([i + 2, j+2 + 2, 0])

            # # Top ring
            faces.append([i + n + 2, j + n + 2, j + 2])
            faces.append([i + n + 2, i + 2, j + 2])

            # Cylinder sides
            faces.append([i + 2 * n + 2, j + 2 * n + 2, j + n + 2])
            faces.append([i + 2 * n + 2, i + n + 2, j + n + 2])

            # Cylinder base
            faces.append([i+2*n + 2, j + 2 * n + 2, 1])

        for i in range(6*n):
            colors.append([0.6] * 3 + [1])

        points = np.array(points) - np.array([0,0,-0.5*(tail_length-1)])
        faces = np.array(faces)
        colors = np.array(colors)

        return gl.GLMeshItem(vertexes=points, faces=faces, faceColors=colors,
                             drawEdges=False, edgeColor=(0, 0, 0, 1), smooth=True)

    @staticmethod
    def createCubeTransform(theta_deg: float, phi_deg: float, psi_deg: float, scaling: List[float]) -> Transform3D:

        # Get rotation matrix
        r_mat = Rz(phi_deg)@Ry(theta_deg)@Rz(psi_deg)@np.diag(scaling)

        # Get the 4x4 transformation matrix, by (1) padding by zeros (2) setting the corner element to 1
        trans_mat = np.pad(r_mat, ((0, 1), (0, 1)))
        trans_mat[-1, -1] = 1
        trans_mat[2, -1] = 2

        return Transform3D(trans_mat)