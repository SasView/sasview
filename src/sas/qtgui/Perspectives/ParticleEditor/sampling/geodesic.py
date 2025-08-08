from collections import defaultdict

import numpy as np
from scipy.spatial import ConvexHull

_ico_ring_h = np.sqrt(1 / 5)
_ico_ring_r = np.sqrt(4 / 5)

class Geodesic:
    """ Points arranged pretty uniformly and regularly on a sphere"""

    #
    # Need to define an icosahedron, upon which everything else is based
    #

    _base_vertices = \
        [(0.0, 0.0, 1.0)] + \
        [(_ico_ring_r * np.cos(angle), _ico_ring_r * np.sin(angle), _ico_ring_h) for angle in
         2 * np.pi * np.arange(5) / 5] + \
        [(_ico_ring_r * np.cos(angle), _ico_ring_r * np.sin(angle), -_ico_ring_h) for angle in
         2 * np.pi * (np.arange(5) + 0.5) / 5] + \
        [(0.0, 0.0, -1.0)]

    _base_edges = [
        (0, 1),  # Top converging
        (0, 2),
        (0, 3),
        (0, 4),
        (0, 5),
        (1, 2),  # Top radial
        (2, 3),
        (3, 4),
        (4, 5),
        (5, 1),  # Middle diagonals, advanced
        (1, 6),
        (2, 7),
        (3, 8),
        (4, 9),
        (5, 10),
        (1, 10),  # Middle diagonals, delayed
        (2, 6),
        (3, 7),
        (4, 8),
        (5, 9),
        (6, 7),  # Bottom radial
        (7, 8),
        (8, 9),
        (9, 10),
        (10, 6),
        (6, 11),  # Bottom converging
        (7, 11),
        (8, 11),
        (9, 11),
        (10, 11),
    ]

    _base_triangles = [
        (0, 1, 2),  # Top cap
        (0, 2, 3),
        (0, 3, 4),
        (0, 4, 5),
        (0, 5, 1),
        (2, 1, 6),  # Top middle ring
        (3, 2, 7),
        (4, 3, 8),
        (5, 4, 9),
        (1, 5, 10),
        (6, 10, 1),  # Bottom middle ring
        (7, 6, 2),
        (8, 7, 3),
        (9, 8, 4),
        (10, 9, 5),
        (6, 7, 11),  # Bottom cap
        (7, 8, 11),
        (8, 9, 11),
        (9, 10, 11),
        (10, 6, 11)
    ]

    _cache = {}


    @staticmethod
    def points_for_division_amount(n_divisions):
        """ Get the number of points on the sphere for a given number of geodesic divisions
        by which I mean how many sections is each edge of the initial icosahedron split into
        (not how many times it is divided in half, which might be what you think given some other
        geodesic generation methods)

        Icosahedron counts as 1 division

        """

        return 10*n_divisions*n_divisions + 2



    @staticmethod
    def minimal_divisions_for_points(n_points):
        """ What division number should I use if I want at least n_points points on my geodesic

        rounded (ciel) inverse of points_for_division_amount
        """

        n_ish = np.sqrt((n_points - 2)/10)

        return int(max([1.0, np.ceil(n_ish)]))

    @staticmethod
    def by_point_count(self, n_points) -> tuple[np.ndarray, np.ndarray]:
        """ Get point sample on a unit geodesic sphere, *at least* n_points will be returned

        Weights of each point are calculated by fractional spherical area of dual polyhedron, and total weight = 4pi
        """

        return self.by_divisions(self.minimal_divisions_for_points(n_points))

    @staticmethod
    def by_divisions(n_divisions) -> tuple[np.ndarray, np.ndarray]:

        """ Get point sample on a unit geodesic sphere, points are creating by dividing each
        face of an icosahedron into smaller triangles so that each edge is split into n_divisions pieces

        Weights of each point are calculated by fractional spherical area of dual polyhedron, and total weight = 4pi
        """

        # Check cache for pre-existing data
        if n_divisions in Geodesic._cache:
            return Geodesic._cache[n_divisions]


        #
        # Main bit: We have to treat faces, edges and vertices individually to avoid duplicate points
        #

        # Original vertices will become new vertices
        points = [np.array(p) for p in Geodesic._base_vertices]

        # Iterate over edges
        for i, j in Geodesic._base_edges:
            p1 = np.array(Geodesic._base_vertices[i])
            p2 = np.array(Geodesic._base_vertices[j])

            delta = (p2 - p1) / n_divisions

            for a in range(1, n_divisions):
                new_point = p1 + a*delta
                new_point /= np.sqrt(np.sum(new_point ** 2))

                points.append(new_point)


        # Iterate over faces need to, and add divsions
        for i, j, k in Geodesic._base_triangles:
            p1 = np.array(Geodesic._base_vertices[i])
            p2 = np.array(Geodesic._base_vertices[j])
            p3 = np.array(Geodesic._base_vertices[k])

            d1 = p1 - p3
            d2 = p2 - p3

            # Division of the shape, just fill in the inside
            for a_plus_b in range(1, n_divisions):
                for a in range(1, a_plus_b):

                    b = a_plus_b - a

                    new_point = p3 + d1*(a / n_divisions) + d2*(b / n_divisions)
                    new_point /= np.sqrt(np.sum(new_point**2))

                    points.append(new_point)

        points = np.array(points)

        weights = Geodesic._calculate_weights(points)


        # Cache the data
        Geodesic._cache[n_divisions] = (points, weights)

        return points, weights

    @staticmethod
    def _calculate_weights(points) -> np.ndarray:
        """
        Calculate the anular area associated with each point
        """

        z = np.array([0.0, 0.0, 1.0]) # Used in area calculation

        # Calculate convex hull to get the triangles, because it's easy
        hull = ConvexHull(points)

        centroids = []

        # Dictionary to track which centroids are associated with each point
        point_to_centroid = defaultdict(list)

        # calculate centroid, lets not check for correct hull data, as nothing is user
        # facing, and has a reliably triangular and convex input
        for centroid_index, simplex in enumerate(hull.simplices):
            p1 = points[simplex[0], :]
            p2 = points[simplex[1], :]
            p3 = points[simplex[2], :]

            centroid = p1 + p2 + p3
            centroid /= np.sqrt(np.sum(centroid**2))

            centroids.append(centroid)

            point_to_centroid[simplex[0]].append(centroid_index)
            point_to_centroid[simplex[1]].append(centroid_index)
            point_to_centroid[simplex[2]].append(centroid_index)

        # Find the area of the spherical polygon associated with each point
        # 1) get the associated centroids
        # 2) order them to allow the identification of triangles
        # 3) for each triangle [point, centroid_i, centroid_i+1], calculate the area

        areas = []
        for point_index, point in enumerate(points):

            # 1) Get centroids
            centroid_indices = point_to_centroid[point_index]
            centroid_points = [centroids[i] for i in centroid_indices]

            n_centroids = len(centroid_indices)


            # 2) Order them around the point
            rotation = Geodesic._rotation_matrix_to_z_vector(point)

            centroid_points = [np.matmul(rotation, centroid) for centroid in centroid_points]

            centroid_points = sorted(centroid_points, key=lambda x: np.arctan2(x[0], x[1])) # Any angle in x,y will do


            # 3) Calculate areas
            area = 0
            for i in range(n_centroids):
                p1 = centroid_points[i]
                p2 = centroid_points[(i+1)%n_centroids]

                area += 2 * np.abs(
                    np.arctan2(
                        np.cross(p1, p2)[2],
                        1 + np.dot(p1, p2) + p1[2] + p2[2]))

            areas.append(area)

        return np.array(areas)


    @staticmethod
    def _rotation_matrix_to_z_vector(point_on_sphere: np.ndarray) -> np.ndarray:
        """ Calculate *a* rotation matrix that moves a given point onto the z axis"""

        # Find the rotation around the x axis
        y = point_on_sphere[1]
        z = point_on_sphere[2]

        x_angle = np.arctan2(y, z)

        c = np.cos(x_angle)
        s = np.sin(x_angle)

        m1 = np.array([
            [1, 0, 0],
            [0, c, -s],
            [0, s, c]])

        # apply rotation to point
        new_point = np.matmul(m1, point_on_sphere)

        # find the rotation about the y axis for this new point
        x = new_point[0]
        z = new_point[2]

        y_angle = np.arctan2(x, z)

        c = np.cos(y_angle)
        s = np.sin(y_angle)

        m2 = np.array([
            [c, 0, -s],
            [0, 1, 0],
            [s, 0, c]])

        return np.matmul(m2, m1)


class GeodesicDivisions:
    """ Use this so that the GUI program gives geodesic divisions box, rather than a plain int one"""


if __name__ == "__main__":

    """ Shows a point sample"""

    import matplotlib.pyplot as plt

    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')

    points, weights = Geodesic.by_divisions(4)
    ax.scatter(points[:,0], points[:,1], points[:,2])

    ax.set_xlim3d([-1.1, 1.1])
    ax.set_ylim3d([-1.1, 1.1])
    ax.set_zlim3d([-1.1, 1.1])

    ax.set_box_aspect([1,1,1])
    ax.set_proj_type('ortho')

    plt.show()
